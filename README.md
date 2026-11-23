# News Management API (`lab1_Jia_B_Y`)

CRUD API для управления **пользователями**, **новостями** (с поддержкой JSON-контента) и **комментариями**, реализованный на **FastAPI**, **SQLAlchemy 2**, **Alembic** и **PostgreSQL**.

## Стек и требования

- **Python**: `3.10+`
- **Фреймворк**: `FastAPI` + `Uvicorn`
- **ORM и миграции**: `SQLAlchemy`, `Alembic`
- **СУБД**: `PostgreSQL` (`psycopg`)
- **Валидация**: `Pydantic` (`pydantic[email]`, `pydantic-settings`)

Зависимости в [`requirements.txt`](./requirements.txt) сведены к минимуму — только библиотеки, необходимые для работы API и подключения к PostgreSQL.

---

## Архитектура проекта (MVC + Service Layer)

```text
lab1_Jia_B_Y/
├── alembic.ini                       # Конфигурация Alembic
├── docker-compose.yml                # Быстрый запуск PostgreSQL в Docker
├── .env.example                      # Пример переменных окружения
├── requirements.txt                  # Минимальный набор зависимостей
├── migrations/
│   ├── env.py                        # Подключение метаданных ORM и DATABASE_URL
│   └── versions/
│       ├── 0001_create_initial_tables.py   # Миграция 1: создание таблиц и связей
│       └── 0002_seed_mock_data.py          # Миграция 2: наполнение моковыми данными
└── app/
    ├── main.py                       # Точка входа FastAPI, регистрация роутеров
    ├── config.py                     # Настройки приложения из .env
    ├── database.py                   # Engine, SessionLocal, Base, get_db dependency
    ├── models/                       # Model: SQLAlchemy ORM-модели
    │   ├── user.py
    │   ├── news.py
    │   └── comment.py
    ├── schemas/                      # View (DTO): Pydantic-схемы запросов и ответов
    │   ├── user.py
    │   ├── news.py
    │   └── comment.py
    ├── services/                     # Бизнес-логика и работа с сессией БД
    │   ├── user_service.py
    │   ├── news_service.py
    │   └── comment_service.py
    └── controllers/                  # Controller: HTTP-ручки FastAPI
        ├── user_controller.py
        ├── news_controller.py
        └── comment_controller.py
```

### Принцип разделения ответственности

- **`models/`** — описание таблиц, типов колонок, ограничений целостности (`UNIQUE`, `FOREIGN KEY ... ON DELETE CASCADE`) и связей ORM.
- **`schemas/`** — валидация входных данных (включая `EmailStr` и JSON-структуру контента) и сериализация ответов.
- **`services/`** — реализация бизнес-правил: проверка уникальности email (`409 Conflict`), проверка статуса верификации автора перед созданием новости (`403 Forbidden`), проверка существования связанных сущностей (`404 Not Found`), каскадное удаление.
- **`controllers/`** — тонкий HTTP-слой маршрутизации, статусов ответа и инъекции зависимости `Depends(get_db)`.

---

## Проектирование модели данных

### Ключевые решения

1. **Уникальность пользователей**: поле `users.email` имеет уникальный индекс (`UNIQUE`), чтобы исключить дублирование аккаунтов.
2. **Права на публикацию**: флаг `users.is_verified_author` (по умолчанию `false`) проверяется на уровне сервиса при `POST /news` — неавторизованный как автор пользователь получает `403 Forbidden`.
3. **JSON-контент новостей**: поле `news.content` имеет тип `JSON` в PostgreSQL, что позволяет хранить структурированный контент (блоки текста, теги, метаданные).
4. **Каскадное удаление комментариев**: внешние ключи `comments.news_id -> news.id` и `comments.author_id -> users.id` настроены с `ON DELETE CASCADE`, а в ORM-модели `News.comments` заданы `cascade="all, delete-orphan"` и `passive_deletes=True`. При удалении новости все её комментарии автоматически удаляются на уровне СУБД.

### Визуализация моделей и связей (ER-диаграмма)

```mermaid
erDiagram
    USERS ||--o{ NEWS : "publishes (verified only)"
    USERS ||--o{ COMMENTS : "writes"
    NEWS ||--o{ COMMENTS : "has (ON DELETE CASCADE)"

    USERS {
        int id PK
        varchar(120) name
        varchar(255) email UK
        timestamptz registered_at
        boolean is_verified_author
        varchar(500) avatar
    }

    NEWS {
        int id PK
        varchar(255) title
        json content
        timestamptz published_at
        int author_id FK
        varchar(500) cover
    }

    COMMENTS {
        int id PK
        text text
        int news_id FK
        int author_id FK
        timestamptz published_at
    }
```

---

## Миграции (Alembic)

В проекте определены три последовательные миграции:

1. **`0001_create_initial_tables`** — создаёт таблицы `users`, `news`, `comments`, первичный и внешние ключи с `ON DELETE CASCADE`, уникальный индекс `ix_users_email` и индексы для внешних ключей (`ix_news_author_id`, `ix_comments_news_id`, `ix_comments_author_id`). В `downgrade()` выполняется обратное удаление индексов и таблиц.
2. **`0002_seed_mock_data`** — добавляет моковые данные:
   - 3 пользователя (2 верифицированных автора и 1 обычный читатель),
   - 2 новости с JSON-контентом,
   - 3 комментария.
   После вставки явных `id` выполняется синхронизация PostgreSQL-последовательностей (`setval`), чтобы последующие `POST`-запросы не конфликтовали по первичному ключу. В `downgrade()` моковые записи удаляются.
3. **`0003_add_auth`** — добавляет учётные данные, роль администратора и таблицу сессий обновления токенов.

---

## Установка и запуск

### 1. Подготовка окружения

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Сгенерируйте ключ командой `python -c "import secrets; print(secrets.token_urlsafe(48))"` и укажите его в поле `JWT_SECRET` файла `.env`.

### 2. Запуск PostgreSQL

**Вариант A — через Docker Compose:**

```bash
docker compose up -d
```

**Вариант B — локально установленный PostgreSQL:**

Создайте пользователя `postgres` с паролем `postgres` и базу `news_api` (или укажите свои параметры в `.env` в переменной `DATABASE_URL`):

```bash
createdb news_api
```

### 3. Применение миграций

```bash
alembic upgrade head
```

Проверить текущую ревизию:

```bash
alembic current
```

### 4. Запуск FastAPI-сервера

```bash
uvicorn app.main:app --reload
```

- API доступен по адресу: `http://127.0.0.1:8000`
- Интерактивная документация Swagger UI: `http://127.0.0.1:8000/docs`

---

## Аутентификация и примеры API

Настройка GitHub OAuth, работа с JWT, права доступа и команды для проверки описаны в [документации модуля 3](docs/auth/README.md).
