import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="minhtri10a22k5",
        port=5432,
        dbname="postgres"
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"Postgres SQL connection successful. Server version {version}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Postgres SQL connection failed {e}")
    