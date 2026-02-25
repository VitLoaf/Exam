import os
import csv
import datetime
from database import init_db, execute_query
from utils import validate_date, validate_amount, validate_id

# Секція звітів
def report_menu():
    # Оновлене меню для роботи зі звітами
    while True:
        print("\n--- ЗВІТИ ТА АНАЛІТИКА ---")
        print("1. Загальна сума (всі витрати)")
        print("2. MAX/MIN по кожній категорії (GROUP BY)")
        print("3. Найдорожча/Найдешевша витрата у періоді")
        print("4. ТОП-категорія (найбільші витрати)")
        print("5. Середні витрати на день")
        print("6. Розширений пошук (назва, період, категорія)")
        print("7. Експорт звітів у CSV")
        print("0. Повернутися до головного меню")

        choice = input("Оберіть: ")

        if choice == "1":
            report_total()
        elif choice == "2":
            report_max_min_by_category()
        elif choice == "3":
            report_extreme_in_period()
        elif choice == "4":
            report_top_category()
        elif choice == "5":
            report_average_daily()
        elif choice == "6":
            search_expenses()
        elif choice == "7":
            export_csv()
        elif choice == "0":
            break
        else:
            print("Помилка: Невірний вибір. Спробуйте ще раз.")
    return True

# Головне меню
def main_menu():
    # Основна точка входу в інтерфейс програми
    while True:
        print("\n=== СИСТЕМА ОБЛІКУ ВИТРАТ ===")
        print("1. Категорії")
        print("2. Витрати")
        print("3. Звіти")
        print("4. Заповнити тестовими даними (Seed)")
        print("0. Вихід")

        choice = input("Оберіть: ")

        if choice == "1":
            category_menu()
        elif choice == "2":
            expense_menu()
        elif choice == "3":
            report_menu()
        elif choice == "4":
            seed_data()
        elif choice == "0":
            break
        else:
            print("Невірний вибір.")
    return True

# Керування категоріями (CRUD)
def category_menu():
    # Меню для додавання, перегляду та редагування категорій
    while True:
        print("\n--- КАТЕГОРІЇ ---")
        print("1. Додати")
        print("2. Список")
        print("3. Редагувати")
        print("4. Видалити")
        print("0. Назад")

        choice = input("Оберіть: ")

        if choice == "1":
            name = input("Назва категорії: ")
            if not name.strip():
                print("Назва не може бути порожньою.")
                continue
            execute_query("INSERT INTO categories (name) VALUES (%s)", (name,))
            print("Додано.")

        elif choice == "2":
            # Сортування за ID для зручності вибору
            data = execute_query("SELECT id, name FROM categories WHERE is_deleted = FALSE ORDER BY id", fetch=True)
            if not data:
                print("Категорій немає.")
            else:
                for row in data: print(row)

        elif choice == "3":
            cat_id = input("ID категорії: ")
            if not validate_id(cat_id):
                print("Невірний ID.")
                continue
            exists = execute_query("SELECT id FROM categories WHERE id=%s AND is_deleted=FALSE", (cat_id,),
                                   fetch_one=True)
            if not exists:
                print("Не існує.")
                continue
            new_name = input("Нова назва: ")
            execute_query("UPDATE categories SET name=%s WHERE id=%s", (new_name, cat_id))
            print("Оновлено.")

        elif choice == "4":
            cat_id = input("ID категорії для видалення: ")
            if validate_id(cat_id):
                # Перевіряємо наявність витрат перед видаленням
                has_expenses = execute_query(
                    "SELECT 1 FROM expenses WHERE category_id=%s AND is_deleted=FALSE",
                    (cat_id,), fetch_one=True
                )
                if has_expenses:
                    print("ПОМИЛКА: Не можна видалити категорію, поки в ній є активні витрати!")
                else:
                    execute_query("UPDATE categories SET is_deleted=TRUE WHERE id=%s", (cat_id,))
                    print("Категорію видалено.")
        elif choice == "0":
            break
    return True


