import os
import psycopg2
from database import cloud_config

def inspect_cameras():
    conn_str = cloud_config.DB_CONNECTION_STRING
    conn = psycopg2.connect(conn_str)
    cursor = conn.cursor()
    
    print("--- Organizations ---")
    cursor.execute("SELECT id, name FROM organizations")
    for row in cursor.fetchall():
        print(row)

    print("\n--- Cameras ---")
    cursor.execute("SELECT id, org_id, source, label, is_active FROM cameras")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    inspect_cameras()
