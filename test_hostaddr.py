import psycopg2

def test_hostaddr():
    print("Testing host + hostaddr combination...")
    host = "db.dcrdwpkoytycopvnriqn.supabase.co"
    ipv4 = "3.108.251.216" # Resolved from pooler or direct
    user = "postgres"
    password = "siddhant@vanshika1234" # Raw password
    
    try:
        # This forces the IP but tells the server the hostname
        conn = psycopg2.connect(
            host=host,
            database="postgres",
            user=user,
            password=password,
            port=5432,
            hostaddr=ipv4,
            sslmode="require",
            connect_timeout=5
        )
        print("SUCCESS! hostaddr worked.")
        conn.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_hostaddr()
