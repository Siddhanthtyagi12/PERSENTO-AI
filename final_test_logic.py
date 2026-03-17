import psycopg2

def final_attempt():
    project_ref = "dcrdwpkoytycopvnriqn"
    # The standard username for pooler is postgres.[project-ref]
    user = f"postgres.{project_ref}"
    password = "siddhant@vanshika1234" # NOT encoded
    host = "aws-0-ap-south-1.pooler.supabase.com"
    
    # Try Port 6543 (Transaction)
    print(f"Testing {host} on 6543...")
    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database="postgres",
            port=6543,
            sslmode="require",
            connect_timeout=10
        )
        print("SUCCESS on 6543!")
        conn.close()
        return
    except Exception as e:
        print(f"6543 FAILED: {e}")

    # Try Port 5432 (Session)
    print(f"Testing {host} on 5432...")
    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database="postgres",
            port=5432,
            sslmode="require",
            connect_timeout=10
        )
        print("SUCCESS on 5432!")
        conn.close()
        return
    except Exception as e:
        print(f"5432 FAILED: {e}")

    # Try standard host but with hostaddr to force IPv4
    ipv4 = "3.108.251.216"
    print(f"Testing hostaddr trick with IP {ipv4}...")
    try:
        conn = psycopg2.connect(
            host="db.dcrdwpkoytycopvnriqn.supabase.co",
            hostaddr=ipv4,
            user="postgres",
            password=password,
            database="postgres",
            port=5432,
            sslmode="require",
            connect_timeout=10
        )
        print("SUCCESS on hostaddr trick!")
        conn.close()
        return
    except Exception as e:
        print(f"hostaddr FAILED: {e}")

if __name__ == "__main__":
    final_attempt()
