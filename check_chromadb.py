import sqlite3

conn = sqlite3.connect('telecom_assistant/data/chromadb/chroma.sqlite3')
cursor = conn.cursor()

print("=== ChromaDB Embeddings Table Schema ===")
cursor.execute("PRAGMA table_info(embeddings)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

print("\n=== Embeddings Data ===")
cursor.execute("SELECT * FROM embeddings LIMIT 1")
embedding = cursor.fetchone()
if embedding:
    print(f"Found 1 embedding:")
    print(f"  Columns: {[desc[0] for desc in cursor.description]}")
    print(f"  Data: {embedding}")
else:
    print("No embeddings found")

print("\n=== Collections ===")
cursor.execute("SELECT id, name FROM collections")
collections = cursor.fetchall()
for coll in collections:
    print(f"  Collection: {coll[1]} (ID: {coll[0]})")

conn.close()
