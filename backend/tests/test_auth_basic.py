from pathlib import Path
import importlib.util
import sys

# На GitHub Actions проект может быть смонтирован в разном месте,
# поэтому safest‑вариант — подгружать auth.py напрямую по пути файла,
# а не полагаться только на PYTHONPATH.
BACKEND_DIR = Path(__file__).resolve().parents[1]
AUTH_PATH = BACKEND_DIR / "auth.py"

if not AUTH_PATH.is_file():
    raise RuntimeError(f"auth.py not found at expected path: {AUTH_PATH}")

spec = importlib.util.spec_from_file_location("auth", AUTH_PATH)
auth = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
assert spec.loader is not None
spec.loader.exec_module(auth)  # type: ignore[call-arg]


def test_password_hash_and_verify_roundtrip():
    """Пароль после хэширования успешно проходит verify, а другой пароль — нет."""
    password = "My_S3cret_pass"
    wrong_password = "other_pass"

    hashed = auth.get_password_hash(password)

    assert hashed != password
    assert auth.verify_password(password, hashed) is True
    assert auth.verify_password(wrong_password, hashed) is False


def test_create_and_verify_access_token_contains_sub_and_role():
    """Токен, созданный create_access_token, успешно декодируется verify_token-ом."""
    data = {"sub": "test-user", "role": "admin"}

    token = auth.create_access_token(data)
    assert isinstance(token, str)
    # Базовая форма JWT: три части через точку
    assert len(token.split(".")) == 3

    payload = auth.verify_token(token)
    assert payload is not None
    assert payload["sub"] == data["sub"]
    assert payload["role"] == data["role"]
    # В payload должен быть exp (срок жизни токена)
    assert "exp" in payload


def test_verify_token_returns_none_for_invalid_token():
    """Невалидный токен должен возвращать None, а не поднимать исключение наружу."""
    # Явно испорченный токен
    fake_token = "invalid.token.value"
    payload = auth.verify_token(fake_token)
    assert payload is None


