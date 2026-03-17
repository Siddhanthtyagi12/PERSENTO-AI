import psycopg2
import concurrent.futures

def test_ip(region, ip):
    project_ref = "dcrdwpkoytycopvnriqn"
    user = f"postgres.{project_ref}"
    password = "siddhant@vanshika1234"
    
    # Try Port 6543 (Transaction mode)
    try:
        conn = psycopg2.connect(
            host=ip,
            user=user,
            password=password,
            database="postgres",
            port=6543,
            sslmode="require",
            connect_timeout=3
        )
        conn.close()
        return region, ip, True, None
    except Exception as e:
        error = str(e)
        return region, ip, False, error

if __name__ == "__main__":
    targets = [
        ("us-east-1", "44.208.221.186"),
        ("us-east-2", "13.59.95.192"),
        ("us-west-1", "54.177.55.191"),
        ("us-west-2", "44.238.118.41"),
        ("ap-southeast-1", "54.255.219.82"),
        ("ap-southeast-2", "3.106.102.114"),
        ("ap-northeast-1", "52.68.3.1"),
        ("ap-northeast-2", "15.165.245.138"),
        ("eu-west-1", "52.209.89.87"),
        ("eu-west-2", "18.169.28.97"),
        ("eu-west-3", "13.39.246.141"),
        ("eu-central-1", "52.59.152.35"),
        ("eu-central-2", "51.96.34.188"),
        ("sa-east-1", "54.94.90.106"),
        ("ca-central-1", "15.156.114.158")
    ]
    
    print("Testing connection to all regions via IPv4...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        results = [executor.submit(test_ip, r, i) for r, i in targets]
        
        for future in concurrent.futures.as_completed(results):
            region, ip, success, error = future.result()
            if success:
                print(f"!!! SUCCESS !!! Region: {region}, IP: {ip}")
            elif "Tenant or user not found" not in error:
                print(f"Region: {region} ({ip}) -> ERROR: {error}")
