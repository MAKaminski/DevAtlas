
## SUMMARY ###########################################################################################################
# Describe Class Methods
# - REQUIRES: schema, table
# - connection.
# - connect: Connect to SQLite database and return connection and cursor
# - close: Close the database connection
# - initialize_datebase():
    # - create_tables: Create tables with the specified schema
    # - drop_db: Drop the database and all its tables
# - load_test_data: Load test data into the database
# - operations: Perform operations on the database
    # - Create: Create a new record in the database
    # - Update: Update an existing record in the database
    # - Delete: Delete a record from the database
## LIBRARIES ###########################################################################################################
import os
import random
import sqlite3
## CLASS IMPORTS #####################################################################################################
from sqlite3 import Error
## FUNCTIONS #########################################################################################################
from dotenv import load_dotenv
## CONFIGURATION #######################################################################################################
load_dotenv()
DB = os.getenv("DATABASE")
## TESTING ###########################################################################################################
RUN_STYLE = 'INIT' # 'PROD'
## CLASSES ###########################################################################################################
class Database:
    def __init__(self, db_file=DB):
        """Initialize the Database connection"""
        self.db_file = db_file
        self.connection = None
        self.cursor = None

    def connect(self):
        """Connect to the SQLite database"""
        try:
            self.connection = sqlite3.connect(self.db_file)
            self.cursor = self.connection.cursor()
            print("Successfully connected to SQLite")
            return self.connection, self.cursor
        except Error as e:
            print(f"Error connecting to database: {e}")
            return None, None

    def disconnect(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            print("Connection closed.")

    class API:
        def __init__(self, db_instance):
            self.db_instance = db_instance

        def create(self, table, data):
            """
            Create a new record in the database.

            Parameters:
            table (str): The name of the table where the record will be inserted.
            data (dict): A dictionary containing the column names and values to be inserted into the table.

            Example:
            To insert a new record into the 'repos' table with columns (name, platform, url), you can call:
            api.create('repos', {'name': 'Repo Name', 'platform': 'GitHub', 'url': 'https://github.com/repo'})

            This will execute the following SQL query:
            INSERT INTO repos (name, platform, url) VALUES ('Repo Name', 'GitHub', 'https://github.com/repo')
            """
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?"] * len(data))
            query = f"""
                INSERT INTO {table} ({columns})
                VALUES ({placeholders})
            """
            try:
                self.db_instance.cursor.execute(query, tuple(data.values()))
                self.db_instance.connection.commit()
                print(data)
            except Error as e:
                print(f"Error adding record: {e}")

        def update(self, table, data, condition):
            """
            Update an existing record in the database.

            Parameters:
            table (str): The name of the table where the record will be updated.
            data (dict): A dictionary containing the columns and values to be updated in the table.
            condition (str): The condition to identify the record to be updated.

            Example:
            To update a record in the 'repos' table with columns (name, platform, url), you can call:
            api.update('repos', {'name': 'New Repo Name', 'platform': 'GitHub', 'url': 'https://github.com/newrepo'}, "id = 1")

            This will execute the following SQL query:
            UPDATE repos SET name = 'New Repo Name', platform = 'GitHub', url = 'https://github.com/newrepo' WHERE id = 1
            """
            set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
            query = f"""
                UPDATE {table}
                SET {set_clause}
                WHERE {condition}
            """
            try:
                self.db_instance.cursor.execute(query, tuple(data.values()))
                self.db_instance.connection.commit()
                print(data)
            except Error as e:
                print(f"Error updating record: {e}")

    def initialize_database(self):
        """Initialize the database with the specified schema and load test data"""
        self.drop_db()
        self.create_tables()

    def create_tables(self):
        """Create tables with the specified schema"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS repos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                platform TEXT NOT NULL,
                url TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS fileObjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                FOREIGN KEY (repo_id) REFERENCES repos (id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fileObject_id INTEGER NOT NULL,
                description TEXT,
                summary TEXT,
                domain_id INTEGER,
                FOREIGN KEY (fileObject_id) REFERENCES fileObjects (id),
                FOREIGN KEY (domain_id) REFERENCES domains (id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS content_domain_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER NOT NULL,
                domain_id INTEGER NOT NULL,
                relatedness_percentage INTEGER NOT NULL,
                FOREIGN KEY (content_id) REFERENCES content (id),
                FOREIGN KEY (domain_id) REFERENCES domains (id)
            );
            """
        ]

        try:
            for query in queries:
                self.cursor.execute(query)
            self.connection.commit()
            print("Tables created successfully.")
        except Error as e:
            print(f"Error creating tables: {e}")

    def drop_db(self):
        """Drop the database and all its tables"""
        try:
            # Drop tables in reverse order of dependency
            self.cursor.execute("DROP TABLE IF EXISTS content_domain_relationships")
            self.cursor.execute("DROP TABLE IF EXISTS content")
            self.cursor.execute("DROP TABLE IF EXISTS domains")
            self.cursor.execute("DROP TABLE IF EXISTS fileObjects")
            self.cursor.execute("DROP TABLE IF EXISTS repos")
            self.connection.commit()
            print("Database and all tables dropped successfully.")
        except Error as e:
            print(f"Error dropping tables: {e}")

## FUNCTIONS #########################################################################################################
def main():
    from datetime import datetime

    print("Starting the main program.")
    st = datetime.now()

    # Initialize the database
    database = Database()
    connection, cursor = database.connect()

    if RUN_STYLE == 'INIT':
        database.initialize_database()

    table_name = "repos"
    create_data = {"name": "Repo Name", "platform": "GitHub", "url": "https://github.com/repo"}
    update_data = {"name": "Updated Repo Name", "platform": "GitHub", "url": "https://github.com/updatedrepo"}
    condition = "id = 1"

    api = Database.API(database)
    api.create(table_name, create_data)
    api.update(table_name, update_data, condition)

    et = datetime.now()
    duration = (et - st).total_seconds()
    print(f"Program completed in {duration} seconds.")

    # Close the database connection
    database.disconnect()
## UNIT TEST #########################################################################################################
if __name__ == '__test__':
    # Connect()
    # Disconnect()
    # Initialize_database
    # drop table
    # create table
    # update record
    # delete record
    
    # Test connect
    def test_connect():
        db = Database()
        connection, cursor = db.connect()
        assert connection is not None
        assert cursor is not None
        db.disconnect()
    
    test_connect()

## MAIN ##############################################################################################################
if __name__ == "__main__":
    main()