import sys
import os
# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db_operations
from database import cloud_config

print("=== PRESENTO DB TEST ===")
print(f"USE_CLOUD: {cloud_config.USE_CLOUD}")

try:
    conn = db_operations.connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    ver = cursor.fetchone()
    print(f"[SUCCESS] Database connected!")
    print(f"[INFO] Server Version: {ver[0]}")
    
    # Check tables
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = cursor.fetchall()
    print(f"[INFO] Tables found: {[t[0] for t in tables]}")
    
    conn.close()
except Exception as e:
    print(f"[FAILED] Connection Error: {e}")
    print("\nHELP: Agar ye error 'Connection Timeout' ya 'Authentication Failed' hai, to:")
    print("1. Supabase me 'Allow All IPs' (0.0.0.0/0) check karein.")
    print("2. cloud_config.py me URL check karein.")
