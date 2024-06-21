from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler
from copy import deepcopy
from database.db import DataBase


class Command:
    def __init__(self):
        self.markup = None
        self.database = DataBase("database/polls.db")

    async def start(self, update, context):
        """Отправляет сообщение когда получена команда /start"""
        user = update.effective_user
        user_id = update.effective_chat.id
        if len(self.database.find_user(user_id)) == 0:
            # Если пользователь не найден запоминаем его
            self.database.remember_user(user_id)

        # Создаем начальную клавиатуру
        reply_keyboard = [['Создать опрос', 'Ответить на опрос'], ['Мои опросы']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        self.markup = markup
        await update.message.reply_html(
            rf"Привет {user.mention_html()}! Выберите действие.",
            reply_markup=self.markup
        )

    async def get_question(self, update, context):
        """Начало диолога"""

        # Создаем поля для избежания ошибки KeyError
        context.user_data['question'] = ''
        context.user_data['media'] = ('', '')
        context.user_data['answer_options'] = ''

        # Удаляем клавиатуру
        self.markup = {'remove_keyboard': True}
        await update.message.reply_text(
            'Отправьте мне вопрос, если хотите добавить фото видео или аудио введите /add_media,'
            ' чтобы завершить введите /done',
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

        return 1

    async def get_poll_data(self, update, context):
        """Записывает данные и завершает диалог"""
        text = update.message.text

        if text == '/done':

            # Сохраняем информацию об опросе
            user_data = context.user_data
            user_id = int(update.effective_user.id)
            question, answer_opt, media = user_data['question'], user_data['answer_options'], str(
                user_data[
                    'media'])
            # Делаем строку-шаблон для сохранения в бд '1-;2-;3-'
            statistics = ''.join([f'{i + 1}-;' for i in range(len(answer_opt.split(';')))])[:-1]

            # Возвращаем клавиатуру
            reply_keyboard = [['Создать опрос', 'Ответить на опрос'], ['Мои опросы']]
            self.markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

            # Если недостаточно данных говорим об этом и завершаем диалог
            if not question:
                # Сообщаем о недостатке данных
                await update.message.reply_text('Опрос не был создан (нет вопроса)',
                                                reply_markup=self.markup)
                # Отчищаем user_data
                user_data.clear()

                # Завершаем диалог
                return ConversationHandler.END

            if len(answer_opt.split(';')) < 2:
                # Сообщаем о недостатке данных
                await update.message.reply_text('Опрос не был создан (меньше двух вариантов ответа)',
                                                reply_markup=self.markup)
                # Отчищаем user_data
                user_data.clear()

                # Завершаем диалог
                return ConversationHandler.END

            # Если есть media записываем ее
            if media != "('', '')":
                self.database.insert_media(question, answer_opt, media, user_id, statistics)
            else:
                self.database.insert_poll_data(question, answer_opt, user_id, statistics)

            # Отчищаем user_data
            user_data.clear()
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
            context.user_data['answer_options_state'] = 0
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
        if update.message.text == '/done':
            # Перенаправляем на self.get_poll_data
            await self.get_poll_data(update, context)
            return ConversationHandler.END

        await update.message.reply_text('Нужно отправить фото, видео, или аудио')
        return 2

    async def wrong_data(self, update, context):
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
            # Возвращаем клавиатуру
            reply_keyboard = [['Создать опрос', 'Ответить на опрос'], ['Мои опросы']]
            self.markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            await update.message.reply_text('Выберите действие', reply_markup=self.markup)
            # Отчищаем user_data
            context.user_data.clear()
            # Завершаем диалог
            return ConversationHandler.END
        else:
            await update.message.reply_text('Чтобы закончить введите /done.')
            return 3

    async def help(self, update, _):
        """Обрабатывает текст вне диалога"""
        await update.message.reply_text('Чтобы начать введите /start.')

    async def get_answer(self, update, context):
        """Начало диалога ответа на опрос"""

        # Удаляем клавиатуру
        self.markup = {'remove_keyboard': True}
        # Отправляем опрос и выводим подсказку
        await update.message.reply_text('Чтобы закончить введите /done.', reply_markup=self.markup)
        await self.send_poll(update, context)
        # Выполняется когда пользователь уже ответил на все опросы
        if context.user_data['end']:
            context.user_data.clear()
            return ConversationHandler.END
        return 3

    async def select_answer(self, update, context):
        """Отлавливает какая кнопка была нажата в ответе на опрос и сохраняет данные"""
        query = update.callback_query
        variant = int(query.data)
        await query.answer()
        self.write_statistic(context.user_data['poll_id'], update.effective_chat.id, variant)

        # Удаляем предыдущий опрос и создаем новый
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        await self.send_poll(update, context)
        # Выполняется когда пользователь уже ответил на все опросы
        if context.user_data['end']:
            context.user_data.clear()
            return ConversationHandler.END
        return 3

    async def send_poll(self, update, context):
        """Отправляет отформатированный опрос"""
        user_id = int(update.effective_user.id)
        responses = self.database.get_responses(user_id).split(';')
        context.user_data['end'] = False
        if len(responses) != 1 and len(responses) - 1 == len(self.database.get_all_polls()):
            context.user_data['end'] = True
            # Возвращаем клавиатуру
            reply_keyboard = [['Создать опрос', 'Ответить на опрос'], ['Мои опросы']]
            self.markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            await context.bot.send_message(text=f'Приходите позже.Вы ответили на все опросы.',
                                           chat_id=update.effective_chat.id,
                                           reply_markup=self.markup)
        else:
            poll = self.database.get_random_poll()
            while str(poll[0]) in responses:
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
                    context.user_data['poll_msg'] = await context.bot.send_photo(chat_id=update.effective_chat.id,
                                                                                 photo=file_id, caption=poll[1],
                                                                                 reply_markup=self.markup)

                elif file_type == 'video':
                    context.user_data['poll_msg'] = await context.bot.send_video(chat_id=update.effective_chat.id,
                                                                                 video=file_id, caption=poll[1],
                                                                                 reply_markup=self.markup)

                elif file_type == 'audio':
                    context.user_data['poll_msg'] = await context.bot.send_audio(chat_id=update.effective_chat.id,
                                                                                 audio=file_id, caption=poll[1],
                                                                                 reply_markup=self.markup)
            else:
                context.user_data['poll_msg'] = await context.bot.send_message(text=f'{poll[1]}',
                                                                               chat_id=update.effective_chat.id,
                                                                               reply_markup=self.markup)

    async def write_results(self, update, context):
        query = update.callback_query
        variant = int(query.data)
        await query.answer()
        self.write_statistic(context.user_data['poll_id'], update.effective_chat.id, variant)
        # Удаляем предыдущий опрос
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

    async def show_polls(self, update, context):
        user_id = int(update.effective_user.id)
        polls = self.database.get_user_polls(user_id)
        if len(polls) != 0:
            keyboard = [[InlineKeyboardButton(f'{poll[1]}', callback_data=poll[0])] for poll in polls]
            self.markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text('Выберите опрос, чтобы выйти введите /done', reply_markup=self.markup)
            return 4
        else:
            # Возвращаем клавиатуру
            reply_keyboard = [['Создать опрос', 'Ответить на опрос'], ['Мои опросы']]
            self.markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            await context.bot.send_message(text=f'Похоже у вас нет опросов, чтобы создать опрос введите Создать опрос',
                                           chat_id=update.effective_chat.id,
                                           reply_markup=self.markup)
            return ConversationHandler.END

    async def show_stats(self, update, context):
        query = update.callback_query

        poll_id = int(query.data)
        await query.answer()
        poll = self.database.get_poll(poll_id=poll_id)
        # Возвращаем клавиатуру
        reply_keyboard = [['Создать опрос', 'Ответить на опрос'], ['Мои опросы']]
        self.markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        msg = f'{poll[1]}\n{self.format_anw_options_stats(poll[0], poll[2], poll[5], poll[6])}'
        # Если есть медиа отправляем ее, а вопрос отправляем как подпись к медиа
        if poll[3]:
            media = poll[3].split()
            file_id = media[0][2:-2]
            file_type = media[1][1:-2]
            if file_type == 'photo':
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=file_id, caption=msg,
                                             reply_markup=self.markup)

            elif file_type == 'video':
                await context.bot.send_video(chat_id=update.effective_chat.id, video=file_id, caption=msg,
                                             reply_markup=self.markup)

            elif file_type == 'audio':
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=file_id, caption=msg,
                                             reply_markup=self.markup)
        else:
            await context.bot.send_message(text=f'{msg}', chat_id=update.effective_chat.id,
                                           reply_markup=self.markup)
        return ConversationHandler.END

    async def show_stats_help(self, update, context):
        if update.message.text == '/done':
            # Возвращаем клавиатуру
            reply_keyboard = [['Создать опрос', 'Ответить на опрос'], ['Мои опросы']]
            self.markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            await update.message.reply_text('Выберите действие', reply_markup=self.markup)
            return ConversationHandler.END
        await update.message.reply_text('Выберите опрос, чтобы выйти введите /done')
        return 4

    def format_anw_options_stats(self, poll_id, answ_opt, stats, total):
        msg = ''
        stats_list = stats.split(';')
        answ_opt_list = answ_opt.split(';')
        for i in range(len(answ_opt_list)):
            if len(stats_list[i]) != 2:
                msg += f'{answ_opt_list[i]} - {stats_list[i][2:]} голосов\n'
            else:
                msg += f'{answ_opt_list[i]} - 0 голосов\n'
        if total is not None:
            msg += 'Всего:' + str(total)
        else:
            msg += 'Всего:' + str(0)
        msg += '\nСсылка - ' + f"https://t.me/polls0654_bot?start={poll_id}"
        return msg

    def write_statistic(self, poll_id, user_id, variant):
        # Достаем из базы данных строку с количеством проголосовавших
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
        self.database.insert_responses(int(user_id), poll_id)
