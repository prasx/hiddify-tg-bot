import logging
import sqlite3
import json
from datetime import datetime

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            uuid TEXT,
            profile TEXT,
            pos TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE
        )
    """)
    conn.commit()
    conn.close()


def get_all_user_ids():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    logging.info(f"Результат запроса get_all_user_ids: {users}")
    conn.close()
    return [user[0] for user in users]
    

def get_user(user_id):
    logging.info(f"Запрос данных пользователя с user_id: {user_id}")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    logging.info(f"Результат запроса get_user для user_id {user_id}: {user}")
    return user


def add_user(user_id, username, balance=0.0):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        profile = {
            "username": username,
            "date_reg": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "balance": balance,
            "ticket_tariff": None
        }
        profile_json = json.dumps(profile)
        cursor.execute("INSERT INTO users (user_id, profile) VALUES (?, ?)", (user_id, profile_json))
        conn.commit()


def update_user_uuid(user_id, uuid):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET uuid = ? WHERE user_id = ?", (uuid, user_id))
    conn.commit()
    conn.close()


def get_admins():
    """Получить список администраторов"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT tg_id FROM admins")
    admins = cursor.fetchall()
    conn.close()
    logging.info(f"Результат запроса get_admins: {admins}")
    return [admin[0] for admin in admins]


def update_pos(new_pos, user_id):
    """Обновляет позицию (pos) пользователя в БД."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET pos = ? WHERE user_id = ?", (new_pos, user_id))
    logging.info(f"Результат запроса update_pos: {new_pos} у пользователя с user_id: {user_id}")
    conn.commit()
    conn.close()


def add_balance(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT profile FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if user:
        profile = json.loads(user[0])
        current_balance = profile.get('balance', 0)
        new_balance = current_balance + 400

        profile['balance'] = new_balance
        cursor.execute("UPDATE users SET profile = ? WHERE user_id = ?", (json.dumps(profile), user_id))
        logging.info(f"Результат запроса add_balance: {new_balance} у пользователя с user_id: {user_id}")
        conn.commit()
    conn.close()


def get_user_balance(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT profile FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if user:
        profile = json.loads(user[0])
        return profile.get('balance', 0)
    logging.info(f"Результат запроса get_user_balance: {profile} у пользователя с user_id: {user_id}")
    conn.close()
    return 0


def update_balance(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT profile FROM users WHERE user_id = ?", (user_id,))
    profile_json = cursor.fetchone()

    if profile_json:
        profile = json.loads(profile_json[0])
        profile['balance'] += amount
        cursor.execute("UPDATE users SET profile = ? WHERE user_id = ?", (json.dumps(profile), user_id))
        conn.commit()
    conn.close()


def update_user_profile(user_id, profile_data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
            UPDATE users
            SET profile = ?
            WHERE user_id = ?
        """, (profile_data, user_id))
    conn.commit()
    conn.close()


def update_user_tariff(user_id, tariff):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT profile FROM users WHERE user_id = ?", (user_id,))
    profile_json = cursor.fetchone()

    if profile_json:
            profile = json.loads(profile_json[0])
            profile['ticket_tariff'] = tariff
            cursor.execute("UPDATE users SET profile = ? WHERE user_id = ?", (json.dumps(profile), user_id))
            conn.commit()
    conn.close()


def clear_user_tariff(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT profile FROM users WHERE user_id = ?", (user_id,))
    profile_json = cursor.fetchone()

    if profile_json:
        profile = json.loads(profile_json[0])
        profile.pop('ticket_tariff', None)
        cursor.execute("UPDATE users SET profile = ? WHERE user_id = ?", (json.dumps(profile), user_id))
        conn.commit()
    conn.close()


def get_user_profile(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT profile FROM users WHERE user_id = ?", (user_id,))
    profile_json = cursor.fetchone()

    if profile_json:
        profile = json.loads(profile_json[0])
        logging.info(f"Результат запроса get_user_profile: {profile} у пользователя с user_id: {user_id}")
        conn.close()
        return profile
