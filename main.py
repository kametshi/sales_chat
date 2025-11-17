import json
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
import requests
from trello import TrelloClient
import seed

app = FastAPI()

OPENROUTER_API_KEY = "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"

conn = psycopg2.connect(
    host="localhost",
    database="sales",
    user="postgres",
    password="zec123123"
)
cursor = conn.cursor()

# Trello

def list_tables():
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    return [row[0] for row in cursor.fetchall()]


import re

ALLOWED_TABLES = {"customers", "orders", "order_items", "products", "payments"}
FORBIDDEN = [
    ";", "--", "/*", "*/", "union", "information_schema",
    "pg_", "case", "when", "sleep", "pg_sleep"
]

def query_database(sql: str):
    safe_sql = sql.strip()

    if not safe_sql.lower().startswith("select"):
        raise ValueError("❌ Разрешены только SELECT запросы")

    lowered = safe_sql.lower()
    for bad in FORBIDDEN:
        if bad in lowered:
            raise ValueError(f"❌ Запрещённый SQL паттерн: {bad}")

    tables = re.findall(r"from\s+([a-z_]+)", lowered)
    joins = re.findall(r"join\s+([a-z_]+)", lowered)
    all_tables = set(tables + joins)

    if not all_tables:
        raise ValueError("❌ SQL должен содержать FROM")

    for table in all_tables:
        if table not in ALLOWED_TABLES:
            raise ValueError(f"❌ Доступ к таблице запрещён: {table}")

    if "limit" not in lowered:
        safe_sql += " LIMIT 20"

    cursor.execute(safe_sql)
    rows = cursor.fetchall()
    colnames = [desc[0] for desc in cursor.description]
    result = [dict(zip(colnames, row)) for row in rows]

    return result


def create_ticket(text: str, board_name: str = "Karina"):
    client = TrelloClient(
        api_key='1da7f18b31eaf401ed4dcfb1d272c815',
        token='ATTAdd24b0c9ee01639d47020cd374d7fcee736d5ce36e3a79fbd1df83adab0d0f8eC9FCAFCF'
    )

    board = client.add_board(board_name)
    print(f"Доска создана: {board.name} ({board.id})")

    todo_list = board.add_list(name="Tickets")
    print(f"Список создан: {todo_list.name} ({todo_list.id})")

    card = todo_list.add_card("Новая карточка", text)
    print(f"Карточка создана: {card.id}")

    return "Тикет создан, спасибо!"


functions = [
    {
        "name": "list_tables",
        "description": "Получить список таблиц из базы данных",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "query_database",
        "description": "Выполнить SQL SELECT запрос (только SELECT)",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {"type": "string"}
            },
            "required": ["sql"]
        },
    },
    {
        "name": "create_ticket",
        "description": "Создать тикет поддержки в Trello",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"}
            },
            "required": ["title", "description"]
        },
    },
]

system_prompt = """
Ты — Data Insights Agent.

❗ ВСЕГДА вместо текста вызывай функцию.

Структура базы данных:

TABLE customers:
  id SERIAL PRIMARY KEY
  full_name TEXT
  email TEXT
  city TEXT

TABLE orders:
  id SERIAL PRIMARY KEY
  customer_id INTEGER REFERENCES customers(id)
  total_amount DECIMAL
  status TEXT
  order_date TIMESTAMP

TABLE order_items:
  id SERIAL PRIMARY KEY
  order_id INTEGER REFERENCES orders(id)
  product_id INTEGER REFERENCES products(id)
  quantity INTEGER
  unit_price DECIMAL

TABLE products:
  id SERIAL PRIMARY KEY
  name TEXT
  category TEXT
  price DECIMAL

TABLE payments:
  id SERIAL PRIMARY KEY
  order_id INTEGER REFERENCES orders(id)
  amount DECIMAL
  method TEXT

Правила:
- Всегда используй JOIN через customers.id
- НЕЛЬЗЯ писать SQL в ответе (только function_call)
- НЕЛЬЗЯ писать DELETE/UPDATE/DROP/INSERT
- Есть статусы completed, pending, cancelled
- У p просто id, а не product_id
"""


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat(data: ChatRequest):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000/",
        "X-Title": "Sales Insights Agent"
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json={
            "model": "openai/gpt-4.1-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data.message}
            ],
            "tools": [
                {"type": "function", "function": fn} for fn in functions
            ],
            "tool_choice": "auto",
            "max_tokens": 200,
        }
    )

    res = response.json()
    msg = res["choices"][0]["message"]

    if "tool_calls" in msg:
        for call in msg["tool_calls"]:
            fn = call["function"]["name"]
            args = json.loads(call["function"]["arguments"])

            if fn == "list_tables":
                return {"tables": list_tables()}

            if fn == "query_database":
                sql = args["sql"]
                if any(bad in sql.lower() for bad in ["delete", "drop", "update", "insert"]):
                    return {"error": "⚠ Опасный SQL запрещён"}
                return query_database(sql)

            if fn == "create_ticket":
                return create_ticket(args["title"], args["description"])

    return {"reply": msg.get("content")}


if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