# Керування витратами (CRUD)
def expense_menu():
    # Меню для роботи з транзакціями (витратами)
    while True:
        print("\n--- ВИТРАТИ ---")
        print("1. Додати")
        print("2. Список")
        print("3. Деталі")
        print("4. Редагувати")
        print("5. Видалити")
        print("0. Назад")

        choice = input("Оберіть: ")

        if choice == "1":
            add_expense()
        elif choice == "2":
            list_expenses()
        elif choice == "3":
            show_expense_details()
        elif choice == "4":
            update_expense()
        elif choice == "5":
            delete_expense()
        elif choice == "0":
            break
    return True


def add_expense():
    # Вибір категорії (існуюча логіка)
    cats = execute_query("SELECT id, name FROM categories WHERE is_deleted=FALSE ORDER BY id", fetch=True)
    if not cats:
        print("Спочатку створіть категорію.")
        return None
    for c in cats: print(c)

    cat_id = input("ID категорії: ")
    if not validate_id(cat_id):
        print("Невірний ID.")
        return None

    exists = execute_query("SELECT id FROM categories WHERE id=%s AND is_deleted=FALSE", (cat_id,), fetch_one=True)
    if not exists:
        print("Категорія не існує.")
        return None

    # Основні дані
    title = input("Назва: ")
    date = input("Дата (YYYY-MM-DD): ")
    amount = input("Сума: ")

    # Опис та Валюта
    description = input("Опис (можна залишити порожнім): ").strip() or None

    # Якщо користувач натисне Enter, встановиться "UAH"
    currency_input = input("Валюта (за замовчуванням UAH): ").strip().upper()
    currency = currency_input if currency_input else "UAH"

    # Валідація та запис у БД
    if validate_date(date) and validate_amount(amount):
        execute_query("""
            INSERT INTO expenses (title, date, category_id, amount, description, currency) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, date, cat_id, amount, description, currency))
        print(f"Витрату додано ({currency}).")
    else:
        print("Помилка даних (перевірте формат дати та суму).")
    return True

def list_expenses():
    data = execute_query("""
        SELECT e.id, e.title, e.date, c.name, e.amount, e.currency 
        FROM expenses e JOIN categories c ON e.category_id = c.id 
        WHERE e.is_deleted=FALSE ORDER BY e.id
    """, fetch=True)
    if not data:
        print("Витрат немає.")
    else:
        # Виводимо суму разом з валютою
        for row in data:
            print(f"ID: {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} {row[5]}")
    return data

def show_expense_details():
    # Перегляд повної інформації про конкретну витрату за ID
    exp_id = input("ID витрати: ")
    if not validate_id(exp_id):
        return None 

    data = execute_query("""
        SELECT e.id, e.title, e.date, c.name, e.amount, e.currency, e.description 
        FROM expenses e JOIN categories c ON e.category_id = c.id 
        WHERE e.id=%s AND e.is_deleted=FALSE
    """, (exp_id,), fetch_one=True)

    if not data:
        print("Не знайдено.")
        return None
    else:
        print(f"\n--- ДЕТАЛІ ВИТРАТИ ID:{data[0]} ---")
        # ... твій код виводу ...
        print(f"Опис: {data[6] if data[6] else '-'}")
        return True

def search_expenses():
    print("\n--- Розширений пошук (залиште порожнім, щоб ігнорувати параметр) ---")
    title_part = input("Назва (частковий збіг): ").strip()
    cat_name = input("Назва категорії: ").strip()
    start_date = input("Початок періоду (YYYY-MM-DD): ").strip()
    end_date = input("Кінець періоду (YYYY-MM-DD): ").strip()

    query = """
        SELECT e.id, e.title, e.date, c.name, e.amount, e.currency, e.description 
        FROM expenses e 
        JOIN categories c ON e.category_id = c.id 
        WHERE e.is_deleted = FALSE
    """
    params = []

    if title_part:
        query += " AND e.title ILIKE %s"
        params.append(f"%{title_part}%")
    if cat_name:
        query += " AND c.name ILIKE %s"
        params.append(f"%{cat_name}%")
    if start_date and validate_date(start_date):
        query += " AND e.date >= %s"
        params.append(start_date)
    if end_date and validate_date(end_date):
        query += " AND e.date <= %s"
        params.append(end_date)

    results = execute_query(query, tuple(params), fetch=True)
    if not results:
        print("Нічого не знайдено.")
    else:
        for r in results:
            desc = f" | Опис: {r[6]}" if r[6] else ""
            print(f"[{r[2]}] {r[1]} ({r[3]}) - {r[4]} {r[5]}{desc}")

def update_expense():
    # Редагування існуючої витрати, включаючи нові поля та зміну категорії
    exp_id = input("ID витрати: ")
    if not validate_id(exp_id):
        print("Некоректний ID.")
        return None

    # Перевіряємо, чи існує така витрата
    exists = execute_query(
        "SELECT id, category_id, title, date, amount, description, currency FROM expenses WHERE id=%s AND is_deleted=FALSE",
        (exp_id,), fetch_one=True)
    if not exists:
        print("Витрату з таким ID не знайдено.")
        return None

    print(f"\nПоточні дані: {exists}")
    print("--- Залиште порожнім, щоб не змінювати ---")

    # Зміна категорії
    new_cat_id = input(f"Новий ID категорії (поточний {exists[1]}): ").strip()
    if new_cat_id:
        if not validate_id(new_cat_id) or not execute_query(
                "SELECT id FROM categories WHERE id=%s AND is_deleted=FALSE", (new_cat_id,), fetch_one=True):
            print("Помилка: такої категорії не існує.")
            return None
    else:
        new_cat_id = exists[1]

    # Редагування назви, дати та суми
    new_title = input(f"Нова назва (поточна '{exists[2]}'): ").strip() or exists[2]

    new_date = input(f"Нова дата YYYY-MM-DD (поточна {exists[3]}): ").strip() or str(exists[3])
    if not validate_date(new_date):
        print("Невірний формат дати.")
        return None

    new_amount = input(f"Нова сума (поточна {exists[4]}): ").strip() or str(exists[4])
    if not validate_amount(new_amount):
        print("Сума має бути додатним числом.")
        return None

    # Редагування опису та валюти
    new_description = input(f"Новий опис (поточний '{exists[5]}'): ").strip()
    # Якщо нічого не ввели — залишаємо старий, якщо ввели "0" або "none" — очищуємо (NULL)
    if not new_description:
        new_description = exists[5]
    elif new_description.lower() in ['clear', 'none', '-']:
        new_description = None

    new_currency = input(f"Нова валюта (поточна {exists[6]}): ").strip().upper() or exists[6]

    # Виконання оновлення в БД
    success = execute_query("""
        UPDATE expenses 
        SET category_id=%s, title=%s, date=%s, amount=%s, description=%s, currency=%s 
        WHERE id=%s
    """, (new_cat_id, new_title, new_date, new_amount, new_description, new_currency, exp_id))

    if success:
        print("Дані успішно оновлено!")
    return True

def delete_expense():
    #Логічне видалення витрати (прапорець is_deleted)
    exp_id = input("ID: ")
    if validate_id(exp_id):
        execute_query("UPDATE expenses SET is_deleted=TRUE WHERE id=%s", (exp_id,))
        print("Видалено.")
    return True

# Логіка експорту за звітів
def report_total():
    print("\n--- ЗАГАЛЬНА СУМА ВИТРАТ ---")
    # Групуємо за валютою, щоб не додавати долари до гривень
    data = execute_query("""
        SELECT currency, SUM(amount) FROM expenses 
        WHERE is_deleted=FALSE GROUP BY currency
    """, fetch=True)
    if not data:
        print("Витрат немає.")
    else:
        for row in data:
            print(f"Всього у {row[0]}: {row[1]:.2f}")

def report_totals_by_category():
    print("\n--- ПІДСУМКИ ПО КАТЕГОРІЯХ (ЗА ВАЛЮТАМИ) ---")
    query = """
        SELECT c.name, e.currency, SUM(e.amount)
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.is_deleted = FALSE
        GROUP BY c.name, e.currency
        ORDER BY c.name
    """
    results = execute_query(query, fetch=True)
    if not results:
        print("Дані відсутні.")
    else:
        print(f"{'Категорія':<20} | {'Сума':<15} | {'Валюта'}")
        print("-" * 45)
        for r in results:
            print(f"{r[0]:<20} | {r[2]:>10.2f} | {r[1]}")
            
def report_max_min_by_category():
    # Макс/Мін у кожній категорії
    print("\n--- Максимальні та мінімальні витрати по категоріях ---")
    query = """
        SELECT c.name, MAX(e.amount), MIN(e.amount), COUNT(e.id)
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.is_deleted = FALSE
        GROUP BY c.name
    """
    results = execute_query(query, fetch=True)
    if not results:
        print("Дані відсутні.")
    else:
        print(f"{'Категорія':<20} | {'MAX':<10} | {'MIN':<10} | {'К-сть'}")
        print("-" * 55)
        for r in results:
            print(f"{r[0]:<20} | {r[1]:<10} | {r[2]:<10} | {r[3]}")

def report_extreme_in_period():
    # Макс/Мін у періоді
    start = input("З якої дати (YYYY-MM-DD): ")
    end = input("По яку дату (YYYY-MM-DD): ")
    if not (validate_date(start) and validate_date(end)):
        print("Невірний формат дат.")
        return
    max_exp = execute_query("SELECT title, amount, currency, date FROM expenses WHERE is_deleted=FALSE AND date BETWEEN %s AND %s ORDER BY amount DESC LIMIT 1", (start, end), fetch_one=True)
    min_exp = execute_query("SELECT title, amount, currency, date FROM expenses WHERE is_deleted=FALSE AND date BETWEEN %s AND %s ORDER BY amount ASC LIMIT 1", (start, end), fetch_one=True)
    if max_exp:
        print(f"\nНайдорожча: {max_exp[0]} ({max_exp[1]} {max_exp[2]}) від {max_exp[3]}")
        print(f"Найдешевша: {min_exp[0]} ({min_exp[1]} {min_exp[2]}) від {min_exp[3]}")
    else: print("Витрат не знайдено.")


def report_average_daily():
    # Середні витрати на день за період з урахуванням різних валют
    start = input("З якої дати (YYYY-MM-DD): ")
    end = input("По яку дату (YYYY-MM-DD): ")

    if not (validate_date(start) and validate_date(end)):
        print("Невірний формат дат.")
        return None

    # Розраховуємо кількість днів у періоді
    d1 = datetime.datetime.strptime(start, "%Y-%m-%d")
    d2 = datetime.datetime.strptime(end, "%Y-%m-%d")
    days_count = (d2 - d1).days + 1

    if days_count <= 0:
        print("Помилка: Кінцева дата має бути більшою за початкову.")
        return None

    # Отримуємо суми, згруповані за валютою (GROUP BY)
    results = execute_query("""
        SELECT currency, COALESCE(SUM(amount), 0) 
        FROM expenses 
        WHERE is_deleted=FALSE AND date BETWEEN %s AND %s
        GROUP BY currency
    """, (start, end), fetch=True)

    if not results:
        print("\nВитрат за цей період не знайдено.")
        return None

    print(f"\n--- Аналіз періоду ({days_count} днів) ---")
    for row in results:
        curr = row[0]
        total_in_curr = float(row[1])
        average = total_in_curr / days_count
        print(f"Валюта: {curr}")
        print(f"  Загальна сума: {total_in_curr:.2f} {curr}")
        print(f"  Середні витрати на день: {average:.2f} {curr}")

    print("\nПримітка: Розрахунок проведено окремо для кожної валюти.")
    return True

def report_top_category():
    print("\n--- ТОП-КАТЕГОРІЇ ЗА ВАЛЮТАМИ ---")
    query = """
        SELECT c.name, SUM(e.amount) as total, e.currency
        FROM expenses e JOIN categories c ON e.category_id = c.id
        WHERE e.is_deleted = FALSE 
        GROUP BY c.name, e.currency
        ORDER BY total DESC
    """
    results = execute_query(query, fetch=True)
    if results:
        # Показуємо лідера для кожної валюти
        seen_currencies = set()
        for r in results:
            if r[2] not in seen_currencies:
                print(f"Топ у {r[2]}: '{r[0]}' ({r[1]:.2f})")
                seen_currencies.add(r[2])


def export_csv():
    # Експорт усіх активних витрат у файл CSV у папку export
    data = execute_query("""
        SELECT e.date, e.title, e.amount, c.name FROM expenses e 
        JOIN categories c ON e.category_id = c.id WHERE e.is_deleted=FALSE
    """, fetch=True)
    if not data: return None

    os.makedirs("export", exist_ok=True)
    with open("export/report.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Дата", "Назва", "Сума", "Категорія"])
        writer.writerows(data)
    print("Збережено в export/report.csv")
    return True

# Системні функції (SEED DATA)
def seed_data():
    # Заповнення бази демонстраційними даними
    categories = ["Продукти", "Транспорт", "Розваги", "Комунальні", "Здоров'я", "Освіта", "Інше"]
    for cat in categories:
        execute_query("INSERT INTO categories (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (cat,))

    cat_rows = execute_query("SELECT id, name FROM categories WHERE is_deleted=FALSE ORDER BY id", fetch=True)
    cat_map = {name: cat_id for cat_id, name in cat_rows}

    # Структура: (Назва, Дата, ID Категорії, Сума, Опис, Валюта)
    test_expenses = [
        ("Сільпо", "2026-02-01", cat_map["Продукти"], 850.50, "Закупівля на тиждень", "UAH"),
        ("WOG Паливо", "2026-02-02", cat_map["Транспорт"], 1200.00, None, "UAH"),
        ("Спортзал", "2026-02-03", cat_map["Здоров'я"], 1500.00, "Абонемент на місяць", "UAH"),
        ("Кіно", "2026-02-05", cat_map["Розваги"], 400.00, "Квитки на вечірній сеанс", None),
        ("Інтернет", "2026-02-07", cat_map["Комунальні"], 350.00, None, "UAH"),
        ("Курс Python (Освіта)", "2026-02-10", cat_map["Освіта"], 5000.00, "Оплата за модуль", "UAH"),
        ("Аптека", "2026-02-12", cat_map["Здоров'я"], 320.00, "Вітаміни", None),
        ("Таксі Bolt", "2026-02-14", cat_map["Транспорт"], 180.00, None, "UAH"),
        ("Вечеря", "2026-02-15", cat_map["Розваги"], 750.00, "Зустріч з друзями", "UAH"),
        ("Овочі", "2026-02-18", cat_map["Продукти"], 420.00, "Ринок", "UAH"),
        ("Електроенергія", "2026-02-20", cat_map["Комунальні"], 980.00, "За січень", "UAH"),
        ("Подарунок", "2026-02-22", cat_map["Інше"], 600.00, "Механічна клавіатура", "UAH"),
        ("Метро", "2026-02-23", cat_map["Транспорт"], 200.00, "Поповнення смарт-картки", "UAH"),
        ("Книга по Blender", "2026-02-24", cat_map["Освіта"], 550.00, "Довідник по композиції", "UAH")
    ]

    for t, d, c, a, desc, curr in test_expenses:
        execute_query("""
            INSERT INTO expenses (title, date, category_id, amount, description, currency) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (t, d, c, a, desc, curr))

    print("\n[УСПІХ]: Дані додано.")
    return True


if __name__ == "__main__":
    # Ініціалізація бази даних та запуск головного меню
    init_db()
    main_menu()