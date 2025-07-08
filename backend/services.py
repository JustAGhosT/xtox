import subprocess
import shutil
import uuid
from pathlib import Path
from fastapi import HTTPException
from typing import Tuple

from config import TEMP_DIR
from database import Database
from models import ConversionResult
from utils import parse_latex_errors, auto_fix_latex

class LatexService:
    @staticmethod
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
            db = Database.get_db()
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