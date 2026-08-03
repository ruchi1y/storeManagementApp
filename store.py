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