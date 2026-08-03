from store import (create_product, update_product, add_stock, remove_stock, get_products, get_product, register_sale, is_cash_open, 
                   close_cash, get_daily_summary, open_cash, get_low_stock, get_sales, get_closings)

import json

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

def test_register_sale_creates_sale_and_items(conn):
    create_product(conn, name="Coca", type="gaseosa", cost=1200.0, price=1500.0)
    create_product(conn, name="Agua", type="gaseosa", cost=500.0, price=800.0)
    coca_id = conn.execute("SELECT id FROM products WHERE name='Coca'").fetchone()["id"]
    agua_id = conn.execute("SELECT id FROM products WHERE name='Agua'").fetchone()["id"]
    add_stock(conn, coca_id, quantity=10)
    add_stock(conn, agua_id, quantity=10)

    register_sale(conn, items=[(coca_id, 2), (agua_id, 1)], payment_method="cash")

    sale = conn.execute("SELECT * FROM sales").fetchone()
    assert sale is not None
    assert sale["total"] == 2 * 1500.0 + 1 * 800.0
    assert sale["payment_method"] == "cash"

    items = conn.execute("SELECT * FROM sale_items").fetchall()
    assert len(items) == 2

def test_register_sale_decrements_stock(conn):
    create_product(conn, name="Coca", type="gaseosa", cost=1200.0, price=1500.0)
    coca_id = conn.execute("SELECT id FROM products WHERE name='Coca'").fetchone()["id"]
    add_stock(conn, coca_id, quantity=10)

    register_sale(conn, items=[(coca_id, 2)], payment_method="cash")

    row = conn.execute("SELECT * FROM products WHERE id = ?", (coca_id,)).fetchone()
    assert row["stock"] == 8

    mov = conn.execute(
        "SELECT * FROM movements WHERE product_id = ? AND type='exit'",
        (coca_id,),
    ).fetchone()
    assert mov is not None
    assert mov["quantity"] == 2
    assert mov["reason"] == "venta"

def test_register_sale_insufficient_stock_rolls_back(conn):
    create_product(conn, name="Coca", type="gaseosa", cost=1200.0, price=1500.0)
    create_product(conn, name="Agua", type="gaseosa", cost=500.0, price=800.0)
    coca_id = conn.execute("SELECT id FROM products WHERE name='Coca'").fetchone()["id"]
    agua_id = conn.execute("SELECT id FROM products WHERE name='Agua'").fetchone()["id"]
    add_stock(conn, coca_id, quantity=10)
    add_stock(conn, agua_id, quantity=2)

    try:
        register_sale(conn, items=[(coca_id, 5), (agua_id, 3)], payment_method="cash")
        assert False, "debería haber fallado por stock insuficiente"
    except ValueError:
        pass

    assert conn.execute("SELECT COUNT(*) AS n FROM sales").fetchone()["n"] == 0
    assert conn.execute("SELECT COUNT(*) AS n FROM sale_items").fetchone()["n"] == 0

    coca = conn.execute("SELECT * FROM products WHERE id = ?", (coca_id,)).fetchone()
    agua = conn.execute("SELECT * FROM products WHERE id = ?", (agua_id,)).fetchone()
    assert coca["stock"] == 10
    assert agua["stock"] == 2

def test_is_cash_open_default(conn):
    assert is_cash_open(conn) is True

def test_close_cash_saves_summary(conn):
    create_product(conn, name="Coca", type="gaseosa", cost=1200.0, price=1500.0)
    coca_id = conn.execute("SELECT id FROM products WHERE name='Coca'").fetchone()["id"]
    add_stock(conn, coca_id, quantity=10)

    register_sale(conn, items=[(coca_id, 2)], payment_method="cash")
    register_sale(conn, items=[(coca_id, 1)], payment_method="card")

    close_cash(conn)

    row = conn.execute("SELECT * FROM closings").fetchone()
    assert row is not None
    assert row["total"] == 2 * 1500.0 + 1 * 1500.0
    assert row["sales_count"] == 2

    breakdown = json.loads(row["payment_breakdown"])
    assert breakdown["cash"] == 2 * 1500.0
    assert breakdown["card"] == 1 * 1500.0
    assert breakdown["qr"] == 0

def test_daily_summary_ignores_old_sales(conn):
    create_product(conn, name="Coca", type="gaseosa", cost=1200.0, price=1500.0)
    coca_id = conn.execute("SELECT id FROM products WHERE name='Coca'").fetchone()["id"]
    add_stock(conn, coca_id, quantity=10)

    register_sale(conn, items=[(coca_id, 1)], payment_method="cash")

    conn.execute(
        "INSERT INTO sales (created_at, total, payment_method) "
        "VALUES (datetime('now', '-1 day'), 5000.0, 'card')"
    )
    conn.commit()

    summary = get_daily_summary(conn)
    assert summary["sales_count"] == 1
    assert summary["total"] == 1500.0
    assert summary["breakdown"]["card"] == 0

def test_open_cash_reopens(conn):
    close_cash(conn)
    assert is_cash_open(conn) is False
    open_cash(conn)
    assert is_cash_open(conn) is True

def test_get_low_stock(conn):
    create_product(conn, name="Coca", type="gaseosa", cost=1200.0, price=1500.0)
    create_product(conn, name="Agua", type="gaseosa", cost=500.0, price=800.0)
    coca_id = conn.execute("SELECT id FROM products WHERE name='Coca'").fetchone()["id"]
    agua_id = conn.execute("SELECT id FROM products WHERE name='Agua'").fetchone()["id"]

    conn.execute("UPDATE products SET minimum = 5 WHERE id = ?", (coca_id,))
    conn.execute("UPDATE products SET minimum = 5 WHERE id = ?", (agua_id,))
    conn.commit()

    add_stock(conn, coca_id, quantity=10)
    add_stock(conn, agua_id, quantity=3)

    bajos = get_low_stock(conn)
    names = [p["name"] for p in bajos]
    assert names == ["Agua"]

def test_get_sales_returns_history(conn):
    create_product(conn, name="Coca", type="gaseosa", cost=1200.0, price=1500.0)
    coca_id = conn.execute("SELECT id FROM products WHERE name='Coca'").fetchone()["id"]
    add_stock(conn, coca_id, quantity=10)

    register_sale(conn, items=[(coca_id, 1)], payment_method="cash")
    register_sale(conn, items=[(coca_id, 2)], payment_method="card")

    ventas = get_sales(conn)
    assert len(ventas) == 2
    assert ventas[0]["payment_method"] == "card"
    assert ventas[0]["total"] == 2 * 1500.0
    assert ventas[1]["payment_method"] == "cash"

def test_get_closings_returns_history(conn):
    create_product(conn, name="Coca", type="gaseosa", cost=1200.0, price=1500.0)
    coca_id = conn.execute("SELECT id FROM products WHERE name='Coca'").fetchone()["id"]
    add_stock(conn, coca_id, quantity=10)

    register_sale(conn, items=[(coca_id, 1)], payment_method="cash")
    close_cash(conn)

    cierres = get_closings(conn)
    assert len(cierres) == 1
    assert cierres[0]["total"] == 1500.0
    assert cierres[0]["sales_count"] == 1
    assert cierres[0]["payment_breakdown"]["cash"] == 1500.0