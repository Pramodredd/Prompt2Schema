# app/database/mongodb.py

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from contextlib import asynccontextmanager
 
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "prompt2schema_db"
COLLECTIONS = ["sales", "marketing", "finance", "hr"]

# These variables are now considered internal to this module
_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None

async def connect_to_mongo():
    """Establishes a connection to MongoDB and initializes the database object."""
    global _client, _db
    # Only try to connect if not already connected
    if _db is None:
        try:
            _client = AsyncIOMotorClient(MONGO_URL)
            # The ismaster command is cheap and does not require auth.
            await _client.admin.command('ismaster')
            _db = _client[DB_NAME]
            print("✅ Connected to MongoDB")

            # Ensure all required collections exist
            existing_collections = await _db.list_collection_names()
            for name in COLLECTIONS:
                if name not in existing_collections:
                    await _db.create_collection(name)
                    print(f"➕ Created collection: {name}")
                else:
                    print(f"✔️ Collection '{name}' already exists.")
        except Exception as e:
            print(f"🔥 Failed to connect to MongoDB: {e}")
            _client = None
            _db = None
    else:
        print("ℹ️ MongoDB connection already established.")


async def close_mongo_connection():
    """Closes the MongoDB connection and resets the state."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        print("❌ MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """
    Retrieves the database instance safely.

    This function acts as a guard to ensure the application does not
    access the database object before it has been successfully initialized.

    Returns:
        AsyncIOMotorDatabase: The active database instance.

    Raises:
        RuntimeError: If called before `connect_to_mongo()` has successfully run.
    """
    if _db is None:
        raise RuntimeError(
            "Database is not connected. "
            "Ensure `connect_to_mongo()` is called and awaited successfully before accessing the database."
        )
    return _db

@asynccontextmanager
async def lifespan(app):
    # Code here runs on startup
    await connect_to_mongo()
    yield
    # Code here runs on shutdown
    await close_mongo_connection()