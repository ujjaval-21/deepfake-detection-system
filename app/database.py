import sqlite3

conn = sqlite3.connect('models/database.db')
cur = conn.cursor()

cur.execute('''
CREATE TABLE users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
password TEXT
)
''')

cur.execute('''
CREATE TABLE history (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
filetype TEXT,
result TEXT
)
''')

conn.commit()
conn.close()
