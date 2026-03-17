import psycopg2

def test_options():
    print("Testing connection with explicit -c project option...")
    # This IP is ap-south-1, which we found reachable but routing-unknown
    ip = "3.111.105.85"
    project_ref = "dcrdwpkoytycopvnriqn"
    user = "postgres"
    password = "siddhant@vanshika1234"
    
    try:
        # Pass options as a parameter to connect() instead of in DSN string
        conn = psycopg2.connect(
            host=ip,
            database="postgres",
            user=user,
            password=password,
            port=5432,
            sslmode="require",
            options=f"-c project={project_ref}",
            connect_timeout=10
        )
        print("SUCCESS! explicit options worked.")
        conn.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_options()
