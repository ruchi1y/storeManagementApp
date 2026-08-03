def create_product(conn, name, type, cost, price):
    conn.execute(
        "INSERT INTO products (name, type, cost, price) VALUES (?, ?, ?, ?)",
        (name, type, cost, price),
    )
    conn.commit()

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