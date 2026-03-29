import sys
import os

print(f"Current Python executable: {sys.executable}")
print(f"Current sys.path: {sys.path}")

try:
    import fastapi
    print(f"FastAPI found at: {fastapi.__file__}")
except ImportError:
    print("FastAPI not found")
