import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

dbname = os.getenv('DB_NAME')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')

print(f"Attempting to connect with:")
print(f"DB_NAME: {dbname}")
print(f"DB_USER: {user}")
print(f"DB_HOST: {host}")
print(f"DB_PORT: {port}")
# Do NOT print the password

try:
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    print("SUCCESS: Connection established!")
    conn.close()
except Exception as e:
    print(f"FAILURE: {e}")
