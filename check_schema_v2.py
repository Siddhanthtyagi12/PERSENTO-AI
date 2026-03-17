import psycopg2
from database import cloud_config

def check_schema():
    try:
        conn = psycopg2.connect(cloud_config.DB_CONNECTION_STRING)
        cursor = conn.cursor()
        
        tables = ['organizations', 'users']
        for table in tables:
            print(f"\n--- Schema for: {table} ---")
            cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}';")
            columns = cursor.fetchall()
            for col in columns:
                print(f"{col[0]}: {col[1]}")
            
        conn.close()
    except Exception as e:
        print(f"\n[ERROR] Schema Check Failed: {e}")

if __name__ == "__main__":
    check_schema()
