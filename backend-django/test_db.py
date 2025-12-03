import psycopg2
import sys

print(f"Python version: {sys.version}")
print(f"Psycopg2 version: {psycopg2.__version__}")

try:
    print("Attempting to connect to database openehr_django on port 5433 with password 'pass'...")
    conn = psycopg2.connect(
        dbname="openehr_django",
        user="fhir_user",
        password="pass",
        host="127.0.0.1",
        port="5433"
    )
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
