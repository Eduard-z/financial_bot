# financial_bot

Telegram бот для учёта личных расходов и ведения бюджета.

`BOT_TOKEN` — API токен бота
`ACCESS_ID` — ID Telegram аккаунта, от которого будут приниматься сообщения
`DB_USER` — Username пользователя базы данных
`DB_PASSWORD` — Пароль к базе данных
`DB_NAME` — Название базы данных
`DB_HOST` — URL-адрес базы данных
`DB_PORT` — 5432 by default

Использование с Docker показано ниже. 
SQLite база данных будет лежать в папке проекта `db/finance.db`.

Копировать файл .env:
```
scp -P server_port .env login@host:project_path
```

Создать образ:
```
docker build -t fin-image .
or
docker compose build
```

Запустить контейнер(ы):
```
docker run --rm -itd -v ${pwd}/artefacts:/home/artefacts -v ${pwd}/db:/home/db fin-image
or
docker compose up
```

Чтобы войти в работающий контейнер:
```
docker exec -ti b5d1 bash
or
docker exec -it container_name psql -h DB_HOST --username=DB_USER -d DB_NAME
```

Войти в контейнере в SQL шелл:
```
docker exec -ti exbot bash
sqlite3 /home/db/finance.db
```