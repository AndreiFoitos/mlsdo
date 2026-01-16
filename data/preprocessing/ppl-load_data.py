import os
import pandas as pd
import psycopg2
from psycopg2 import extras

def load_csv_to_postgres(csv_file_path, postgres_url):
    if not os.path.exists(csv_file_path):
        print(f"Error: {csv_file_path} not found. Run 'dvc repro' first.")
        return
    
    df = pd.read_csv(csv_file_path)
    
    print(f"Connecting to database...")
    conn = psycopg2.connect(postgres_url)
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
    postgres_url = os.getenv('POSTGRES_URL', 'postgresql://postgres:pw1@localhost:5432/reviews_db')
    csv_path = os.getenv('CSV_PATH', 'issue_with_labels.csv')
    
    print(f"Using CSV path: {csv_path}")
    load_csv_to_postgres(csv_path, postgres_url)