import re

import jwt

import auth


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


