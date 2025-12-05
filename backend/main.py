from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import auth
from database import engine, get_db, init_restaurant_config, wait_for_db
from schemas import (
    UserCreate,
    UserResponse,
    DishCreate,
    DishResponse,
    OrderItemCreate,
    OrderItemResponse,
    OrderCreate,
    OrderResponse,
    OrderUpdate,
    TableResponse,
    RestaurantConfigUpdate,
    UserLogin,
    PasswordChange,
)
from datetime import datetime
import uvicorn
import os
import random
import string
from redis_client import redis_client


app = FastAPI()


origins = [
    "http://localhost",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.on_event("startup")
def startup_event():
    # Сначала дожидаемся готовности базы данных
    if wait_for_db():
        try:
            print("Создание таблиц в базе данных...")
            models.Base.metadata.create_all(bind=engine)
            print("Таблицы успешно созданы")

            # Инициализируем конфигурацию ресторана (создаст 10 столов при первом запуске)
            print("Инициализация конфигурации ресторана...")
            init_restaurant_config()
            print("База данных успешно инициализирована")
        except Exception as e:
            print(f"Ошибка при создании/инициализации базы данных: {e}")
    else:
        print("Не удалось дождаться готовности базы данных при старте сервиса")

    # После БД проверяем доступность Redis
    if redis_client.is_available():
        print("✅ Redis доступен")
    else:
        print("⚠️ Redis недоступен, кеширование отключено")


@app.get("/cache-test")
def cache_test():
    """Пример кеширования: первый запрос записывает значение, второй берёт из Redis."""
    if not redis_client.is_available():
        return {"cached": False, "message": "Redis недоступен", "redis_available": False}
    
    try:
        cached = redis_client.client.get("greeting")
        if cached:
            return {"cached": True, "message": cached, "redis_available": True}
        
        redis_client.client.setex("greeting", 60, "Hello from Redis!")
        return {"cached": False, "message": "Hello from Redis!", "redis_available": True}
    except Exception as e:
        return {"cached": False, "message": f"Ошибка Redis: {e}", "redis_available": False}


@app.get("/cache/info")
def get_cache_info():
    """Получить информацию о состоянии кеша"""
    return redis_client.get_cache_info()


# Разделение логики по типу сервиса
SERVICE_TYPE = os.getenv("SERVICE_TYPE", "menu")

if SERVICE_TYPE == "auth":
    @app.get("/auth/health")
    def auth_health():
        return {"status": "auth service healthy"}
else:
    @app.get("/menu/health")
    def menu_health():
        return {"status": "menu service healthy"}

async def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")
    payload = auth.verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@app.get("/")
def read_root():
    return {"message": "Restaurant API is working!"}


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running"}


@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    print(f"Регистрация пользователя: {user.username}")

    # if user.role == "admin":
    #     existing_admin = db.query(models.User).filter(models.User.role == "admin").first()
    #     if existing_admin:
    #         raise HTTPException(status_code=400, detail="Administrator already exists")

    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    print(f"Пользователь создан: {db_user.id}")
    return db_user


@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    print(f"Вход пользователя: {user.username}")
    db_user = auth.authenticate_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    access_token = auth.create_access_token(data={"sub": db_user.username, "role": db_user.role})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "role": db_user.role
        }
    }


@app.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can view users")
    return db.query(models.User).all()


@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can delete users")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")

    transfer_message = ""

    try:
        # Если удаляем официанта - обрабатываем его заказы
        if user_to_delete.role == "waiter":
            # Сначала исправляем заказы с NULL waiter_id
            null_orders = db.query(models.Order).filter(models.Order.waiter_id == None).all()
            for order in null_orders:
                table = db.query(models.Table).filter(models.Table.current_order_id == order.id).first()
                if table:
                    table.is_available = True
                    table.current_order_id = None
                # OrderItem будут удалены автоматически благодаря cascade
                db.delete(order)

            if null_orders:
                print(f"Удалено {len(null_orders)} заказов с NULL waiter_id")

            # Получаем заказы официанта
            waiter_orders = db.query(models.Order).filter(models.Order.waiter_id == user_id).all()

            if waiter_orders:
                # Ищем другого официанта
                other_waiter = db.query(models.User).filter(
                    models.User.role == "waiter",
                    models.User.id != user_id
                ).first()

                if other_waiter:
                    # Массовое обновление заказов
                    for order in waiter_orders:
                        order.waiter_id = other_waiter.id
                    transfer_message = f" All {len(waiter_orders)} orders transferred to {other_waiter.username}."
                else:
                    # Массовое удаление заказов
                    for order in waiter_orders:
                        table = db.query(models.Table).filter(models.Table.current_order_id == order.id).first()
                        if table:
                            table.is_available = True
                            table.current_order_id = None
                        db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id).delete()
                        db.delete(order)
                    transfer_message = f" All {len(waiter_orders)} orders deleted (no other waiters available)."

            db.flush()  # Применяем изменения, но не коммитим

        # Удаляем пользователя
        db.delete(user_to_delete)
        db.commit()

        return {"message": f"User {user_to_delete.username} deleted successfully." + transfer_message}

    except Exception as e:
        db.rollback()
        print(f"Error deleting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting user: {str(e)}"
        )

