import logging
from telegram.ext import Application, BaseHandler, TypeHandler, MessageHandler, filters, CommandHandler, \
    ConversationHandler
from telegram import ReplyKeyboardMarkup
from commands import Command
from config import TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


class Logic:
    def __init__(self):
        self.app = Application.builder().token(TOKEN).build()
        self.command = Command()

    def start(self):
        """Добавляем все обработчики и создаем начальную клавиатуру"""
        reply_keyboard = [['Создать опрос', 'Ответить на опрос']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        self.command.markup = markup
        self.app.add_handler(CommandHandler('start', self.command.start))
        self.app.add_handler(MessageHandler(filters.Regex("^Ответить на опрос$"), self.command.answer_to_poll))
        self.app.add_handler(self.create_poll_dialoge())

    def create_poll_dialoge(self):
        """Создает диалог опроса ConversationHandler и возвращает его"""
        conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^Создать опрос$"), self.command.get_question)],
            states={
                1: [
                    MessageHandler(
                        filters.TEXT, self.command.get_answer
                    )
                ]

            },
            fallbacks=[CommandHandler('done', self.command.done)],
        )
        return conv_handler