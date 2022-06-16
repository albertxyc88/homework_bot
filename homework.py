
import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Dict, List, Union

import requests
import telegram
from dotenv import load_dotenv

import exceptions

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


def send_message(bot, message: str):
    """Функция отправки сообщения через Telegram."""
    return bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp: int):
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
    homework_status = requests.get(**data)
    if homework_status.status_code != HTTPStatus.OK:
        raise exceptions.APIStatusCodeError(
            'Неверный ответ сервера: '
            f'http code = {homework_status.status_code}; '
            f'reason = {homework_status.reason}; '
            f'content = {homework_status.text}'
        )
    return homework_status.json()


def check_response(
    response: Dict[str, List[Dict[str, Union[int, str]]]]
) -> Dict[str, Union[int, str]]:
    """Проверяет наличие всех ключей в ответе API practicum."""
    logging.info('Начинаем проверку ответа от API.')
    if not isinstance(response, dict):
        raise TypeError(
            'В ответе от API нет словаря: '
            f'response = {response}'
        )
    if (
        response.get('homeworks') is None
        or response.get('current_date') is None
    ):
        raise KeyError(
            'В ответе API отсутствуют необходимые ключи "homeworks" и/или '
            '"current_date".'
        )
    if not isinstance(response.get('homeworks'), list):
        raise TypeError(
            'В ответе API в ключе "homeworks" нет списка: '
            f'response = {response.get("homeworks")}'
        )

    if not response.get('homeworks'):
        logging.debug('Статус проверки не изменился')
        return []
    logging.info('Проверка ответа от API завершена.')
    return response['homeworks']


def parse_status(homework: dict[str, Union[int, str]]) -> str:
    """Проверяем статус домашнего задания."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except Exception as error:
        raise exceptions.SomethingWentWrong(f'{error}')
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


def main() -> None:
    """Основная функция работы бота."""
    # Проверяем наличие всех обязательных параметров.
    if not check_tokens():
        error_message = (
            'Отсутствуют обязательные переменные окружения: '
            'PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID. '
            'Аварийное завершение работы программы.'
        )
        logging.critical(error_message)
        sys.exit(error_message)

    logging.info('Запуск бота')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = '0'  # int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for work in homeworks:
                message = parse_status(work)
                try:
                    send_message(bot, message)
                except telegram.error.TelegramError as error:
                    logging.error(
                        f'Не удалось отправить сообщение {message} '
                        f'пользователю {TELEGRAM_CHAT_ID}. '
                        f'Ошибка: {error}'
                    )
                else:
                    logging.info(
                        f'Сообщение {message} '
                        f'пользователю {TELEGRAM_CHAT_ID} '
                        f'успешно отправлено.'
                    )
            current_timestamp = response['current_date']
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = 'Сбой в работе программы: ', error
            logging.error(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            pass


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
