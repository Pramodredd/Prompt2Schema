from app.database.mongodb import COLLECTIONS,get_database
from app.database.pinecone import pinecone
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
# db = get_database()
# if db is None:
#     raise ValueError("Database connection not established.")

async def insert_document(collection_name, document):
    if collection_name not in COLLECTIONS:
        raise ValueError(f"Collection '{collection_name}' does not exist.")
    
    collection = db[collection_name]
    result = (await collection.insert_one(document)).inserted_id
    return result

async def display_documents(collection_name):
    if collection_name not in COLLECTIONS:
        raise ValueError(f"Collection '{collection_name}' does not exist.")
    
    collection = db[collection_name]
    documents = await collection.find().to_list(length=None)
    return documents

# async def get_document(collection_name, document_id):
#     if collection_name not in COLLECTIONS:
#         raise ValueError(f"Collection '{collection_name}' does not exist.")
    
#     collection = db[collection_name]
#     document = await collection.find_one({"_id": document_id})
#     return document

async def get_all_documents(collection_name: str):
    """
    Fetches all documents from a specified collection.

    Args:
        collection_name (str): The name of the collection to query.

    Returns:
        list: A list of all documents found in the collection.
        
    Raises:
        ValueError: If the collection_name does not exist in the predefined list.
    """
    if collection_name not in COLLECTIONS:
        raise ValueError(f"Collection '{collection_name}' does not exist.")
    collection = db[collection_name]
    cursor = collection.find({})
    documents = await cursor.to_list(length=None)
    
    return documents

async def delete_document(collection_name, document_id):
    if collection_name not in COLLECTIONS:
        raise ValueError(f"Collection '{collection_name}' does not exist.")
    
    collection = db[collection_name]
    result = await collection.delete_one({"_id": document_id})
    return result.deleted_count

async def json_to_text(json_data):
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

async def get_id_by_document(collection_name,document):
    if collection_name not in COLLECTIONS:
        raise ValueError(f"Collection '{collection_name}' does not exist.")
    try:
        # 2. Safely get the database instance.
        collection = db[collection_name]

        # 3. Search for one document that exactly matches the provided dictionary.
        found_document = await collection.find_one(document)

        # 4. If a document was found, return its '_id'. Otherwise, return None.
        if found_document:
            return found_document.get('_id')
        else:
            return None
            
    except Exception as e:
        print(f"🔥 An error occurred in get_id_by_document: {e}")
        return None

from typing import List, Dict, Any
from fastapi import HTTPException
from bson import ObjectId  
import asyncio

# async def query_schema(query_text: str) -> List[Dict[str, Any]]:
#     """
#     Queries Pinecone for similar schema and retrieves the corresponding full documents
#     from MongoDB using original_id and collection from Pinecone metadata.
#     """
#     if not query_text:
#         return []

#     try:
#         # Step 1: Embed query
#         vector = model.encode(query_text)

#         # Step 2: Query Pinecone
#         results = pinecone.query(
#             vector=vector.tolist(),
#             top_k=1,
#             include_metadata=True
#         )

#         db = get_database()
#         if db is None:
#             raise HTTPException(status_code=500, detail="Database not connected.")

#         # Step 3: Extract metadata and fetch documents
#         full_documents = []

#         for match in results.matches:
#             metadata = match.metadata
#             if "original_id" in metadata and "collection" in metadata:
#                 collection_name = metadata["collection"]
#                 original_id = metadata["original_id"]

#                 try:
#                     doc = db[collection_name].find_one({"_id": ObjectId(original_id)})
#                     if doc:
#                         full_documents.append(doc)
#                 except Exception as fetch_error:
#                     print(f"Failed to fetch document with ID {original_id} from '{collection_name}': {fetch_error}")

#         return full_documents

#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"Failed to query chunks and fetch schemas: {e}")
    
async def query_schema(query_text: str) -> List[Dict[str, Any]]:
    """
    Queries Pinecone for similar schema and retrieves the corresponding full documents
    from MongoDB using original_id and collection from Pinecone metadata.
    """
    if not query_text:
        return []

    try:
        vector = model.encode(query_text)
        results = pinecone.query(
            vector=vector.tolist(),
            top_k=1,  # Fetching a few results is usually better
            include_metadata=True
        )

        db = get_database()
        if db is None:
            raise HTTPException(status_code=500, detail="Database not connected.")

        # --- IMPROVED CONCURRENT FETCH ---
        tasks = []
        for match in results.matches:
            metadata = match.metadata
            if "original_id" in metadata and "collection" in metadata:
                collection_name = metadata["collection"]
                original_id = metadata["original_id"]
                
                # CHANGE 2: Create a task to fetch the doc, but don't await yet
                task = db[collection_name].find_one({"_id": ObjectId(original_id)})
                tasks.append(task)
        
        # CHANGE 3: Run all database queries concurrently and await their results
        if tasks:
            documents_results = await asyncio.gather(*tasks)
            # Filter out any potential None results if a doc wasn't found
            return [doc for doc in documents_results if doc is not None]
        
        return []

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to query and fetch schemas: {e}")
