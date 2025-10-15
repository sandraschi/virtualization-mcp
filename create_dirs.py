import os

base_path = os.path.join("src", "virtualization-mcp")
dirs = ["api", "models", "services", "utils"]

for d in dirs:
    dir_path = os.path.join(base_path, d)
    try:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")
    except Exception as e:
        print(f"Error creating {dir_path}: {e}")
