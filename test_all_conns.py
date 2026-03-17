import psycopg2
import time

def test_connection(label, host, port, user):
    print(f"\n--- Testing: {label} ---")
    print(f"Host: {host}, Port: {port}, User: {user}")
    dsn = f"postgresql://{user}:siddhant%40vanshika1234@{host}:{port}/postgres?sslmode=require"
    try:
        conn = psycopg2.connect(dsn, connect_timeout=5)
        print(f"SUCCESS: {label} Connected!")
        conn.close()
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    project_ref = "dcrdwpkoytycopvnriqn"
    # Try different combinations
    
    # 1. Pooler Hostname + Transaction Port (6543) + Project-Ref User
    test_connection("Pooler Host (6543)", "aws-0-ap-south-1.pooler.supabase.com", 6543, f"postgres.{project_ref}")
    
    # 2. Pooler Hostname + Session Port (5432) + Project-Ref User
    test_connection("Pooler Host (5432)", "aws-0-ap-south-1.pooler.supabase.com", 5432, f"postgres.{project_ref}")
    
    # 3. Direct IPv4 + Transaction Port (6543) + Project-Ref User
    test_connection("Direct IP (6543)", "3.108.251.216", 6543, f"postgres.{project_ref}")
    
    # 4. Direct IPv4 + Session Port (5432) + Project-Ref User
    test_connection("Direct IP (5432)", "3.108.251.216", 5432, f"postgres.{project_ref}")
