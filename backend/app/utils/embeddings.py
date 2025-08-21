
import asyncio
import os
import uuid
import json
from typing import Optional, Dict, Any, List

# --- Model & Tokenizer Imports ---
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer

# --- Database & Environment Imports ---
from pinecone import Pinecone
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId

print("🚀 Script starting...")

# ==============================================================================
# 1. INITIALIZATION (Models, Pinecone, etc.)
# ==============================================================================

print("🔧 Initializing models and connections...")

# --- Load Sentence Transformer Model ---
# This model is great for generating meaningful vector embeddings from text.
try:
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print("✅ Models and tokenizer loaded successfully.")
except Exception as e:
    print(f"🔥 Failed to load SentenceTransformer models: {e}")
    exit() # Exit if models can't be loaded

# --- Initialize Pinecone ---
# Loads credentials from a .env file and connects to your Pinecone index.
try:
    load_dotenv()
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME")

    if not api_key or not index_name:
        raise ValueError("PINECONE_API_KEY or PINECONE_INDEX_NAME not set in .env file.")

    pc = Pinecone(api_key=api_key)
    pinecone_index = pc.Index(index_name)
    print(f"✅ Pinecone initialized for index '{index_name}'.")
    # A quick check to ensure the index is ready
    pinecone_index.describe_index_stats()
    print("✅ Pinecone index is online.")
except Exception as e:
    print(f"🔥 Failed to initialize Pinecone: {e}")
    exit()

# ==============================================================================
# 2. MONGODB CONNECTION & HELPERS
# ==============================================================================

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "prompt2schema_db"
COLLECTIONS = ["sales", "marketing", "finance", "hr"]

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None

async def connect_to_mongo():
    """Establishes and validates the connection to MongoDB."""
    global _client, _db
    if _db is None:
        print("🔌 Connecting to MongoDB...")
        try:
            _client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
            await _client.admin.command('ping') # Check connection
            _db = _client[DB_NAME]
            print("✅ Connected to MongoDB successfully.")
        except Exception as e:
            print(f"🔥 Failed to connect to MongoDB: {e}")
            _client = None
            _db = None
            raise

async def close_mongo_connection():
    """Closes the MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        print("❌ MongoDB connection closed.")

def get_database() -> AsyncIOMotorDatabase:
    """Safely retrieves the database instance."""
    if _db is None:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return _db

# --- Standalone CRUD Functions ---

async def get_all_documents(collection_name: str) -> List[Dict[str, Any]]:
    """Fetches all documents from a specified collection."""
    db = get_database()
    return await db[collection_name].find().to_list(length=None)

def json_to_text(json_data):
    """
    Converts a JSON object to a text string.

    Args:
        json_data (dict): The JSON data to convert.

    Returns:
        str: The text representation of the JSON data.
    """
    if not isinstance(json_data, dict):
        raise ValueError("Input must be a dictionary.")
    
    return "\n".join(f"{key}: {value}" for key, value in json_data.items())


# ==============================================================================
# 3. CORE LOGIC
# ==============================================================================

async def embed_and_store_data():
    """
    Fetches data from MongoDB, creates embeddings, and stores them in Pinecone.
    """
    print("\n--- 🚀 Starting Embedding and Storage Process ---")
    for collection_name in COLLECTIONS:
        print(f"\n--- Processing collection: '{collection_name}' ---")
        try:
            documents = await get_all_documents(collection_name)
            if not documents:
                print(f"🟡 No documents found in '{collection_name}'. Skipping.")
                continue
            print(f"📚 Found {len(documents)} documents to process.")
        except Exception as e:
            print(f"🔥 ERROR fetching from '{collection_name}': {e}")
            continue

        vectors_to_upsert = []
        for doc in documents:
            try:
                doc_id = doc.get("_id")
                if not doc_id:
                    print(f"⚠️ Skipping document due to missing '_id': {doc}")
                    continue

                text = json_to_text(doc)
                if not text:
                    continue

                tokens = tokenizer.encode(text, add_special_tokens=False)
                if len(tokens) > 256:
                    print(f"⚠️ Doc {doc_id} too long ({len(tokens)} tokens), skipping.")
                    continue

                vector = model.encode(text)

                vectors_to_upsert.append({
                    "id": str(uuid.uuid4()),
                    "values": vector.tolist(),
                    "metadata": {
                        "original_id": str(doc_id),
                        "collection": collection_name
                    }
                })
            except Exception as e:
                print(f"🔥 ERROR processing document {doc.get('_id', 'N/A')}: {e}")
                continue
        
        if vectors_to_upsert:
            print(f"🌲 Upserting {len(vectors_to_upsert)} vectors to Pinecone...")
            try:
                # Pinecone SDK v3+ is synchronous, so we run it in a thread
                # to avoid blocking the asyncio event loop.
                await asyncio.to_thread(pinecone_index.upsert, vectors=vectors_to_upsert)
                print(f"✅ Successfully upserted vectors for '{collection_name}'.")
            except Exception as e:
                print(f"🔥 FATAL ERROR during Pinecone upsert for '{collection_name}': {e}")
        else:
            print(f"🟡 No valid vectors were generated for '{collection_name}'.")

# ==============================================================================
# 4. SCRIPT EXECUTION
# ==============================================================================

async def main():
    """Main function to orchestrate the connection, processing, and disconnection."""
    try:
        await connect_to_mongo()
        await embed_and_store_data()
    except Exception as e:
        print(f"\nAn unhandled error occurred during execution: {e}")
    finally:
        await close_mongo_connection()
        print("\n✅ Script finished.")

if __name__ == "__main__":
    # This block runs the main asynchronous function
    asyncio.run(main())
