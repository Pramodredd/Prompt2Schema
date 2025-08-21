from pydantic import BaseModel,constr
from typing import Dict, Any , Union, List

class UploadRequest(BaseModel):
    """Request model for uploading a JSON schema."""
    collection_name : str
    schema_data: Union[Dict[str, Any], List[Dict[str, Any]]]

class LLMResponse(BaseModel):
    response: str
    # convo_id: str

class RetrieveQuery(BaseModel):
    query: constr(min_length=3, max_length=400) # type: ignore
    # convo_id: str 