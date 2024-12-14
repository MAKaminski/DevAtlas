## IMPORTS ###########################################################################################################
import os
from datetime import datetime
from dotenv import load_dotenv
## CLASSES ############################################################################################################
from services import contentAnalyzer, databaseController, repoScraper, networkVisualizer
## CONFIGUREATION #####################################################################################################
RUN_STYLE = 'INIT' # 'PROD'
## FUNCTIONS ############################################################################################################
def initialize_database():
    connection, cursor = Local_database.connect()
    Local_database.drop_db()
    Local_database.create_tables()
    Local_database.load_test_data()
    
def fetch_network_data(visualizer):
        connection, cursor = visualizer.connect()
        repos, file_objects, domains, content = visualizer.fetch_data()
        return repos, file_objects, domains, content
    
def create_network_graph(visualizer):
    G = visualizer.create_network_graph(repos, file_objects, domains, content)
    visualizer.plot_graph(G)        
    visualizer.close()
## MAIN ##############################################################################################################
## Test 1 Full Repo Transformation
if __name__ == "__main__":

    print("Starting the main program.")
    st = datetime.now()
    duration = 0

    # Load environment variables
    load_dotenv()
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO = os.getenv("MAIN_REPO")
    DATABASE = os.getenv("DATABASE")
    OPENAPI_TOKEN = os.getenv("OPENAI_TOKEN")
    
    # Initialize Classes
    Local_database = databaseController.DatabaseInitializer(DATABASE)
    Local_repoScraper = repoScraper.RepoScraper(DATABASE, GITHUB_TOKEN)
    Local_gptController = contentAnalyzer.GPTContentAnalyzer(DATABASE)
    Local_networkVisualizer = networkVisualizer.InteractiveNetworkGraphVisualizer(DATABASE)
    
    # Initialize Database
    if RUN_STYLE == 'INIT':
        initialize_database() 
                   
    # Scrape the Repo, Analyze the Content, Create Domain Relationships
    Local_repoScraper.run()
    
    et = datetime.now()
    duration = et - st
    
    print(f"Program completed in {duration} seconds.")
    
    repos, file_objects, domains, content = fetch_network_data(Local_networkVisualizer)
    create_network_graph(Local_networkVisualizer)
    