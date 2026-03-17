import psycopg2

def test_hostaddr():
    project_ref = "dcrdwpkoytycopvnriqn"
    user = f"postgres.{project_ref}"
    password = "siddhant@vanshika1234"
    host = f"aws-0-ap-south-1.pooler.supabase.com"
    ip = "3.108.251.216" # ap-south-1 IP
    
    print(f"Testing {host} with hostaddr={ip}...")
    try:
        conn = psycopg2.connect(
            host=host,
            hostaddr=ip,
            user=user,
            password=password,
            database="postgres",
            port=6543,
            sslmode="require",
            connect_timeout=10
        )
        print("!!! SUCCESS !!! Connection established.")
        conn.close()
        return True
    except Exception as e:
        print(f"FAILED: {e}")
    return False

if __name__ == "__main__":
    test_hostaddr()
