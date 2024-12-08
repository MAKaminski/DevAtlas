# Roadmap

## Prompt for GPT Interface:

We are working with a system that recursively searches a GitHub repository. The system will retrieve directories and files and store them as "nodes" with the following structure:

## Node Attributes:

ID: Integer (Primary Key)
Type: Enum (either Directory or File)
Name: String (name of the file or directory)
URL: String (URL pointing to the file or directory on GitHub)
Content: Text (This is the extracted content from the file or directory. If it's a directory, it will contain metadata about the files within it.)
The content from the files will be categorized based on the context and type of content (e.g., code, documentation, configuration, etc.) using the GPT Flow.

Your task is to analyze the content of the files extracted and provide a categorization, summary, and potentially actionable insights based on the following types of data:

Code: Categorize the code based on the programming language and its purpose (e.g., script, configuration, API endpoint, etc.)
Documentation: Summarize the documentation, if any, and identify key sections like installation, usage, and requirements.
Configuration: Identify configuration files and extract key configuration parameters.
Other: Any other content should be categorized and summarized based on relevance.
Once the content is processed, please categorize it and return the classification alongside any recommendations for improvements or next steps.

--