import datetime
import os
import json

import psycopg2

def load_data_to_postgres(file_path, db_config):
   conn = psycopg2.connect(**db_config)
   cursor = conn.cursor()

   cursor.execute("""
   SELECT EXISTS (
      SELECT FROM information_schema.tables 
      WHERE table_name = 'book_reviews'
   );
   """)
   exists = cursor.fetchone()[0]

   if exists:
      print("Table already exists. Assuming the reviews have already been inserted. Skipping loading.")

   if not exists:
      print("Creating table book_reviews.")
      cursor.execute("""
      CREATE TABLE book_reviews (
         item_id VARCHAR(255),
         title TEXT,
         subtitle TEXT,
         author TEXT,
         timestamp DATE,
         source TEXT,
         review_title TEXT,
         review_text TEXT,
         review_length INTEGER,
         rating FLOAT
      )
      """)
      conn.commit()
   
   # In JSONL, each line is a valid JSON object
   with open(file_path, 'r') as f:
      print("Inserting reviews.")
      for line in f:
            record = json.loads(line)
            record = {
               k: v.replace('\x00', '') if isinstance(v, str) else v
               for k, v in record.items()
            }
            date = datetime.datetime.fromtimestamp(record['timestamp'] / 1000)
            cursor.execute("""
            INSERT INTO book_reviews (
               item_id, title, subtitle, author, timestamp,
               source, review_title, review_text, review_length, rating
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
               record['item_id'], record['title'], record.get('subtitle'),
               record['author'], date, record['source'],
               record['review_title'], record['review_text'],
               record['review_length'], record['rating']
            ))

   conn.commit()
   cursor.close()
   conn.close()

if __name__ == "__main__":
   required_env_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DATASET_FILEPATH']
   for var in required_env_vars:
      if not os.getenv(var):
         raise EnvironmentError(f"{var} environment variable is not set.")   
   
   DB_CONFIG = {
      'dbname': os.getenv('DB_NAME'),
      'user': os.getenv('DB_USER'),
      'password': os.getenv('DB_PASSWORD'),
      'host': os.getenv('DB_HOST'),
      'port': int(os.getenv('DB_PORT'))
   }
   dataset_file_path = os.getenv('DATASET_FILEPATH')
   load_data_to_postgres(dataset_file_path, DB_CONFIG)
   print("Data loaded.")
