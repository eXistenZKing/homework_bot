import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)


class ExceptionBotWork(Exception):
    """Общий класс исключения для бота"""

    def __init__(self, *args: object) -> None:
        self.text = 'Сбой в работе программы!'
        self.message = args[0] if args else self.text

    def __str__(self) -> str:
        return f'{self.message}'

    def log_error(self, error):
        logger.error(f'{self.__str__()} {error}', exc_info=True)


class ExceptionEnvVariable(ExceptionBotWork):
    """Класс исключения при проверки доступноски переменных окружения"""

    def __init__(self):
        self.text = ('При проверки доступности переменных '
                     'окружения возникла ошибка')
        super().__init__(self.text)

    def add_logs(self):
        """Логирование ошибки и выход из программы"""
        logger.critical(self.__str__())
        exit()


class ExceptionSendMessage(ExceptionBotWork):
    """Класс исключения и логирования для функции отправки сообщения в чат"""

    def __init__(self):
        self.text = 'При отправке сообщения в чат произошла ошибка.'
        super().__init__(self.text)

    def log_error(self):
        logger.error(self.__str__(), exc_info=True)

    def log_debug(self):
        logger.debug('Сообщение успешно отправлено в Telegram.')


class LogsApiAnswer(ExceptionBotWork):
    """Класс логирования для функций работы с API Домашка.Практикум"""

    def log_error(self, error):
        logger.error(f'Ошибка при запросе к API: {error}')

    def log_debug(self, message):
        logger.debug(message)
