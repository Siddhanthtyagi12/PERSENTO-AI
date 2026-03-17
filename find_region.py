import requests
import ipaddress

def find_aws_region(ip_to_check):
    url = "https://ip-ranges.amazonaws.com/ip-ranges.json"
    print(f"Downloading {url}...")
    try:
        data = requests.get(url).json()
    except Exception as e:
        print(f"Failed to download: {e}")
        return
        
    target = ipaddress.ip_address(ip_to_check)
    print(f"Searching for {target}...")
    
    # Check IPv6 prefixes
    for entry in data.get('ipv6_prefixes', []):
        network = ipaddress.ip_network(entry['ipv6_prefix'])
        if target in network:
            print(f"!!! MATCH FOUND !!!")
            print(f"Region: {entry['region']}")
            print(f"Service: {entry['service']}")
            print(f"Prefix: {entry['ipv6_prefix']}")
            return entry['region']

    # Check IPv4 prefixes just in case
    if target.version == 4:
        for entry in data.get('prefixes', []):
            network = ipaddress.ip_network(entry['ip_prefix'])
            if target in network:
                print(f"!!! MATCH FOUND !!!")
                print(f"Region: {entry['region']}")
                print(f"Service: {entry['service']}")
                print(f"Prefix: {entry['ip_prefix']}")
                return entry['region']
                
    print("No match found in AWS IP ranges.")
    return None

if __name__ == "__main__":
    find_aws_region("2406:da1a:6b0:f62f:799d:3fc5:bfc8:22cd")
