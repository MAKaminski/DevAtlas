import unittest
import os
import sys

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))

from databaseController import Database

class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up a temporary database for testing"""
        cls.db_file = "test.db"
        cls.database = Database(cls.db_file)
        cls.connection, cls.cursor = cls.database.connect()
        cls.api = Database.API(cls.database)
        cls.database.create_tables()  # Ensure tables are created before tests

    @classmethod
    def tearDownClass(cls):
        """Clean up the temporary database"""
        cls.database.drop_db()
        cls.database.disconnect()
        if os.path.exists(cls.db_file):
            os.remove(cls.db_file)

    def test_connect(self):
        """Test connecting to the database"""
        self.assertIsNotNone(self.connection)
        self.assertIsNotNone(self.cursor)

    def test_create_tables(self):
        """Test creating tables"""
        self.database.create_tables()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='repos';")
        self.assertIsNotNone(self.cursor.fetchone())
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fileObjects';")
        self.assertIsNotNone(self.cursor.fetchone())
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='domains';")
        self.assertIsNotNone(self.cursor.fetchone())
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='content';")
        self.assertIsNotNone(self.cursor.fetchone())
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='content_domain_relationships';")
        self.assertIsNotNone(self.cursor.fetchone())

    def test_create_record(self):
        """Test creating a record in the database"""
        self.api.create("repos", {"name": "repos", "platform": "GitHub", "url": "https://github.com/repo"})
        self.cursor.execute("SELECT * FROM repos WHERE name='repos';")
        record = self.cursor.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record[1], "repos")
        self.assertEqual(record[2], "GitHub")
        self.assertEqual(record[3], "https://github.com/repo")

    def test_update_record(self):
        """Test updating a record in the database"""
        self.api.create("repos", {"name": "repos", "platform": "GitHub", "url": "https://github.com/repo"})
        self.api.update("repos", {"name": "Updated Repo Name", "platform": "GitHub", "url": "https://github.com/updatedrepo"}, "name = 'repos'")
        self.cursor.execute("SELECT * FROM repos WHERE name='Updated Repo Name';")
        record = self.cursor.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record[1], "Updated Repo Name")
        self.assertEqual(record[2], "GitHub")
        self.assertEqual(record[3], "https://github.com/updatedrepo")

    def test_drop_db(self):
        """Test dropping the database"""
        self.database.drop_db()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='repos';")
        self.assertIsNone(self.cursor.fetchone())
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fileObjects';")
        self.assertIsNone(self.cursor.fetchone())
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='domains';")
        self.assertIsNone(self.cursor.fetchone())
        
        # Must drop double FK table prior to dropping content table
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='content_domain_relationships';")
        self.assertIsNone(self.cursor.fetchone())
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='content';")
        self.assertIsNone(self.cursor.fetchone())
        
if __name__ == "__main__":
    unittest.main()