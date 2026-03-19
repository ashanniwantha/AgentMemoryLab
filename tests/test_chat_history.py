import sqlite3
from src.config import settings

conn = sqlite3.connect(settings.SQL_DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT * FROM messages")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
