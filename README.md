# 📊 Sales Insights Chat — AI + SQL Analytics + Trello Tickets

Sales Insights Chat is an AI-powered analytics system built with **FastAPI**, **Streamlit**, **PostgreSQL**, and **OpenRouter GPT**.  
The agent answers natural language questions, generates secure SQL queries, visualizes data, and can create Trello support tickets.

---
### [Project URL](https://project1.ai-softdev.com)
## 🚀 Features

### 🔍 AI Chat Agent  
- Understands natural language questions about sales  
- Generates **only secure SELECT SQL queries**  
- Extracts data from PostgreSQL safely  
- Supports function calling via OpenRouter GPT  
- Automatically adds `LIMIT 20`  
- JOIN rules enforced (only valid table relations)

### 📊 Interactive Streamlit UI  
- Chat-style interface  
- Tables preview  
- Automatic data visualization with Plotly  
- Metrics display  
- Error-safe message handling

### 🛡 Secure SQL Layer  
- Blocks SQL injection patterns  
- Allows only whitelisted tables  
- Rejects DELETE/UPDATE/INSERT/DROP entirely  
- Sanitizes JOIN and FROM clauses  
- Protects backend using pattern-based filtering

### 📌 Trello Integration  
The AI can create Trello tickets via function calls:
- Auto-create board
- Auto-create task list
- Add card with title + description

### 🧪 Automatic Database Seeding  
`seed.py` fills the database with:
- Products  
- Customers  
- Orders  
- Order items  
- Payments  
- With realistic Faker data

---

## 📂 Project Structure

```project/
│── main.py # FastAPI backend + SQL agent + Trello
│── seed.py # Database seeding script
│── ui.py # Streamlit-based frontend
│── README.md # Project documentation
```

---

## 🛠 Installation

### 1. Clone the project
```bash
git clone https://github.com/kametshi/sales_chat.git
```

### 2. Install dependencies
```pip install -r requirements.txt```
### If you're on Windows, you may need:
```pip install psycopg2```
### If you're on Linux, install:
```pip install psycopg2-binary```

### 3. Create PostgreSQL database

```CREATE DATABASE sales;```

### 4. Configure connection

In main.py and seed.py:
```
host="localhost",
database="sales",
user="postgres",
password="your_password"
```

### 5. Seed the database
```
python seed.py
```

### 6. Run FastAPI backend
```
uvicorn main:app --reload --port 8000
```

### 7. Run UI
```
streamlit run ui.py
```

## 🧠 How the AI Works
### 1. User sends a question

Example:
```
“Show me top customers by revenue”
```

### 2. The model returns a function_call
```
Example:
{
  "tool_calls": [
    {
      "function": {
        "name": "query_database",
        "arguments": "{\"sql\":\"SELECT ...\"}"
      }
    }
  ]
}
```

### 3. Backend validates SQL:

- Only SELECT
- Only approved tables
- No UPDATE/DELETE/INSERT
- Blocks keywords (--, /*, union, pg_, etc.)
- Requires FROM
- Adds LIMIT

### 4. Backend executes safely and returns rows

## UI displays tables + charts.

## 🔒 SQL Injection Protection

Both the backend and seeding script include:

Forbidden patterns:
```;
--
/*
*/
union
information_schema
pg_
case
when
sleep
pg_sleep
```
Allowed tables:
```
customers, orders, order_items, products, payments
```
### 🛡 Protected logic: 
- Regex parsing of FROM/JOIN tables
- Safe SQL whitelist
- Auto LIMIT
- Rejects raw text SQL from the model

### 📌 Trello Integration

create_ticket() creates a fully structured Trello card:

```
create_ticket(title="Bug report", description="Payment calculation error")
```

### Automatically:
- Creates board
- Creates ToDo list
- Adds a card

# 🖼 Streamlit UI

### Features
- Chat-like interface  
- One message processed per refresh (prevents duplicates)  
- Automatic:
  - DataFrames  
  - Plotly charts  
  - Metrics  
  - JSON fallback  
- Error-safe requests  

---

# 📦 API Endpoint

### **POST** `/chat`

#### Request:
```json
{
  "message": "Show total sales for January"
}
```

## Response examples:
- List of rows
- Error message
- Trello card ID
- Text response

## 🧪 Example Queries
- "Top 10 products by revenue"
- "Show number of orders by status"
- "Payments by method"
- "Average order amount by city"
- "Which customers spent the most?"

## ❌ Not allowed
```sql
delete customers
drop table orders
insert into products
```

