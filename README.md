# Prompt2Schema Backend

An intelligent schema recommendation system that analyzes user prompts and returns the most relevant schema from a curated database. Built with FastAPI, MongoDB, Pinecone, and advanced LLM integration for semantic understanding and retrieval.

## Overview

Prompt2Schema is a backend service that combines vector similarity search with traditional database operations to provide intelligent schema recommendations. The system uses semantic embeddings to understand user queries and matches them with the most appropriate schemas from predefined collections.

## Architecture

### Backend Stack
- **FastAPI**: Modern, high-performance web framework for building APIs
- **MongoDB**: Document database for schema storage and management
- **Pinecone**: Vector database for semantic similarity search
- **LangChain**: LLM integration and prompt management
- **Sentence Transformers**: Text embedding generation
- **Nebius AI**: LLM provider using Mistral-Nemo-Instruct-2407

### System Components

```
backend/
├── main.py                          # FastAPI application entry point
├── app/
│   ├── router/
│   │   └── routes.py               # API endpoint definitions
│   ├── model/
│   │   ├── schema.py               # Pydantic data models
│   │   └── llm.py                  # LLM configuration and wrapper
│   ├── database/
│   │   ├── mongodb.py              # MongoDB connection and management
│   │   └── pinecone.py             # Pinecone vector database setup
│   └── utils/
│       └── crud_ops.py             # Database operations and query logic
└── requirements.txt                # Python dependencies
```

## Features

### Core Functionality
- **Schema Upload**: Store JSON schemas in organized collections (sales, marketing, finance, hr)
- **Intelligent Retrieval**: Semantic search using vector embeddings and LLM analysis
- **Contextual Responses**: AI-powered schema explanation and field analysis
- **Debug Mode**: Raw document retrieval for debugging and testing

### API Endpoints

#### Health Check
```
GET /
```
Returns backend status confirmation.

#### Schema Upload
```
POST /upload
```
Upload single or multiple JSON schemas to specified collections.

**Request Body:**
```json
{
  "collection_name": "string",
  "schema_data": {} | [{}]
}
```

#### Schema Retrieval
```
POST /retrieve
```
Query for relevant schemas using natural language prompts.

**Request Body:**
```json
{
  "query": "string (3-400 characters)"
}
```

**Response:**
```json
{
  "response": "AI-generated schema analysis and explanation"
}
```

#### Debug Retrieval
```
POST /debug-retrieval
```
Returns raw retrieved documents without LLM processing for debugging purposes.

## Installation & Setup

### Prerequisites
- Python 3.8+
- MongoDB (local or remote instance)
- Pinecone account and API key
- Nebius AI API key

### Environment Configuration

Create a `.env` file in the backend directory:

```env
# Nebius AI Configuration
NEBIUS_API_KEY=your_nebius_api_key

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_pinecone_index_name

# MongoDB Configuration (default: localhost:27017)
MONGO_URL=mongodb://localhost:27017
```

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Pramodredd/Prompt2Schema.git
   cd Prompt2Schema/backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up MongoDB:**
   - Install and start MongoDB locally, or configure remote connection
   - The application will automatically create the database `prompt2schema_db`
   - Default collections: `sales`, `marketing`, `finance`, `hr`

4. **Configure Pinecone:**
   - Create a Pinecone account and project
   - Create an index with appropriate dimensions for sentence-transformers model
   - Add credentials to `.env` file

5. **Run the application:**
   ```bash
   python main.py
   ```

The server will start on `http://localhost:8000`.

## API Testing with Swagger UI

The backend provides interactive API documentation through FastAPI's built-in Swagger UI:

```
http://localhost:8000/docs
```

### Using Swagger UI

1. **Navigate to the docs URL** after starting the server
2. **Explore available endpoints** with detailed request/response schemas
3. **Test API calls directly** using the "Try it out" functionality
4. **View response codes and examples** for each endpoint

### Example Workflow in Swagger UI

1. **Upload Schema:**
   - Use `/upload` endpoint
   - Select collection (sales, marketing, finance, hr)
   - Provide JSON schema data

