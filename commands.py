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

    async def get_question(self, update, context):
        """Начало диолога"""
        await update.message.reply_text('Отправьте мне вопрос')
        return 1

    async def get_answer(self, update, context):
        """Завершает диалог когда введена команда /done иначе повторяется"""
        text = update.message.text
        print(text)
        if text == '/done':
            await update.message.reply_text('Готово!')
            return ConversationHandler.END
        await update.message.reply_text('Отправьте мне вариант ответа или введите /done')
        return 1

    async def done(self, update, context):
        """Завершает диалог"""
        return ConversationHandler.END

    async def answer_to_poll(self, update, context):
        await update.message.reply_text('Опрос номер 1')
