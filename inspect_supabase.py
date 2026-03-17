import urllib.request
import json

def get_supabase_info():
    project_ref = "dcrdwpkoytycopvnriqn"
    url = f"https://{project_ref}.supabase.co/rest/v1/"
    print(f"Inspecting Project: {project_ref}")
    try:
        # We expect a 401 or 404, we just want the headers
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            pass
    except urllib.error.HTTPError as e:
        print("\n--- Headers ---")
        for key, value in e.headers.items():
            print(f"{key}: {value}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_supabase_info()
