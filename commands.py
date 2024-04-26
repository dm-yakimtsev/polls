import types
import sqlite3
from telegram import ReplyKeyboardMarkup
from telegram.ext import ConversationHandler


class Command:
    def __init__(self):
        self.markup = None
        self.question = False
        self.poll_data = {
            'question': '',
            'answer_options': '',
            'media': ('', ''),
            'quantity': 0,
            'total': 0,
        }

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
            self.poll_data['media'] = update.message.photo[0].file_id, 'photo'
        elif update.message.video:
            self.poll_data['media'] = update.message.video[0].file_id, 'video'
        elif update.message.audio:
            self.poll_data['media'] = update.message.audio[0].file_id, 'audio'

        await update.message.reply_text(
            'Успешно сохраненно!')
        # Если /add_media было введенно до вопросса напоминаем пользователю ввести вопрос
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
            # Подключение к БД
            con = sqlite3.connect("polls.db")
            cur = con.cursor()
            # Записываем все данные в бд
            question, answer_opt, media = self.poll_data['question'], self.poll_data['answer_options'], self.poll_data[
                'media']
            cur.execute("INSERT INTO poll (question, answer_options, media) VALUES (?, ?, ?)",
                        (question, answer_opt, media))
            con.commit()
            con.close()

            print(self.poll_data)
            # Обновляем poll_data
            self.poll_data = {
                'question': '',
                'answer_options': '',
                'media': '',
                'quantity': 0,
                'total': 0,
            }
            # Обновляем флаг для вопроса
            self.question = False

            # Возвращаем клавиатуру
            reply_keyboard = [['Создать опрос'], ['Ответить на опрос']]
            self.markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            # Завершаем диалог
            await update.message.reply_text(text='Готово!', reply_markup=self.markup)

            return ConversationHandler.END
        elif text == '/add_media':
            # Перенаправляем на 2 состояние для сохранения медиа
            await update.message.reply_text('Отправьте мне медиафайл')
            return 2
        elif not self.question:
            # Если получен вопрос, записывем
            self.poll_data['question'] = text
            self.question = True
        else:
            # Записываем другой текст как варианты ответа если вопрос уже был получен
            if self.poll_data['answer_options']:
                self.poll_data['answer_options'] = f"{self.poll_data['answer_options']};{text}"
            else:
                self.poll_data['answer_options'] = f"{text}"

        await update.message.reply_text('Отправьте мне вариант ответа или введите /done')
        # Повторяется пока не будет отправленн /done
        return 1

    async def wrong_input(self, update, context):
        """Оброботчик для других типов помимо video, photo, audio"""
        await update.message.reply_text('Нужно отправить фото, видео, или аудио')
        return 2

    async def done(self, update, context):
        """Завершает диалог"""
        return ConversationHandler.END

    async def answer_to_poll(self, update, context):
        # Удаляем клавиатуру
        self.markup = {'remove_keyboard': True}
        await update.message.reply_text('Опрос номер 1', reply_markup=self.markup)
