import psycopg2
import time

# Wait for Postgres to be ready
for i in range(10):
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="postgres",
            host="db",
            port=5432
        )
        break
    except Exception as e:
        print(f"Waiting for database... ({i+1}/10)")
        time.sleep(2)
else:
    raise Exception("Could not connect to the database.")

cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS dummy_data (
        id SERIAL PRIMARY KEY,
        info TEXT NOT NULL
    );
""")
cur.execute("INSERT INTO dummy_data (info) VALUES (%s)", ("Hello from Python in Docker!",))
conn.commit()
cur.execute("SELECT * FROM dummy_data;")
rows = cur.fetchall()
print("Rows in dummy_data:", rows)
cur.close()
conn.close() 