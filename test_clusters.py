import psycopg2
import socket

def test_clusters():
    project_ref = "dcrdwpkoytycopvnriqn"
    user = f"postgres.{project_ref}"
    password = "siddhant@vanshika1234"
    region = "ap-south-1"
    
    for i in range(5):
        host = f"aws-{i}-{region}.pooler.supabase.com"
        print(f"Testing cluster {i}: {host}...")
        try:
            ip = socket.gethostbyname(host)
            print(f"  Resolved to {ip}")
            conn = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database="postgres",
                port=6543,
                sslmode="require",
                connect_timeout=5
            )
            print(f"  !!! SUCCESS on cluster {i} !!!")
            conn.close()
            return host
        except Exception as e:
            print(f"  Failed: {e}")
            
    return None

if __name__ == "__main__":
    test_clusters()
