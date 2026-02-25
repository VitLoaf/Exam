import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def create_database_if_not_exists():
    # Підключення до системної бази postgres для виконання команди CREATE DATABASE
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"]
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Перевірка наявності робочої бази даних
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (DB_CONFIG["dbname"],))
        exists = cursor.fetchone()

        if not exists:
            print(f"Створюю базу даних {DB_CONFIG['dbname']}...")
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['dbname']}")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[Помилка ініціалізації сервера]: {e}")


def get_connection():
    # Повертає об'єкт з'єднання з робочою базою
    return psycopg2.connect(**DB_CONFIG)


def init_db():
    # Створення бази та таблиць
    create_database_if_not_exists()
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # 1. Створюємо базові таблиці (якщо їх ще немає)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    is_deleted BOOLEAN DEFAULT FALSE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    date DATE NOT NULL,
                    category_id INTEGER REFERENCES categories(id),
                    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
                    is_deleted BOOLEAN DEFAULT FALSE
                )
            """)

            # 2. МІГРАЦІЯ: Перевіряємо та додаємо нові стовпці, якщо вони відсутні
            cursor.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='expenses' AND column_name='description') THEN
                        ALTER TABLE expenses ADD COLUMN description TEXT;
                    END IF;

                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='expenses' AND column_name='currency') THEN
                        ALTER TABLE expenses ADD COLUMN currency CHAR(3);
                    END IF;
                END $$;
            """)
            conn.commit()
        conn.close()
        print("[СИСТЕМА]: База даних успішно синхронізована.")
    except Exception as e:
        print(f"[Помилка створення таблиць]: {e}")
def execute_query(query, params=None, fetch=False, fetch_one=False):
    # Універсальний метод для SQL запитів
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            if fetch:
                result = cursor.fetchall()
                conn.close()
                return result
            if fetch_one:
                result = cursor.fetchone()
                conn.close()
                return result
            conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("\n[Помилка БД]:", e)
        return None