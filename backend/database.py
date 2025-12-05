from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import time
from sqlalchemy.exc import OperationalError

load_dotenv()

# Всегда используем одно и то же подключение, совпадающее с docker-compose
# (service postgres), чтобы оба backend‑сервиса работали с одной базой.
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@postgres:5432/restaurant"
)


def wait_for_db(max_retries=30, retry_interval=2):
    print("Ожидание подключения к базе данных...")

    for attempt in range(max_retries):
        try:
            # Пробуем создать временное подключение
            temp_engine = create_engine(SQLALCHEMY_DATABASE_URL)
            with temp_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(" База данных доступна!")
            temp_engine.dispose()
            return True
        except OperationalError as e:
            print(f" Попытка {attempt + 1}/{max_retries}: База данных еще не доступна. Ошибка: {e}")
            if attempt < max_retries - 1:
                print(f" Повторная попытка через {retry_interval} секунд...")
                time.sleep(retry_interval)

    print(" Не удалось подключиться к базе данных после всех попыток")
    return False


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    pool_recycle=300,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_restaurant_config():
    from models import RestaurantConfig, Table
    db = SessionLocal()
    try:
        config = db.query(RestaurantConfig).first()
        if not config:
            # Ограничиваем начальное количество столов 100
            initial_tables = 10
            if initial_tables > 100:
                initial_tables = 100
                print(" Initial tables limited to 100")

            config = RestaurantConfig(total_tables=initial_tables)
            db.add(config)
            db.commit()
            db.refresh(config)
            print(" Конфигурация ресторана создана")

        existing_tables = db.query(Table).count()
        if existing_tables == 0:
            # Ограничиваем создаваемые таблицы конфигурацией
            tables_to_create = min(config.total_tables, 100)
            for i in range(1, tables_to_create + 1):
                table = Table(number=i, is_available=True)
                db.add(table)
            db.commit()
            print(f" Создано {tables_to_create} столов")
        else:
            print(f" В базе уже есть {existing_tables} столов")

    except Exception as e:
        print(f" Ошибка при инициализации конфигурации: {e}")
        db.rollback()
        raise
    finally:
        db.close()