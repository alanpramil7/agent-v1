# SQL Data Chat Agent Architecture

## System Overview

The SQL Data Chat Agent is built using a modular architecture that combines several key components:

1. **FastAPI Web Application** - Provides the HTTP interface and handles request routing
2. **LangGraph Agent Framework** - Powers the core conversational AI capabilities 
3. **SQL Database Interface** - Manages connections and queries to the underlying database
4. **Document Retrieval System** - Enables access to unstructured knowledge sources
5. **Azure OpenAI Integration** - Provides the language model capabilities

### Architectural Principles

The architecture follows several key principles:

- **Separation of Concerns**: Each component has a distinct responsibility, making the system easier to maintain and extend
- **Loose Coupling**: Components interact through well-defined interfaces, enabling independent development and testing
- **Statelessness**: API endpoints are designed to be stateless for scalability, with conversation state managed explicitly
- **Extensibility**: The design allows for easily adding new capabilities or data sources
- **Observability**: Comprehensive logging and monitoring are built into each component

### High-Level Architecture Diagram

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│    Client       │ ◄─────► │    FastAPI      │ ◄─────► │  Agent Service  │
│    Application  │         │    Web Server   │         │                 │
│                 │         │                 │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                                               │
                                                               │
                                                               ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│   Azure OpenAI  │ ◄─────► │   LangGraph     │ ◄─────► │  Tool Executor  │
│   Service       │         │   Framework     │         │                 │
│                 │         │                 │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                                               │
                                                               │
                                                               ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│  SQL Database   │ ◄─────► │  SQL Toolkit    │         │  Vector Store   │
│                 │         │                 │         │  (ChromaDB)     │
│                 │         │                 │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

## Component Architecture

### API Layer

The application exposes its functionality through a RESTful API built with FastAPI. The API provides endpoints for:

- Processing queries (`/v1/agent`)
- Streaming responses (`/v1/agent/stream`)
- Health checking (`/check-health`)

The API layer handles HTTP request validation, error handling, and response formatting.

#### Endpoint Implementation Details

1. **Agent Endpoint** (`/v1/agent`)
   - Accepts POST requests with a JSON payload containing the user's question
   - Validates the request using Pydantic models
   - Delegates processing to the AgentService
   - Returns a synchronous response with the agent's answer

2. **Streaming Endpoint** (`/v1/agent/stream`)
   - Accepts POST requests with the same payload format
   - Uses FastAPI's streaming response capability to deliver results incrementally
   - Returns chunks of the response as they become available
   - Maintains a single connection throughout the interaction

3. **Health Check Endpoint** (`/check-health`)
   - Provides basic health and version information
   - Used for monitoring and deployment verification
   - Returns simple JSON with status and version details

#### API Security and Performance

- **CORS Middleware**: Configured to allow cross-origin requests
- **Request Validation**: Uses Pydantic for strong type checking
- **Error Handling**: Consistent error responses with appropriate HTTP status codes
- **Response Formatting**: Standardized JSON responses across endpoints
- **Async Processing**: Leverages FastAPI's asynchronous capabilities for better concurrency

### Agent Service Layer

The core of the application is the AgentService, which orchestrates the process of:

1. Receiving natural language questions
2. Planning the approach to answering (using SQL or document retrieval)
3. Generating and executing SQL queries when appropriate
4. Retrieving relevant documents when needed
5. Formulating comprehensive responses

The agent uses a ReAct (Reasoning and Acting) framework implemented with LangGraph to manage the multi-step reasoning process.

#### Agent Service Components

1. **Initialization**:
   - Sets up connections to the language model
   - Initializes the SQL toolkit with database connection
   - Creates the document retrieval tool
   - Configures the LangGraph agent with appropriate system prompts

2. **Question Processing Logic**:
   - Formats the user question into agent-compatible messages
   - Invokes the LangGraph agent to process the question
   - Extracts the final answer from the agent's response
   - Handles errors that might occur during processing

3. **Streaming Implementation**:
   - Uses LangGraph's streaming capabilities
   - Provides incremental updates during agent reasoning steps
   - Filters and formats streaming events for client consumption
   - Ensures reliable delivery of partial responses

#### Agent Execution Flow

1. **Agent receives the question**
2. **Reasoning phase**: Agent analyzes what information is needed
3. **Tool selection**: Agent chooses appropriate tool(s) for the task
4. **Tool execution**: Agent uses selected tools to gather information
5. **Response formulation**: Agent synthesizes information into an answer
6. **Result delivery**: Agent returns the final response

### SQL Integration Layer

This layer provides tools for the agent to:

