import psycopg2
from database import cloud_config

def fix_data():
    conn = psycopg2.connect(cloud_config.DB_CONNECTION_STRING)
    cursor = conn.cursor()
    
    print("Fetching cameras to clean...")
    cursor.execute("SELECT id, source FROM cameras")
    cameras = cursor.fetchall()
    
    count = 0
    for cid, source in cameras:
        if source and (source.startswith(" ") or source.endswith(" ")):
            clean_source = source.strip()
            print(f"Cleaning ID {cid}: '{source}' -> '{clean_source}'")
            cursor.execute("UPDATE cameras SET source = %s WHERE id = %s", (clean_source, cid))
            count += 1
            
    conn.commit()
    conn.close()
    print(f"Successfully cleaned {count} camera records.")

if __name__ == "__main__":
    fix_data()
