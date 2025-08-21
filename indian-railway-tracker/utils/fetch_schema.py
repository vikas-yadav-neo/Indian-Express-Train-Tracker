import psycopg2

# DB connection info
DB_HOST = "yamanote.proxy.rlwy.net"
DB_PORT = 29855
DB_NAME = "railway"
DB_USER = "postgres"
DB_PASSWORD = "iaCkmHPhuyhFLEBDGdwxQGGqlHvdgWJA"

output_file = "db_schema.txt"

def fetch_db_schema():
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        # Get all table names in public schema
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()

        with open(output_file, "w") as f:
            for (table_name,) in tables:
                f.write(f"Table: {table_name}\n")
                f.write("-" * (7 + len(table_name)) + "\n")

                # Fetch table columns and types
                cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))
                columns = cursor.fetchall()

                for col_name, col_type in columns:
                    f.write(f"{col_name} ({col_type})\n")
                f.write("\n")

        cursor.close()
        conn.close()
        print(f"Schema written to {output_file}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_db_schema()
