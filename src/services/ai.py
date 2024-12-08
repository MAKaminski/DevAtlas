import openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class ChatGPT:
    def __init__(self):
        """ Initialize the ChatGPT class with API key """
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key
        
    def create_prompt(self, content):
        """
        Create the prompt for GPT based on content passed from the database.
        """
        prompt = f"""
        We have a file with the following content:

        {content}

        Please categorize the content based on the following types:
        1. Code: If it's code, categorize by language and purpose.
        2. Documentation: Summarize the documentation sections (e.g., installation, usage).
        3. Configuration: Extract key configuration parameters.
        4. Other: Any other content should be categorized.

        Provide a detailed summary and recommendations where possible.
        """
        return prompt

    def analyze_content(self, content):
        """
        Analyze the content using OpenAI's GPT API and return categorized results.
        """
        prompt = self.create_prompt(content)
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",  # You can change this to a newer model if needed
                prompt=prompt,
                max_tokens=500,
                temperature=0.7
            )
            result = response.choices[0].text.strip()
            return result
        except Exception as e:
            print(f"Error with GPT API: {e}")
            return None
    
    def process_nodes(self, db):
        """
        Fetch nodes from the database and process their content with GPT.
        """
        nodes = db.fetch_all_nodes()
        for node in nodes:
            node_id, node_type, node_name, node_url, node_content = node
            print(f"\nProcessing node: {node_name}")
            categorized_content = self.analyze_content(node_content)
            print(f"Categorized Content: {categorized_content}\n")
