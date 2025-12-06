# Restaurant Management System

Система управления заказами и столами ресторана с микросервисной архитектурой,
веб‑интерфейсом и автоматизированным CI/CD на GitHub Actions.

## Краткое описание

Полнофункциональная система управления рестораном:
- роли пользователей (администратор, официант);
- управление меню и заказами;
- учёт столов и состояний заказов;
- health‑мониторинг и кеширование (Redis);
- развёртывание в Kubernetes через GitHub Actions.

## Архитектура

### Микросервисы

- **Backend API** (FastAPI) — основной API для меню, заказов, столов;
- **Backend Auth** (FastAPI) — аутентификация и управление пользователями;
- **Frontend** (HTML/JS/CSS + Nginx) — веб‑интерфейс;
- **Health Monitor** (Python) — регулярные проверки всех сервисов;
- **PostgreSQL 15** — реляционная база данных;
- **Redis 7** — кеширование и вспомогательные операции.

### Основные возможности

- аутентификация и авторизация на основе JWT;
- управление пользователями (администраторы и официанты);
- управление меню и блюдами;
- создание и отслеживание заказов;
- управление столами ресторана;
- кеширование ответов API (Redis);
- мониторинг работоспособности сервисов;
- валидация данных на всех уровнях;
- уникальные номера заказов (формат: Б123).

## Быстрый старт

### Вариант 1. Docker Compose (локальная разработка)

```bash
# старт всех сервисов
docker-compose up -d

# просмотр логов
docker-compose logs -f

# остановка
docker-compose down
```

Приложение будет доступно по адресу: `http://localhost`.

### Вариант 2. Kubernetes + GitHub Actions (Minikube)

1. Запустить Minikube (Windows):
   ```powershell
   minikube start
   kubectl config use-context minikube
   kubectl get pods -A
   ```

2. В Ubuntu/WSL настроить self‑hosted runner (один раз) и kubeconfig
   так, чтобы команда показывала те же поды:
   ```bash
   kubectl config use-context minikube
   kubectl get pods -A
   ```

3. Запустить self‑hosted runner:
   ```bash
   cd ~/actions-runner
   ./run.sh    # оставить окно открытым (Listening for Jobs)
   ```

4. Любой `git push` в ветку `main` запускает CI/CD пайплайн:
   - `Backend tests` — pytest‑тесты backend;
   - `Frontend tests` — pytest‑тесты фронтенда;
   - `Build and push images` — сборка docker‑образов и пуш в GHCR;
   - `Deploy to Kubernetes` — обновление деплойментов в namespace `restaurant`.

5. После успешного пайплайна можно проверить приложение в Minikube:
   ```powershell
   kubectl get pods -n restaurant
   minikube service frontend -n restaurant --url
   ```

Для подробностей по манифестам Kubernetes см. [k8s/README.md](k8s/README.md).

## Структура проекта

```
.
├── backend/
│   ├── main.py              # Основной API
│   ├── auth.py              # Аутентификация
│   ├── models.py            # SQLAlchemy модели
│   ├── schemas.py           # Pydantic схемы
│   ├── database.py          # Конфигурация БД
│   ├── redis_client.py      # Redis клиент
│   ├── health_monitor.py    # Мониторинг
│   ├── requirements.txt     # Python зависимости
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── script.js
│   ├── style.css
│   ├── nginx.conf
│   └── Dockerfile
├── k8s/                     # Kubernetes манифесты
│   ├── 00-namespace.yaml
│   ├── 01-configmap.yaml
│   ├── ...
│   └── README.md
├── docker-compose.yml
└── README.md
```

## Технологии

### Backend
- **FastAPI** - современный веб-фреймворк для Python
- **SQLAlchemy** - ORM для работы с БД
- **Pydantic** - валидация данных
- **JWT** - токен-based аутентификация
- **Redis** - кеширование
- **PostgreSQL** - реляционная БД

### Frontend
- Vanilla JavaScript (ES6+)
- HTML5 / CSS3
- Nginx для проксирования

### DevOps
- Docker & Docker Compose
- Kubernetes
- Health monitoring

## Роли пользователей

