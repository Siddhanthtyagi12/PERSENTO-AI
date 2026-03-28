import os
import psycopg2
from database import cloud_config

def inspect_cameras():
    conn_str = cloud_config.DB_CONNECTION_STRING
    conn = psycopg2.connect(conn_str)
    cursor = conn.cursor()
    
    print("Checking 'cameras' table...")
    try:
        cursor.execute("SELECT * FROM cameras")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error reading 'cameras' table: {e}")
        
    print("\nChecking sequence...")
    try:
        # PostgreSQL specific to get sequence of a serial column
        cursor.execute("SELECT pg_get_serial_sequence('cameras', 'id')")
        seq_name = cursor.fetchone()[0]
        print(f"Sequence name: {seq_name}")
        if seq_name:
            cursor.execute(f"SELECT last_value FROM {seq_name}")
            print(f"Sequence last_value: {cursor.fetchone()[0]}")
            cursor.execute(f"SELECT max(id) FROM cameras")
            print(f"Max(id) from cameras: {cursor.fetchone()[0]}")
    except Exception as e:
        print(f"Could not check sequence: {e}")
        
    conn.close()

if __name__ == "__main__":
    inspect_cameras()
