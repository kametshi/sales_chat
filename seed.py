import io
import psycopg2
from faker import Faker
import random
import re

# --- Инициализация ---
faker = Faker()

# Определения таблиц (SQL DDL)
# Внимание: Убедитесь, что FOREIGN KEY references корректны.
TABLE_CREATION_QUERIES = {
    "customers": """
        CREATE TABLE customers (
            id SERIAL PRIMARY KEY,
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            city VARCHAR(100)
        );
    """,
    "products": """
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            price DECIMAL(10, 2) NOT NULL
        );
    """,
    "orders": """
        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(id),
            order_date DATE NOT NULL,
            status VARCHAR(50) NOT NULL,
            total_amount DECIMAL(10, 2) DEFAULT 0.00
        );
    """,
    "order_items": """
        CREATE TABLE order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL
        );
    """,
    "payments": """
        CREATE TABLE payments (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
            amount DECIMAL(10, 2) NOT NULL,
            method VARCHAR(50) NOT NULL,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
}

ALLOWED_TABLES = list(TABLE_CREATION_QUERIES.keys())

def safe_sql_raw(query: str):
    """Базовая защита от внедрения SQL-кода."""
    lowered = query.lower()

    forbidden = [
        ";", "--", "/*", "*/", "pg_", "information_schema",
        "union", "sleep", "case", "when", "drop table", "alter table"
    ]

    for bad in forbidden:
        if bad in lowered:
            raise ValueError(f"❌ Опасный SQL запрещён: {bad}")

    return query

# --- Подключение к базе данных ---
try:
    conn = psycopg2.connect(
        host="localhost",
        database="sales",
        user="postgres",
        password="zec123123"
    )
    cursor = conn.cursor()
except psycopg2.Error as e:
    print(f"❌ Ошибка подключения к базе данных: {e}")
    exit()

# --- 1. Проверка и создание таблиц (DDL) ---
print("--- 1. Проверка и создание таблиц ---")
for table_name, create_query in TABLE_CREATION_QUERIES.items():
    # Проверка существования таблицы
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
    """, (table_name,))
    
    table_exists = cursor.fetchone()[0]

    if not table_exists:
        print(f"🛠️ Таблица '{table_name}' не найдена. Создание...")
        try:
            cursor.execute(create_query)
            conn.commit()
            print(f"✅ Таблица '{table_name}' успешно создана.")
        except psycopg2.Error as e:
            conn.rollback()
            print(f"❌ Ошибка при создании таблицы '{table_name}': {e}")
    else:
        print(f"✅ Таблица '{table_name}' уже существует.")

# --- 2. Очистка и сброс последовательностей (DML/DDL) ---
print("\n--- 2. Очистка существующих данных ---")
for table in ALLOWED_TABLES:
    try:
        # TRUNCATE безопасно, так как имя таблицы берется из ALLOWED_TABLES
        print(f"🗑️ Очистка таблицы: {table}")
        cursor.execute(f"TRUNCATE {table} CASCADE")
        
        # Сброс последовательности (для SERIAL ID)
        seq_name = f"{table}_id_seq"
        print(f"🔄 Сброс последовательности: {seq_name}")
        cursor.execute(f"ALTER SEQUENCE {seq_name} RESTART WITH 1")
    except psycopg2.ProgrammingError as e:
        # Игнорируем ошибки, если последовательность не существует (например, для таблиц без SERIAL)
        print(f"⚠️ Пропущена последовательность для {table}. Ошибка: {e}")
        conn.rollback() # Откат, если была ошибка
    except Exception as e:
        print(f"❌ Критическая ошибка при очистке {table}: {e}")
        conn.rollback()

conn.commit()
print("✅ Очистка и сброс последовательностей завершены.")

# --- 3. Заполнение таблицы products ---
print("\n--- 3. Заполнение таблицы products ---")
product_names = [
    "Smartphone X", "Laptop Pro", "Wireless Mouse", "Bluetooth Headphones",
    "Monitor 27", "USB-C Charger", "Mechanical Keyboard", "Smartwatch",
    "LED Lamp", "Office Chair", "Camera HD", "Tripod", "Backpack",
    "Flash Drive", "Tablet Mini", "Speaker Portable", "Power Bank",
    "Graphics Tablet", "Webcam", "Gaming Console"
]

categories = ["Electronics", "Accessories", "Office", "Gadgets"]

for name in product_names:
    price = round(random.uniform(10, 2000), 2)
    category = random.choice(categories)

    cursor.execute("""
        INSERT INTO products (name, category, price)
        VALUES (%s, %s, %s)
    """, (name, category, price))
print(f"✅ Добавлено {len(product_names)} продуктов.")
conn.commit()


# --- 4. Заполнение таблицы customers ---
print("\n--- 4. Заполнение таблицы customers ---")
num_customers = 100
for _ in range(num_customers):
    cursor.execute("""
        INSERT INTO customers (full_name, email, city)
        VALUES (%s, %s, %s)
    """, (
        faker.name(),
        faker.email(),
        faker.city(),
    ))
print(f"✅ Добавлено {num_customers} покупателей.")
conn.commit()


# --- 5. Заполнение orders, order_items и payments ---
print("\n--- 5. Заполнение заказов, позиций и платежей ---")
num_orders = 700
for i in range(1, num_orders + 1):
    customer_id = random.randint(1, num_customers)
    order_status = random.choice(["completed", "pending", "cancelled"])
    order_date = faker.date_between(start_date="-6M", end_date="today")

    cursor.execute("""
        INSERT INTO orders (customer_id, order_date, status)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (customer_id, order_date, order_status))

    order_id = cursor.fetchone()[0]

    total_amount = 0

    num_items = random.randint(1, 5)
    for _ in range(num_items):
        product_id = random.randint(1, len(product_names))
        quantity = random.randint(1, 3)

        cursor.execute("SELECT price FROM products WHERE id = %s", (product_id,))
        unit_price = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
        """, (order_id, product_id, quantity, unit_price))

        total_amount += float(unit_price) * quantity # Явное преобразование в float

    cursor.execute("""
        UPDATE orders SET total_amount = %s WHERE id = %s
    """, (total_amount, order_id))

    if order_status.lower() == "completed":
        cursor.execute("""
            INSERT INTO payments (order_id, amount, method)
            VALUES (%s, %s, %s)
        """, (order_id, total_amount, random.choice(["Card", "Cash", "Click", "Payme"])))

    if i % 100 == 0:
        print(f"  > Обработано {i} заказов...")

conn.commit()
print(f"✅ Добавлено {num_orders} заказов, позиций и платежей.")

# --- 6. Завершение работы ---
cursor.close()
conn.close()
print("\n🎉 Скрипт завершен. Соединение закрыто.")
