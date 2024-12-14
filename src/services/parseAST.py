## IMPORT #################################################################################################################
import os
import ast
import networkx as nx
import matplotlib.pyplot as plt
from localContentAnalyzer import GPT2TokenGenerator

# Modular - State of Graph should remain persistant (locations are remembered) and the dots should be able to be interacted with - specifically click and drag for moving

## CONSTANTS ##############################################################################################################
TARGET_DIRECTORY = "/Users/makaminski1337/Developer/DevAtlas/cloned_repo"
SENSITIVE_FILES = [".env", ".git/", ".pyc"]
SENSITIVE_DIRECTORIES = [".git/", ".git", ".env"]
CACHE = ["__pycache__"]
REQUIREMENTS = [".toml"]
DATABASES = ["db-journal"]
EXCLUSIONS=SENSITIVE_FILES+SENSITIVE_DIRECTORIES+CACHE+REQUIREMENTS+DATABASES
ARCHITECTURE_CLASSIFICATION=["Front-end","Back-end", "Database", "Infrastructure", "Other"]
BUSINESS_FRAMEWORK=["Sales","Operations","Product"]
## CLASS DEFINITION #######################################################################################################
class DirectoryVisualizer:
    def __init__(self, directory, exclusions_files, exclusions_dirs, gpt2_generator=None):
        """
        Initialize the DirectoryVisualizer with the target directory.

        :param directory: Path to the directory to visualize
        :param exclusions_files: List of files to exclude from the visualization
        :param exclusions_dirs: List of directories to exclude from the visualization
        :param gpt2_generator: An instance of GPT2TokenGenerator for inference
        """
        self.directory = directory
        self.exclude_files = exclusions_files
        self.exclude_dirs = exclusions_dirs
        self.graph = nx.DiGraph()
        self.node_colors = {}
        self.processed_functions = set()
        self.hierarchy = {}
        self.gpt2_generator = gpt2_generator  # GPT-2 for inferencing classifications

    def classify_node(self, name, context=""):
        """
        Classify a node based on predefined architecture or business classifications.
        If no match is found, use GPT-2 for inference.

        :param name: The name of the node (file, class, or function)
        :param context: Additional context (docstring, file path, etc.)
        :return: A dictionary with classifications
        """
        classification = {
            "architecture": "Other",  # Default classification
            "business": "Product"     # Default business framework
        }

        # Rule-based classification
        if "frontend" in name.lower() or "ui" in name.lower():
            classification["architecture"] = "Front-end"
        elif "backend" in name.lower() or "server" in name.lower():
            classification["architecture"] = "Back-end"
        elif "db" in name.lower() or "database" in name.lower():
            classification["architecture"] = "Database"
        elif "infra" in name.lower() or "config" in name.lower():
            classification["architecture"] = "Infrastructure"

        if "sales" in name.lower():
            classification["business"] = "Sales"
        elif "ops" in name.lower() or "operation" in name.lower():
            classification["business"] = "Operations"

        # Use GPT-2 if classification remains ambiguous
        if classification["architecture"] == "Other" or classification["business"] == "Product":
            if self.gpt2_generator:
                prompt = f"Classify this: '{name}' with context: '{context}'."
                suggestion = self.gpt2_generator.generate_text(prompt, max_length=50)
                if "Front-end" in suggestion:
                    classification["architecture"] = "Front-end"
                elif "Back-end" in suggestion:
                    classification["architecture"] = "Back-end"
                elif "Database" in suggestion:
                    classification["architecture"] = "Database"
                elif "Infrastructure" in suggestion:
                    classification["architecture"] = "Infrastructure"
                if "Sales" in suggestion:
                    classification["business"] = "Sales"
                elif "Operations" in suggestion:
                    classification["business"] = "Operations"

        return classification

    def parse_python_file(self, file_path):
        """
        Parse a Python file to extract classes and functions.

        :param file_path: Path to the Python file
        """
        try:
            with open(file_path, "r") as file:
                tree = ast.parse(file.read(), filename=file_path)
                file_key = os.path.basename(file_path)
                self.hierarchy[file_key] = {"classes": {}, "functions": []}

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        class_docstring = ast.get_docstring(node)
                        classification = self.classify_node(class_name, class_docstring or "")
                        self.hierarchy[file_key]["classes"][class_name] = {
                            "docstring": class_docstring,
                            "functions": [],
                            "classification": classification
                        }
                        class_node = class_name
                        self.graph.add_node(class_node)
                        self.node_colors[class_node] = "purple"  # Class node
                        self.graph.add_edge(file_key, class_node)

                        # Add functions within the class
                        for child in node.body:
                            if isinstance(child, ast.FunctionDef):
                                function_name = child.name
                                function_docstring = ast.get_docstring(child)
                                func_classification = self.classify_node(function_name, function_docstring or "")
                                self.hierarchy[file_key]["classes"][class_name]["functions"].append(
                                    {"name": function_name, "docstring": function_docstring, "classification": func_classification}
                                )
                                if function_name not in self.processed_functions:
                                    function_node = function_name
                                    self.graph.add_node(function_node)
                                    self.node_colors[function_node] = "orange"  # Function node
                                    self.graph.add_edge(class_node, function_node)
                                    self.processed_functions.add(function_name)
                    elif isinstance(node, ast.FunctionDef):
                        function_name = node.name
                        function_docstring = ast.get_docstring(node)
                        func_classification = self.classify_node(function_name, function_docstring or "")
                        if function_name not in self.processed_functions:
                            self.hierarchy[file_key]["functions"].append(
                                {"name": function_name, "docstring": function_docstring, "classification": func_classification}
                            )
                            function_node = function_name
                            self.graph.add_node(function_node)
                            self.node_colors[function_node] = "orange"  # Function node
                            self.graph.add_edge(file_key, function_node)
                            self.processed_functions.add(function_name)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    def parse_directory(self):
        """
        Parse the directory and create a graph representation with a singular root node.
        """
        root_node = os.path.basename(self.directory)
        self.graph.add_node(root_node)
        self.node_colors[root_node] = "blue"  # Root node is a directory
        self.hierarchy[root_node] = {}

        for root, dirs, files in os.walk(self.directory):
            relative_root = os.path.relpath(root, self.directory)

            # Ensure correct parent-child relationships
            if relative_root == ".":
                current_node = root_node
            else:
                current_node = os.path.basename(relative_root)
                self.graph.add_edge(root_node, current_node)
                self.node_colors[current_node] = "blue"  # Directory
                self.hierarchy[current_node] = {}

            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not any(excluded in d for excluded in self.exclude_dirs)]

            for d in dirs:
                dir_node = d
                self.graph.add_edge(current_node, dir_node)
                self.node_colors[dir_node] = "blue"  # Directory
                self.hierarchy[current_node][dir_node] = {}

            for f in files:
                if not any(excluded in f for excluded in self.exclude_files):
                    file_node = f
                    self.graph.add_edge(current_node, file_node)
                    self.node_colors[file_node] = "green"  # File
                    if file_node.endswith(".py"):
                        self.parse_python_file(os.path.join(root, f))

    def visualize_directory(self, title="Directory Structure"):
        """
        Visualize the directory structure as a left-to-right graph.

        :param title: Title of the graph
        """
        plt.figure(figsize=(12, 8))

        # Set the layout to display left-to-right
        try:
            pos = nx.nx_agraph.graphviz_layout(self.graph, prog="dot", args="-Grankdir=LR")
        except ImportError:
            print("Error: PyGraphviz or pydot is required for graph layout. Falling back to spring layout.")
            pos = nx.spring_layout(self.graph)

        # Extract node colors
        node_colors = [self.node_colors[node] for node in self.graph.nodes]

        # Draw the graph
        nx.draw(self.graph, pos, with_labels=True, node_size=2000, font_size=6, font_color="black",
                node_color=node_colors, edge_color="gray", font_weight="bold", alpha=0.8)

        plt.title(title)
        plt.show()

    def save_hierarchy_to_markdown(self, output_file="directory_hierarchy.md"):
        """
        Save the parsed hierarchy to a markdown file.

        :param output_file: The name of the output markdown file
        """
        with open(output_file, "w") as md_file:
            md_file.write("# Application Summary\n\n")
            md_file.write("This document provides an overview of the application's structure, including directories, Python files, classes, and functions.\n\n")

            def write_dict_to_md(d, indent=0):
                for key, value in d.items():
                    md_file.write("    " * indent + f"- {key}\n")
                    if isinstance(value, dict):
                        if "docstring" in value:
                            doc = value["docstring"] or "No description available."
                            md_file.write("    " * (indent + 1) + f"> {doc.strip()}\n")
                        if "classification" in value:
                            arch = value["classification"].get("architecture", "Other")
                            bus = value["classification"].get("business", "Product")
                            md_file.write("    " * (indent + 1) + f"> Architecture: {arch}, Business: {bus}\n")
                        if "functions" in value:
                            for func in value["functions"]:
                                md_file.write("    " * (indent + 1) + f"- {func['name']}\n")
                                if func.get("docstring"):
                                    md_file.write("    " * (indent + 2) + f"> {func['docstring'].strip()}\n")
                                if func.get("classification"):
                                    f_arch = func["classification"].get("architecture", "Other")
                                    f_bus = func["classification"].get("business", "Product")
                                    md_file.write("    " * (indent + 2) + f"> Architecture: {f_arch}, Business: {f_bus}\n")
                        write_dict_to_md(value, indent + 1)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                md_file.write("    " * (indent + 1) + f"- {item['name']}\n")
                                if item.get("docstring"):
                                    md_file.write("    " * (indent + 2) + f"> {item['docstring'].strip()}\n")
                                if item.get("classification"):
                                    f_arch = item["classification"].get("architecture", "Other")
                                    f_bus = item["classification"].get("business", "Product")
                                    md_file.write("    " * (indent + 2) + f"> Architecture: {f_arch}, Business: {f_bus}\n")
                            else:
                                md_file.write("    " * (indent + 1) + f"- {item}\n")

            write_dict_to_md(self.hierarchy)

    def generate_readme(self, output_file="README_test.md"):
        """
        Generate a comprehensive README.md file summarizing the application.

        :param output_file: The name of the README file
        """
        with open(output_file, "w") as readme_file:
            readme_file.write("# Project README\n\n")
            readme_file.write("## Overview\n")
            readme_file.write("This project provides a hierarchical overview of directories, Python files, classes, and their functions. "
                              "It includes classifications based on architectural and business logic to aid developers in navigating the codebase.\n\n")
            readme_file.write("## Structure\n")
            readme_file.write("Below is a high-level view of the project structure:\n\n")

            def write_readme_structure(d, indent=0):
                for key, value in d.items():
                    if key == "functions":
                        continue
                    readme_file.write("    " * indent + f"- **{key}**\n")
                    if isinstance(value, dict):
                        if "docstring" in value:
                            doc = value["docstring"] or "No description available."
                            readme_file.write("    " * (indent + 1) + f"> {doc.strip()}\n")
                        if "classification" in value:
                            arch = value["classification"].get("architecture", "Other")
                            bus = value["classification"].get("business", "Product")
                            readme_file.write("    " * (indent + 1) + f"> Architecture: {arch}, Business: {bus}\n")
                        if "functions" in value:
                            readme_file.write("    " * (indent + 1) + "Functions:\n")
                            for func in value["functions"]:
                                readme_file.write("    " * (indent + 2) + f"- {func['name']}\n")
                                if func.get("docstring"):
                                    readme_file.write("    " * (indent + 3) + f"> {func['docstring'].strip()}\n")
                                if func.get("classification"):
                                    f_arch = func["classification"].get("architecture", "Other")
                                    f_bus = func["classification"].get("business", "Product")
                                    readme_file.write("    " * (indent + 3) + f"> Architecture: {f_arch}, Business: {f_bus}\n")
                        write_readme_structure(value, indent + 1)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                readme_file.write("    " * (indent + 1) + f"- {item['name']}\n")
                                if item.get("docstring"):
                                    readme_file.write("    " * (indent + 2) + f"> {item['docstring'].strip()}\n")
                                if item.get("classification"):
                                    f_arch = item["classification"].get("architecture", "Other")
                                    f_bus = item["classification"].get("business", "Product")
                                    readme_file.write("    " * (indent + 2) + f"> Architecture: {f_arch}, Business: {f_bus}\n")
                            else:
                                readme_file.write("    " * (indent + 1) + f"- {item}\n")

            write_readme_structure(self.hierarchy)

            readme_file.write("\n## Usage\n")
            readme_file.write("### CLI Example\n")
            readme_file.write("Run the following command to execute the visualization:\n")
            readme_file.write("```bash\n")
            readme_file.write("python visualize.py\n")
            readme_file.write("```\n")
            readme_file.write("\n### Output\n")
            readme_file.write("This program generates:\n")
            readme_file.write("- An interactive graph visualizing the directory structure.\n")
            readme_file.write("- A detailed markdown hierarchy (`directory_hierarchy.md`).\n")
            readme_file.write("- A comprehensive README file summarizing the application (`README.md`).\n\n")

            readme_file.write("## Contributing\n")
            readme_file.write("Contributions are welcome! Submit pull requests or report issues.\n\n")
            readme_file.write("## License\n")
            readme_file.write("This project is licensed under the MIT License. See the LICENSE file for details.\n")

## MAIN ###################################################################################################################
def main():
    """
    Main function to analyze the directory and generate classifications.
    """
    # Initialize GPT-2
    gpt2_generator = GPT2TokenGenerator()
    gpt2_generator.load_model_and_tokenizer()
    gpt2_generator.warm_up("Classify the following: Example")

    # Initialize DirectoryVisualizer with GPT-2
    visualizer = DirectoryVisualizer(
        directory=TARGET_DIRECTORY,
        exclusions_files=EXCLUSIONS,
        exclusions_dirs=EXCLUSIONS,
        gpt2_generator=gpt2_generator
    )

    # Parse and classify
    print("Parsing directory...")
    visualizer.parse_directory()
    print("Saving hierarchy to markdown...")
    visualizer.save_hierarchy_to_markdown()
    print("Visualizing directory structure...")
    visualizer.visualize_directory()
    visualizer.generate_readme()
    
if __name__ == "__main__":
    main()

# if a function exists beneath a class make it a different color vs if the function exists beneath a file