import json

def create_product(conn, name, type, cost, price):
    cur = conn.execute(
        "INSERT INTO products (name, type, cost, price) VALUES (?, ?, ?, ?)",
        (name, type, cost, price),
    )
    conn.commit()
    return cur.lastrowid

def update_product(conn, product_id, name, type, cost, price):
    conn.execute(
        "UPDATE products SET name=?, type=?, cost=?, price=? WHERE id=?",
        (name, type, cost, price, product_id),
    )
    conn.commit()

def add_stock(conn, product_id, quantity, reason="compra a proveedor"):
    conn.execute(
        "UPDATE products SET stock = stock + ? WHERE id = ?",
        (quantity, product_id),
    )
    conn.execute(
        "INSERT INTO movements (product_id, type, quantity, reason) VALUES (?, 'entry', ?, ?)",
        (product_id, quantity, reason),
    )
    conn.commit()

def remove_stock(conn, product_id, quantity, reason="venta"):
    conn.execute(
        "UPDATE products SET stock = stock - ? WHERE id = ?",
        (quantity, product_id),
    )
    conn.execute(
        "INSERT INTO movements (product_id, type, quantity, reason) VALUES (?, 'exit', ?, ?)",
        (product_id, quantity, reason),
    )
    conn.commit()

def get_products(conn, q=""):
    if q:
        return conn.execute(
            "SELECT * FROM products WHERE name LIKE ? ORDER BY name",
            (f"%{q}%",),
        ).fetchall()
    return conn.execute("SELECT * FROM products ORDER BY name").fetchall()

def get_product(conn, product_id):
    return conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

def register_sale(conn, items, payment_method):
    with conn:
        total = 0.0
        for product_id, quantity in items:
            product = get_product(conn, product_id)
            if product["stock"] < quantity:
                raise ValueError(f"Stock insuficiente para '{product['name']}'")
            total += product["price"] * quantity

        cur = conn.execute(
            "INSERT INTO sales (total, payment_method) VALUES (?, ?)",
            (total, payment_method),
        )
        sale_id = cur.lastrowid

        for product_id, quantity in items:
            product = get_product(conn, product_id)
            conn.execute(
                "INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (sale_id, product_id, quantity, product["price"]),
            )
            conn.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (quantity, product_id),
            )
            conn.execute(
                "INSERT INTO movements (product_id, type, quantity, reason) VALUES (?, 'exit', ?, ?)",
                (product_id, quantity, "venta"),
            )

def is_cash_open(conn):
    row = conn.execute("SELECT value FROM settings WHERE key = 'cash_open'").fetchone()
    return row is None or row["value"] == "1"

def get_daily_summary(conn):
    row = conn.execute(
        "SELECT COUNT(*) AS sales_count, COALESCE(SUM(total), 0) AS total "
        "FROM sales WHERE date(created_at) = date('now')"
    ).fetchone()
    breakdown = {"cash": 0.0, "card": 0.0, "qr": 0.0}
    for r in conn.execute(
        "SELECT payment_method, SUM(total) AS subtotal FROM sales "
        "WHERE date(created_at) = date('now') GROUP BY payment_method"
    ).fetchall():
        breakdown[r["payment_method"]] = r["subtotal"]
    return {
        "total": row["total"],
        "sales_count": row["sales_count"],
        "breakdown": breakdown,
    }

def close_cash(conn):
    summary = get_daily_summary(conn)
    conn.execute(
        "INSERT INTO closings (total, sales_count, payment_breakdown) VALUES (?, ?, ?)",
        (summary["total"], summary["sales_count"], json.dumps(summary["breakdown"])),
    )
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('cash_open', '0')"
    )
    conn.commit()

def open_cash(conn):
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('cash_open', '1')")
    conn.commit()

def get_low_stock(conn):
    return conn.execute(
        "SELECT * FROM products WHERE stock <= minimum ORDER BY name"
    ).fetchall()

def get_sales(conn):
    return conn.execute(
        "SELECT * FROM sales ORDER BY id DESC"
    ).fetchall()

def get_closings(conn):
    rows = conn.execute("SELECT * FROM closings ORDER BY id DESC").fetchall()
    result = []
    for r in rows:
        item = dict(r)
        item["payment_breakdown"] = json.loads(item["payment_breakdown"])
        result.append(item)
    return result

def set_product_image(conn, product_id, image):
    conn.execute(
        "UPDATE products SET image = ? WHERE id = ?",
        (image, product_id),
    )
    conn.commit()