# 📁 File: Server/src/db/mongodb.py

# Import AsyncIOMotorClient to connect to MongoDB asynchronously
from motor.motor_asyncio import AsyncIOMotorClient

# Import settings to get MongoDB URL

from src.core.config import settings

client = None
db = None

# Function to connect to MongoDB
async def connect_to_mongo():
    global client # Tell Python we are using the global client variable
    global db # Tell Python we are using the global db variable
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        # Select the database (we'll name it "mindbridge")
        db = client[settings.DATABASE_NAME]
    except Exception as err:
        raise err

# Function to close MongoDB connection
async def close_mongo_connection():
    global client  # Use the global client

    try:
        # Close the MongoDB connection if it exists
        if client:
            client.close()
    except Exception as err:
        raise err