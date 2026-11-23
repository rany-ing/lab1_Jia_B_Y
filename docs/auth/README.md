# Аутентификация и права доступа

После [настройки окружения](../../README.md#установка-и-запуск) выполните
`alembic upgrade head` и запустите `uvicorn app.main:app`. Миграция
`0003_add_auth` сохраняет существующих пользователей, новости и комментарии.
Секрет подписи JWT задаётся в `JWT_SECRET` в локальном файле `.env`.

## Локальные учётные записи

Новый пользователь регистрируется через `POST /auth/register` с полями `name`,
`email` и `password`. Пароль хранится в виде хеша Argon2id. Роль автора
назначает администратор. У существующих пользователей можно задать пароль
командой, которая запрашивает его интерактивно.

```bash
python -m app.auth.bootstrap alice.author@example.com
python -m app.auth.bootstrap boris.author@example.com
python -m app.auth.bootstrap viktor.reader@example.com
```

На демонстрационной базе можно назначить Бориса администратором командой
`python -m app.auth.bootstrap boris.author@example.com --admin`. Команда
обновляет пароль выбранной учётной записи и отзывает её прежние сессии.

## GitHub OAuth

1. Создайте [GitHub OAuth App](https://github.com/settings/applications/new).
   Для локального запуска используйте Homepage URL `http://127.0.0.1:8000`
   и Authorization callback URL `http://127.0.0.1:8000/auth/github/callback`.
2. Укажите `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` и `GITHUB_CALLBACK_URL`
   в `.env`.
3. Откройте `http://127.0.0.1:8000/auth/github/login` и подтвердите
   авторизацию. После перенаправления API вернёт пару JWT в теле ответа.

`fastapi-sso` проверяет OAuth state и использует PKCE. При первом входе
пользователь создаётся по постоянному GitHub ID и подтверждённому основному
адресу GitHub. Если этот адрес уже занят другой учётной записью, сервер отвечает
`409`. Повторный вход выполняется по GitHub ID. Вне localhost callback должен
использовать HTTPS.

## Маршруты

| Метод и путь | Назначение |
| --- | --- |
| `POST /auth/register` | Создаёт обычную локальную учётную запись, `201` |
| `POST /auth/login` | Принимает `email` и `password`, возвращает пару JWT |
| `GET /auth/github/login` | Перенаправляет на GitHub |
| `GET /auth/github/callback` | Завершает вход через GitHub и возвращает пару JWT |
| `POST /auth/refresh` | Принимает `{"refresh_token":"…"}`, возвращает новую пару JWT |
| `POST /auth/logout` | Принимает актуальный refresh token, отзывает сессию, `204` |
| `GET /auth/sessions` | Возвращает активные сессии текущего пользователя |
| `GET /users/me` | Возвращает профиль текущего пользователя |

Access token передаётся заголовком `Authorization: Bearer …`. Сроки по умолчанию
составляют 15 минут для access token и 30 дней с момента входа для сессии.
Сессия хранит хеш текущего refresh token, User-Agent и сроки действия.
Каждое обновление заменяет refresh token. Выход сразу отзывает все access
tokens этой сессии.

Чтение бизнес-ресурсов доступно вошедшим пользователям. Обычный пользователь
может комментировать новости и изменять или удалять свой профиль и свои
материалы. Новость создаёт верифицированный автор или администратор.
Администратор может управлять чужими ресурсами, создавать профили через
`POST /users` и изменять поля `is_admin` и `is_verified_author`.
В запросах создания новости и комментария автор определяется по access token.

## Проверка через curl

```bash
BASE=http://127.0.0.1:8000
curl -i "$BASE/news" # 401
curl -i "$BASE/health" # 200

read -rs PASSWORD
echo
PAIR=$(jq -cn --arg email alice.author@example.com --arg password "$PASSWORD" \
  '{email:$email,password:$password}' |
  curl -fsS "$BASE/auth/login" -A 'ITMO module 3 test' \
    -H 'Content-Type: application/json' --data-binary @-)
unset PASSWORD

ACCESS=$(jq -r .access_token <<<"$PAIR")
REFRESH=$(jq -r .refresh_token <<<"$PAIR")
curl -i "$BASE/users/me" -H "Authorization: Bearer $ACCESS"
curl -i "$BASE/auth/sessions" -H "Authorization: Bearer $ACCESS"

curl -i "$BASE/news" -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' --data '{"title":"OAuth test","content":{"text":"Example"}}'

NEW_PAIR=$(jq -cn --arg token "$REFRESH" '{refresh_token:$token}' |
  curl -fsS "$BASE/auth/refresh" -H 'Content-Type: application/json' --data-binary @-)
jq -cn --arg token "$REFRESH" '{refresh_token:$token}' |
  curl -i "$BASE/auth/refresh" -H 'Content-Type: application/json' --data-binary @- # 401

jq -c '{refresh_token}' <<<"$NEW_PAIR" |
  curl -i "$BASE/auth/logout" -H 'Content-Type: application/json' --data-binary @- # 204
curl -i "$BASE/auth/sessions" -H "Authorization: Bearer $ACCESS" # 401
```
