import sqlite3


class DataBase:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def insert_poll_data(self, question, answer_opt, statistics):
        """Сохраняет в дб вопрос и варианты ответа"""
        with self.connection:
            self.cursor.execute("INSERT INTO poll (question, answer_options, statistics) VALUES (?, ?, ?)",
                                (question, answer_opt, statistics))
            self.connection.commit()

    def insert_media(self, question, answer_opt, media, statistics):
        """Сохраняет в дб медиа"""
        with self.connection:
            self.cursor.execute("INSERT INTO poll (question, answer_options, media, statistics) VALUES (?, ?, ?, ?)",
                                (question, answer_opt, media, statistics))
            self.connection.commit()

    def get_statistics(self, id):
        with self.connection:
            res = self.cursor.execute(f"SELECT quantity FROM poll WHERE id={id}").fetchall()[0][0]
            return res

    def update_statistics(self, id, statistics):
        with self.connection:
            self.cursor.execute(f"""UPDATE poll
               SET statistics = ?
               WHERE id = ?""", (statistics, id))
            self.connection.commit()

    def get_random_poll(self):
        # Выбираем случайный опрос
        with self.connection:
            poll = self.cursor.execute(f"SELECT * FROM main.poll ORDER BY RANDOM() LIMIT 1").fetchall()[0]
            return poll
