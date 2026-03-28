import psycopg2
from database import cloud_config

def check_orgs():
    conn_str = cloud_config.DB_CONNECTION_STRING
    conn = psycopg2.connect(conn_str)
    cursor = conn.cursor()
    
    print("Checking 'organizations' table...")
    try:
        cursor.execute("SELECT id, name, email FROM organizations")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        cursor.execute("SELECT id, name, email FROM Organizations")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
            
    conn.close()

if __name__ == "__main__":
    check_orgs()
