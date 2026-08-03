import sqlite3

def get_conn(db_path="store.db"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(db_path="store.db"):
    conn = get_conn(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            type TEXT,
            cost REAL,
            price REAL,
            stock INTEGER,
            minimum INTEGER,
            active INTEGER DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            type TEXT,
            quantity INTEGER,
            reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            total REAL,
            payment_method TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY,
            sale_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            FOREIGN KEY (sale_id) REFERENCES sales(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS closings (
            id INTEGER PRIMARY KEY,
            closed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            total REAL,
            sales_count INTEGER,
            payment_breakdown TEXT
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()