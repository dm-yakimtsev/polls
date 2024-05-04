import sqlite3
from telegram import ReplyKeyboardMarkup
from telegram.ext import ConversationHandler
from copy import deepcopy


class Command:
    def __init__(self):
        self.markup = None
        # Нужен для восстановления отключаемых обработчиков
        self.all_handlers = []
        self.already_answered = []

    async def start(self, update, context):
        """Отправляет сообщение когда получена команда /start"""
        user = update.effective_user
        # Создаем начальную клавиатуру
        reply_keyboard = [['Создать опрос'], ['Ответить на опрос']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        self.markup = markup

        await update.message.reply_html(
            rf"Привет {user.mention_html()}! Выберите действие",
            reply_markup=self.markup
        )

    async def get_question(self, update, context):
        """Начало диолога"""
        # Копируем все обработчики
        self.all_handlers = deepcopy(context.application.handlers)
        # Отключаем все кроме нашего
        for i in context.application.handlers:
            for handler in context.application.handlers[i]:
                if str(handler.__class__) != "<class 'telegram.ext._handlers.conversationhandler.ConversationHandler'>":

                    context.application.remove_handler(handler)
                elif handler.name != 'create_poll_dialoge':

                    context.application.remove_handler(handler)

        # Создаем поля для избежания ошибки KeyError
        context.user_data['question'] = ''
        context.user_data['media'] = ('', '')
        context.user_data['answer_options'] = ''

        # Удаляем клавиатуру
        self.markup = {'remove_keyboard': True}
        await update.message.reply_text(
            'Отправьте мне вопрос, если хотите добавить фото видео или аудио введите /add_media',
            reply_markup=self.markup)

        return 1

    async def add_media(self, update, context):
        """Сохраняет медиа данные"""
        # Сохраняем и указываем на тип media
        if update.message.photo:
            context.user_data['media'] = update.message.photo[0].file_id, 'photo'
        elif update.message.video:
            context.user_data['media'] = update.message.video[0].file_id, 'video'
        elif update.message.audio:
            context.user_data['media'] = update.message.audio[0].file_id, 'audio'

        await update.message.reply_text(
            'Успешно сохраненно!')
        # Если /add_media было введенно до вопросса напоминаем пользователю ввести вопрос
        if not context.user_data['question']:
            await update.message.reply_text(
                'Отправьте мне вопрос.')
        # Иначе напоминаем ввести вариант ответа (первый, второй, и тд)
        else:
            if context.user_data['answer_options_state'] == 1:
                await update.message.reply_text('Отправьте второй вариант ответа.')
            elif context.user_data['answer_options_state'] == 2:
                await update.message.reply_text('Отправьте вариант ответа или введите /done')
            else:
                await update.message.reply_text('Отправьте первый вариант ответа.')
        # Передаем управление get_answer
        return 1

    async def get_answer(self, update, context):
        """Записывает данные и завершает диалог"""
        text = update.message.text

        if text == '/done':
            user_data = context.user_data
            # Подключение к БД
            con = sqlite3.connect("polls.db")
            cur = con.cursor()
            # Записываем все данные в бд
            question, answer_opt, media = user_data['question'], user_data['answer_options'], str(
                user_data[
                    'media'])
            # Если недостаточно данных говорим об этом и завершаем диалог
            if not question:
                # Возвращаем клавиатуру
                reply_keyboard = [['Создать опрос'], ['Ответить на опрос']]
                self.markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
                # Сообщаем о недостатке данных
                await update.message.reply_text('Опрос не был создан (нет вопроса)',
                                                reply_markup=self.markup)
                # Завершаем диалог
                return ConversationHandler.END

            if len(answer_opt.split(';')) < 2:
                # Возвращаем клавиатуру
                reply_keyboard = [['Создать опрос'], ['Ответить на опрос']]
                self.markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
                # Сообщаем о недостатке данных
                await update.message.reply_text('Опрос не был создан (меньше двух вариантов ответа)',
                                                reply_markup=self.markup)
                # Завершаем диалог
                return ConversationHandler.END

            # Если нет media не записывем ее
            if media != "('', '')":
                cur.execute("INSERT INTO poll (question, answer_options, media) VALUES (?, ?, ?)",
                            (question, answer_opt, media))
            else:
                cur.execute("INSERT INTO poll (question, answer_options) VALUES (?, ?)",
                            (question, answer_opt))
            con.commit()
            con.close()

            # Отчищаем user_data
            user_data.clear()

            # Востонавливаем обработчики
            context.application.handlers = self.all_handlers
            self.all_handlers = []

            # Возвращаем клавиатуру
            reply_keyboard = [['Создать опрос'], ['Ответить на опрос']]
            self.markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            await update.message.reply_text('Готово!', reply_markup=self.markup)

            # Завершаем диалог
            return ConversationHandler.END

        elif text == '/add_media':
            # Перенаправляем на 2 состояние для сохранения медиа
            await update.message.reply_text('Отправьте мне медиафайл')
            return 2

        elif not context.user_data['question']:
            # Если получен вопрос, записываем и просим дать ответ
            context.user_data['question'] = text
            await update.message.reply_text('Отправьте первый вариант ответа.')
            return 1
        else:

            # Если answer_options еще пустой, то был получен первый ответ
            if not context.user_data['answer_options']:
                # Записываем и просим дать второй
                context.user_data['answer_options'] = f"{text}"
                # Для /add_media
                context.user_data['answer_options_state'] = 1
                await update.message.reply_text('Отправьте мне второй вариант ответа.')
                return 1
            # Если в answer_options только 1 вариант ответа, то был получен второй
            elif len(context.user_data['answer_options'].split(';')) == 1:
                context.user_data['answer_options'] = f"{context.user_data['answer_options']};{text}"
                context.user_data['answer_options_state'] = 2
                await update.message.reply_text('Отправьте вариант ответа или введите /done')
                return 1
            else:
                context.user_data['answer_options'] = f"{context.user_data['answer_options']};{text}"
                await update.message.reply_text('Отправьте вариант ответа или введите /done')
                return 1

    async def wrong_input(self, update, context):
        """Оброботчик для других типов помимо video, photo, audio"""
        await update.message.reply_text('Нужно отправить фото, видео, или аудио')
        return 2

    async def wrong_get_answer(self, update, context):
        """Оброботчик для других типов помимо text"""
        await update.message.reply_text('Eсли хотите добавить фото видео или аудио введите /add_media')
        return 1

    async def done(self, update, context):
        """Завершает диалог"""
        return ConversationHandler.END

    async def help(self, update, _):
        await update.message.reply_text('Чтобы начать введите /start.')
