import psycopg2
import socket

def brute_force_regions():
    regions = [
        "ap-south-1", "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ap-northeast-2",
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-central-1", "eu-west-1", "eu-west-2", "eu-west-3", "eu-north-1",
        "sa-east-1", "ca-central-1"
    ]
    project_ref = "dcrdwpkoytycopvnriqn"
    user = f"postgres.{project_ref}"
    password = "siddhant@vanshika1234"
    
    for r in regions:
        host = f"aws-0-{r}.pooler.supabase.com"
        print(f"Testing region: {r} ({host})...")
        try:
            # First Resolve to verify it exists
            ip = socket.gethostbyname(host)
            print(f"  Resolved to {ip}")
            
            # Try connect to port 6543 (Transaction)
            conn = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database="postgres",
                port=6543,
                sslmode="require",
                connect_timeout=5
            )
            print(f"  !!! SUCCESS in {r} !!!")
            conn.close()
            return r
        except Exception as e:
            if "Tenant or user not found" in str(e):
                print(f"  Incorrect region (Tenant not found)")
            else:
                print(f"  Error: {e}")
    return None

if __name__ == "__main__":
    found = brute_force_regions()
    if found:
        print(f"\nFINAL RESULT: Project is in {found}")
    else:
        print("\nFINAL RESULT: No region found.")
