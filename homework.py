"""DOCSTRING."""
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Union

import requests
import telegram
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """DOCSTRING."""
    print(TELEGRAM_CHAT_ID)
    return bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """DOCSTRING."""
    timestamp = current_timestamp or int(time.time())
    data = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {
            'from_date': timestamp,
        },
    }
    # Делаем GET-запрос к url с заголовками headers и параметрами params
    homework_status = requests.get(**data)
    return homework_status.json()


def check_response(
    response: Dict[str, List[Dict[str, Union[int, str, datetime]]]]) -> Dict:
    """Проверяет наличие всех ключей в ответе API practicum."""
    logging.info('Начинаем проверку ответа от API.')
    if not isinstance(response, list):
        raise TypeError(
            'В ответет от API нет списка: '
            f'response = {response}'
        )
    homeworks = {}

    for item in response:
        if not isinstance(item, dict):
            raise TypeError



def parse_status(homework):
    """DOCSTRING."""
    homework_name = homework['homework_name']
    # homework_status = homework['status']

    ...

    verdict = ...

    ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяем наличие всех необходимых переменных окружения."""
    return all(
        (
            PRACTICUM_TOKEN,
            TELEGRAM_TOKEN,
            TELEGRAM_CHAT_ID
        )
    )


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        error_message = (
            f'Отсутствуют обязательные переменные окружения: '
            'PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID. '
            'Аварийное завершение работы программы.'
        )
        logging.critical(error_message)
        sys.exit(error_message)

    logging.info('Запуск бота')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = '0'  # int(time.time())
    current_answer = None
    previous_answer = current_answer
    while True:
        try:
            response = get_api_answer(current_timestamp)
            print(response)
            homework = response['homeworks'][0]
            send_message(bot, homework)

            # current_timestamp = ...
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = 'Сбой в работе программы: ', error
            logging.error(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            pass


if __name__ == '__main__':
    log_file = os.path.join(BASE_DIR, 'output.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s, %(levelname)s, %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    main()
