#!/usr/bin/env python3
import sqlite3


conn = sqlite3.connect(".coverage")
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

# Check schema for each table
for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [(row[1], row[2]) for row in cursor.fetchall()]
    print(f"\n{table} columns:")
    for col_name, col_type in columns:
        print(f"  - {col_name} ({col_type})")

conn.close()
