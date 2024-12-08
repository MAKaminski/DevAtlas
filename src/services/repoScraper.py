import os
import sqlite3
from github import Github
from gptController import GPTContentAnalyzer
from github.GithubException import UnknownObjectException
from dotenv import load_dotenv
import re

load_dotenv()
DB = os.getenv("DATABASE")

class GitHubRepoScraper:
    IGNORE_REPOS = ["src/data/", "env/", ".env", ".venv"]  # List of files or directories to ignore

    def __init__(self, db_file, github_token):
        self.db_file = db_file
        self.github = Github(github_token)
        self.connection = None
        self.cursor = None
        self.repo_list = []  # List of repositories to scrape

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

    def recommend_domains_from_db(self):
        """Recommend domains based on scraped data in the database."""
        self.connect_db()
        try:
            # Fetch all content descriptions and associated domains
            self.cursor.execute(
                """
                SELECT c.description, d.name
                FROM content c
                JOIN domains d ON c.domain_id = d.id
                """
            )
            data = self.cursor.fetchall()

            domain_recommendations = {}

            # Analyze content and aggregate domain recommendations
            for description, domain_name in data:
                if domain_name not in domain_recommendations:
                    domain_recommendations[domain_name] = 0
                domain_recommendations[domain_name] += 1

            # Display recommendations
            if domain_recommendations:
                print("Recommended Domains based on scraped data:")
                for domain, count in sorted(domain_recommendations.items(), key=lambda x: x[1], reverse=True):
                    print(f"{domain}: {count} mentions")
            else:
                print("No domains could be recommended from the scraped data.")
        finally:
            self.close_db()

    def parse_gitignore(self, repo):
        """Parse the .gitignore file in the repository, if it exists."""
        try:
            gitignore_file = repo.get_contents(".gitignore")
            gitignore_path = gitignore_file.decoded_content.decode("utf-8", errors="ignore").splitlines()
            print(f".gitignore found and parsed for {repo.full_name}")
            return gitignore_path
        except self.github.UnknownObjectException:
            print(f"No .gitignore found in {repo.full_name}. Proceeding without ignoring files.")
            return []
        except Exception as e:
            print(f"Unexpected error while accessing .gitignore in {repo.full_name}: {e}")
            return []


    def should_ignore(self, path, gitignore_patterns):
        """Check if a file or directory should be ignored based on .gitignore and IGNORE_REPOS."""
        for pattern in gitignore_patterns:
            if re.match(re.escape(pattern).replace("\\*", ".*"), path):
                return True
        for ignore in self.IGNORE_REPOS:
            if ignore in path:
                return True
        return False

    def scrape_repo(self, repo_full_name):
        """Scrape a GitHub repository and insert data into the database."""
        repo = self.github.get_repo(repo_full_name)
        repo_id = self.insert_repo(repo.name, "GitHub", repo.html_url)

        # Parse the .gitignore file
        gitignore_patterns = self.parse_gitignore(repo)

        # Recursively scrape the repository contents
        self.scrape_directory(repo_id, repo.get_contents(""), gitignore_patterns)

        # Print results after scraping the repository
        self.print_repo_results(repo_full_name)

    def scrape_directory(self, repo_id, contents, gitignore_patterns):
        """Recursively scrape a directory in the repository."""
        domains = self.fetch_domains()
        for content_file in contents:
            if self.should_ignore(content_file.path, gitignore_patterns):
                print(f"Ignoring {content_file.path}")
                continue

            if content_file.type == "dir":
                try:
                    dir_contents = self.github.get_repo(content_file.repository.full_name).get_contents(content_file.path)
                    self.scrape_directory(repo_id, dir_contents, gitignore_patterns)
                except Exception as e:
                    print(f"Error accessing directory {content_file.path}: {e}")
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

                description = file_content[:10000]  # Truncate content to 10,000 characters

                summary, domainRelatedness = GPTContentAnalyzer(DB).analyze_content_with_gpt(description, domains)
                
                # Ensure Summary is also inserted, as is domainRelatedness as records to the content
                # Then RUN!
                
                
                self.insert_content(file_id, description, domain_id)

    def print_repo_results(self, repo_full_name):
        """Print the results of the repository scrape."""
        print(f"\nResults for repository: {repo_full_name}")

        # Count files scraped
        self.cursor.execute(
            "SELECT COUNT(*) FROM fileObjects WHERE repo_id IN (SELECT id FROM repos WHERE name = ?)",
            (repo_full_name.split('/')[-1],)
        )
        file_count = self.cursor.fetchone()[0]

        # Count content entries
        self.cursor.execute(
            "SELECT COUNT(*) FROM content WHERE fileObject_id IN (SELECT id FROM fileObjects WHERE repo_id IN (SELECT id FROM repos WHERE name = ?))",
            (repo_full_name.split('/')[-1],)
        )
        content_count = self.cursor.fetchone()[0]

        print(f"Files Scraped: {file_count}")
        print(f"Content Entries Added: {content_count}")

    def run(self):
        """Run the scraper for all repositories in the list."""
        self.connect_db()
        try:
            for repo_full_name in self.repo_list:
                try:
                    self.scrape_repo(repo_full_name)
                except Exception as e:
                    print(f"Error scraping repo {repo_full_name}: {e}")
        finally:
            self.close_db()

# Usage example
if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPOS = os.getenv("REPO")  # Comma-separated list of repositories, e.g., "torvalds/linux,python/cpython"

    if not GITHUB_TOKEN or not REPOS:
        raise ValueError("Environment variables GITHUB_TOKEN and REPOS must be set.")

    db_file = "DevAtlas.db"

    scraper = GitHubRepoScraper(db_file, GITHUB_TOKEN)

    # Add repositories to scrape
    scraper.repo_list = [repo.strip() for repo in REPOS.split(",")]

    # Run scraper for the GitHub repositories
    scraper.run()

    # Recommend domains based on the database
    scraper.recommend_domains_from_db()
