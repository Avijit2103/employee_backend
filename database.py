import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

DB_NAME = "assessment_db"
COLLECTION_NAME = "employees"

class MongoDB:
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db = None
        self.collection = None

    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(MONGO_URI)
            self.db = self.client[DB_NAME]
            self.collection = self.db[COLLECTION_NAME]
            print("Successfully connected to MongoDB!")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")

    async def close(self):
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")

db_client = MongoDB()
