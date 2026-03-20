import sqlite3
from src.config import settings

conn = sqlite3.connect(settings.SQL_DB_PATH)
cursor = conn.cursor()
cursor.execute(
    "SELECT * FROM messages WHERE session_id='3b5e966c-007a-4e94-8391-1825d69e714e'",
)
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
