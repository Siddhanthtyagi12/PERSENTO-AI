import socket
import concurrent.futures

regions = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "ap-south-1", "ap-southeast-1", "ap-southeast-2", 
    "ap-northeast-1", "ap-northeast-2", "ap-northeast-3",
    "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1", "eu-central-2",
    "sa-east-1", "ca-central-1", "me-south-1", "af-south-1"
]

def check_pooler(region):
    host = f"aws-0-{region}.pooler.supabase.com"
    try:
        # Get IPv4 address
        addr = socket.gethostbyname(host)
        return region, addr
    except:
        return region, None

if __name__ == "__main__":
    print("Checking which pooler regions have IPv4 addresses...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(check_pooler, regions))
    
    for region, ip in results:
        if ip:
            print(f"Region: {region} -> IP: {ip}")