@app.put("/users/{user_id}/password")
def change_password(
    user_id: int,
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Разрешаем менять пароль только для своего аккаунта
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only change your own password")

    user_to_update = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")

    # Хэшируем новый пароль
    hashed_password = auth.get_password_hash(password_data.new_password)
    user_to_update.password = hashed_password

    db.commit()
    return {"message": "Password updated successfully"}


@app.put("/orders/{order_id}/transfer")
def transfer_order(order_id: int, new_waiter_id: int, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    """
    Передача заказа другому официанту
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can transfer orders")

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    new_waiter = db.query(models.User).filter(
        models.User.id == new_waiter_id,
        models.User.role == "waiter"
    ).first()

    if not new_waiter:
        raise HTTPException(status_code=404, detail="New waiter not found")

    # Гарантируем, что новый waiter_id не None
    if not new_waiter.id:
        raise HTTPException(status_code=400, detail="Invalid waiter ID")

    order.waiter_id = new_waiter.id
    db.commit()

    return {"message": f"Order #{order_id} transferred to {new_waiter.username}"}


@app.delete("/me")
def delete_own_account(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Удаление своей учётной записи.
    """
    # Для администраторов проверяем, что это не последний администратор
    if current_user.role == "admin":
        admin_count = db.query(models.User).filter(models.User.role == "admin").count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the last administrator account"
            )

    transfer_message = ""

    try:
        # Если удаляем официанта - обрабатываем его заказы
        if current_user.role == "waiter":
            # Исправляем заказы с NULL waiter_id
            null_orders = db.query(models.Order).filter(models.Order.waiter_id == None).all()
            for order in null_orders:
                table = db.query(models.Table).filter(models.Table.current_order_id == order.id).first()
                if table:
                    table.is_available = True
                    table.current_order_id = None
                # OrderItem будут удалены автоматически благодаря cascade
                db.delete(order)

            if null_orders:
                print(f"Удалено {len(null_orders)} заказов с NULL waiter_id")

            # Получаем заказы текущего пользователя
            user_orders = db.query(models.Order).filter(models.Order.waiter_id == current_user.id).all()

            if user_orders:
                # Ищем другого официанта
                other_waiter = db.query(models.User).filter(
                    models.User.role == "waiter",
                    models.User.id != current_user.id
                ).first()

                if other_waiter:
                    # Массовое обновление заказов
                    for order in user_orders:
                        order.waiter_id = other_waiter.id
                    transfer_message = f" Все {len(user_orders)} заказов переданы официанту {other_waiter.username}."
                else:
                    # Массовое удаление заказов
                    for order in user_orders:
                        table = db.query(models.Table).filter(models.Table.current_order_id == order.id).first()
                        if table:
                            table.is_available = True
                            table.current_order_id = None
                        db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id).delete()
                        db.delete(order)
                    transfer_message = f" Все {len(user_orders)} заказов удалены (нет других официантов)."

            db.flush()

        # Сохраняем имя пользователя
        username = current_user.username

        # Удаляем пользователя
        db.delete(current_user)
        db.commit()

        return {
            "message": f"Ваш аккаунт {username} успешно удален." + transfer_message,
            "deleted_user": username
        }

    except Exception as e:
        db.rollback()
        print(f"Error deleting user account {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting account: {str(e)}"
        )


