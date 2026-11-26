# News Portal Frontend (`lab6_Jia_B_Y`)

Фронтенд-приложение на **React + Vite** для API новостей (лабораторные работы 2–5).

## Стек

- **Node.js**: `18+`
- **Сборщик**: `Vite`
- **Библиотеки**: `react`, `react-router-dom`
- **HTTP-клиент**: встроенный `fetch` (`src/api/client.js`) с автоматической подстановкой `Authorization: Bearer <token>` и обновлением access-токена через `POST /auth/refresh`
- **Стилизация**: CSS Modules (`*.module.css`)

## Структура проекта

```text
src/
├── api/
│   ├── client.js          # Обёртка над fetch, Bearer-токен и авто-refresh
│   ├── auth.js            # login, register, logout, getMe, getSessions, GitHub OAuth
│   ├── news.js            # CRUD новостей и список комментариев к новости
│   ├── comments.js        # Создание, редактирование и удаление комментариев
│   └── users.js           # Получение списка пользователей
├── components/
│   ├── Navbar.jsx / Navbar.module.css
│   ├── NewsCard.jsx / NewsCard.module.css
│   └── CommentItem.jsx / CommentItem.module.css
├── context/
│   └── AuthContext.jsx    # Состояние авторизации, роли и localStorage
├── pages/
│   ├── HomePage.jsx / HomePage.module.css
│   ├── NewsDetailPage.jsx / NewsDetailPage.module.css
│   ├── NewsFormPage.jsx / NewsFormPage.module.css
│   └── LoginPage.jsx / LoginPage.module.css
├── utils/
│   └── format.js
├── App.jsx / App.module.css
├── index.css
└── main.jsx
```

## Установка и запуск

1. Установите зависимости:

```bash
npm install
```

2. Укажите базовый URL локально поднятого FastAPI-сервера в `.env` (например, адрес вашего бекенда на порту `8000` или префикс прокси `/api`):

```bash
cp .env.example .env
# VITE_API_BASE_URL=http://localhost:8000
```

3. Запустите dev-сервер:

```bash
npm run dev
```

## Страницы и используемые эндпоинты API

| Страница | Маршрут | Запросы к API (`fetch`) |
| --- | --- | --- |
| **Главная (лента новостей)** | `/` | `GET /news`, `GET /users` (для отображения имён авторов) |
| **Страница новости и комментариев** | `/news/:id` | `GET /news/{id}`, `GET /news/{id}/comments`, `POST /comments`, `PATCH /comments/{id}`, `DELETE /comments/{id}`, `DELETE /news/{id}` |
| **Создание / редактирование новости** | `/news/new`, `/news/:id/edit` | `POST /news`, `GET /news/{id}`, `PATCH /news/{id}` |
| **Авторизация и регистрация** | `/login` | `POST /auth/login`, `POST /auth/register`, `GET /users/me`, `POST /auth/logout`, `GET /auth/github/login` |

## Ролевая модель в интерфейсе

- **Неавторизованный пользователь**: просмотр новостей и комментариев; скрыты формы создания новостей/комментариев и кнопки редактирования/удаления.
- **Обычный авторизованный пользователь** (`is_verified_author: false`, `is_admin: false`): может оставлять комментарии, а также редактировать и удалять **свои** комментарии; создание новостей недоступно.
- **Верифицированный автор** (`is_verified_author: true`): дополнительно получает кнопку «+ Создать новость» и может редактировать/удалять **свои** новости.
- **Администратор** (`is_admin: true`): может создавать новости, а также редактировать и удалять **любые** новости и **любые** комментарии.
