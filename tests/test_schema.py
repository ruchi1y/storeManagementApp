def test_init_db_creates_all_tables(conn):
    tables = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    assert {"products", "movements", "sales", "sale_items", "closings", "settings"} <= tables