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
        reply_keyboard = [['Создать опрос', 'Ответить на опрос']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        self.command.markup = markup
        self.app.add_handler(CommandHandler('start', self.command.start))
