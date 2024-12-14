# **DevAtlas**

## **Overview**
The DevAtlas is a Python-based tool designed to automate the process of analyzing and documenting the structure of repositories, directories, and files. It identifies classes, functions, and their purposes, classifies them into architecture and business frameworks, and generates comprehensive documentation in Markdown format, complete with interactive visualizations.

## **Features**
- **Codebase Analysis**:
  - Parses Python files, directories, and GitHub repositories.
  - Extracts class structures, function definitions, and relationships.
  - Classifies architecture (`Front-end`, `Back-end`, `Database`)
- **Interactive Visualizations**:
  - Creates interactive graphs to represent the codebase structure.
- **Auto-Generated Documentation**:
  - Generates a detailed, developer-friendly `DEVATLAS_README.md`.
  - Includes usage examples, architecture summaries, and code flow insights.
- **AI-Driven Classifications**:
  - Leverages GPT-2 to infer ambiguous classifications for architecture and business logic.

---

## **Quick Start**

### **Installation**
1. Clone the repository:
   ```bash
   git clone https://github.com/MAKaminski/DevAtlas.git
   cd DevAtlas
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Set up GPT-2 for AI-enhanced features:
   - Download the GPT-2 model using `transformers`:
     ```bash
     python -m transformers-cli download gpt2
     ```

### **Usage**
Run the tool to analyze a directory and generate documentation:
```bash
python DevAtlas/main.py --config config/default_config.yaml
```

#### **CLI Options**
| Flag          | Description                                   | Default Value                 |
|---------------|-----------------------------------------------|-------------------------------|
| `--config`    | Path to the configuration file                | `config/default_config.yaml`  |
| `--output`    | Output path for generated `DEVATLAS_README.md`| `DEVATLAS_README.md`          |
| `--visualize` | Generate an interactive graph visualization   | Enabled                       |

---

## **Configuration**
Modify `config/default_config.yaml` to customize the tool:
```yaml
target_directory: "./path/to/target"
exclusions:
  - ".git"
  - "__pycache__"
  - ".env"
generate_visualization: true
output_file: "README.md"
```

---

## **Example Output**
### **Markdown**
After running the tool, the `README.md` file will contain:
- Project structure
- Class and function summaries
- Architecture and business classifications
- Usage instructions

### **Interactive Graph**
An HTML-based interactive graph is generated, showing:
- Relationships between files, classes, and functions.
- Clickable nodes for deeper insights.

---

## **Architecture**
### **Project Structure**
```plaintext
DevAtlas/
├── auto_doc_generator/
│   ├── config/                  # Configurations for parsing
│   ├── parsers/                 # Logic for parsing files and directories
│   ├── analyzers/               # Class and function analysis
│   ├── generators/              # Markdown and visualization generation
│   └── utils/                   # Helpers for I/O, async tasks, etc.
├── .github/workflows/           # GitHub Action workflow for automation
└── requirements.txt             # Dependencies
```

### **Workflow**
1. Parse directory using rules and exclusions.
2. Analyze extracted entities:
   - Class relationships
   - Function call flows
   - Architecture and business classifications
3. Generate:
   - `README.md` with project documentation
   - Interactive graph for visualization.

---

## **GitHub Action Integration**
To run the tool automatically after every commit, add this workflow file in `.github/workflows/auto-doc-generator.yml`:

```yaml
name: Auto Documentation

on:
  push:
    branches:
      - main

jobs:
  auto-doc:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@
