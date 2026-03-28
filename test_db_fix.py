import sqlite3
import os
from database import db_operations

def test_db_fix():
    print("Testing DB Fix (Local SQLite)...")
    
    # Ensure USE_CLOUD is False for this test if possible, 
    # but we can just check if db_operations.add_org_camera works.
    
    org_id = 99
    source = " 1 " # Source with space
    label = "Test DB Fix"
    
    # Manually use SQLite for test
    db_file = db_operations.DB_PATH
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Clear previous test data
    cursor.execute("DELETE FROM Cameras WHERE org_id=?", (org_id,))
    conn.commit()
    conn.close()
    
    # Run the function
    db_operations.add_org_camera(org_id, source, label)
    
    # Check Result
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT source, label, is_active FROM Cameras WHERE org_id=?", (org_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        print(f"Row found: {row}")
        assert row[0] == "1"
        assert row[2] == 1
        print("✓ DB fix verified (stripped source and is_active=1)")
    else:
        print("✗ No row found in local DB")

if __name__ == "__main__":
    test_db_fix()
