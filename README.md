# financial_bot

Telegram бот для учёта личных расходов и ведения бюджета.

`BOT_TOKEN` — API токен бота
`ACCESS_ID` — ID Telegram аккаунта, от которого будут приниматься сообщения


Использование с Docker показано ниже. Предварительно заполните ENV переменные, укажите локальную директорию с проектом вместо `local_project_path`. SQLite база данных будет лежать в папке проекта `db/finance.db`.

```
docker build -t expenses-bot ./
docker run -dp 127.0.0.1:3000:3000 --name exbot -v /local_project_path/db:/home/db expenses-bot
```

Чтобы войти в работающий контейнер:

```
docker exec -ti exbot bash
```

Войти в контейнере в SQL шелл:

```
docker exec -ti exbot bash
sqlite3 /home/db/finance.db
```