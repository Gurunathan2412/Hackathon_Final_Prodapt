import sqlite3

conn = sqlite3.connect('original_data/data/telecom.db')
cursor = conn.cursor()

# Check all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=== All Tables in Database ===")
for table in tables:
    print(f"  - {table[0]}")

print("\n=== Support Tickets Table Schema ===")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='support_tickets'")
result = cursor.fetchone()
if result:
    print(result[0])
else:
    print("Table does not exist")

print("\n=== Sample Support Tickets (if any) ===")
try:
    cursor.execute("SELECT * FROM support_tickets LIMIT 3")
    tickets = cursor.fetchall()
    if tickets:
        for ticket in tickets:
            print(ticket)
    else:
        print("No tickets found")
except:
    print("Table doesn't exist or error querying")

conn.close()
