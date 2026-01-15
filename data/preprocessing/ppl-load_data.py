import os
import pandas as pd
import psycopg2
from psycopg2 import extras

POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'reviews_db')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'pw1')

conn = psycopg2.connect(
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD
)

def load_csv_to_postgres(csv_file_path, db_config):
    if not os.path.exists(csv_file_path):
        print(f"Error: {csv_file_path} not found. Run 'dvc repro' first.")
        return
    
    df = pd.read_csv(csv_file_path)
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    print("Creating table 'processed_issues'...")
    cursor.execute("DROP TABLE IF EXISTS processed_issues")
    cursor.execute("""
    CREATE TABLE processed_issues (
        issue_key VARCHAR(50) PRIMARY KEY,
        summary TEXT,
        description TEXT,
        label_existence BOOLEAN,
        label_executive BOOLEAN,
        label_property BOOLEAN,
        project VARCHAR(50)
    )
    """)
    conn.commit()

    print(f"Inserting {len(df)} records...")
    data_tuples = [
        (row.label_id, row.summary, row.description, 
         row.existence, row.executive, row.property, row.project)
        for row in df.itertuples(index=False)
    ]
    
    query = """
    INSERT INTO processed_issues 
    (issue_key, summary, description, label_existence, label_executive, label_property, project) 
    VALUES %s
    """
    try:
        extras.execute_values(cursor, query, data_tuples)
        conn.commit()
        print("Data loaded successfully.")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    DB_CONFIG = {
        'dbname': os.getenv('POSTGRES_DB', 'reviews_db'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'pw1'),
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432'))
    }
    
    csv_path = os.getenv('CSV_PATH', 'issue_with_labels.csv')
    load_csv_to_postgres(csv_path, DB_CONFIG)