import os
import psycopg2
from database import cloud_config

def fix_sequence():
    conn_str = cloud_config.DB_CONNECTION_STRING
    conn = psycopg2.connect(conn_str)
    cursor = conn.cursor()
    
    print("Fixing 'cameras_id_seq'...")
    try:
        # Reset the sequence to the current max ID + 1
        cursor.execute("SELECT setval('cameras_id_seq', (SELECT MAX(id) FROM cameras))")
        new_val = cursor.fetchone()[0]
        print(f"Sequence synced! New last_value: {new_val}")
        conn.commit()
    except Exception as e:
        print(f"Error fixing sequence: {e}")
        conn.rollback()
        
    conn.close()

if __name__ == "__main__":
    fix_sequence()
