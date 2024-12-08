## IMPORTS ###########################################################################################################
import os
from dotenv import load_dotenv
## CLASSES ############################################################################################################
from services import database, repoScraper, gptController, networkVisualizer
## MAIN ##############################################################################################################
## Test 1 Full Repo Transformation
if __name__ == "__main__":

    # Load environment variables
    load_dotenv()
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO = os.getenv("MAIN_REPO")
    DATABASE = os.getenv("DATABASE")
    OPENAPI_TOKEN = os.getenv("OPENAI_TOKEN")
    
    # Initialize Classes
    Local_database = database.DatabaseInitializer(DATABASE)
    Local_repoScraper = repoScraper.GitHubRepoScraper(DATABASE, GITHUB_TOKEN)
    Local_gptController = gptController.GPTContentAnalyzer(DATABASE)
    Local_networkVisualizer = networkVisualizer.InteractiveNetworkGraphVisualizer(DATABASE)
    
    # Connect to the database, Scrape the Repo, Analyze the Content, Create Domain Relationships, and Visualize the Graph
    # Database
    connection, cursor = Local_database.connect()
    Local_database.drop_db(connection, cursor)
    Local_database.create_tables(connection, cursor)
    Local_database.load_test_data(connection, cursor)
    
    # Scraper
    Local_repoScraper.scrape_repo(REPO)
    
    

    Local_repoScraper.run()
    
    # Analyze Content
    
    # Load environment variables
    load_dotenv()
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO = os.getenv("REPO")
    
  

    # Generate and visualize the graph
    graph = visualizer.generate_graph(REPO, categorized_files)
    visualizer.visualize_graph(graph, output_file=os.path.join("src", "output", "domain_knowledge_graph.png"))