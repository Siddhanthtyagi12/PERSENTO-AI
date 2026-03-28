import psycopg2
import os
import sys
# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sidprojects')))
from database import cloud_config

try:
    conn = psycopg2.connect(cloud_config.DB_CONNECTION_STRING)
    cursor = conn.cursor()
    cursor.execute("SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name = 'users' AND table_schema = 'public';")
    columns = cursor.fetchall()
    print("Columns in 'users' table:")
    for col in columns:
        print(f" - {col[0]} ({col[1]}) Default: {col[2]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
