import psycopg2
from psycopg2 import sql

# Your PostgreSQL connection details
DB_CONFIG = {
    "dbname": "railway",
    "user": "postgres",
    "password": "iaCkmHPhuyhFLEBDGdwxQGGqlHvdgWJA",
    "host": "yamanote.proxy.rlwy.net",
    "port": 29855
}

# SQL commands to execute
# ALTER_TABLE_SQL = [
#     # Drop dependent foreign keys
#     "ALTER TABLE trains DROP CONSTRAINT IF EXISTS trains_from_station_code_fkey;",
#     "ALTER TABLE trains DROP CONSTRAINT IF EXISTS trains_to_station_code_fkey;",
#     "ALTER TABLE schedules DROP CONSTRAINT IF EXISTS schedules_station_code_fkey;",
#
#     # Alter column types
#     "ALTER TABLE stations ALTER COLUMN station_code TYPE VARCHAR(20);",
#     "ALTER TABLE trains ALTER COLUMN from_station_code TYPE VARCHAR(20);",
#     "ALTER TABLE trains ALTER COLUMN to_station_code TYPE VARCHAR(20);",
#     "ALTER TABLE schedules ALTER COLUMN station_code TYPE VARCHAR(20);",
#
#     # Recreate foreign keys with ON DELETE CASCADE
#     """ALTER TABLE trains
#        ADD CONSTRAINT trains_from_station_code_fkey
#        FOREIGN KEY (from_station_code) REFERENCES stations(station_code) ON DELETE CASCADE;""",
#     """ALTER TABLE trains
#        ADD CONSTRAINT trains_to_station_code_fkey
#        FOREIGN KEY (to_station_code) REFERENCES stations(station_code) ON DELETE CASCADE;""",
#     """ALTER TABLE schedules
#        ADD CONSTRAINT schedules_station_code_fkey
#        FOREIGN KEY (station_code) REFERENCES stations(station_code) ON DELETE CASCADE;"""
# ]

ALTER_TABLE_SQL = [
    # -- Drop foreign key if exists
"ALTER TABLE schedules DROP CONSTRAINT IF EXISTS schedules_train_number_fkey;",

# -- Alter both tables
"ALTER TABLE trains ALTER COLUMN train_number TYPE VARCHAR(20);",
"ALTER TABLE schedules ALTER COLUMN train_number TYPE VARCHAR(20);",

# -- Recreate foreign key
"ALTER TABLE schedules ADD CONSTRAINT schedules_train_number_fkey FOREIGN KEY (train_number) REFERENCES trains(train_number) ON DELETE CASCADE;",

]

def alter_tables():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False  # Use transaction
        cur = conn.cursor()

        print("Starting table alterations...")
        for command in ALTER_TABLE_SQL:
            print(f"Running: {command.strip()}")
            cur.execute(command)

        conn.commit()
        print("✅ All ALTER TABLE commands executed successfully.")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error occurred, rolled back changes: {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    alter_tables()
