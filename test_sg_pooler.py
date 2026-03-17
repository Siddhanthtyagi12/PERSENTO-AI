import psycopg2

def test_sg_pooler():
    project_ref = "dcrdwpkoytycopvnriqn"
    user = f"postgres.{project_ref}"
    password = "siddhant@vanshika1234"
    host = "aws-0-ap-southeast-1.pooler.supabase.com"
    
    for port in [6543, 5432]:
        print(f"Testing {host} on {port}...")
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
            print(f"!!! SUCCESS !!! Port: {port}")
            conn.close()
            return True
        except Exception as e:
            print(f"FAILED on {port}: {e}")
    return False

if __name__ == "__main__":
    test_sg_pooler()
