import types

from telegram.ext import ConversationHandler


class Command:
    def __init__(self):
        self.markup = None
        self.question = False

    async def start(self, update, context):
        """Отправляет сообщение когда получена команда /start"""
        user = update.effective_user

        await update.message.reply_html(
            rf"Привет {user.mention_html()}! Выберите действие",
            reply_markup=self.markup
        )

    async def get_question(self, update, context):
        """Начало диолога"""
        self.markup = {'remove_keyboard': True}
        await update.message.reply_text(
            'Отправьте мне вопрос, если хотите добавить фото видео или аудио введите /add_media',
            reply_markup=self.markup)
        return 1

    async def add_media(self, update, context):
        """Сохраняет медиа данные"""
        print(update.message)
        await update.message.reply_text(
            'Успешно сохраненно!')
        if self.question is False:
            await update.message.reply_text(
                'Отправьте мне вопрос.')
        else:
            await update.message.reply_text(
                'Отправьте мне вариант ответа или введите /done')
        return 1

    async def get_answer(self, update, context):
        """Завершает диалог когда введена команда /done иначе повторяется"""
        text = update.message.text

        if text == '/done':
            message = await update.message.reply_text(text='Готово')
            await message
            return ConversationHandler.END
        elif text == '/add_media':
            await update.message.reply_text('Отправьте мне медиафайл')
            return 2
        self.question = True
        await update.message.reply_text('Отправьте мне вариант ответа или введите /done')
        return 1

    async def wrong_input(self, update, context):
        await update.message.reply_text('Нужно отправить фото, видео, или аудио')
        return 2

    async def done(self, update, context):
        """Завершает диалог"""
        return ConversationHandler.END

    async def answer_to_poll(self, update, context):
        self.markup = {'remove_keyboard': True}
        await update.message.reply_text('Опрос номер 1', reply_markup=self.markup)
