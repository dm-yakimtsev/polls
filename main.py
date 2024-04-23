# Импортируем необходимые классы.
import logging
from telegram.ext import Application, BaseHandler, TypeHandler, MessageHandler, filters
from config import TOKEN

# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


def main():
    # Создаём объект Application.
    application = Application.builder().token(TOKEN).build()

    # Запускаем приложение.
    application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