@app.post("/cleanup/problematic-orders")
def cleanup_problematic_orders(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Очистка проблемных заказов (с NULL waiter_id)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can cleanup orders")

    try:
        # Находим заказы с NULL waiter_id
        problematic_orders = db.query(models.Order).filter(models.Order.waiter_id == None).all()

        deleted_count = 0
        for order in problematic_orders:
            # Освобождаем столы
            table = db.query(models.Table).filter(models.Table.current_order_id == order.id).first()
            if table:
                table.is_available = True
                table.current_order_id = None

            # Удаляем заказ (order_items удалятся автоматически благодаря cascade)
            db.delete(order)
            deleted_count += 1

        db.commit()
        
        # Инвалидируем кеш
        redis_client.invalidate_all_orders_cache()
        redis_client.invalidate_tables_cache()

        return {
            "message": f"Cleaned up {deleted_count} problematic orders with NULL waiter_id",
            "deleted_count": deleted_count
        }
    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup error: {str(e)}")

@app.get("/tables", response_model=List[TableResponse])
def get_tables(db: Session = Depends(get_db)):
    # Пытаемся получить из кеша
    cached_tables = redis_client.get_cached_tables()
    if cached_tables:
        return [TableResponse(**table) for table in cached_tables]
    
    # Если нет в кеше, получаем из БД
    tables = db.query(models.Table).order_by(models.Table.number).all()
    tables_data = [{"id": t.id, "number": t.number, "is_available": t.is_available, "current_order_id": t.current_order_id} for t in tables]
    
    # Кешируем результат
    redis_client.cache_tables(tables_data)
    
    return tables


@app.get("/tables/available", response_model=List[TableResponse])
def get_available_tables(db: Session = Depends(get_db)):
    # Пытаемся получить из кеша
    cached_tables = redis_client.get_cached_available_tables()
    if cached_tables:
        return [TableResponse(**table) for table in cached_tables]
    
    # Если нет в кеше, получаем из БД
    tables = db.query(models.Table).filter(models.Table.is_available == True).order_by(models.Table.number).all()
    tables_data = [{"id": t.id, "number": t.number, "is_available": t.is_available, "current_order_id": t.current_order_id} for t in tables]
    
    # Кешируем результат
    redis_client.cache_available_tables(tables_data)
    
    return tables


@app.put("/restaurant/config")
def update_restaurant_config(config: RestaurantConfigUpdate, db: Session = Depends(get_db),
                             current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can update restaurant config")

    # Проверка ограничения (дополнительная страховка)
    if config.total_tables < 1 or config.total_tables > 100:
        raise HTTPException(
            status_code=400,
            detail="Количество столов должно быть от 1 до 100"
        )

    try:
        db_config = db.query(models.RestaurantConfig).first()
        if not db_config:
            db_config = models.RestaurantConfig(total_tables=config.total_tables)
            db.add(db_config)
        else:
            db_config.total_tables = config.total_tables

        # Считаем существующие столы
        existing_tables = db.query(models.Table).count()

        # Находим максимальный номер среди занятых столов
        busy_tables = db.query(models.Table).filter(models.Table.is_available == False).all()
        max_busy_number = max((t.number for t in busy_tables), default=0)

        # Нельзя уменьшить количество столов ниже номера самого "старшего" занятого стола
        if config.total_tables < max_busy_number:
            raise HTTPException(
                status_code=400,
                detail=f"Невозможно уменьшить количество столов ниже номера последнего занятого стола (#{max_busy_number})"
            )

        if config.total_tables > existing_tables:
            # Добавляем новые столы
            for i in range(existing_tables + 1, config.total_tables + 1):
                new_table = models.Table(number=i, is_available=True)
                db.add(new_table)
        elif config.total_tables < existing_tables:
            # Удаляем лишние столы (только свободные и без активных заказов)
            tables_to_delete = db.query(models.Table).filter(
                models.Table.number > config.total_tables,
                models.Table.is_available == True,
                models.Table.current_order_id == None
            ).all()
            for table in tables_to_delete:
                db.delete(table)

        db.commit()
        
        # Инвалидируем кеш столов
        redis_client.invalidate_tables_cache()

        return {
            "message": f"Restaurant configuration updated successfully. Total tables: {config.total_tables}",
            "total_tables": config.total_tables
        }
    except HTTPException:
        # Перебрасываем бизнес-ошибки дальше
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating restaurant config: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while updating restaurant config")


@app.get("/dishes", response_model=List[DishResponse])
def get_dishes(db: Session = Depends(get_db)):
    # Пытаемся получить из кеша
    cached_dishes = redis_client.get_cached_dishes()
    if cached_dishes:
        return [DishResponse(**dish) for dish in cached_dishes]
    
    # Если нет в кеше, получаем из БД
    dishes = db.query(models.Dish).all()
    # Преобразуем в словари для кеширования
    dishes_data = [
        {
            "id": dish.id,
            "name": dish.name,
            "description": dish.description,
            "price": float(dish.price),
            "available": dish.available
        }
        for dish in dishes
    ]
    
    # Кешируем результат
    redis_client.cache_dishes(dishes_data)
    
    return dishes


@app.post("/dishes", response_model=DishResponse)
def create_dish(dish: DishCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can create dishes")

    try:
        # Проверяем, что цена положительная
        if dish.price <= 0:
            raise HTTPException(status_code=400, detail="Price must be greater than 0")
        
        db_dish = models.Dish(**dish.dict())
        db.add(db_dish)
        db.commit()
        db.refresh(db_dish)
        
        # Инвалидируем кеш блюд
        redis_client.invalidate_dishes_cache()
        
        return db_dish
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error creating dish: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating dish")


@app.put("/dishes/{dish_id}", response_model=DishResponse)
def update_dish(dish_id: int, dish: DishCreate, db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can update dishes")

    try:
        db_dish = db.query(models.Dish).filter(models.Dish.id == dish_id).first()
        if not db_dish:
            raise HTTPException(status_code=404, detail="Dish not found")

        for key, value in dish.dict().items():
            setattr(db_dish, key, value)

        db.commit()
        db.refresh(db_dish)
        
        # Инвалидируем кеш блюд
        redis_client.invalidate_dishes_cache()
        
        return db_dish
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating dish {dish_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating dish")


@app.delete("/dishes/{dish_id}")
def delete_dish(dish_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can delete dishes")

    try:
        db_dish = db.query(models.Dish).filter(models.Dish.id == dish_id).first()
        if not db_dish:
            raise HTTPException(status_code=404, detail="Dish not found")

        db.delete(db_dish)
        db.commit()
        
        # Инвалидируем кеш блюд
        redis_client.invalidate_dishes_cache()
        
        return {"message": "Dish deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting dish {dish_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting dish")


@app.post("/orders", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    if current_user.role != "waiter":
        raise HTTPException(status_code=403, detail="Only waiters can create orders")

    # Проверяем доступность стола
    table = db.query(models.Table).filter(models.Table.number == order.table_number).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    if not table.is_available:
        raise HTTPException(status_code=400, detail="Table is not available")

    # Проверяем, что current_user.id установлен
    if not current_user.id:
        raise HTTPException(status_code=400, detail="Invalid user session")

    # Создаем заказ с явной проверкой waiter_id
    try:
        db_order = models.Order(
            table_number=order.table_number,
            waiter_id=current_user.id  # Гарантируем, что waiter_id установлен
        )

        # Генерируем человеко-читаемый код заказа (например, например, ABC1234)
        db_order.code = generate_unique_order_code(db)

        db.add(db_order)
        db.commit()
        db.refresh(db_order)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    # Добавляем items
    for item in order.items:
        db_item = models.OrderItem(order_id=db_order.id, **item.dict())
        db.add(db_item)

    # Обновляем статус стола
    table.is_available = False
    table.current_order_id = db_order.id

    db.commit()
    db.refresh(db_order)
    
    # Инвалидируем кеш столов
    redis_client.invalidate_tables_cache()

    # Получаем полные данные заказа
    order_response = get_order_response(db, db_order.id)
    
    # Кешируем заказ
    if order_response:
        order_dict = order_response.dict()
        redis_client.cache_order(db_order.id, order_dict)
    
    return order_response


@app.post("/cleanup/fast-cleanup")
def fast_cleanup(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Быстрая очистка проблемных данных
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can cleanup")

    try:
        # Находим и удаляем заказы с NULL waiter_id
        null_orders = db.query(models.Order).filter(models.Order.waiter_id == None).all()
        deleted_count = 0

        for order in null_orders:
            # Освобождаем стол
            table = db.query(models.Table).filter(models.Table.current_order_id == order.id).first()
            if table:
                table.is_available = True
                table.current_order_id = None

            # Удаляем позиции заказа
            db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id).delete()

            # Удаляем заказ
            db.delete(order)
            deleted_count += 1

        db.commit()

        return {
            "message": f"Fast cleanup completed. Deleted {deleted_count} problematic orders.",
            "deleted_count": deleted_count
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Cleanup error: {str(e)}")

@app.get("/orders", response_model=List[OrderResponse])
def get_orders(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role == "admin":
        orders = db.query(models.Order).all()
    else:
        orders = db.query(models.Order).filter(models.Order.waiter_id == current_user.id).all()

    return [get_order_response(db, order.id) for order in orders]

@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Проверяем права доступа
    if current_user.role == "waiter" and db_order.waiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own orders")

    return get_order_response(db, order_id)

@app.delete("/orders/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can delete orders")

    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Освобождаем стол, если он был занят этим заказом
    table = db.query(models.Table).filter(models.Table.current_order_id == order_id).first()
    if table:
        table.is_available = True
        table.current_order_id = None

    # Удаляем заказ (order_items удалятся автоматически благодаря cascade)
    db.delete(db_order)
    db.commit()
    
    # Инвалидируем кеш заказа и столов
    redis_client.invalidate_order_cache(order_id)
    redis_client.invalidate_tables_cache()

    return {"message": "Order deleted successfully"}

@app.put("/orders/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, order_update: OrderUpdate, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Проверяем права доступа
    if current_user.role == "waiter" and db_order.waiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own orders")

    # Обновляем номер стола если нужно
    if order_update.table_number and order_update.table_number != db_order.table_number:
        # Освобождаем старый стол
        old_table = db.query(models.Table).filter(models.Table.number == db_order.table_number).first()
        if old_table:
            old_table.is_available = True
            old_table.current_order_id = None

        # Занимаем новый стол
        new_table = db.query(models.Table).filter(models.Table.number == order_update.table_number).first()
        if not new_table:
            raise HTTPException(status_code=404, detail="Table not found")
        if not new_table.is_available and new_table.current_order_id != order_id:
            raise HTTPException(status_code=400, detail="Table is not available")

        new_table.is_available = False
        new_table.current_order_id = order_id
        db_order.table_number = order_update.table_number

    # Обновляем статус если нужно
    if order_update.status:
        db_order.status = order_update.status
        # Если заказ завершен, освобождаем стол
        if order_update.status == "completed":
            table = db.query(models.Table).filter(models.Table.number == db_order.table_number).first()
            if table:
                table.is_available = True
                table.current_order_id = None

    # Обновляем items если нужно
    if order_update.items is not None:
        # Удаляем старые items
        db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).delete()
        # Добавляем новые items
        for item in order_update.items:
            db_item = models.OrderItem(order_id=order_id, **item.dict())
            db.add(db_item)

    db.commit()
    
    # Инвалидируем кеш заказа и столов
    redis_client.invalidate_order_cache(order_id)
    redis_client.invalidate_tables_cache()
    
    order_response = get_order_response(db, order_id)
    
    # Кешируем обновленный заказ
    if order_response:
        order_dict = order_response.dict()
        redis_client.cache_order(order_id, order_dict)
    
    return order_response


@app.put("/orders/{order_id}/status")
def update_order_status(order_id: int, status: str, db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Проверяем права доступа
    if current_user.role == "waiter" and db_order.waiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own orders")

    db_order.status = status

    # Если заказ завершен, освобождаем стол
    if status == "completed":
        table = db.query(models.Table).filter(models.Table.number == db_order.table_number).first()
        if table:
            table.is_available = True
            table.current_order_id = None

    db.commit()
    
    # Инвалидируем кеш заказа и столов
    redis_client.invalidate_order_cache(order_id)
    redis_client.invalidate_tables_cache()
    
    return {"message": "Order status updated"}


def get_order_response(db: Session, order_id: int):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return None

    # Получаем waiter имя
    waiter = db.query(models.User).filter(models.User.id == order.waiter_id).first()
    waiter_name = waiter.username if waiter else "Unknown"

    # Получаем items с названиями блюд
    items = db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).all()
    order_items = []
    for item in items:
        dish = db.query(models.Dish).filter(models.Dish.id == item.dish_id).first()
        order_items.append(OrderItemResponse(
            id=item.id,
            dish_id=item.dish_id,
            dish_name=dish.name if dish else "Unknown",
            dish_price=dish.price if dish else 0,
            quantity=item.quantity
        ))

    return OrderResponse(
        id=order.id,
        code=order.code,
        table_number=order.table_number,
        status=order.status,
        created_at=order.created_at,
        waiter_id=order.waiter_id,
        waiter_name=waiter_name,
        items=order_items,
    )


def generate_unique_order_code(db: Session) -> str:
    """Генерирует уникальный код заказа в формате БЦЦЦ:
    первая позиция — заглавная кириллическая буква, остальные три — цифры.
    """
    cyrillic_letters = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ"
    while True:
        letter = random.choice(cyrillic_letters)
        digits = "".join(random.choices(string.digits, k=3))
        code = f"{letter}{digits}"
        exists = db.query(models.Order).filter(models.Order.code == code).first()
        if not exists:
            return code


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)