import psycopg2
from database import cloud_config

def check_db():
    conn = psycopg2.connect(cloud_config.DB_CONNECTION_STRING)
    cursor = conn.cursor()
    
    # Check Columns
    print("--- Cameras Columns ---")
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'cameras'")
    for row in cursor.fetchall():
        print(row[0])
        
    # Check Recent Additions
    print("\n--- Recent Cameras ---")
    cursor.execute("SELECT * FROM cameras ORDER BY id DESC LIMIT 5")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_db()
