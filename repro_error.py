import sqlite3
import os

def test_placeholder_mismatch():
    db_path = "test_logic.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS test (name TEXT)")
    
    q = "%s" # Mismatch placeholder (Postgres style in SQLite)
    try:
        cursor.execute(f"SELECT * FROM test WHERE name={q}", ("test",))
    except Exception as e:
        print(f"Caught Expected Error: {e}")
    finally:
        conn.close()
        os.remove(db_path)

if __name__ == "__main__":
    test_placeholder_mismatch()
