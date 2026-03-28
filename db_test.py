import os
import sys
# Add parent to path to import database
sys.path.append(os.getcwd())
from database import db_operations
import time

print("Attempting to connect to DB...")
try:
    conn = db_operations.connect_db()
    print("Connection successful!")
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    print("Query successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
