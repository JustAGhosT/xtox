"""
Service layer for document and audio conversion.
"""
import logging
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import aiofiles
import aiofiles.os

from config import TEMP_DIR
from database import Database
from fastapi import HTTPException
from models import AudioConversionResult, ConversionResult
from utils import auto_fix_latex, parse_latex_errors
from utils.security import sanitize_filename, validate_file_path

logger = logging.getLogger(__name__)

# Import audio converter
# Path structure: xtox/backend/services.py -> xtox/core/audio_converter.py
backend_dir = Path(__file__).parent
xtox_dir = backend_dir.parent
if str(xtox_dir) not in sys.path:
    sys.path.insert(0, str(xtox_dir))
from core.audio_converter import AudioConverter


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
            
            # Sanitize filename to prevent path traversal
            safe_filename = sanitize_filename(filename)
            
            # Write LaTeX file (async I/O)
            tex_file = temp_dir / f"{safe_filename}.tex"
            # Validate path is within temp_dir
            validate_file_path(temp_dir, tex_file)
            # POC: Using aiofiles for async file I/O. For production, consider
            # buffering strategies for very large files.
            async with aiofiles.open(tex_file, 'w', encoding='utf-8') as f:
                await f.write(file_content)
            
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
            
            # Parse errors and warnings (async I/O)
            errors = []
            warnings = []
            if result.returncode != 0 or not success:
                log_file = temp_dir / f"{filename}.log"
                if await aiofiles.os.path.exists(log_file):
                    async with aiofiles.open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = await f.read()
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
            logger.error(f"LaTeX compilation timed out for conversion {conversion_id}")
            raise HTTPException(
                status_code=408, 
                detail="LaTeX compilation timed out. The document may be too complex or contain errors."
            )
        except ValueError as e:
            # Security-related errors (path traversal, invalid filename)
            logger.warning(f"Security validation error for conversion {conversion_id}: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid file: {str(e)}")
        except FileNotFoundError as e:
            logger.error(f"File not found error for conversion {conversion_id}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=404, detail="Required file not found during processing")
        except PermissionError as e:
            logger.error(f"Permission error for conversion {conversion_id}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="File system permission error")
        except Exception as e:
            # Log full exception for debugging
            logger.error(
                f"Unexpected error processing LaTeX for conversion {conversion_id}: {str(e)}",
                exc_info=True
            )
            # Don't expose internal error details to users
            raise HTTPException(
                status_code=500, 
                detail="An error occurred during processing. Please try again or contact support."
            )
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except:
                pass


class AudioService:
    @staticmethod
    async def process_audio_file(
        file_content: bytes,
        filename: str,
        target_format: str = 'mp3',
        bitrate: str = '192k',
        sample_rate: int = None
    ) -> AudioConversionResult:
        """Process audio file and convert to target format"""
        conversion_id = str(uuid.uuid4())
        
        # Create temporary directory for this conversion
        temp_dir = TEMP_DIR / conversion_id
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Sanitize filename to prevent path traversal
            safe_filename = sanitize_filename(filename)
            original_format = Path(safe_filename).suffix.lower().lstrip('.')
            
            # Save uploaded file with safe filename (async I/O)
            input_file = temp_dir / safe_filename
            # Validate path is within temp_dir
            validate_file_path(temp_dir, input_file)
            # POC: Using aiofiles for async file I/O. For production, consider
            # streaming for very large audio files.
            async with aiofiles.open(input_file, 'wb') as f:
                await f.write(file_content)
            
            # Initialize audio converter
            converter = AudioConverter()
            
            # Get audio info before conversion
            audio_info = converter.get_audio_info(input_file)
            duration = audio_info.get('duration')
            
            # Convert audio with safe filename
            safe_stem = Path(safe_filename).stem
            output_filename = f"{safe_stem}.{target_format}"
            output_file = temp_dir / output_filename
            validate_file_path(temp_dir, output_file)
            
            converted_path = converter.convert_audio(
                input_file,
                output_file,
                target_format=target_format,
                bitrate=bitrate,
                sample_rate=sample_rate
            )
            
            success = Path(converted_path).exists()
            
            errors = []
            warnings = []
            
            if not success:
                errors.append("Audio conversion failed - output file not created")
            
            # Move converted file to accessible location if successful
            audio_path = None
            file_size_kb = None
            if success:
                final_audio_path = TEMP_DIR / f"{conversion_id}.{target_format}"
                shutil.move(converted_path, final_audio_path)
                audio_path = str(final_audio_path)
                file_size_kb = final_audio_path.stat().st_size / 1024
            
            result_obj = AudioConversionResult(
                id=conversion_id,
                filename=Path(safe_filename).stem,
                original_format=original_format,
                target_format=target_format,
                success=success,
                errors=errors,
                warnings=warnings,
                audio_path=audio_path,
                file_size_kb=file_size_kb,
                duration=duration
            )
            
            # Store result in database
            db = Database.get_db()
            await db.audio_conversions.insert_one(result_obj.dict())
            
            return result_obj
                
        except ValueError as e:
            # Security-related errors (path traversal, invalid filename)
            logger.warning(f"Security validation error for audio conversion {conversion_id}: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid file: {str(e)}")
        except FileNotFoundError as e:
            logger.error(f"File not found error for audio conversion {conversion_id}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=404, detail="Required file not found during processing")
        except PermissionError as e:
            logger.error(f"Permission error for audio conversion {conversion_id}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="File system permission error")
        except Exception as e:
            # Log full exception for debugging
            logger.error(
                f"Unexpected error processing audio for conversion {conversion_id}: {str(e)}",
                exc_info=True
            )
            # Don't expose internal error details to users
            raise HTTPException(
                status_code=500,
                detail="An error occurred during audio processing. Please try again or contact support."
            )
        finally:
            # Clean up temporary directory with retry logic
            max_retries = 3
            retry_delay = 0.1
            
            for attempt in range(max_retries):
                try:
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir)
                    break
                except PermissionError as e:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} cleaning up {temp_dir}: {e}"
                        )
                    else:
                        logger.error(f"Failed to clean up {temp_dir} after {max_retries} attempts: {e}")
                except Exception as e:
                    logger.error(
                        f"Error cleaning up temporary directory {temp_dir}: {e}",
                        exc_info=True
                    )
                    break