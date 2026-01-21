import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

POSTGRES_URL = os.environ.get(
    'POSTGRES_URL', 
    'postgresql://postgres:pw1@postgres-ml:5432/reviews_db'
)

def create_tables():
    """Create all required database tables"""

    print("🔌 Connecting to database...")
    conn = psycopg2.connect(POSTGRES_URL)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    print("Creating 'issues' table...")
    create_issues_table = """
    CREATE TABLE IF NOT EXISTS issues (
        id SERIAL PRIMARY KEY,
        task_id TEXT UNIQUE,
        summary TEXT NOT NULL,
        description TEXT NOT NULL,
        label VARCHAR(20),
        prediction VARCHAR(20),
        confidence FLOAT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(create_issues_table)
    print("'issues' table ready")

    print("Creating search index on 'issues' table...")
    create_issues_index = """
    CREATE INDEX IF NOT EXISTS idx_issues_search 
    ON issues USING gin(to_tsvector('english', summary || ' ' || description));
    """
    cursor.execute(create_issues_index)
    print("Search index created")

    print("Creating 'labeled_issues' table...")
    create_labeled_table = """
    CREATE TABLE IF NOT EXISTS labeled_issues (
        id SERIAL PRIMARY KEY,
        summary TEXT NOT NULL,
        description TEXT NOT NULL,
        label VARCHAR(20) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        source VARCHAR(50) DEFAULT 'user_submission',
        notes TEXT
    );
    """
    cursor.execute(create_labeled_table)
    print("'labeled_issues' table ready")


    print("Creating index on 'labeled_issues' table...")
    create_labeled_index = """
    CREATE INDEX IF NOT EXISTS idx_labeled_issues_label 
    ON labeled_issues(label);
    """
    cursor.execute(create_labeled_index)
    print("Index on labeled_issues created")

    print("Inserting sample data...")
    insert_sample_data = """
    INSERT INTO issues (summary, description, label)
    VALUES 
        ('Refactor authentication module', 'We need to refactor the authentication system to use OAuth2 instead of basic auth', 'ADD'),
        ('Fix login button color', 'The login button should be blue instead of green', 'non-ADD'),
        ('Migrate to microservices architecture', 'Proposal to break down the monolith into microservices for better scalability', 'ADD')
    ON CONFLICT DO NOTHING;
    """
    try:
        cursor.execute(insert_sample_data)
        print("Sample data inserted")
    except Exception as e:
        print(f"Could not insert sample data (may already exist): {e}")

    cursor.close()
    conn.close()

    print("\nDatabase initialization complete!")
    print("=" * 50)

def verify_tables():
    """Verify that all tables were created successfully"""

    print("\nVerifying tables...")
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name IN ('issues', 'labeled_issues')
    """)

    tables = cursor.fetchall()
    table_names = [t[0] for t in tables]

    print(f"Found tables: {table_names}")

    for table in table_names:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  - {table}: {count} rows")

    cursor.close()
    conn.close()

    if len(table_names) == 2:
        print("All tables verified successfully!")
    else:
        print("Warning: Not all tables were created")

if __name__ == "__main__":
    try:
        create_tables()
        verify_tables()
    except Exception as e:
        print(f"Error during database initialization: {e}")
        exit(1)
