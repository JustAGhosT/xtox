from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import re
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Create directory for temporary files
TEMP_DIR = Path("/tmp/xtopdf")
TEMP_DIR.mkdir(exist_ok=True)

# Define Models
class ConversionRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    auto_fix: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversionResult(BaseModel):
    id: str
    filename: str
    success: bool
    auto_fix_applied: bool = False
    errors: List[str] = []
    warnings: List[str] = []
    pdf_path: Optional[str] = None
    fixed_content: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

def parse_latex_errors(log_content: str) -> tuple[List[str], List[str]]:
    """Parse LaTeX log file to extract errors and warnings"""
    errors = []
    warnings = []
    
    lines = log_content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('!') and 'Error' in line:
            error_msg = line
            # Try to get the next few lines for more context
            for j in range(i + 1, min(i + 3, len(lines))):
                if lines[j].strip() and not lines[j].startswith('l.'):
                    error_msg += " " + lines[j].strip()
                if lines[j].startswith('l.'):
                    error_msg += " " + lines[j].strip()
                    break
            errors.append(error_msg)
        elif 'Warning' in line and not line.startswith('('):
            warnings.append(line.strip())
    
    return errors, warnings

def auto_fix_latex(content: str) -> tuple[str, bool]:
    """Apply basic auto-fixes to LaTeX content"""
    original_content = content
    fixed = False
    
    # Remove BOM if present
    if content.startswith('\ufeff'):
        content = content[1:]
        fixed = True
    
    # Check for \documentclass
    if '\\documentclass' not in content:
        content = '\\documentclass{article}\n' + content
        fixed = True
    
    # Check for \begin{document}
    if '\\begin{document}' not in content:
        # Find where to insert \begin{document}
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('\\documentclass'):
                insert_pos = i + 1
                break
        lines.insert(insert_pos, '\\begin{document}')
        content = '\n'.join(lines)
        fixed = True
    
    # Check for \end{document}
    if '\\end{document}' not in content:
        content = content + '\n\\end{document}'
        fixed = True
    
    return content, fixed

async def process_latex_file(file_content: str, filename: str, auto_fix: bool = False) -> ConversionResult:
    """Process LaTeX file and convert to PDF"""
    conversion_id = str(uuid.uuid4())
    
    # Create temporary directory for this conversion
    temp_dir = TEMP_DIR / conversion_id
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Apply auto-fix if requested
        fixed_content = None
        auto_fix_applied = False
        if auto_fix:
            file_content, auto_fix_applied = auto_fix_latex(file_content)
            if auto_fix_applied:
                fixed_content = file_content
        
        # Write LaTeX file
        tex_file = temp_dir / f"{filename}.tex"
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        # Run pdflatex
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', f'{filename}.tex'],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check if PDF was created
        pdf_file = temp_dir / f"{filename}.pdf"
        success = pdf_file.exists()
        
        # Parse errors and warnings
        errors = []
        warnings = []
        if result.returncode != 0 or not success:
            log_file = temp_dir / f"{filename}.log"
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()
                errors, warnings = parse_latex_errors(log_content)
            
            if not errors:
                errors = [f"LaTeX compilation failed with return code {result.returncode}"]
                if result.stderr:
                    errors.append(result.stderr)
        
        # Move PDF to accessible location if successful
        pdf_path = None
        if success:
            final_pdf_path = TEMP_DIR / f"{conversion_id}.pdf"
            shutil.move(pdf_file, final_pdf_path)
            pdf_path = str(final_pdf_path)
        
        result_obj = ConversionResult(
            id=conversion_id,
            filename=filename,
            success=success,
            auto_fix_applied=auto_fix_applied,
            errors=errors,
            warnings=warnings,
            pdf_path=pdf_path,
            fixed_content=fixed_content if auto_fix_applied else None
        )
        
        # Store result in database
        await db.conversions.insert_one(result_obj.dict())
        
        return result_obj
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="LaTeX compilation timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

@api_router.post("/convert", response_model=ConversionResult)
async def convert_latex_to_pdf(
    file: UploadFile = File(...),
    auto_fix: bool = False
):
    """Convert LaTeX file to PDF"""
    
    # Validate file type
    if not file.filename.endswith('.tex'):
        raise HTTPException(status_code=400, detail="Only .tex files are supported")
    
    # Check file size (limit to 10MB)
    MAX_SIZE = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")
    
    # Decode content
    try:
        file_content = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            file_content = content.decode('latin-1')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Unable to decode file. Please ensure it's a valid text file")
    
    # Extract filename without extension
    filename = file.filename.rsplit('.', 1)[0]
    
    # Process the file
    result = await process_latex_file(file_content, filename, auto_fix)
    
    return result

@api_router.get("/download/{conversion_id}")
async def download_pdf(conversion_id: str):
    """Download the generated PDF"""
    
    # Get conversion result from database
    conversion = await db.conversions.find_one({"id": conversion_id})
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    
    if not conversion.get("success") or not conversion.get("pdf_path"):
        raise HTTPException(status_code=400, detail="PDF not available for this conversion")
    
    pdf_path = Path(conversion["pdf_path"])
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    return FileResponse(
        path=pdf_path,
        filename=f"{conversion['filename']}.pdf",
        media_type="application/pdf"
    )

@api_router.get("/conversion/{conversion_id}", response_model=ConversionResult)
async def get_conversion_result(conversion_id: str):
    """Get conversion result by ID"""
    
    conversion = await db.conversions.find_one({"id": conversion_id})
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    
    return ConversionResult(**conversion)

# Original endpoints
@api_router.get("/")
async def root():
    return {"message": "XToPDF API - Convert LaTeX to PDF"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()