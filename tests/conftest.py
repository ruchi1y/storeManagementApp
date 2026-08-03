import pytest
import db

@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    db.init_db(db_path)
    conn = db.get_conn(db_path)
    yield conn
    conn.close()