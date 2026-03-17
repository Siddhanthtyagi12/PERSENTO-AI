import psycopg2
from database import cloud_config

def check_db():
    print(f"Connecting to: {cloud_config.DB_CONNECTION_STRING.split('@')[-1]}")
    try:
        conn = psycopg2.connect(cloud_config.DB_CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")
        tables = cursor.fetchall()
        print("\nTables found in Supabase:")
        for t in tables:
            print(f"- {t[0]}")
            
        # Check organizations
        if ('organizations',) in tables or ('Organizations',) in tables:
            tbl = "organizations" if ('organizations',) in tables else "Organizations"
            cursor.execute(f"SELECT id, name, email FROM {tbl};")
            orgs = cursor.fetchall()
            print(f"\nOrganizations in {tbl}:")
            for o in orgs:
                print(f"ID: {o[0]}, Name: {o[1]}, Email: {o[2]}")
        else:
            print("\n[WARNING] Organizations table NOT found!")
            
        conn.close()
    except Exception as e:
        print(f"\n[ERROR] Could not connect or query: {e}")

if __name__ == "__main__":
    check_db()
