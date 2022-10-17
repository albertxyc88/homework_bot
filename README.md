# Telegram bot.

## Бот проверяющий статусы домашнего задания на Яндекс.Практикум с отправкой результатов в Telegram.

Подключается к API https://practicum.yandex.ru/api/user_api/homework_statuses/.

Получает статусы домашнего задания и отправляет сообщение в Telegram.

- Ведется полный лог работы бота.
- Проверяется корректность ответа от сервера.
- Отправляет "человеческий" статус домашнего задания в чат.


## Технологии

Python 3.7, Telegram, bot.

## Установка

- склонируйте репозитарий 

- создайте и активируйте виртуальное окружение

`python3 -m venv venv`

`python3 venv/bin/activate`

- установите все зависимости из файла requirements.txt командой: 

`pip install -r requirements.txt`

- для запуска в работу необходимо заполнить своими данными токен подключения к API Яндекс.Практикум, токен Telegram, и Telegram chat ID

`PRACTICUM_TOKEN = 'your_practicum_token'`

`TELEGRAM_TOKEN = 'your_telegram_token'`

`TELEGRAM_CHAT_ID = 'your_telegram_chat_id'`
