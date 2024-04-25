import logging
import os
import time

from dotenv import load_dotenv
import requests
import telegram

from exceptions import (ExceptionEnvVariable,
                        ExceptionSendMessage,
                        LogsApiAnswer,
                        ExceptionBotWork)


load_dotenv()

logger = logging.getLogger(__name__)

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
    try:
        if None in [TELEGRAM_CHAT_ID, PRACTICUM_TOKEN, TELEGRAM_TOKEN]:
            raise ExceptionEnvVariable
    except ExceptionEnvVariable as error:
        error.add_logs()


def send_message(bot, message):
    """Отправка сообщения в чате об изменении статуса ревью."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except ExceptionSendMessage as error:
        error.log_error()
    else:
        ExceptionSendMessage().log_debug()


def get_api_answer(timestamp):
    """Запрос к API Практикум.Домашка."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except Exception as error:
        LogsApiAnswer().log_error(error)

    if response.status_code != 200:
        error = 'Код ответа страницы отличен от "200"'
        raise LogsApiAnswer().log_error(error)

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

    try:
        return response['homeworks'][0]
    except IndexError:
        return None


def parse_status(homework):
    """Парсинг необходимой информации из ответа API."""
    if homework['status'] not in HOMEWORK_VERDICTS.keys():
        error = ('Статус последней отправленной '
                 'домашней работы не соответствует документации')
        raise LogsApiAnswer().log_error(error)
    elif 'homework_name' not in homework:
        error = 'В списке "homeworks" отсутствует ключ "homework_name"'
        raise LogsApiAnswer().log_error(error)
    verdict = HOMEWORK_VERDICTS[homework['status']]
    homework_name = homework['homework_name']
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 1704056618
    message_to_chat = ''

    while True:
        try:

            api_answer = get_api_answer(timestamp)
            check = check_response(api_answer)
            if not check:
                LogsApiAnswer().log_debug('Список "homeworks" пуст.')
            elif message_to_chat != parse_status(check):
                message_to_chat = parse_status(check)
                send_message(bot, message_to_chat)
            else:
                LogsApiAnswer().log_debug('Статус последней отправленной '
                                          'работы на ревью не поменялся.')

        except Exception as error:
            ExceptionBotWork().log_error(error)

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