- List available database tables
- Retrieve schema information
- Formulate and execute SQL queries
- Process query results

The SQL integration is implemented using SQLDatabaseToolkit from LangChain, which provides a secure, read-only interface to the database.

#### SQL Toolkit Components

1. **Database Connection**:
   - Establishes connection to the SQL database using SQLAlchemy
   - Configures connection pools for efficient resource usage
   - Supports multiple database backends (PostgreSQL, MySQL, SQLite, etc.)
   - Implements connection retry and timeout handling

2. **Schema Introspection Tool**:
   - Dynamically retrieves database structure at runtime
   - Identifies tables, columns, data types, and relationships
   - Formats schema information for LLM consumption
   - Caches schema data to improve performance

3. **Query Generation and Execution**:
   - Safely formats and executes SQL queries
   - Implements query timeout protection
   - Converts database results to Python objects
   - Formats results based on query context
   - Provides explanations of query execution details

4. **Security Measures**:
   - Enforces read-only operations
   - Prevents SQL injection through parameterized queries
   - Limits query complexity and resource usage
   - Implements query auditing for compliance

### Document Retrieval Layer

The IndexerService component manages:

- Document processing and chunking
- Vector embeddings generation
- Storage of documents in a vector store (ChromaDB)
- Similarity search for relevant content

This layer enables the agent to retrieve contextual information that might not be stored in the SQL database.

#### Document Processing Pipeline

1. **Document Ingestion**:
   - Supports multiple document formats (PDF, DOCX, etc.)
   - Chunks documents into manageable pieces
   - Handles document metadata
   - Implements deduplication strategies

2. **Embedding Generation**:
   - Uses Azure OpenAI embeddings API
   - Converts text chunks to vector representations
   - Optimizes batch processing for efficiency
   - Handles rate limiting and retries

3. **Vector Store Operations**:
   - Uses ChromaDB as the vector store
   - Implements persistent storage in the file system
   - Supports metadata filtering for refined searches
   - Optimizes for retrieval performance

4. **Retrieval Interface**:
   - Provides semantic search capabilities
   - Supports top-k document retrieval
   - Implements relevance scoring
   - Returns formatted documents with source tracking

#### Supported File Formats

The document retrieval system supports the following file types:

| Format | Description | Implementation |
|--------|-------------|----------------|
| PDF (.pdf) | Portable Document Format | Uses PyPDF for text extraction |
| Word (.docx) | Microsoft Word Documents | Uses docx2txt for text extraction |
| Text (.txt) | Plain text files | Direct text loading |
| Markdown (.md) | Markdown documentation | Direct text loading with optional formatting preservation |
| HTML (.html) | Web page content | Uses BeautifulSoup to extract and clean content |
| CSV (.csv) | Tabular data | Converts to text representation with column context |

#### Vector Store Implementation

The system uses ChromaDB for vector storage with the following configuration:

1. **Persistence**: 
   - Vectors are stored in the file system at `data/vector_store/`
   - Full persistence ensures data survives application restarts

2. **Embedding Model**:
   - Azure OpenAI embeddings model generates vector representations
   - Uses the `text-embedding-3-small` model by default
   - 1536-dimensional embedding vectors

3. **Chunking Strategy**:
   - Uses RecursiveCharacterTextSplitter for document chunking
   - Default chunk size: 2000 characters
   - Chunk overlap: 400 characters
   - Prioritized splitting by paragraph breaks, then sentences, then words

4. **Search Configuration**:
   - Similarity search using cosine similarity
   - Default retrieval: top 5 most relevant documents
   - Supports filtering by document type and metadata

5. **Performance Optimization**:
   - Chunking balances context preservation with retrieval precision
   - Embedding computations batched for efficiency
   - Query results cached to reduce redundant processing

#### Content Sources

The system can retrieve and index content from multiple sources:

1. **Document Files**:
   - Uploaded through the `/document` API endpoint
   - Stored in the `data/docs/` directory
   - Processed through the DocumentService

2. **Websites**:
   - Crawled via the `/website` API endpoint
   - Respects robots.txt directives
   - Extracts clean text content from HTML
   - Configurable crawl depth and URL filtering

3. **Wikis**:
   - Retrieved via the `/wiki` API endpoint
   - Supports Azure DevOps wikis
   - Authenticates with Personal Access Tokens (PAT)
   - Recursively fetches all wiki pages

#### Data Flow for Document Processing

