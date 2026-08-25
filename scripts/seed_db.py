import os
import sqlite3
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SQL_DIR = os.path.join(BASE_DIR, "sql")
DB_PATH = os.path.join(BASE_DIR, "fintech_analytics.db")

def seed_database():
    print(f"Connecting to SQLite Database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Run Schema creation
    schema_path = os.path.join(SQL_DIR, "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
            cursor.executescript(schema_sql)
        print("Schema and indexes created successfully.")
    else:
        print("Warning: schema.sql not found!")

    # 2. Load Merchants
    merchants_csv = os.path.join(DATA_DIR, "merchants.csv")
    if os.path.exists(merchants_csv):
        df_mch = pd.read_csv(merchants_csv)
        cursor.execute("DELETE FROM merchants;")
        df_mch.to_sql("merchants", conn, if_exists="append", index=False)
        print(f"Loaded {len(df_mch)} records into 'merchants' table.")
    else:
        print("Error: merchants.csv missing!")

    # 3. Load Users
    users_csv = os.path.join(DATA_DIR, "users.csv")
    if os.path.exists(users_csv):
        df_usr = pd.read_csv(users_csv)
        cursor.execute("DELETE FROM users;")
        df_usr.to_sql("users", conn, if_exists="append", index=False)
        print(f"Loaded {len(df_usr)} records into 'users' table.")
    else:
        print("Error: users.csv missing!")

    # 4. Load Transactions in chunks
    txns_csv = os.path.join(DATA_DIR, "transactions.csv")
    if os.path.exists(txns_csv):
        cursor.execute("DELETE FROM transactions;")
        chunksize = 10000
        total_loaded = 0
        for chunk in pd.read_csv(txns_csv, chunksize=chunksize):
            chunk.to_sql("transactions", conn, if_exists="append", index=False)
            total_loaded += len(chunk)
        print(f"Loaded {total_loaded} records into 'transactions' table.")
    else:
        print("Error: transactions.csv missing!")

    # 5. Execute Analysis View creation scripts
    views_path = os.path.join(SQL_DIR, "analysis_queries.sql")
    if os.path.exists(views_path):
        with open(views_path, "r", encoding="utf-8") as f:
            views_sql = f.read()
            cursor.executescript(views_sql)
        print("Analytical SQL views and queries executed successfully.")

    conn.commit()
    conn.close()
    print("Database seeding completed cleanly!")

if __name__ == "__main__":
    seed_database()
