from http import HTTPStatus
import logging
import os
import time

from dotenv import load_dotenv
import requests
import telegram

from exceptions import (ExceptionEnvVariable,
                        ExceptionSendMessage,
                        LogsApiAnswer,
                        ExceptionAvailabilityHomework)


load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    env_tokens = (TELEGRAM_CHAT_ID, PRACTICUM_TOKEN, TELEGRAM_TOKEN)
    if all(env_tokens):
        return True
    else:
        raise ExceptionEnvVariable


def send_message(bot, message):
    """Отправка сообщения в чате об изменении статуса ревью."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.debug('Сообщение успешно отправлено в чат Telegram')


def get_api_answer(timestamp):
    """Запрос к API Практикум.Домашка."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        raise LogsApiAnswer(error)

    if response.status_code != HTTPStatus.OK:
        raise requests.RequestException

    response = response.json()
    return response


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ от API получен не в виде словаря')

    elif 'homeworks' not in response.keys():
        raise KeyError('Ключ "homeworks" отсутствует в словаре response')

    elif not isinstance(response['homeworks'], list):
        raise TypeError('Ключ "homeworks" не соответствует типа данных list')

    if not response['homeworks'][0]:
        raise ExceptionAvailabilityHomework
    else:
        return response['homeworks'][0]


def parse_status(homework):
    """Парсинг необходимой информации из ответа API."""
    for key in ['homework_name', 'status']:
        if key not in homework:
            message = f'В списке "homeworks" отсутствует ключ "{key}"'
            raise LogsApiAnswer(message)

    if homework['status'] not in HOMEWORK_VERDICTS.keys():
        message = ('Статус последней отправленной '
                   'домашней работы не соответствует документации')
        raise LogsApiAnswer(message)

    verdict = HOMEWORK_VERDICTS[homework['status']]
    homework_name = homework['homework_name']
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 1704056618
    message_to_chat = ''

    while True:
        try:

            check_tokens()

            api_answer = get_api_answer(timestamp)
            check = check_response(api_answer)
            if message_to_chat != parse_status(check):
                message_to_chat = parse_status(check)
                send_message(bot, message_to_chat)
            else:
                raise ExceptionSendMessage

        except ExceptionEnvVariable as error:
            logger.critical(error)
            exit()
        except LogsApiAnswer as error:
            logger.error(error)
        except ExceptionAvailabilityHomework:
            logger.error('Список "homeworks" пуст.')
        except ExceptionSendMessage:
            logger.debug('Статус последней отправленной '
                         'работы на ревью не поменялся.')
        except requests.RequestException:
            logger.error('Ответ от API не равен коду "200"')
        except Exception as error:
            logger.error(error)

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
