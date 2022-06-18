"""Бот проверяющий статусы домашнего задания с отправкой в Telegram."""
import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

previous_error = None

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Функция отправки сообщения через Telegram."""
    logging.info('Отправляем сообщение в Telegram.')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logging.error(
            f'Не удалось отправить сообщение {message} '
            f'пользователю {TELEGRAM_CHAT_ID}. '
            f'Ошибка: {error}'
        )
        raise telegram.error.TelegramError(
            f'Ошибка при отправке сообщения в Telegram: {error}'
        )
    else:
        logging.info(
            f'Сообщение {message} '
            f'пользователю {TELEGRAM_CHAT_ID} '
            f'успешно отправлено.'
        )


def get_api_answer(current_timestamp):
    """Получаем ответ от API."""
    timestamp = current_timestamp or int(time.time())
    data = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {
            'from_date': timestamp,
        },
    }
    # Делаем GET-запрос к url с заголовками headers и параметрами params
    logging.info('Делаем запрос к API.')
    try:
        homework_status = requests.get(**data)
    except Exception as error:
        raise exceptions.ConnectionError(f'Ошибка подключения к API: {error}')

    if homework_status.status_code != HTTPStatus.OK:
        message = (
            f'При отправке запроса к API с параметрами: {data}'
            'пришел неверный ответ от сервера: '
            f'http code = {homework_status.status_code}; '
            f'reason = {homework_status.reason}; '
            f'content = {homework_status.text}'
        )
        raise exceptions.APIStatusCodeError(message)
    logging.info('Запрос к API завершен.')
    return homework_status.json()


def check_response(response):
    """Проверяет наличие всех ключей в ответе API practicum."""
    logging.info('Начинаем проверку ответа от API.')
    if not isinstance(response, dict):
        raise TypeError(
            'В ответе от API нет словаря: '
            f'response = {response}'
        )
    if response.get('homeworks') is None:
        raise exceptions.NoDictKey(
            'В ответе API отсутствует необходимый ключ "homeworks"!'
        )
    if response.get('current_date') is None:
        raise exceptions.NoDictKey(
            'В ответе API отсутствует необходимый ключ "current_date"!'
        )
    if not isinstance(response.get('homeworks'), list):
        raise TypeError(
            'В ответе API в ключе "homeworks" нет списка: '
            f'response = {response.get("homeworks")}'
        )
    logging.info('Проверка ответа от API завершена.')
    if len(response.get('homeworks')) == 0:
        logging.info('Список работ пустой или работу еще не взяли на проверку')
    return response['homeworks']


def parse_status(homework):
    """Проверяем статус домашнего задания."""
    logging.info('Начинаем проверку статуса домашнего задания.')
    if homework['homework_name'] is None:
        raise exceptions.NoDictKey(
            'В ответе API отсутствует необходимый ключ "homework_name"!'
        )
    else:
        homework_name = homework['homework_name']
    if homework['status'] is None:
        raise exceptions.NoDictKey(
            'В ответе API отсутствует необходимый ключ "status"!'
        )
    else:
        homework_status = homework['status']
    if HOMEWORK_VERDICTS[homework_status] is None:
        raise exceptions.NoDictKey(
            f'В словаре "HOMEWORK_VERDICTS" не найден ключ {homework_status}!'
        )
    else:
        verdict = HOMEWORK_VERDICTS[homework_status]
    logging.info('Окончание проверки статуса домашнего задания.')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяем наличие всех необходимых переменных окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return all(tokens)


def main() -> None:
    """Основная функция работы бота."""
    global previous_error
    # Проверяем наличие всех обязательных параметров.
    if not check_tokens():
        error_message = (
            'Отсутствуют обязательные переменные окружения: '
            'PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID. '
            'Аварийное завершение работы программы.'
        )
        logging.critical(error_message)
        sys.exit(error_message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.info('Запуск бота')
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for work in homeworks:
                message = parse_status(work)
            send_message(bot, message)
            current_timestamp = response['current_date']

        except Exception as error:
            message = 'Сбой в работе программы: ', error
            logging.error(message)
            if message != previous_error:
                send_message(bot, message)
                previous_error = message

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    # Получаем текущую директорию откуда запущена программа.
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Подготавливаем log файл для хранения журнала.
    log_file = os.path.join(BASE_DIR, 'output.log')
    # Устанавливаем уровень, формат, обработчик логов.
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s, %(levelname)s, %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    main()
