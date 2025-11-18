import os

# 🚀 Corrected scaffold schema
# RULES:
# - dict  => directory
# - list  => list of filenames
# - str   => filename containing the given string as content (or empty)
SCAFFOLD = {
    "data": [],
    "scripts": [],
    "ui": ["streamlit_app.py"],
    "src": {
        "buying_guide": {
            "__files__": ["__init__.py", "config.py"],
            "models": {
                "__files__": ["__init__.py", "plan.py", "product.py"]
            },
            "llm": {
                "__files__": ["__init__.py", "client.py", "planner.py", "explainer.py"]
            },
            "index": {
                "__files__": ["__init__.py", "loader.py", "filters.py", "scoring.py", "retriever.py"]
            },
            "app": {
                "__files__": ["__init__.py", "session.py", "cli.py", "api.py"]
            }
        }
    }
}


def create_structure(base_path, structure):
    """ Recursively create files and folders from SCAFFOLD definition. """
    for name, content in structure.items():
        # Create directories
        if isinstance(content, dict):
            dir_path = os.path.join(base_path, name)
            os.makedirs(dir_path, exist_ok=True)

            # handle any "__files__" inside this dict
            file_list = content.get("__files__", [])
            for fname in file_list:
                file_path = os.path.join(dir_path, fname)
                open(file_path, "w").close()

            # recurse into subdirectories (excluding __files__)
            subdirs = {k: v for k, v in content.items() if k != "__files__"}
            create_structure(dir_path, subdirs)

        # Create files inside a directory
        elif isinstance(content, list):
            dir_path = os.path.join(base_path, name)
            os.makedirs(dir_path, exist_ok=True)

            for fname in content:
                file_path = os.path.join(dir_path, fname)
                open(file_path, "w").close()


if __name__ == "__main__":
    project_root = os.getcwd()
    print(f"📁 Creating scaffold in: {project_root}\n")

    create_structure(project_root, SCAFFOLD)

    print("✅ Project scaffold created successfully!\n")
    print("Folders created:")
    print("""
    data/
    scripts/
    ui/
        streamlit_app.py
    src/buying_guide/
        config.py
        models/
        llm/
        index/
        app/
    """)
