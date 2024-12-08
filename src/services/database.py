## IMPORTS ###########################################################################################################
from dotenv import load_dotenv
import os
import random
import sqlite3
from sqlite3 import Error
load_dotenv()
DB = os.getenv("DATABASE")
## CLASSES ###########################################################################################################
class DatabaseInitializer:
    def __init__(self, db_file):
        """Initialize the Database connection"""
        self.db_file = db_file
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Connect to SQLite database and return connection and cursor"""
        try:
            self.connection = sqlite3.connect(self.db_file)
            self.cursor = self.connection.cursor()
            print("Successfully connected to SQLite")
        except Error as e:
            print(f"Error connecting to database: {e}")
            return None, None
        
        return self.connection, self.cursor

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
                domain_id INTEGER NOT NULL,
                FOREIGN KEY (fileObject_id) REFERENCES fileObjects (id),
                FOREIGN KEY (domain_id) REFERENCES domains (id)
            );
            """
            ,"""
            CREATE TABLE content_domain_relationships (
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

    def load_test_data(self):
        """Load test data into the tables"""
        # Repositories
        # repos_data = [
        #     ("Repo1", "GitHub", "https://github.com/repo1"),
        #     ("Repo2", "GitHub", "https://github.com/repo2"),
        #     ("Repo3", "GitHub", "https://github.com/repo3"),
        #     ("Repo4", "GitLab", "https://gitlab.com/repo4"),
        #     ("Repo5", "Bitbucket", "https://bitbucket.org/repo5")
        # ]
        
        # # Domains
        domains_data = [
            ("Technology", " content"),
            ("API", " content"),
            ("Product", " content"),
            ("Finance", " content"),
            ("Knowledge", " content"),
            ("Operations", " content")
        ]
        
        # File objects (2-5 per repo)
        file_objects_data = []
        content_data = []
        
        # Add repos and generate file objects
        for repo_id in range(1, 6):
            num_files = random.randint(2, 5)  # 2 to 5 file objects per repo
            for i in range(num_files):
                file_object_name = f"File_{repo_id}_{i+1}.py"
                file_objects_data.append((repo_id, "File", file_object_name, f"https://github.com/repo{repo_id}/{file_object_name}"))
                
                # For each file object, generate 1-2 pieces of content
                num_content = random.randint(1, 2)  # 1 to 2 pieces of content per file object
                for j in range(num_content):
                    content_description = f"Content description {repo_id}_{i+1}_{j+1}"
                    domain_id = random.randint(1, 4)  # Assign random domain
                    content_data.append((repo_id, content_description, domain_id))
        
        try:
            # # Insert data into repos
            # self.cursor.executemany("""
            #     INSERT INTO repos (name, platform, url)
            #     VALUES (?, ?, ?)
            # """, repos_data)
            
            # Insert data into domains
            self.cursor.executemany("""
                INSERT INTO domains (name, description)
                VALUES (?, ?)
            """, domains_data)
            
            # # Insert data into fileObjects
            # self.cursor.executemany("""
            #     INSERT INTO fileObjects (repo_id, type, name, url)
            #     VALUES (?, ?, ?, ?)
            # """, file_objects_data)
            
            # # Insert data into content
            # self.cursor.executemany("""
            #     INSERT INTO content (fileObject_id, description, domain_id)
            #     VALUES (?, ?, ?)
            # """, content_data)
            
            self.connection.commit()
            print("Test data loaded successfully.")
        except Error as e:
            print(f"Error loading test data: {e}")

    def drop_db(self):
        """Drop the database and all its tables"""
        try:
            # Drop tables in reverse order of dependency
            self.cursor.execute("DROP TABLE IF EXISTS content")
            self.cursor.execute("DROP TABLE IF EXISTS domains")
            self.cursor.execute("DROP TABLE IF EXISTS fileObjects")
            self.cursor.execute("DROP TABLE IF EXISTS repos")
            self.connection.commit()
            print("Database and all tables dropped successfully.")
        except Error as e:
            print(f"Error dropping tables: {e}")
    
    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            print("Connection closed.")

# Usage example

if __name__ == "__main__":
    # Initialize the DatabaseInitializer class
    db_initializer = DatabaseInitializer(DB)

    # Connect to the database
    connection, cursor = db_initializer.connect()

    # Drop the database and all tables (optional)
    # db_initializer.drop_db()

    # Create tables in the database
    db_initializer.create_tables()

    # Load test data into the database
    # db_initializer.load_test_data()

    # Close the database connection
    db_initializer.close()
