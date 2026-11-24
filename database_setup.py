import os
import pandas as pd
import mysql.connector
from mysql.connector import Error

# MySQL Connection Configuration (Can be overridden via Environment Variables)
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", 3306))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "your_mysql_password") # <-- Replace with your MySQL root password
DB_NAME = os.getenv("MYSQL_DB", "student_portal")
CSV_FILE = "student_reportcard.csv"

def get_server_connection(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD):
    """Connects to the MySQL Server without specifying a database first."""
    return mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password
    )

def get_db_connection(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME):
    """Connects directly to the student_portal MySQL database."""
    return mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )

def init_db(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME):
    """Creates the MySQL database, table with CHECK constraints (MySQL 8.0.16+), and seeds CSV records."""
    # Step 1: Create Database if it doesn't exist
    server_conn = get_server_connection(host, port, user, password)
    cursor = server_conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database};")
    server_conn.commit()
    cursor.close()
    server_conn.close()

    # Step 2: Connect to the database and create table with PRIMARY KEY & CHECK constraints
    conn = get_db_connection(host, port, user, password, database)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        rno INT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        eng INT NOT NULL CHECK (eng >= 0 AND eng <= 100),
        math INT NOT NULL CHECK (math >= 0 AND math <= 100),
        sci INT NOT NULL CHECK (sci >= 0 AND sci <= 100),
        com INT NOT NULL CHECK (com >= 0 AND com <= 100),
        gk INT NOT NULL CHECK (gk >= 0 AND gk <= 100),
        total INT NOT NULL CHECK (total >= 0 AND total <= 500),
        avg DECIMAL(5,2) NOT NULL CHECK (avg >= 0.00 AND avg <= 100.00)
    );
    """)

    # Step 3: Seed data from student_reportcard.csv if table is empty
    cursor.execute("SELECT COUNT(*) FROM students;")
    count = cursor.fetchone()[0]

    if count == 0 and os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        insert_query = """
        INSERT INTO students (rno, name, eng, math, sci, com, gk, total, avg)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        records = [
            (
                int(row['rno']), str(row['name']),
                int(row['eng']), int(row['math']), int(row['sci']),
                int(row['com']), int(row['gk']),
                int(row['total']), float(row['avg'])
            )
            for _, row in df.iterrows()
        ]
        cursor.executemany(insert_query, records)
        conn.commit()
        print(f"Successfully seeded {len(records)} student records into MySQL database '{database}'.")
    else:
        print(f"MySQL database '{database}' is ready ({count} existing records found).")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        init_db()
    except Error as e:
        print(f"MySQL Error: {e}")
        print("Tip: Update DB_PASSWORD in database_setup.py or configure credentials in the Streamlit sidebar.")
