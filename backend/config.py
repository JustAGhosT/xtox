import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database configuration
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# File storage configuration
TEMP_DIR = Path("/tmp/xtopdf")
DOC_STORAGE_DIR = Path("/tmp/document_storage")

# Application settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
LATEX_TIMEOUT = 30  # seconds

# Create necessary directories
TEMP_DIR.mkdir(exist_ok=True)
DOC_STORAGE_DIR.mkdir(exist_ok=True)