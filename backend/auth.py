from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import secrets
import os

# Используем другую схему если bcrypt не доступен
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # Проверим работу bcrypt
    pwd_context.hash("test")
    print("bcrypt успешно инициализирован")
except Exception as e:
    print(f"bcrypt не доступен: {e}, используем pbkdf2_sha256")
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_secret_key():
    env_key = os.getenv("SECRET_KEY")
    if env_key:
        return env_key

    key_file = ".secret_key"
    if os.path.exists(key_file):
        try:
            with open(key_file, "r", encoding='utf-8') as f:
                return f.read().strip()
        except UnicodeDecodeError:
            # Если файл в неправильной кодировке, создаем новый
            print("Ошибка чтения секретного ключа, создаем новый")
            os.remove(key_file)

    new_key = secrets.token_urlsafe(32)
    with open(key_file, "w", encoding='utf-8') as f:
        f.write(new_key)
    if os.name != 'nt':
        os.chmod(key_file, 0o600)
    print(f"Сгенерирован новый SECRET_KEY")
    return new_key


SECRET_KEY = get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    from models import User
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        return None
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None