2. **Query Schema:**
   - Use `/retrieve` endpoint
   - Enter natural language query
   - Receive AI-generated schema analysis

3. **Debug Results:**
   - Use `/debug-retrieval` for raw document inspection
   - Compare with `/retrieve` for AI processing differences

## Technical Implementation

### Vector Search Pipeline

1. **Query Processing:**
   - User query is embedded using sentence-transformers/all-MiniLM-L6-v2
   - Vector search performed against Pinecone index
   - Top-k relevant documents retrieved with metadata

2. **Document Retrieval:**
   - Original document IDs extracted from Pinecone metadata
   - Full documents fetched from MongoDB collections
   - Concurrent database operations for performance

3. **LLM Processing:**
   - Retrieved schemas formatted as context
   - Enhanced prompt engineering for field analysis
   - Mistral-Nemo model generates explanatory responses

### Database Design

#### MongoDB Collections
- **sales**: Sales-related schemas and data models
- **marketing**: Marketing campaign and analytics schemas
- **finance**: Financial reporting and transaction schemas  
- **hr**: Human resources and employee data schemas

#### Pinecone Index Structure
- **Vectors**: Sentence embeddings of schema content
- **Metadata**: Collection name and original MongoDB document ID
- **Similarity Search**: Cosine similarity for semantic matching

## Configuration Options

### MongoDB Settings
```python
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "prompt2schema_db" 
COLLECTIONS = ["sales", "marketing", "finance", "hr"]
```

### LLM Configuration
- **Model**: mistralai/Mistral-Nemo-Instruct-2407
- **Provider**: Nebius AI
- **Context Window**: Optimized for schema analysis
- **Response Format**: Structured field explanations

### Vector Search Parameters
- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Top-k Results**: 1 (configurable in crud_ops.py)
- **Include Metadata**: True for document retrieval

## Development

### Adding New Collections
1. Update `COLLECTIONS` list in `mongodb.py`
2. Restart application to auto-create collections
3. Upload schemas via `/upload` endpoint

### Customizing LLM Behavior
1. Modify prompts in `routes.py` `/retrieve` endpoint
2. Adjust model parameters in `llm.py`
3. Update response formatting logic

### Performance Optimization
- Concurrent database operations implemented in `crud_ops.py`
- Connection pooling handled by Motor (async MongoDB driver)
- Vector search results cached in Pinecone

## Dependencies

### Core Framework
- **FastAPI (0.116.1)**: Web framework and API routing
- **Uvicorn (0.35.0)**: ASGI server for production deployment
- **Pydantic (2.11.7)**: Data validation and serialization

### Database & Vector Search
- **Motor (3.7.1)**: Async MongoDB driver
- **PyMongo (4.13.2)**: MongoDB operations
- **Pinecone (7.3.0)**: Vector database client

### AI & ML Libraries
- **LangChain (0.3.26)**: LLM integration framework
- **Sentence-Transformers (5.0.0)**: Text embedding models
- **OpenAI (1.97.0)**: API client for LLM providers
- **Transformers (4.53.2)**: Hugging Face model support

### Utility Libraries
- **Python-dotenv (1.1.1)**: Environment variable management
- **Requests (2.32.4)**: HTTP client for API calls

## Deployment Considerations

### Production Settings
- Update CORS origins from `["*"]` to specific domains
- Configure MongoDB connection pooling
- Set up proper environment variable management
- Implement logging and monitoring

### Scaling Options
- Deploy with multiple Uvicorn workers
- Use MongoDB replica sets for high availability
- Implement Redis caching for frequent queries
- Set up load balancing for API endpoints

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed:**
   - Verify MongoDB is running on specified port
   - Check network connectivity and firewall settings
   - Validate connection string format

2. **Pinecone Authentication Error:**
   - Confirm API key is correct and active
   - Verify index name matches Pinecone dashboard
   - Check environment variable loading

3. **LLM Request Timeout:**
   - Validate Nebius AI API key
   - Check network connectivity to API endpoint
   - Monitor rate limits and quota usage
