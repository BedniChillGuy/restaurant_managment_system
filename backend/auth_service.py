from fastapi import FastAPI, Depends, HTTPException, status, Header
from typing import List, Optional
from sqlalchemy.orm import Session
import models
import auth
from database import engine, get_db, init_restaurant_config, wait_for_db
from schemas import UserCreate, UserResponse, PasswordChange

app = FastAPI()


@app.on_event("startup")
def startup_event():

    if wait_for_db():
        try:
            models.Base.metadata.create_all(bind=engine)
            init_restaurant_config()
        except Exception:
            pass


@app.get("/health")
def health_check():
    return {"status": "auth service healthy"}


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


@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/login")
def login(user: dict, db: Session = Depends(get_db)):
    username = user.get("username")
    password = user.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Missing username or password")
    db_user = auth.authenticate_user(db, username, password)
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
    if user_to_delete.role == "waiter":
        waiter_orders = db.query(models.Order).filter(models.Order.waiter_id == user_id).all()
        if waiter_orders:
            other_waiter = db.query(models.User).filter(models.User.role == "waiter", models.User.id != user_id).first()
            if other_waiter:
                for order in waiter_orders:
                    order.waiter_id = other_waiter.id
            else:
                for order in waiter_orders:
                    table = db.query(models.Table).filter(models.Table.current_order_id == order.id).first()
                    if table:
                        table.is_available = True
                        table.current_order_id = None
                    db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id).delete()
                    db.delete(order)
    db.delete(user_to_delete)
    db.commit()
    return {"message": f"User {user_to_delete.username} deleted successfully."}


@app.put("/users/{user_id}/password")
def change_password(user_id: int, password_data: PasswordChange, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only change your own password")
    user_to_update = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    hashed_password = auth.get_password_hash(password_data.new_password)
    user_to_update.password = hashed_password
    db.commit()
    return {"message": "Password updated successfully"}


@app.delete("/me")
def delete_own_account(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role == "admin":
        admin_count = db.query(models.User).filter(models.User.role == "admin").count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last administrator account")
    # Handle waiter orders similar to delete_user
    if current_user.role == "waiter":
        user_orders = db.query(models.Order).filter(models.Order.waiter_id == current_user.id).all()
        if user_orders:
            other_waiter = db.query(models.User).filter(models.User.role == "waiter", models.User.id != current_user.id).first()
            if other_waiter:
                for order in user_orders:
                    order.waiter_id = other_waiter.id
            else:
                for order in user_orders:
                    table = db.query(models.Table).filter(models.Table.current_order_id == order.id).first()
                    if table:
                        table.is_available = True
                        table.current_order_id = None
                    db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id).delete()
                    db.delete(order)
    username = current_user.username
    db.delete(current_user)
    db.commit()
    return {"message": f"Your account {username} deleted.", "deleted_user": username}