### Администратор
- Управление пользователями
- Управление меню (добавление/редактирование/удаление блюд)
- Просмотр всех заказов
- Настройка количества столов
- Передача заказов между официантами

### Официант
- Создание заказов
- Просмотр своих заказов
- Обновление статуса заказов
- Редактирование заказов

## Безопасность

- ✅ JWT токены для аутентификации
- ✅ Хеширование паролей (bcrypt/pbkdf2_sha256)
- ✅ Валидация на уровне Pydantic схем
- ✅ SQL injection защита (SQLAlchemy ORM)
- ✅ CORS настройки
- ✅ Rate limiting (через Redis)

## Основные API‑эндпоинты

### Аутентификация
- `POST /register` - регистрация пользователя
- `POST /login` - вход в систему
- `GET /me` - информация о текущем пользователе

### Меню
- `GET /dishes` - список блюд
- `POST /dishes` - добавить блюдо (admin)
- `PUT /dishes/{id}` - обновить блюдо (admin)
- `DELETE /dishes/{id}` - удалить блюдо (admin)

### Заказы
- `GET /orders` - список заказов
- `POST /orders` - создать заказ (waiter)
- `GET /orders/{id}` - получить заказ
- `PUT /orders/{id}` - обновить заказ
- `DELETE /orders/{id}` - удалить заказ (admin)
- `PUT /orders/{id}/status` - обновить статус

### Столы
- `GET /tables` - список столов
- `GET /tables/available` - доступные столы
- `PUT /restaurant/config` - настройка столов (admin)

### Пользователи
- `GET /users` - список пользователей (admin)
- `DELETE /users/{id}` - удалить пользователя (admin)
- `PUT /users/{id}/password` - изменить пароль

### Health
- `GET /health` - проверка работоспособности
- `GET /cache-test` - тест Redis
- `GET /cache/info` - информация о кеше

## Docker‑образы

### Backend
```dockerfile
FROM python:3.11-slim
# Установка зависимостей и копирование кода
```

### Frontend
```dockerfile
FROM nginx:alpine
# Копирование статики и конфигурации nginx
```

## Валидация данных

### Пользователи
- Username: 3-50 символов
- Password: минимум 4 символа
- Role: только "admin" или "waiter"

### Блюда
- Название: не пустое, до 100 символов
- Цена: > 0, до 1,000,000

### Заказы
- Количество: 1-100 единиц на позицию

## Мониторинг

Health Monitor проверяет каждые 10 секунд:
- ✅ Backend API availability
- ✅ Backend Auth availability
- ✅ Frontend availability
- ✅ PostgreSQL connection
- ✅ Redis availability
- ✅ Cache functionality

## Кеширование

Redis используется для:
- Кеш списка блюд (TTL: 5 минут)
- Кеш списка столов (TTL: 1 минута)
- Кеш доступных столов (TTL: 30 секунд)
- Кеш заказов (TTL: 3 минуты)
- Rate limiting
- Статистика просмотров блюд

## Разработка

### Требования
- Python 3.11+
- Docker & Docker Compose
- Kubernetes (для production)

### Локальная разработка

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (нужен nginx или python http.server)
cd frontend
python -m http.server 8080
```

### Переменные окружения

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/restaurant
REDIS_HOST=localhost
REDIS_PORT=6379
SERVICE_TYPE=menu  # или auth
SECRET_KEY=your-secret-key
```

## Changelog

### v1.0.0
- ✅ Базовая функциональность
- ✅ Аутентификация и авторизация
- ✅ CRUD для пользователей, блюд, заказов
- ✅ Docker Compose поддержка
- ✅ Kubernetes манифесты
- ✅ Health monitoring
- ✅ Redis кеширование
- ✅ Полная валидация данных
- ✅ Cascade delete для связанных записей
- ✅ Русскоязычный интерфейс
- ✅ Уникальные коды заказов

## Contributing

1. Fork проекта
2. Создай feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Открой Pull Request

## License

Этот проект создан в образовательных целях.

## Автор

Проект разработан как учебная система управления рестораном.

## Благодарности

- FastAPI за отличный фреймворк
- SQLAlchemy за мощную ORM
- Redis за быстрое кеширование
- Nginx за надежный reverse proxy

