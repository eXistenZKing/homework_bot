class ExceptionBotWork(Exception):
    """Общий класс исключения для бота."""

    def __init__(self, *args):
        """Условие наличия подробностей сообщения об ошибке."""
        self.message = args[0] if args else None

    def __str__(self):
        """Сообщение при вызове ошибки."""
        if self.message:
            return f'Ошибка в работе: "{self.message}"'
        else:
            return 'В работе бота произошла непредвиденная ошибка.'


class ExceptionEnvVariable(ExceptionBotWork):
    """Исключение при проверки доступноски переменных окружения."""


class ExceptionSendMessage(ExceptionBotWork):
    """Исключение для функции отправки сообщения в чат."""


class LogsApiAnswer(ExceptionBotWork):
    """Исключение для функций работы с API Домашка.Практикум."""


class ExceptionAvailabilityHomework(ExceptionBotWork):
    """Исключение об отсутсвии домашней работы в ответе API."""
