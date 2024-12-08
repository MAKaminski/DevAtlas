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
        # Debug print to confirm repository access
        print(f"Accessing repository: {self.repo.full_name}")
    
    def authenticate_github(self, token):
        """Authenticate with GitHub using a personal access token."""
        return Github(token)

    def fetch_repository_files(self, path=""):
        """Recursively fetch all files and directories in the repository."""
        contents = self.repo.get_contents(path)
        all_files = []
        for content in contents:
            if content.type == "dir":
                print(f"Entering directory: {content.path}")
                all_files.extend(self.fetch_repository_files(content.path))
            else:
                print(f"Found file: {content.path}")
                all_files.append(content)
        return all_files
        
class FileCategorizer:
    """Categorizes files from the repository into defined domain areas."""
    
    def __init__(self):
        self.categories = {
            "frontend": [],
            "backend": [],
            "database": [],
            "documentation": [],
            "other": [],
        }
    
    def categorize_files(self, files):
        """Categorize files based on their extensions."""
        for file in files:
            file_name = file.path.lower()  # Use file.path to get the full path
            if file_name.endswith((".html", ".css", ".js")):
                self.categories["frontend"].append(file_name)
            elif file_name.endswith((".py", ".java", ".rs")):
                self.categories["backend"].append(file_name)
            elif file_name.endswith((".sql", ".db")):
                self.categories["database"].append(file_name)
            elif file_name.endswith((".md", ".txt")):
                self.categories["documentation"].append(file_name)
            else:
                self.categories["other"].append(file_name)
        return self.categories       

class GraphVisualizer:
    """Generates and visualizes graphs based on categorized data."""
    
    def generate_graph(self, repo_name, categories, outputFilename="domain_knowledge_graph.png"):
        """Generate a directed graph from the categorized data."""
        graph = nx.DiGraph()
        # Add the repository as the top-level node
        graph.add_node(repo_name, category="repository")
        
        # Add nodes and edges to the graph based on categories
        for category, files in categories.items():
            for file in files:
                graph.add_node(file, category=category)
                graph.add_edge(repo_name, file)
        
        # Debug print to check nodes and edges
        print("Nodes:", graph.nodes(data=True))
        print("Edges:", graph.edges(data=True))
        
        # Draw the graph
        pos = nx.spring_layout(graph)
        nx.draw(graph, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=2000, font_size=10, font_weight='bold')
        
        # Save the graph to a file within src/output
        output_path = os.path.join("src", "output", outputFilename)
        plt.savefig(output_path)
        plt.close()
        
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
    REPO = os.getenv("REPO")
    
    # Initialize classes
    analyzer = GitHubRepoAnalyzer(GITHUB_TOKEN, REPO)
    categorizer = FileCategorizer()
    visualizer = GraphVisualizer()
    
    # Fetch files and categorize them
    repo_files = analyzer.fetch_repository_files()
    print("Fetched repository files:", [file.path for file in repo_files])
    categorized_files = categorizer.categorize_files(repo_files)
    
    # Debug print to check categorized files
    print("Categorized Files:", categorized_files)
    
    # Generate and visualize the graph
    graph = visualizer.generate_graph(REPO, categorized_files)
    visualizer.visualize_graph(graph, output_file=os.path.join("src", "output", "domain_knowledge_graph.png"))