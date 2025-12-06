from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def test_frontend_index_exists():
    """Проверяем, что основной HTML фронтенда существует и не пустой."""
    index_html = FRONTEND_DIR / "index.html"
    assert index_html.is_file(), "frontend/index.html не найден"
    content = index_html.read_text(encoding="utf-8")
    assert "<html" in content.lower()
    assert "</html>" in content.lower()


def test_frontend_has_login_elements():
    """Простейшая smoke‑проверка: на странице есть элементы для логина/авторизации."""
    index_html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8").lower()

    # Ищем базовые элементы формы логина
    assert "password" in index_html or "пароль" in index_html
    assert "username" in index_html or "логин" in index_html or "user" in index_html


def test_frontend_script_references_backend():
    """script.js должен содержать обращения к backend‑API (fetch / axios / URL сервиса)."""
    script_js = FRONTEND_DIR / "script.js"
    assert script_js.is_file(), "frontend/script.js не найден"
    content = script_js.read_text(encoding="utf-8").lower()

    # Ищем хотя бы одно упоминание fetch / axios / http
    assert "fetch(" in content or "axios" in content or "http://" in content or "https://" in content


