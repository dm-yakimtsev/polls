import sqlite3


class DataBase:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()


    def insert_poll_data(self, question, answer_opt):
        """Сохраняет в дб вопрос и варианты ответа"""
        with self.connection:
            self.cursor.execute("INSERT INTO poll (question, answer_options) VALUES (?, ?)",
                                (question, answer_opt))
            self.connection.commit()

    def insert_media(self, question, answer_opt, media):
        """Сохраняет в дб медиа"""
        with self.connection:
            self.cursor.execute("INSERT INTO poll (question, answer_options, media) VALUES (?, ?, ?)",
                                (question, answer_opt, media))
            self.connection.commit()

    def get_random_poll(self):
        # Выбираем случайный опрос
        with self.connection:
            print()
            poll = self.cursor.execute(f"SELECT * FROM main.poll ORDER BY RANDOM() LIMIT 1").fetchall()[0]
            return poll
