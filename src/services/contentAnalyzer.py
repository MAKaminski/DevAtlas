## LIBRARIES ###########################################################################################################
import sqlite3
from openai import OpenAI
import os
import random
import re
## FUNCTIONS ############################################################################################################
from dotenv import load_dotenv
## CONFIGURATION ########################################################################################################
load_dotenv()
DB = os.getenv("DATABASE")
client = OpenAI(api_key=os.getenv("OPENAI_TOKEN"))
MAX_TOKENS = 500
## CLASSES ############################################################################################################
class ContentAnalyzer:
    def __init__(self, db_file, connection):
        self.db_file = db_file
        if connection is not None:
            self.connection = connection
            self.cursor = self.connection.cursor()
        else:
            self.connection = None
            self.cursor = None
            self.connect_db()
        
    def connect_db(self):
        """Connect to the SQLite database."""
        try:
            self.connection = sqlite3.connect(self.db_file)
            self.cursor = self.connection.cursor()
            print("Connected to the database successfully.")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            self.connection = None
            self.cursor = None

    def close_db(self):
        """Close the SQLite database connection."""
        if self.connection:
            self.connection.commit()
            self.connection.close()
            print("Database connection closed.")

    def fetch_random_content(self):
        """Fetch a random content record from the database."""
        if not self.cursor:
            print("Database cursor is not available.")
            return None, None
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
        if not self.cursor:
            print("Database cursor is not available.")
            return []
        try:
            self.cursor.execute("SELECT id, name FROM domains")
            rows = self.cursor.fetchall()
            return rows if rows else []
        except sqlite3.Error as e:
            print(f"Error fetching domains: {e}")
            return []

    def insert_new_domain(self, domain_name):
        """Insert a new domain into the domains table."""
        if not self.cursor:
            print("Database cursor is not available.")
            return
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
                max_tokens=MAX_TOKENS,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error with OpenAI API: {e}")
            return None

    def process_analysis_result(self, content_id, analysis_result, domains):
        """Process the analysis result to determine relatedness and insert new domains."""
        if not self.cursor:
            print("Database cursor is not available.")
            return []
        print("Analysis Result:")
        print(analysis_result)

        relatedness = {}
        summary_match = re.search(r"Summarize the content:\n(.+?)\n\n", analysis_result, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else ""

        for domain_id, domain_name in domains:
            match = re.search(fr"{domain_name}: ([0-9]+)%", analysis_result)
            if match:
                relatedness[domain_id] = int(match.group(1))

        print("Relatedness percentages:")
        for domain_id, percentage in relatedness.items():
            print(f"Domain {domain_id}: {percentage}%")

        # Sort by relatedness and limit to top 3 domains with > 30% relatedness
        top_related_domains = sorted(
            [(domain_id, percentage) for domain_id, percentage in relatedness.items() if percentage > 30],
            key=lambda x: x[1],
            reverse=True
        )[:3]

        return self.insert_summary_and_relationships(content_id, summary, top_related_domains, analysis_result)

        # Insert summary into the database
        try:
            self.cursor.execute(
                "UPDATE content SET summary = ? WHERE id = ?",
                (summary, content_id)
            )
            self.connection.commit()
            print(f"Inserted summary for Content {content_id}.")
        except sqlite3.Error as e:
            print(f"Error inserting summary: {e}")

        # Insert relationships into the database
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

        # Check for new domain recommendations
        new_domains = []
        new_domain_match = re.findall(r"suggest a new domain: (.+?)", analysis_result, re.IGNORECASE)
        for new_domain in new_domain_match:
            new_domain = new_domain.strip()
            self.insert_new_domain(new_domain)
            self.cursor.execute("SELECT id FROM domains WHERE name = ?", (new_domain,))
            new_domain_id = self.cursor.fetchone()
            if new_domain_id:
                new_domains.append(new_domain_id[0])

        # Return domain IDs for further processing
        return [domain_id for domain_id, _ in top_related_domains] + new_domains
## MAIN ##############################################################################################################
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
                analyzer.process_analysis_result(record_id, analysis_result, existing_domains)
        else:
            print("No content available to analyze.")

    finally:
        # Close the database connection
        analyzer.close_db()
