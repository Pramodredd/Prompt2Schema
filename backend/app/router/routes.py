from fastapi import APIRouter, HTTPException , Depends
from app.model.schema import UploadRequest, LLMResponse , RetrieveQuery
from app.database.mongodb import get_database
from app.utils.crud_ops import query_schema
from app.model.llm import get_llm
from bson import ObjectId
router = APIRouter()

@router.get("/")
async def read_root():
    """Root endpoint for the API."""
    return {"message": "Welcome to the Prompt2Schema API Backend!"}



@router.post("/upload")
async def upload_schema(request: UploadRequest):
    """Upload a single or list of JSON schemas."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected.")
    
    try:
        collection_name = request.collection_name
        schemas = request.schema_data

        # Normalize to list
        if not isinstance(schemas, list):
            schemas = [schemas]

        # Insert all schemas
        await db[collection_name].insert_many(schemas)
        return {"message": "Schema(s) uploaded successfully!", "count": len(schemas)}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.post("/retrieve", response_model=LLMResponse)
async def fetch_response(payload: RetrieveQuery = Depends()):
    
    """
    Retrieves relevant context from the database, passes it to the LLM with the user's query,
    and returns the generated response. Also stores the user message and bot reply.
    """
    query = payload.query

    try:
        # 1. Retrieve relevant context from the vector database
        relevant_schema = await query_schema(query)  # List of dicts from MongoDB
         
        # 2. Get the initialized LLM
        llm = get_llm()

        # 3. Format context for clarity
        formatted_context = "\n\n".join(
            f"Document {idx+1}:\n" + "\n".join([f"• {k}: {v}" for k, v in doc.items()])
            for idx, doc in enumerate(relevant_schema)
        )

        # 4. Construct an enhanced, descriptive prompt
        final_prompt = (
            f"You are a data analyst assistant. A user has asked a question about some JSON documents.\n\n"
            f"The user's query is:\n\"{query}\"\n\n"
            f"Below are parts of documents retrieved from the database:\n\n"
            f"{formatted_context}\n\n"
            f"Your task:\n"
            f"1. Identify and describe the purpose of the keys (fields) in these documents.\n"
            f"2. Explain what each field likely represents based on the field names and values.\n"
            f"3. If possible, relate these descriptions to the user’s query.\n"
            f"4. If the query is directly answerable from the context, answer it concisely.\n"
            f"5. Otherwise, provide a helpful explanation based on the schema.\n"
        )

        # 5. Query the LLM
        llm_response = llm.invoke(final_prompt)

        return {"response": llm_response}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error during LLM inference: {e}")

@router.post("/debug-retrieval")
async def debug_retrieval(payload: RetrieveQuery = Depends()):
    """
    This endpoint is for debugging only. It bypasses the LLM and returns
    the raw documents retrieved from the vector search.
    """
    query = payload.query
    retrieved_docs = await query_schema(query)
    for doc in retrieved_docs:
        if '_id' in doc and isinstance(doc['_id'], ObjectId):
            doc['_id'] = str(doc['_id'])
    # This will be automatically converted to JSON by FastAPI
    return {"query": query, "retrieved": retrieved_docs}