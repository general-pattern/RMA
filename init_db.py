import sqlite3

with open("schema.sql", "r", encoding="utf-8") as f:
    sql = f.read()

conn = sqlite3.connect("rma.db")
conn.executescript(sql)
conn.close()

print("DB created")