from openai import OpenAI
import sqlite3
import os
import random
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB = os.getenv("DATABASE")
client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

class GPTContentAnalyzer:
    def __init__(self, db_file):
        self.db_file = db_file
        self.connection = None
        self.cursor = None

    def connect_db(self):
        """Connect to the SQLite database."""
        try:
            self.connection = sqlite3.connect(self.db_file)
            self.cursor = self.connection.cursor()
            print("Connected to the database successfully.")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")

    def close_db(self):
        """Close the SQLite database connection."""
        if self.connection:
            self.connection.commit()
            self.connection.close()

    def fetch_random_content(self):
        """Fetch a random content record from the database."""
        try:
            self.cursor.execute("SELECT id, description FROM content")
            rows = self.cursor.fetchall()
            if not rows:
                print("No content records found in the database.")
                return None, None
            random_record = random.choice(rows)
            return random_record
        except sqlite3.Error as e:
            print(f"Error fetching content: {e}")
            return None, None

    def fetch_domains(self):
        """Fetch all domain names from the database."""
        try:
            self.cursor.execute("SELECT id, name FROM domains")
            rows = self.cursor.fetchall()
            return rows if rows else []
        except sqlite3.Error as e:
            print(f"Error fetching domains: {e}")
            return []

    def insert_new_domain(self, domain_name):
        """Insert a new domain into the domains table."""
        try:
            self.cursor.execute("INSERT INTO domains (name) VALUES (?)", (domain_name,))
            self.connection.commit()
            print(f"Inserted new domain: {domain_name}")
        except sqlite3.Error as e:
            print(f"Error inserting new domain: {e}")

    def create_prompt(self, content, domains):
        """Create a prompt for GPT analysis."""
        domain_list = "\n".join(f"- {domain[1]}" for domain in domains)
        prompt = f"""
        Analyze the following content and provide the following details:

        1. Summarize the content.
        2. Categorize it into the following existing domains if applicable:
        {domain_list}
        3. If it does not fit into any existing domains, suggest a new domain.
        4. Provide a relatedness percentage for each domain.

        Content:
        {content}
        """
        return prompt

    def analyze_content_with_gpt(self, content, domains):
        """Use OpenAI GPT to analyze the content."""
        prompt = self.create_prompt(content, domains)
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert content analyzer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error with OpenAI API: {e}")
            return None

    def process_analysis_result(self, analysis_result, domains):
        """Process the analysis result to determine relatedness and insert new domains."""
        print("Analysis Result:")
        print(analysis_result)

        relatedness = {}
        for domain_id, domain_name in domains:
            match = re.search(fr"{domain_name}: ([0-9]+)%", analysis_result)
            if match:
                relatedness[domain_name] = int(match.group(1))

        print("Relatedness percentages:")
        for domain, percentage in relatedness.items():
            print(f"{domain}: {percentage}%")

        # Check for new domain recommendations
        new_domain_match = re.search(r"suggest a new domain: (.+?)", analysis_result, re.IGNORECASE)
        if new_domain_match:
            new_domain = new_domain_match.group(1).strip()
            self.insert_new_domain(new_domain)

if __name__ == "__main__":

    # Initialize the analyzer
    analyzer = GPTContentAnalyzer(DB)

    # Connect to the database
    analyzer.connect_db()

    try:
        # Fetch a random content record
        record_id, content_description = analyzer.fetch_random_content()

        if record_id and content_description:
            print(f"Random Content ID: {record_id}")
            print(f"Content Description:\n{content_description}\n")

            # Fetch existing domains
            existing_domains = analyzer.fetch_domains()

            if existing_domains:
                print("Existing Domains:")
                for domain_id, domain_name in existing_domains:
                    print(f"{domain_id}: {domain_name}")

            # Analyze the content using GPT
            analysis_result = analyzer.analyze_content_with_gpt(content_description, existing_domains)

            if analysis_result:
                # Process the analysis result
                analyzer.process_analysis_result(analysis_result, existing_domains)
        else:
            print("No content available to analyze.")

    finally:
        # Close the database connection
        analyzer.close_db()
