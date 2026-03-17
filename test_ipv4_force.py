import socket
import psycopg2
from database import cloud_config

def get_ipv4(host):
    try:
        # Force IPv4 lookup
        addr_info = socket.getaddrinfo(host, None, socket.AF_INET)
        return addr_info[0][4][0]
    except Exception as e:
        print(f"Could not find IPv4 for {host}: {e}")
        return None

def test_ipv4_force():
    host = "db.dcrdwpkoytycopvnriqn.supabase.co"
    ipv4 = get_ipv4(host)
    if not ipv4:
        return
    
    print(f"Hostname: {host}")
    print(f"Resolved IPv4: {ipv4}")
    
    user = "postgres"
    password = "siddhant@vanshika1234"
    
    print("\n--- Testing hostaddr trick with forced IPv4 ---")
    try:
        conn = psycopg2.connect(
            host=host,
            hostaddr=ipv4,
            user=user,
            password=password,
            database="postgres",
            port=5432,
            sslmode="require",
            connect_timeout=10
        )
        print("SUCCESS! hostaddr worked.")
        conn.close()
    except Exception as e:
        print(f"test_ipv4_force FAILED: {e}")

if __name__ == "__main__":
    test_ipv4_force()
