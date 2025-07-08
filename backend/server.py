import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Database
from routers import conversion, status, documents
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title="XToPDF API", description="Convert LaTeX to PDF API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversion.router)
app.include_router(status.router)
app.include_router(documents.router)
@app.on_event("startup")
async def startup_db_client():
    await Database.connect()
    logger.info("Connected to the MongoDB database")

@app.on_event("shutdown")
async def shutdown_db_client():
    await Database.close()
    logger.info("Disconnected from the MongoDB database")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
