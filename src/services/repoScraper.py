## IMPORTS ##############################################################################################################
import re
import os
import sqlite3
## IMPORT CLASSES ########################################################################################################
from github import Github
from github.GithubException import UnknownObjectException
## DEV_ATLAS CLASSES #####################################################################################################
from services.contentAnalyzer import GPTContentAnalyzer
## FUNCTIONS ############################################################################################################
from dotenv import load_dotenv
## CONFIGURATION ########################################################################################################
load_dotenv()
DB = os.getenv("DATABASE")
## TESTING ##############################################################################################################
RUN_STYLE = 'SINGLE' # 'MULTI'
MAX_TOKENS = 500
## CLASSES ############################################################################################################
class RepoScraper:
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
        analyzer = GPTContentAnalyzer(DB, self.connection)

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

                # Fetch file content and analyze it
                try:
                    file_content = content_file.decoded_content.decode("utf-8", errors="ignore")
                except Exception as e:
                    print(f"Failed to decode content for {content_file.name}: {e}")
                    file_content = ""

                # Split content into chunks for pagination
                chunks = self.split_into_chunks(file_content, MAX_TOKENS)

                for chunk in chunks:
                    analysis_result = analyzer.analyze_content_with_gpt(chunk, domains)
                    if analysis_result:
                        # Process analysis result and insert summary and relationships
                        self.process_analysis_result(file_id, chunk, analysis_result, domains)

    def split_into_chunks(self, text, chunk_size):
        """Split text into chunks of a specified size."""
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    def process_analysis_result(self, file_object_id, description, analysis_result, domains):
        """Insert content and analysis results into the database."""
        analyzer = GPTContentAnalyzer(DB, self.connection)

        # Step 1: Insert the content record
        try:
            self.cursor.execute(
                "INSERT INTO content (fileObject_id, description) VALUES (?, ?)",
                (file_object_id, description)
            )
            self.connection.commit()
            content_id = self.cursor.lastrowid
            print(f"Inserted content: ID {content_id}, FileObject {file_object_id}")
        except sqlite3.Error as e:
            print(f"Error inserting content: {e}")
            return []

        # Step 2: Extract summary from analysis result
        relatedness = {}
        summary_match = re.search(r"Summarize the content:\n(.+?)\n\n", analysis_result, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else ""

        # Step 3: Determine relatedness percentages
        for domain_id, domain_name in domains:
            match = re.search(fr"{domain_name}: ([0-9]+)%", analysis_result)
            if match:
                relatedness[domain_id] = int(match.group(1))

        # Step 4: Sort and filter top related domains
        top_related_domains = sorted(
            [(domain_id, percentage) for domain_id, percentage in relatedness.items() if percentage > 30],
            key=lambda x: x[1],
            reverse=True
        )[:3]

        # Step 5: Update summary for the content record
        try:
            self.cursor.execute(
                "UPDATE content SET summary = ? WHERE id = ?",
                (summary, content_id)
            )
            self.connection.commit()
            print(f"Inserted summary for Content {content_id}.")
        except sqlite3.Error as e:
            print(f"Error inserting summary: {e}")

        # Step 6: Insert domain relationships
        for domain_id, percentage in top_related_domains:
            try:
                self.cursor.execute(
                    "INSERT INTO content_domain_relationships (content_id, domain_id, relatedness_percentage) VALUES (?, ?, ?)",
                    (content_id, domain_id, percentage)
                )
                self.connection.commit()
                print(f"Inserted relationship: Content {content_id} -> Domain {domain_id} ({percentage}%)")
            except sqlite3.Error as e:
                print(f"Error inserting relationship: {e}")

        # Step 7: Handle new domain recommendations
        new_domains = []
        new_domain_match = re.findall(r"suggest a new domain: (.+?)", analysis_result, re.IGNORECASE)
        for new_domain in new_domain_match:
            new_domain = new_domain.strip()
            analyzer.insert_new_domain(new_domain)
            self.cursor.execute("SELECT id FROM domains WHERE name = ?", (new_domain,))
            new_domain_id = self.cursor.fetchone()
            if new_domain_id:
                new_domains.append(new_domain_id[0])

        # Step 8: Return the combined domain IDs
        return [domain_id for domain_id, _ in top_related_domains] + new_domains


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
## MAIN ##############################################################################################################
if __name__ == "__main__":

    load_dotenv()
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO= os.getenv("MAIN_REPO")
    DB = os.getenv("DATABASE")
    
    if not GITHUB_TOKEN or not REPO:
        raise ValueError("Environment variables GITHUB_TOKEN and REPOS must be set.")
    
    scraper = RepoScraper(DB, GITHUB_TOKEN)
    
    scraper.repo_list = [repo.strip() for repo in REPO.split(",")]
    
    scraper.run()