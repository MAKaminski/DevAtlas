import os
import sqlite3
from github import Github
from dotenv import load_dotenv
import re

class GitHubRepoScraper:
    def __init__(self, db_file, github_token):
        self.db_file = db_file
        self.github = Github(github_token)
        self.connection = None
        self.cursor = None

    def connect_db(self):
        """Connect to the SQLite database."""
        self.connection = sqlite3.connect(self.db_file)
        self.cursor = self.connection.cursor()

    def close_db(self):
        """Close the SQLite database connection."""
        if self.connection:
            self.connection.commit()
            self.connection.close()

    def insert_repo(self, name, platform, url):
        """Insert a repository into the repos table."""
        self.cursor.execute(
            "INSERT INTO repos (name, platform, url) VALUES (?, ?, ?)",
            (name, platform, url),
        )
        return self.cursor.lastrowid

    def insert_file_object(self, repo_id, file_type, name, url):
        """Insert a file object into the fileObjects table."""
        self.cursor.execute(
            "INSERT INTO fileObjects (repo_id, type, name, url) VALUES (?, ?, ?, ?)",
            (repo_id, file_type, name, url),
        )
        return self.cursor.lastrowid

    def insert_content(self, file_object_id, description, domain_id):
        """Insert content into the content table."""
        self.cursor.execute(
            "INSERT INTO content (fileObject_id, description, domain_id) VALUES (?, ?, ?)",
            (file_object_id, description, domain_id),
        )

    def fetch_domains(self):
        """Fetch all domains from the domains table."""
        self.cursor.execute("SELECT id, name FROM domains")
        return self.cursor.fetchall()

    def map_to_domain(self, content, domains):
        """Fuzzy match content to a domain."""
        for domain_id, domain_name in domains:
            if re.search(rf"\b{re.escape(domain_name)}\b", content, re.IGNORECASE):
                return domain_id
        return None

    def recommend_domains(self, content):
        """Identify and print recommended domains for a given content."""
        self.connect_db()
        try:
            domains = self.fetch_domains()
            matches = []
            for domain_id, domain_name in domains:
                if re.search(rf"\b{re.escape(domain_name)}\b", content, re.IGNORECASE):
                    matches.append(domain_name)
            if matches:
                print("Recommended Domains:", ", ".join(matches))
            else:
                print("No matching domains found.")
        finally:
            self.close_db()

    def scrape_repo(self, repo_full_name):
        """Scrape a GitHub repository and insert data into the database."""
        repo = self.github.get_repo(repo_full_name)
        repo_id = self.insert_repo(repo.name, "GitHub", repo.html_url)

        # Recursively scrape the repository contents
        self.scrape_directory(repo_id, repo.get_contents(""))

    def scrape_directory(self, repo_id, contents):
        """Recursively scrape a directory in the repository."""
        domains = self.fetch_domains()
        for content_file in contents:
            if content_file.type == "dir":
                dir_contents = self.github.get_repo(content_file.repository.full_name).get_contents(content_file.path)
                self.scrape_directory(repo_id, dir_contents)
            elif content_file.type == "file":
                file_id = self.insert_file_object(
                    repo_id, "file", content_file.name, content_file.html_url
                )

                # Fetch file content and insert into database
                try:
                    file_content = content_file.decoded_content.decode("utf-8", errors="ignore")
                except Exception as e:
                    print(f"Failed to decode content for {content_file.name}: {e}")
                    file_content = ""

                description = file_content[:500]  # Truncate content to 500 characters

                # Assign a domain ID using fuzzy logic
                domain_id = self.map_to_domain(description, domains)
                if domain_id is None:
                    domain_id = 1  # Default domain ID if no match

                self.insert_content(file_id, description, domain_id)

    def run(self, repo_full_name):
        """Run the scraper for a given repository."""
        self.connect_db()
        try:
            self.scrape_repo(repo_full_name)
        except Exception as e:
            print(f"Error scraping repo: {e}")
        finally:
            self.close_db()

# Usage example
if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO_FULL_NAME = os.getenv("REPO")  # E.g., "torvalds/linux"

    if not GITHUB_TOKEN or not REPO_FULL_NAME:
        raise ValueError("Environment variables GITHUB_TOKEN and REPO must be set.")

    db_file = "example.db"

    scraper = GitHubRepoScraper(db_file, GITHUB_TOKEN)

    # Run scraper for the GitHub repository
    scraper.run(REPO_FULL_NAME)

    # Example of recommending domains for a piece of content
    sample_content = "This is an example content mentioning backend and database."
    scraper.recommend_domains(sample_content)
