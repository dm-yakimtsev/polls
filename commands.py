from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler
from copy import deepcopy
from database.db import DataBase


class Command:
    def __init__(self):
        self.markup = None
        # Нужен для восстановления отключаемых обработчиков
        self.all_handlers = []
        self.handlers_to_remove = []
        self.database = DataBase("database/polls.db")

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

        # Отключаем все кроме нашего
        for i in context.application.handlers:
            for handler in context.application.handlers[i]:
                if str(handler.__class__) != "<class 'telegram.ext._handlers.conversationhandler.ConversationHandler'>":
                    self.handlers_to_remove.append(handler)
                elif handler.name != 'create_poll_dialoge':
                    self.handlers_to_remove.append(handler)

        for handler in self.handlers_to_remove:
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
            context.user_data['media'] = update.message.video.file_id, 'video'
        elif update.message.audio:
            context.user_data['media'] = update.message.audio.file_id, 'audio'

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

    async def get_poll_data(self, update, context):
        """Записывает данные и завершает диалог"""
        text = update.message.text

        if text == '/done':
            # Сохраняем информацию об опросе
            user_data = context.user_data
            question, answer_opt, media = user_data['question'], user_data['answer_options'], str(
                user_data[
                    'media'])
            # Делаем строку-шаблон для сохранения в бд '1-;2-;3-'
            statistics = ''.join([f'{i + 1}-;' for i in range(len(answer_opt.split(';')))])[:-1]
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

            # Если есть media записываем ее
            if media != "('', '')":
                self.database.insert_media(question, answer_opt, media, statistics)
            else:
                self.database.insert_poll_data(question, answer_opt, statistics)

            # Отчищаем user_data
            user_data.clear()

            # Восстанавливаем обработчики
            for handler in self.handlers_to_remove:
                context.application.add_handler(handler)
            self.handlers_to_remove = []

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

    async def answer_to_poll_help(self, update, context):
        """Обрабатывает текст от пользователя в диалоге ответа на опрос"""
        # Если была введенна команда /done завершаем диалог
        if update.message.text == '/done':
            # Отчищаем user_data
            context.user_data.clear()

            # Восстанавливаем обработчики
            for handler in self.handlers_to_remove:
                context.application.add_handler(handler)
            self.handlers_to_remove = []

            # Возвращаем клавиатуру
            reply_keyboard = [['Создать опрос'], ['Ответить на опрос']]
            self.markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            await update.message.reply_text('Выберите действие', reply_markup=self.markup)

            # Завершаем диалог
            return ConversationHandler.END
        else:
            await update.message.reply_text('Чтобы закончить введите /done.')
            return 1

    async def help(self, update, _):
        """Обравбатывает текст вне диалога"""
        await update.message.reply_text('Чтобы начать введите /start.')

    async def get_answer(self, update, context):
        """Начало диалога ответа на опрос"""
        # Отключаем обработчики все кроме нашего
        self.handlers_to_remove = []
        for i in context.application.handlers:
            for handler in context.application.handlers[i]:
                if str(handler.__class__) != "<class 'telegram.ext._handlers.conversationhandler.ConversationHandler'>":
                    self.handlers_to_remove.append(handler)
                elif handler.name != 'answer_to_poll_dialoge':
                    self.handlers_to_remove.append(handler)

        for handler in self.handlers_to_remove:
            context.application.remove_handler(handler)
        # Отправляем опрос и выводим подсказку
        await update.message.reply_text('Чтобы закончить введите /done.')
        await self.send_poll(update, context)
        return 1

    async def select_answer(self, update, context):
        """Отлавливает какая кнопка была нажата в ответе на опрос"""
        query = update.callback_query

        variant = int(query.data)
        await query.answer()
        # Достаем из контекста id опроса
        poll_id = context.user_data['poll_id']
        # Достаем из базы данных строку с количеством проголосовавши
        statistics = self.database.get_statistics(poll_id).split(';')

        # Если строка вида 1- значит это был первый проголосовавший
        if len(statistics[variant]) == 2:
            statistics[variant] += '1'
        else:
            # Прибавляем еще 1
            number_of_answer_opt = statistics[variant].split('-')[0]
            statistics_of_answer_opt = statistics[variant].split('-')[1]
            statistics[variant] = number_of_answer_opt + '-' + str(int(statistics_of_answer_opt) + 1)

        # Делаем из этого списка строку и сохраняем в бд
        self.database.update_statistics(poll_id, ';'.join(statistics))
        # Обновляем значение суммы
        self.database.update_total(poll_id, statistics)

        context.user_data.clear()
        # Удаляем предыдущий опрос и создаем новый
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        await self.send_poll(update, context)
        return 1

    async def send_poll(self, update, context):
        """Отправляет отформатированный опрос"""
        poll = self.database.get_random_poll()

        # Сохраняем id полученного опроса
        context.user_data['poll_id'] = poll[0]
        # Cоздаем inline клавиатуру
        answer_opt_list = poll[2].split(';')

        keyboard = [[InlineKeyboardButton(f'{answer_opt_list[i]}', callback_data=i)] for i in
                    range(len(answer_opt_list))]
        self.markup = InlineKeyboardMarkup(keyboard)

        # Если есть медиа отправляем ее, а вопрос отправляем как подпись к медиа
        if poll[3]:
            media = poll[3].split()
            file_id = media[0][2:-2]
            file_type = media[1][1:-2]
            if file_type == 'photo':
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=file_id, caption=poll[1],
                                             reply_markup=self.markup)

            elif file_type == 'video':
                await context.bot.send_video(chat_id=update.effective_chat.id, video=file_id, caption=poll[1],
                                             reply_markup=self.markup)

            elif file_type == 'audio':
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=file_id, caption=poll[1],
                                             reply_markup=self.markup)
        else:
            await context.bot.send_message(text=f'{poll[1]}', chat_id=update.effective_chat.id,
                                           reply_markup=self.markup)
