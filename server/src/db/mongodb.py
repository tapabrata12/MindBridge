# File: server/src/db/mongodb.py  # Full file path comment as requested

from typing import Optional  # Import Optional typing for nullable global client/db references
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase  # Import async MongoDB client and database types
from pymongo.errors import PyMongoError  # Import MongoDB base error type for controlled exception handling
from src.core.config import settings  # Import validated application settings

client: Optional[AsyncIOMotorClient] = None  # Create global MongoDB client reference initialized as None
db: Optional[AsyncIOMotorDatabase] = None  # Create global MongoDB database reference initialized as None


async def connect_to_mongo() -> None:  # Define async startup function to connect and validate MongoDB
    global client  # Mark global client variable for assignment
    global db  # Mark global db variable for assignment

    if client is not None and db is not None:  # Check if connection was already initialized
        return  # Exit early to avoid creating duplicate connections

    try:  # Start controlled connection block
        client = AsyncIOMotorClient(  # Create async MongoDB client instance
            settings.MONGODB_URL,  # Use MongoDB URL from validated settings
            serverSelectionTimeoutMS=5000,  # Fail quickly if server is unreachable
            maxPoolSize=50,  # Set reasonable max connection pool size for backend workloads
            minPoolSize=1,  # Keep at least one pooled connection available
        )  # Finish client configuration
        await client.admin.command("ping")  # Verify server availability with lightweight ping command
        db = client[settings.DATABASE_NAME]  # Bind configured database handle after successful ping
    except PyMongoError as exc:  # Catch MongoDB-specific failures
        client = None  # Reset client global to safe state after connection failure
        db = None  # Reset db global to safe state after connection failure
        raise RuntimeError(f"Failed to connect to MongoDB: {str(exc)}") from exc  # Raise explicit runtime error for startup visibility
    except Exception as exc:  # Catch unexpected non-PyMongo exceptions defensively
        client = None  # Reset client global to safe state on unknown failure
        db = None  # Reset db global to safe state on unknown failure
        raise RuntimeError(f"Unexpected MongoDB initialization error: {str(exc)}") from exc  # Raise clear generic runtime error


async def close_mongo_connection() -> None:  # Define async shutdown function to cleanly close MongoDB client
    global client  # Mark global client variable for reassignment
    global db  # Mark global db variable for reassignment

    if client is None:  # Check whether client is already absent
        db = None  # Ensure db is also reset when no client exists
        return  # Exit early because there is nothing to close

    try:  # Start protected close operation block
        client.close()  # Close MongoDB client and its connection pool
    finally:  # Always reset globals even if close raises unexpectedly
        client = None  # Clear global client reference after shutdown
        db = None  # Clear global db reference after shutdown


def get_database() -> AsyncIOMotorDatabase:  # Provide safe accessor for database handle
    if db is None:  # Check if database was initialized successfully
        raise RuntimeError("Database not initialized. Call connect_to_mongo() at app startup.")  # Raise explicit error instead of failing later with attribute errors
    return db  # Return active database handle for service-layer usage