from telegram.ext import ConversationHandler



class Command:
    def __init__(self):
        self.markup = None


    async def start(self, update, context):
        """Отправляет сообщение когда получена команда /start"""
        user = update.effective_user
        await update.message.reply_html(
            rf"Привет {user.mention_html()}! Выберите действие",
            reply_markup=self.markup
        )




