# FILE: test_database.py
import sqlite3

def test_database_tables():
    """Check if all required tables exist"""
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    required_tables = ['Organizations', 'Users', 'Attendance', 'Cameras']
    
    print("=== DATABASE TABLE CHECK ===")
    for table in required_tables:
        if table in tables:
            print(f"✅ {table} exists")
        else:
            print(f"❌ {table} MISSING!")
    
    conn.close()

# RUN THIS:
test_database_tables()