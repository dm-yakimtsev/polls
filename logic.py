import logging
from telegram.ext import Application, BaseHandler, TypeHandler, MessageHandler, filters, CommandHandler, \
    ConversationHandler, CallbackQueryHandler
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
        """Добавляем все обработчики"""
        self.app.add_handler(CommandHandler('start', self.command.start))
        self.app.add_handler(self.create_poll_dialoge())
        self.app.add_handler(self.create_answer_to_poll_dialoge())
        self.app.add_handler(MessageHandler(filters.ALL, self.command.help))

    def create_poll_dialoge(self):
        """Создает сценарий диалога опроса ConversationHandler и возвращает его"""
        conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^Создать опрос$"), self.command.get_question)],
            states={
                1: [
                    MessageHandler(
                        filters.TEXT, self.command.get_poll_data),
                    MessageHandler(
                        filters.ALL, self.command.wrong_get_answer)
                ],
                2: [
                    MessageHandler(filters.AUDIO, self.command.add_media),
                    MessageHandler(filters.PHOTO, self.command.add_media),
                    MessageHandler(filters.VIDEO, self.command.add_media),
                    MessageHandler(filters.ALL, self.command.wrong_input)
                ],
            },
            fallbacks=[CommandHandler('done', self.command.done),
                       ],
            name='create_poll_dialoge'
        )
        return conv_handler

    def create_answer_to_poll_dialoge(self):
        conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^Ответить на опрос$"), self.command.get_answer)],
            states={
                1: [
                    CallbackQueryHandler(self.command.select_answer, pattern='^.*$'),
                    MessageHandler(filters.TEXT, self.command.answer_to_poll_help)


                ],

            },
            fallbacks=[CommandHandler('done', self.command.done),
                       ],
            name='answer_to_poll_dialoge'
        )
        return conv_handler
