from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import zipfile
import tempfile
from pathlib import Path
from services.parser import parse_project, parse_python_file
from services.java_parser import parse_java_code
from services.graph_builder import generate_mermaid_diagram
from pydantic import BaseModel

app = FastAPI(title="CodeViz API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = Path("temp_uploads")
TEMP_DIR.mkdir(exist_ok=True)

class CodeInput(BaseModel):
    code: str
    language: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/analyze-code")
async def analyze_code_text(input_data: CodeInput):
    try:
        if input_data.language.lower() == "python":
            # We need to save it to a temp file for parse_python_file 
            # or refactor parser to accept string. 
            # For now, let's just parse it directly if we had a function for that.
            # I'll add a helper to services/parser.py to parse from string.
            from services.parser import parse_python_code
            project_structure = parse_python_code(input_data.code)
        elif input_data.language.lower() == "java":
            project_structure = parse_java_code(input_data.code)
        else:
            raise HTTPException(status_code=400, detail=f"Language {input_data.language} not supported")

        from services.ai_analyzer import analyze_with_ai
        project_structure = analyze_with_ai(project_structure, input_data.code)

        mermaid_code = generate_mermaid_diagram(project_structure)
        return {
            "structure": project_structure.dict(),
            "mermaid": mermaid_code
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_code(file: UploadFile = File(...)):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported")
    
    # Save uploaded file
    file_path = TEMP_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Extract
    extract_dir = TEMP_DIR / file.filename.replace(".zip", "")
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir()
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        # Parse
        project_structure = parse_project(str(extract_dir))
        
        from services.ai_analyzer import analyze_with_ai
        project_structure = analyze_with_ai(project_structure)
        
        # Generate Diagram
        mermaid_code = generate_mermaid_diagram(project_structure)
        
        return {
            "structure": project_structure.dict(),
            "mermaid": mermaid_code
        }
        
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid zip file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        # In a real app, we might want to keep these or use a proper tempfile context
        if file_path.exists():
            os.remove(file_path)
        if extract_dir.exists():
            shutil.rmtree(extract_dir)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
