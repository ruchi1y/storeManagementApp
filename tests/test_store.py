from store import create_product, update_product, add_stock, remove_stock, get_products, get_product

def test_create_product(conn):
    create_product(conn, name="Coca", type="gaseosa", cost=1200.0, price=1500.0)

    row = conn.execute(
        "SELECT * FROM products WHERE name = 'Coca'"
    ).fetchone()
    assert row is not None
    assert row["name"] == "Coca"
    assert row["price"] == 1500.0

def test_update_product(conn):
    create_product(conn, name="Coca", type="gaseosa", cost=1200.0, price=1500.0)
    product_id = conn.execute("SELECT id FROM products WHERE name='Coca'").fetchone()["id"]

    update_product(conn, product_id, name="Coca 1.5L", type="gaseosa", cost=1200.0, price=2500.0)

    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    assert row["name"] == "Coca 1.5L"
    assert row["price"] == 2500.0

def test_add_stock(conn):
    create_product(conn, name="Coca", type="gaseosa", cost=1200.0, price=1500.0)
    product_id = conn.execute("SELECT id FROM products WHERE name='Coca'").fetchone()["id"]

    add_stock(conn, product_id, quantity=10)

    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    assert row["stock"] == 10

    mov = conn.execute("SELECT * FROM movements WHERE product_id = ?", (product_id,)).fetchone()
    assert mov is not None
    assert mov["type"] == "entry"
    assert mov["quantity"] == 10

def test_remove_stock(conn):
    create_product(conn, name="Coca", type="gaseosa", cost=1200.0, price=1500.0)
    product_id = conn.execute("SELECT id FROM products WHERE name='Coca'").fetchone()["id"]
    add_stock(conn, product_id, quantity=10)

    remove_stock(conn, product_id, quantity=3)

    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    assert row["stock"] == 7

    mov = conn.execute(
        "SELECT * FROM movements WHERE product_id = ? AND type='exit'",
        (product_id,),
    ).fetchone()
    assert mov is not None
    assert mov["quantity"] == 3

def test_get_products_with_search(conn):
    create_product(conn, name="Coca", type="gaseosa", cost=1200.0, price=1500.0)
    create_product(conn, name="Agua", type="gaseosa", cost=500.0, price=800.0)

    results = get_products(conn, q="co")
    names = [p["name"] for p in results]
    assert names == ["Coca"]

def test_get_product(conn):
    create_product(conn, name="Coca", type="gaseosa", cost=1200.0, price=1500.0)
    pid = conn.execute("SELECT id FROM products WHERE name='Coca'").fetchone()["id"]

    p = get_product(conn, pid)

    assert p["name"] == "Coca"