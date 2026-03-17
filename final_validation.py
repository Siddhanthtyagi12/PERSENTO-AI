import psycopg2

def test_final_check():
    project_ref = "dcrdwpkoytycopvnriqn"
    user = f"postgres.{project_ref}"
    password = "siddhant@vanshika1234"
    host = "aws-1-ap-south-1.pooler.supabase.com"
    
    for port in [5432, 6543]:
        print(f"Testing {host} on port {port}...")
        try:
            conn = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database="postgres",
                port=port,
                sslmode="require",
                connect_timeout=10
            )
            print(f"  !!! SUCCESS on port {port} !!!")
            conn.close()
        except Exception as e:
            print(f"  Failed on port {port}: {e}")

if __name__ == "__main__":
    test_final_check()
