## IMPORTS ##############################################################################################################
import os
import sqlite3
import networkx as nx
import plotly.graph_objects as go
## FUNCTIONS ############################################################################################################
from dotenv import load_dotenv
## CONFIGURATION ########################################################################################################
load_dotenv()
DB = os.getenv("DATABASE") 
## CLASSES ############################################################################################################
class InteractiveNetworkGraphVisualizer:
    def __init__(self, db_file):
        """Initialize the Database connection"""
        self.db_file = db_file
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Connect to SQLite database"""
        try:
            self.connection = sqlite3.connect(self.db_file)
            self.cursor = self.connection.cursor()
            print("Successfully connected to SQLite")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return None, None
        
        return self.connection, self.cursor

    def fetch_data(self):
        """Fetch data from all tables and prepare the graph"""
        query_repos = "SELECT id, name FROM repos"
        query_file_objects = "SELECT id, repo_id, name, url, type FROM fileObjects"
        query_domains = "SELECT id, name FROM domains"
        query_content = "SELECT id, fileObject_id, domain_id, description FROM content"
        
        # Fetch all data
        self.cursor.execute(query_repos)
        repos = self.cursor.fetchall()
        
        self.cursor.execute(query_file_objects)
        file_objects = self.cursor.fetchall()
        
        self.cursor.execute(query_domains)
        domains = self.cursor.fetchall()
        
        self.cursor.execute(query_content)
        content = self.cursor.fetchall()
        
        return repos, file_objects, domains, content

    def create_network_graph(self, repos, file_objects, domains, content):
        """Create a network graph from the fetched data"""
        G = nx.Graph()

        # Add nodes for repositories
        for repo_id, repo_name in repos:
            G.add_node(f"repo_{repo_id}", label=repo_name, type="repo")

        # Add nodes for file objects and edges to repos
        for file_id, repo_id, file_name, file_url, file_type in file_objects:
            G.add_node(f"file_{file_id}", label=file_name, type="file", url=file_url, file_type=file_type)
            G.add_edge(f"repo_{repo_id}", f"file_{file_id}")

        # Add nodes for domains
        for domain_id, domain_name in domains:
            G.add_node(f"domain_{domain_id}", label=domain_name, type="domain")

        # Add nodes for content and edges to file objects and domains
        for content_id, file_id, domain_id, description in content:
            G.add_node(f"content_{content_id}", label=f"Content {content_id}", type="content", description=description)
            G.add_edge(f"file_{file_id}", f"content_{content_id}")
            G.add_edge(f"domain_{domain_id}", f"content_{content_id}")

        return G

    def plot_graph(self, G):
        """Plot the graph using Plotly"""
        pos = nx.spring_layout(G)  # Layout for the graph
        node_x = []
        node_y = []
        node_labels = []
        node_tooltips = []  # Tooltips for the nodes
        node_types = []
        
        # Collect node data
        for node, data in G.nodes(data=True):
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_labels.append(data['label'])
            node_tooltips.append(self.get_tooltip(data))
            node_types.append(data['type'])
        
        # Collect edge data
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.append(x0)
            edge_y.append(y0)
            edge_x.append(x1)
            edge_y.append(y1)

        # Create the Plotly graph
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')

        # Group nodes by type for interactive legend
        node_traces = {}
        node_colors = {
            "repo": 'rgb(0, 0, 255)',   # Blue for repos
            "file": 'rgb(0, 255, 0)',   # Green for file objects
            "domain": 'rgb(255, 0, 0)', # Red for domains
            "content": 'rgb(255, 255, 0)' # Yellow for content
        }
        
        for node_type, color in node_colors.items():
            node_traces[node_type] = go.Scatter(
                x=[],
                y=[],
                mode='markers',
                hoverinfo='text',
                text=[],
                marker=dict(size=15, color=color),
                name=node_type.capitalize()  # Add to legend
            )
        
        for i, node_type in enumerate(node_types):
            node_traces[node_type].x += (node_x[i],)
            node_traces[node_type].y += (node_y[i],)
            node_traces[node_type].text += (node_tooltips[i],)

        # Combine edge trace and node traces
        fig_data = [edge_trace] + list(node_traces.values())
        
        # Create the figure
        fig = go.Figure(data=fig_data,
                        layout=go.Layout(
                            title="Interactive Network Graph",
                            titlefont_size=16,
                            showlegend=True,
                            hovermode='closest',
                            margin=dict(b=0, l=0, r=0, t=40),
                            xaxis=dict(showgrid=False, zeroline=False),
                            yaxis=dict(showgrid=False, zeroline=False),
                            plot_bgcolor='black',  # Set background color to black
                            paper_bgcolor='black',  # Set paper background to black
                            font=dict(color='white')  # Set font color for legend and title
                        ))
        
        fig.show()

    def get_tooltip(self, data):
        """Generate a tooltip string based on node type"""
        if data['type'] == 'file':
            return f"File Name: {data['label']}<br>URL: {data.get('url', 'N/A')}<br>Type: {data.get('file_type', 'N/A')}"
        elif data['type'] == 'repo':
            return f"Repository: {data['label']}"
        elif data['type'] == 'domain':
            return f"Domain: {data['label']}"
        elif data['type'] == 'content':
            return f"Content ID: {data['label']}<br>Description: {data.get('description', 'N/A')}"
        else:
            return f"{data['label']}"

    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            print("Connection closed.")
## MAIN  ##############################################################################################################
if __name__ == "__main__":

    visualizer = InteractiveNetworkGraphVisualizer(DB)
    
    # Connect to the database
    connection, cursor = visualizer.connect()
    
    # Fetch data from the database
    repos, file_objects, domains, content = visualizer.fetch_data()
    
    # Create the network graph
    G = visualizer.create_network_graph(repos, file_objects, domains, content)
    
    # Plot the graph
    visualizer.plot_graph(G)
    
    # Close the database connection
    visualizer.close()