1. **Content Receipt** → The system receives content (file upload, URL, or wiki identifier)
2. **Preprocessing** → Content is cleaned and prepared for processing
3. **Text Extraction** → Plain text is extracted from the source format
4. **Chunking** → Text is split into manageable chunks with appropriate overlap
5. **Embedding Generation** → Each chunk is converted to a vector embedding
6. **Vector Storage** → Embeddings and metadata are stored in ChromaDB
7. **Metadata Recording** → Processing history is recorded in the SQLite database

### Model Integration Layer

The system integrates with Azure OpenAI to provide:

- Natural language understanding
- Query planning and generation
- Response formulation
- Contextual reasoning

#### Azure OpenAI Integration

1. **Model Configuration**:
   - Connects to Azure OpenAI deployment
   - Configures appropriate model parameters (temperature, max tokens, etc.)
   - Implements retry logic and error handling
   - Manages API key security

2. **Prompt Engineering**:
   - Designs system prompts for agent behavior
   - Formats user questions and context
   - Structures tool inputs and outputs
   - Optimizes token usage

3. **Response Processing**:
   - Parses model outputs
   - Extracts structured information
   - Handles streaming responses
   - Formats final answers for presentation

4. **Performance Optimization**:
   - Implements caching strategies
   - Manages token budget efficiently
   - Balances response quality and latency
   - Handles rate limits and quotas

## Data Flow

1. **User Request** → The user submits a natural language question through the API
2. **Agent Planning** → The agent analyzes the question and determines the best approach
3. **Tool Selection** → The agent selects appropriate tools (SQL or document retrieval)
4. **Data Retrieval** → The agent executes the selected tools to gather information
5. **Response Generation** → The agent formulates a response based on the retrieved data
6. **Response Delivery** → The response is returned to the user via the API

### Detailed Request/Response Flow

```
User Question
    │
    ▼
┌─────────────────┐
│  FastAPI        │  1. Receives HTTP request
│  Endpoint       │  2. Validates request format
└─────────────────┘  3. Passes to Agent Service
    │
    ▼
┌─────────────────┐
│  Agent Service  │  1. Prepares question for agent
│                 │  2. Invokes LangGraph agent
└─────────────────┘  3. Handles results/errors
    │
    ▼
┌─────────────────┐
│  LangGraph      │  1. Plans reasoning steps
│  Agent          │  2. Determines needed tools
└─────────────────┘  3. Executes tools
    │
    ▼
┌─────────────────┐
│  Tool Executor  │  1. Routes to appropriate tool
│                 │  2. Executes SQL or retrieval
└─────────────────┘  3. Returns tool results
    │
    ▼
┌─────────────────┐
│  SQL/Vector     │  1. Retrieves requested data
│  Data Source    │  2. Formats results
└─────────────────┘  3. Returns to tool executor
    │
    ▼
┌─────────────────┐
│  LangGraph      │  1. Processes tool results
│  Agent          │  2. Formulates final answer
└─────────────────┘  3. Returns to Agent Service
    │
    ▼
┌─────────────────┐
│  FastAPI        │  1. Formats HTTP response
│  Endpoint       │  2. Returns to user
└─────────────────┘
    │
    ▼
User Response
```

## Technology Stack

- **Backend Framework**: FastAPI
  - Provides high-performance asynchronous API capabilities
  - Enables automatic OpenAPI documentation
  - Supports dependency injection pattern
  - Offers built-in validation via Pydantic

- **Agent Framework**: LangGraph, LangChain
  - LangGraph manages multi-step reasoning workflows
  - LangChain provides tool abstractions and integrations
  - Implements ReAct agent pattern for planning and execution
  - Offers streaming capabilities for long-running operations

- **Database Interface**: SQLAlchemy
  - Provides database-agnostic connection management
  - Supports multiple database backends
  - Offers secure query parameterization
  - Enables efficient connection pooling

- **Vector Database**: ChromaDB
  - Stores and indexes document embeddings
  - Provides efficient similarity search
  - Supports persistence across restarts
  - Offers metadata filtering capabilities

- **AI Models**: Azure OpenAI
  - Powers natural language understanding
  - Generates SQL queries from natural language
  - Formulates human-friendly responses
  - Provides reasoning capabilities for complex questions

- **Embedding Models**: Azure OpenAI (text-embedding-3-small)
  - Generates vector representations of text
  - Enables semantic search capabilities
  - Optimized for document retrieval tasks
  - Provides high-quality embeddings with dimension reduction

- **Logging**: Python logging module
  - Structured logging for all components
  - Configurable log levels
  - Rotation-based log management
  - Support for external log aggregation

- **Configuration**: Pydantic Settings
  - Type-safe configuration management
  - Environment variable integration
  - Secrets handling
  - Configuration validation 