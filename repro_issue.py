import sys
import os
from pathlib import Path

# Add the directory containing this file to sys.path
sys.path.append(str(Path(__file__).parent))

from services.parser import parse_project
from services.graph_builder import generate_mermaid_diagram

import tempfile
import shutil
from pathlib import Path

def test():
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a sample python file
        file_path = Path(tmp_dir) / "test.py"
        with open(file_path, "w") as f:
            f.write("""
class A:
    "This is class A summary"
    pass

class B(A):
    "This is class B summary"
    def method(self):
        pass
            """)
        
        print(f"Created file at {file_path}")
        
        # Parse
        try:
            structure = parse_project(tmp_dir)
            print("Structure:", structure)
            
            # Generate Diagram
            mermaid = generate_mermaid_diagram(structure)
            print("Mermaid Code:\n", mermaid)
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test()
