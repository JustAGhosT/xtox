from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List

from config import MAX_FILE_SIZE
from models import ConversionResult, ConversionRequest
from services import LatexService
from database import Database

router = APIRouter(prefix="/api")

@router.post("/convert", response_model=ConversionResult)
async def convert_latex_to_pdf(
    file: UploadFile = File(...),
    auto_fix: bool = False
):
    """Convert LaTeX file to PDF"""
    
    # Validate file type
    if not file.filename.endswith('.tex'):
        raise HTTPException(status_code=400, detail="Only .tex files are supported")
    
    # Check file size (limit to 10MB)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
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
    result = await LatexService.process_latex_file(file_content, filename, auto_fix)
    
    return result

@router.get("/download/{conversion_id}")
async def download_pdf(conversion_id: str):
    """Download the generated PDF"""
    
    # Get conversion result from database
    db = Database.get_db()
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

@router.get("/conversion/{conversion_id}", response_model=ConversionResult)
async def get_conversion_result(conversion_id: str):
    """Get conversion result by ID"""
    
    db = Database.get_db()
    conversion = await db.conversions.find_one({"id": conversion_id})
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    
    return ConversionResult(**conversion)