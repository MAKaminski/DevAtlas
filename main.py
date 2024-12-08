## IMPORTS ###########################################################################################################
import os
from dotenv import load_dotenv
from github import Github
import networkx as nx
import matplotlib.pyplot as plt
## CLASSES ############################################################################################################
class GitHubRepoAnalyzer:
    """Handles GitHub repository authentication and file fetching."""
    
    def __init__(self, token, repo_name):
        self.github = self.authenticate_github(token)
        self.repo = self.github.get_repo(repo_name)
    
    def authenticate_github(self, token):
        """Authenticate with GitHub using a personal access token."""
        return Github(token)

    def fetch_repository_files(self):
        """Fetch all top-level files and directories in the repository."""
        return [content for content in self.repo.get_contents("")]
        
class FileCategorizer:
    """Categorizes files from the repository into defined domain areas."""
    
    def __init__(self):
        self.categories = {
            "frontend": [],
            "backend": [],
            "database": [],
            "documentation": [],
        }
    
    def categorize_files(self, files):
        """Categorize files based on their extensions."""
        for file in files:
            file_name = file.name.lower()
            if file_name.endswith((".html", ".css", ".js")):
                self.categories["frontend"].append(file_name)
            elif file_name.endswith((".py", ".java", ".rs")):
                self.categories["backend"].append(file_name)
            elif file_name.endswith((".sql", ".db")):
                self.categories["database"].append(file_name)
            elif file_name.endswith((".md", ".txt")):
                self.categories["documentation"].append(file_name)
        return self.categories       

class GraphVisualizer:
    """Generates and visualizes graphs based on categorized data."""
    
    def generate_graph(self, categories):
        """Generate a directed graph from the categorized data."""
        graph = nx.DiGraph()
        for category, files in categories.items():
            graph.add_node(category, size=len(files))
            for file in files:
                graph.add_edge(category, file)
        return graph

    def visualize_graph(self, graph, output_file="graph.png"):
        """Visualize the graph and save it to a file."""
        pos = nx.spring_layout(graph)
        plt.figure(figsize=(12, 8))
        nx.draw(graph, pos, with_labels=True, node_size=1500, node_color="skyblue", font_size=10)
        plt.savefig(output_file)
## MAIN ###########################################################################################################
if __name__ == "__main__":

    # Load environment variables
    load_dotenv()
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO_NAME = os.getenv("GITHUB_REPO")
    
    # Initialize classes
    analyzer = GitHubRepoAnalyzer(GITHUB_TOKEN, REPO)
    categorizer = FileCategorizer()
    visualizer = GraphVisualizer()
    
    # Fetch files and categorize them
    repo_files = analyzer.fetch_repository_files()
    categorized_files = categorizer.categorize_files(repo_files)
    
    # Generate and visualize the graph
    graph = visualizer.generate_graph(categorized_files)
    visualizer.visualize_graph(graph, output_file="domain_knowledge_graph.png")