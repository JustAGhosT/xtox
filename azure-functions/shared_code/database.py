import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'xtotext')

# Create a MongoDB motor client
client = None
db = None

async def initialize_database():
    """Initialize MongoDB connection"""
    global client, db
    if client is not None:
        return db
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        # Verify connection is successful
        await client.admin.command('ismaster')
        db = client[db_name]
        logging.info(f"MongoDB connection established to {db_name}")
        return db
    except ConnectionFailure as e:
        logging.error(f"MongoDB connection failed: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error initializing MongoDB: {str(e)}")
        raise

async def get_database():
    """Get MongoDB database connection"""
    global db
    if db is None:
        db = await initialize_database()
    return db

async def close_database_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        logging.info("MongoDB connection closed")