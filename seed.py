import psycopg2
from faker import Faker
import random
import re

faker = Faker()

ALLOWED_TABLES = ["customers", "products", "orders", "order_items", "payments"]

def safe_sql_raw(query: str):
    lowered = query.lower()

    forbidden = [
        ";", "--", "/*", "*/", "pg_", "information_schema",
        "union", "sleep", "case", "when", "drop table", "alter table"
    ]

    for bad in forbidden:
        if bad in lowered:
            raise ValueError(f"❌ Опасный SQL запрещён: {bad}")

    return query


conn = psycopg2.connect(
    host="localhost",
    database="sales",
    user="postgres",
    password="zec123123"
)
cursor = conn.cursor()

for table in ALLOWED_TABLES:
    safe_sql_raw(f"TRUNCATE {table} CASCADE")
    cursor.execute(f"TRUNCATE {table} CASCADE")

for table in ALLOWED_TABLES:
    safe_sql_raw(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1")
    cursor.execute(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1")

conn.commit()


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

conn.commit()


for _ in range(100):
    cursor.execute("""
        INSERT INTO customers (full_name, email, city)
        VALUES (%s, %s, %s)
    """, (
        faker.name(),
        faker.email(),
        faker.city(),
    ))

conn.commit()


for _ in range(700):
    customer_id = random.randint(1, 100)
    order_status = random.choice(["completed", "pending", "cancelled"])
    order_date = faker.date_between(start_date="-6M", end_date="today")

    cursor.execute("""
        INSERT INTO orders (customer_id, order_date, status)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (customer_id, order_date, order_status))

    order_id = cursor.fetchone()[0]

    total_amount = 0

    for _ in range(random.randint(1, 5)):
        product_id = random.randint(1, len(product_names))
        quantity = random.randint(1, 3)

        cursor.execute("SELECT price FROM products WHERE id = %s", (product_id,))
        unit_price = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
        """, (order_id, product_id, quantity, unit_price))

        total_amount += unit_price * quantity

    cursor.execute("""
        UPDATE orders SET total_amount = %s WHERE id = %s
    """, (total_amount, order_id))

    if order_status.lower() == "completed":
        cursor.execute("""
            INSERT INTO payments (order_id, amount, method)
            VALUES (%s, %s, %s)
        """, (order_id, total_amount, random.choice(["Card", "Cash", "Click", "Payme"])))

conn.commit()
cursor.close()
conn.close()