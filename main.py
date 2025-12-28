import os
import sqlite3
from fastmcp import FastMCP


DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP(name="expense-tracker-mcp-server")


def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)


init_db()


@mcp.tool()
def add_expense(amount: float, category: str, date: str, subcategory: str = "", note: str = "") -> dict:
    """Add a new expense to the database."""
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("""
            INSERT INTO expenses (amount, category, date, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
        """, (amount, category, date, subcategory, note))
    return {"status": "ok", "msg": "Expense added successfully.", "id": cur.lastrowid}


@mcp.tool()
def list_expenses(start_date, end_date) -> list[dict]:
    """List expenses entries within an inclusive date range."""
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT id, amount, category, date, subcategory, note FROM expenses
            where date between ? and ?
            order by id asc
            """,
            (start_date, end_date)
        )
        col = [d[0] for d in cur.description]
        return [dict(zip(col, row)) for row in cur.fetchall()]


@mcp.tool()
def summarize(start_date, end_date, category=None) -> list[dict]:
    """Summarize total expenses by category within an inclusive date range."""
    with sqlite3.connect(DB_PATH) as c:
        query = """
            SELECT category, SUM(amount) as total FROM expenses
            where date between ? and ?
            """
        if category:
            query += " AND category = ?"
            cur = c.execute(
                query + " GROUP BY category order by category asc",
                (start_date, end_date, category)
            )
        else:
            query += " GROUP BY category"
        cur = c.execute(
            query,
            (start_date, end_date, category) if category else (start_date, end_date)
        )
        col = [d[0] for d in cur.description]
        return [dict(zip(col, row)) for row in cur.fetchall()]


@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    """Read fresh each time so you can edit the file without restarting."""
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
