from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL, DB_NAME

class Database:
    client = None
    db = None

    @classmethod
    async def connect(cls):
        """Connect to MongoDB database"""
        cls.client = AsyncIOMotorClient(MONGO_URL)
        cls.db = cls.client[DB_NAME]
        return cls.db

    @classmethod
    async def close(cls):
        """Close database connection"""
        if cls.client:
            cls.client.close()

    @classmethod
    def get_db(cls):
        """Get database instance"""
        return cls.db