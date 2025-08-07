import sqlite3
from datetime import datetime
import os
import cv2
import numpy as np
from math import sqrt, ceil, floor
import random
DATABASE = 'prizes.db'

class DatabaseManager:
    def __init__(self, database):
        self.database = database
        self.create_tables()
    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    user_name TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS prizes (
                    prize_id INTEGER PRIMARY KEY,
                    image TEXT,
                    used INTEGER DEFAULT 0
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS winners (
                    user_id INTEGER,
                    prize_id INTEGER,
                    win_time TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    FOREIGN KEY(prize_id) REFERENCES prizes(prize_id)
                )
            ''')
            conn.commit()

    def execute_query(self, query, params=(), fetchone=False):
        try:
            with sqlite3.connect(self.database) as conn:
                cur = conn.cursor()
                cur.execute(query, params)
                if fetchone:
                    return cur.fetchone()
                return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        
    def add_user(self, user_id, user_name):
        self.execute_query('INSERT INTO users VALUES (?, ?)', (user_id, user_name))

    def get_users(self):
        return self.execute_query('SELECT user_id, user_name FROM users')
    
    def add_prize(self, data):
        try:
            conn = sqlite3.connect(self.database)
            with conn:
                conn.executemany('INSERT INTO prizes (image) VALUES (?)', data)
                conn.commit()
        except sqlite3.Error as e:
            print(f"An error occurred while adding prizes: {e}")

    def add_winner(self, user_id, prize_id):
        win_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            conn = sqlite3.connect(self.database)
            with conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM winners WHERE user_id = ? AND prize_id = ?", (user_id, prize_id))
                if cur.fetchall():
                    return 0
                else:
                    conn.execute('INSERT INTO winners (user_id, prize_id, win_time) VALUES (?, ?, ?)', (user_id, prize_id, win_time))
                    conn.commit()
                    return 1
        except sqlite3.Error as e:
            print(f"An error occurred while adding winner: {e}")
            return 0
        
    def mark_prize_used(self, prize_id):
        try:
            conn = sqlite3.connect(self.database)
            with conn:
                conn.execute('UPDATE prizes SET used = 1 WHERE prize_id = ?', (prize_id,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"An error occurred while marking prize as used: {e}")

    def get_prize_img(self, prize_id):
        try:
            conn = sqlite3.connect(self.database)
            with conn:
                cur = conn.cursor()
                cur.execute('SELECT image FROM prizes WHERE prize_id = ?', (prize_id,))
                result = cur.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            print(f"An error occurred while fetching prize image: {e}")
            return None
        
    def get_random_prize(self):
        try:
            conn = sqlite3.connect(self.database)
            with conn:
                cur = conn.cursor()
                cur.execute('SELECT prize_id, image FROM prizes WHERE used = 0')
                available_prizes = cur.fetchall()
                return random.choice(available_prizes) if available_prizes else None
        except sqlite3.Error as e:
            print(f"An error occurred while fetching random prize: {e}")
            return None
        
    def get_winners_count(self, prize_id):
        try:
            conn = sqlite3.connect(self.database)
            with conn:
                cur = conn.cursor()
                cur.execute('SELECT COUNT(*) FROM winners WHERE prize_id = ?', (prize_id,))
                return cur.fetchone()[0]
        except sqlite3.Error as e:
            print(f"An error occurred while counting winners: {e}")
            return 0
        
    def get_winners_img(self, user_id):
        try:
            conn = sqlite3.connect(self.database)
            with conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT image FROM winners 
                    INNER JOIN prizes ON winners.prize_id = prizes.prize_id
                    WHERE user_id = ?
                ''', (user_id,))
                return cur.fetchall()
        except sqlite3.Error as e:
            print(f"An error occurred while fetching winner images: {e}")
            return []
        
    def get_rating(self):
        try:
            conn = sqlite3.connect(self.database)
            with conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT users.user_name, COUNT(winners.prize_id) as count_prize 
                    FROM winners 
                    INNER JOIN users ON users.user_id = winners.user_id
                    GROUP BY winners.user_id 
                    ORDER BY count_prize DESC
                    LIMIT 10
                ''')
                return cur.fetchall()
        except sqlite3.Error as e:
            print(f"An error occurred while fetching ratings: {e}")
            return []

def hide_img(img_name):
    img_path = f'img/{img_name}'
    if not os.path.exists(img_path):
        print(f"Image {img_name} does not exist.")
        return
def create_collage(image_paths):
    images = []
    for path in image_paths:
        if os.path.exists(path):
            img = cv2.imread(path)
            images.append(img)

    if not images:
        return None

    collage_width = max(img.shape[1] for img in images)
    collage_height = sum(img.shape[0] for img in images)
    collage = np.zeros((collage_height, collage_width, 3), dtype=np.uint8)

    y_offset = 0
    for img in images:
        collage[y_offset:y_offset + img.shape[0], :img.shape[1]] = img
        y_offset += img.shape[0]
        
        return collage

    image = cv2.imread(img_path)
    blurred_image = cv2.GaussianBlur(image, (15, 15), 0)
    pixelated_image = cv2.resize(blurred_image, (30, 30), interpolation=cv2.INTER_NEAREST)
    pixelated_image = cv2.resize(pixelated_image, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(f'hidden_img/{img_name}', pixelated_image)

if __name__ == '__main__':
    manager = DatabaseManager(DATABASE)
    
    # Проверка существования папок
    os.makedirs('img', exist_ok=True)
    os.makedirs('hidden_img', exist_ok=True)

    # Добавление призов в базу данных
    prizes_img = os.listdir('img')
    data = [(x,) for x in prizes_img]
    manager.add_prize(data)

    # Пример использования функций
    manager.add_user(1, 'User1')
    random_prize = manager.get_random_prize()

    if random_prize:
        prize_id, image = random_prize
        print(f"Random prize: {image}")
        hide_img(image)
        manager.add_winner(1, prize_id)

    # Получение рейтинга
    rating = manager.get_rating()
    print("Top winners:")
    for user_name, count in rating:
        print(f"{user_name}: {count} prizes")
