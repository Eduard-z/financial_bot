# financial_bot

Telegram бот для учёта личных расходов и ведения бюджета.

`BOT_TOKEN` — API токен бота
`ACCESS_ID` — ID Telegram аккаунта, от которого будут приниматься сообщения

Использование с Docker показано ниже. 
SQLite база данных будет лежать в папке проекта `db/finance.db`.

```
docker build -t fin-image .
docker run --rm -itd -v $(pwd)/artefacts:/home/artefacts -v $(pwd)/db:/home/db fin-image
```

Чтобы войти в работающий контейнер:

```
docker exec -ti b5d1 bash
```

Войти в контейнере в SQL шелл:

```
docker exec -ti exbot bash
sqlite3 /home/db/finance.db
```