import logging
from telegram.ext import Application, BaseHandler, TypeHandler, MessageHandler, filters, CommandHandler
from telegram import ReplyKeyboardMarkup
from config import TOKEN

from logic import Logic


# Запускаем логгирование


def main():
    logic = Logic()
    logic.start()

    # Запускаем приложение.
    logic.app.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()

