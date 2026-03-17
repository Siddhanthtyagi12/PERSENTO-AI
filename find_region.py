import psycopg2
import concurrent.futures

def test_region(region):
    project_ref = "dcrdwpkoytycopvnriqn"
    host = f"{region}.pooler.supabase.com"
    user = f"postgres.{project_ref}"
    password = "siddhant@vanshika1234"
    
    # Try Port 5432 (Session mode usually more reliable for initial check)
    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database="postgres",
            port=5432,
            sslmode="require",
            connect_timeout=5
        )
        conn.close()
        return region, True, None
    except Exception as e:
        return region, False, str(e)

if __name__ == "__main__":
    regions = [
        "aws-0-us-east-1", "aws-0-us-east-2", "aws-0-us-west-1", "aws-0-us-west-2",
        "aws-0-ap-south-1", "aws-0-ap-southeast-1", "aws-0-ap-southeast-2", "aws-0-ap-northeast-1",
        "aws-0-eu-central-1", "aws-0-eu-west-1", "aws-0-eu-west-2", "aws-0-eu-west-3",
        "aws-0-sa-east-1", "aws-0-ca-central-1", "aws-0-me-south-1"
    ]
    
    print("Searching for the correct Supabase region...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(test_region, regions))
    
    found = False
    for region, success, error in results:
        if success:
            print(f"FOUND WORKING REGION: {region}")
            found = True
        elif "Tenant or user not found" not in error and "timeout" not in error.lower():
             # If it's a different error (like auth), it might actually be the right region but wrong creds
             # (Unlikely since we know creds work locally)
             pass

    if not found:
        print("No region matched with current credentials.")
        # Try to find which ones DID NOT return 'Tenant or user not found'
        for region, success, error in results:
            if "Tenant or user not found" not in error:
                print(f"Region {region} returned a different error: {error}")
