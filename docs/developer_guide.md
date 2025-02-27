# SQL Data Chat Agent Developer Guide

## Development Environment

### Local Development Setup

1. Follow the [Installation Guide](installation.md) to set up the basic environment
2. Additional developer tools:
   ```bash
   pip install pytest pytest-cov black isort mypy
   ```
3. Set up pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Development Environment Configuration

For an optimal development experience, configure your environment with:

1. **IDE Configuration**:
   - **VS Code**: Use the Python extension with pylance for improved type checking
   - **PyCharm**: Enable type checking and linting integration
   - **Recommended settings**:
     ```json
     {
       "python.linting.enabled": true,
       "python.linting.mypyEnabled": true,
       "python.formatting.provider": "black",
       "editor.formatOnSave": true,
       "python.linting.pylintEnabled": true
     }
     ```

2. **Environment Variables for Development**:
   Create a `.env.dev` file with development-specific settings:
   ```
   # Development settings
   LOG_LEVEL=DEBUG
   DATABASE=sqlite:///data/dev.db
   RELOAD=True
   ```

   Load this file when running in development:
   ```bash
   export $(grep -v '^#' .env.dev | xargs)
   ```

3. **Git Hooks**:
   The pre-commit configuration includes:
   - Code formatting with black
   - Import sorting with isort
   - Type checking with mypy
   - Linting with pylint
   - Checking for secrets and large files

## Project Structure

The SQL Data Chat Agent follows a modular architecture:

```
app/
├── __init__.py
├── main.py                  # Application entry point
├── api/                     # API endpoints
│   ├── __init__.py
│   ├── dependency.py        # Dependency injection
│   └── v1/                  # API version 1
│       ├── __init__.py
│       ├── router.py        # Main router
│       └── endpoints/       # API endpoints
├── core/                    # Core application components
│   ├── __init__.py
│   └── config.py            # Configuration settings
├── models/                  # Data models
│   ├── __init__.py
│   └── agent.py             # Agent request/response models
├── services/                # Business logic services
│   ├── __init__.py
│   ├── agent.py             # Agent service
│   ├── react_agent.py       # ReAct agent implementation
│   └── indexer.py           # Document indexing service
└── utils/                   # Utility functions
    ├── __init__.py
    └── logger.py            # Logging configuration
```

### Directory Structure Details

#### `app/main.py`

The entry point for the application. This file:
- Creates the FastAPI application
- Configures middleware
- Includes API routers
- Sets up the health check endpoint
- Initializes core services

#### `app/api/`

Contains API routes and endpoint implementations:
- `dependency.py`: Defines dependency injection for services
- `v1/router.py`: Main router that includes all endpoint routers
- `v1/endpoints/`: Individual endpoint implementations (agent, document, etc.)

#### `app/core/`

Core application components:
- `config.py`: Configuration settings using Pydantic BaseSettings

#### `app/models/`

Pydantic models for request/response objects:
- `agent.py`: Models for agent requests and responses

#### `app/services/`

Business logic implementations:
- `agent.py`: Main agent service orchestrating the conversation flow
- `react_agent.py`: Implementation of the ReAct agent pattern
- `indexer.py`: Document indexing and retrieval service

#### `app/utils/`

Utility functions and helpers:
- `logger.py`: Logging configuration and utilities

### Code Organization Principles

The codebase follows these organizational principles:

1. **Separation of Concerns**: Each module has a clearly defined responsibility
2. **Dependency Injection**: Services are injected rather than imported directly
3. **Configuration as Code**: Settings are defined as Pydantic models
4. **Interface Segregation**: APIs expose only what clients need
5. **Domain-Driven Design**: Organization around business capabilities

## Key Components

### Agent Service

The `AgentService` class in `app/services/agent.py` is the central component of the application. It orchestrates:

1. Natural language processing
2. Tool selection and execution
3. Response generation

Key methods:
- `process_question()`: Process a question and return a complete response
- `stream_question()`: Process a question and stream the response
- `_create_agent()`: Create the LangGraph agent

#### Agent Service Implementation

```python
class AgentService:
    def __init__(self, indexer: IndexerService):
        # Initialization code - sets up LLM, tools, and agent
        self.llm = settings.llm
        self.indexer = indexer
        self.db = SQLDatabase.from_uri(settings.database)
        self.sql_toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.sql_tools = self.sql_toolkit.get_tools()
        self.retriver_tool = self._create_retriver_tool()
        self.tools = self.sql_tools + [self.retriver_tool]
        self.agent_executor = self._create_agent()
```

Key components of the implementation:

1. **Tool Creation**: The agent creates tools for SQL interaction and document retrieval
2. **Agent Configuration**: The agent is configured with system prompts and tools
3. **Question Processing**: Methods for processing questions synchronously or streaming
4. **Error Handling**: Robust error handling to ensure graceful failure modes

#### Agent Service Extension Points

To extend the `AgentService`:

1. Add new tool methods using the `_create_X_tool()` pattern
2. Modify the system message to alter agent behavior
3. Add additional processing steps before or after agent execution
4. Implement custom result formatting

### ReAct Agent

The ReAct (Reasoning and Acting) agent implementation in `app/services/react_agent.py` provides the core conversational AI functionality using LangGraph. This follows a deliberate reasoning approach where the agent:

1. Analyzes the question
2. Plans the approach
3. Executes the necessary tools
4. Synthesizes the results

#### ReAct Implementation Details

The ReAct agent is implemented using LangGraph's state-based agent framework:

1. **State Definition**:
   ```python
   class AgentState(TypedDict):
       messages: Annotated[Sequence[BaseMessage], add_messages]
       is_last_step: IsLastStep
       remaining_steps: RemainingSteps
       structured_response: StructuredResponse
   ```

2. **Graph Construction**:
   ```python
   def create_react_agent(...):
       # Define state schema
       # Create agent executor
       # Set up the graph structure for reasoning and acting
   ```

3. **Reasoning Process**:
   The agent follows a ReAct pattern:
   - Reason about the question and required information
   - Act by selecting and using appropriate tools
   - Observe the results of tool execution
   - Continue reasoning until a satisfactory answer is reached

#### ReAct Agent Customization

The ReAct agent can be customized at several levels:

1. **System Prompt**: Modify the prompt template to change agent behavior
2. **Tool Availability**: Add or remove tools to change agent capabilities
3. **Reasoning Steps**: Adjust the maximum number of reasoning steps
4. **Output Parsing**: Customize how tool outputs are parsed and presented

### SQL Toolkit

The SQL toolkit from LangChain provides tools for interacting with the database:

- `sql_db_list_tables`: List all tables in the database
- `sql_db_schema`: Get the schema of a table
- `sql_db_query`: Execute a SQL query

#### SQL Toolkit Configuration

The SQL toolkit is configured in the `AgentService`:

```python
self.db = SQLDatabase.from_uri(settings.database)
self.sql_toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
self.sql_tools = self.sql_toolkit.get_tools()
```

This creates a set of tools that the agent can use to interact with the database.

#### SQL Toolkit Security Considerations

The SQL toolkit includes several security features:

1. **Read-Only Access**: By default, only SELECT queries are allowed
2. **Query Validation**: Queries are validated before execution
3. **Parameter Binding**: Values are bound as parameters to prevent SQL injection
4. **Error Handling**: Database errors are caught and reported safely

### Indexer Service

The `IndexerService` class manages:

1. Initializes the embedding model
2. Sets up the vector store
3. Configures text splitting for document processing

The service works as follows:
- Setting up the embedding model with Azure OpenAI
- Initializing the ChromaDB vector store
- Configuring text splitting for document processing

#### Document Processing Pipeline

The complete document processing pipeline includes:
1. **Document Loading**: Loading and parsing document files
2. **Text Splitting**: Splitting documents into manageable chunks
3. **Embedding Generation**: Converting text chunks to vector representations
4. **Storage**: Storing embeddings in the vector store

#### Indexer Service Implementation

```python
class IndexerService:
    def __init__(self):
        self.vector_store: Optional[Chroma] = None
        self.embedding_model: Optional[AzureOpenAIEmbeddings] = None
        self.text_splitter: Optional[RecursiveCharacterTextSplitter] = None
        self._initialize()
```

### Custom Document Processing

Implementing custom document processing:

```python
from langchain_core.documents import Document
from app.services.indexer import IndexerService

class DocumentProcessor:
    """Custom document processor for specialized content."""
    
    def __init__(self, indexer: IndexerService):
        self.indexer = indexer
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    async def process_document(self, documents: List[Document]) -> int:
        """Process a document and add it to the vector store."""
        # Split documents into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        # Add to vector store
        await self.indexer.add_documents(chunks)
        
        return len(chunks)
```

## Extending the Agent

### Adding New Tools

To add a new tool to the agent:

1. Create a new tool function using the LangChain `@tool` decorator:
   ```python
   from langchain_core.tools import tool

   @tool
   def new_tool(argument: str) -> str:
       """
       Tool description that explains what the tool does and when to use it.
       
       Args:
           argument: Description of the argument
           
       Returns:
           Description of the return value
       """
       # Tool implementation
       return result
   ```

2. Add the tool to the agent's tools list in `AgentService.__init__`:
   ```python
   self.new_tool = self._create_new_tool()
   self.tools = self.sql_tools + [self.retriver_tool, self.new_tool]
   ```

#### Tool Implementation Best Practices

1. **Clear Documentation**: Provide clear descriptions that help the agent understand when and how to use the tool
2. **Type Annotations**: Use proper type annotations for arguments and return values
3. **Error Handling**: Implement robust error handling within the tool
4. **Async Support**: Consider implementing async versions of tools for better performance

#### Example: Adding a Resource Tagging Tool

```python
@tool
async def get_resource_tags(resource_id: str) -> str:
    """
    Retrieve all tags associated with an Azure resource.
    Use this tool when you need to find metadata or categorization information about a specific resource.
    
    Args:
        resource_id: The full Azure resource ID
        
    Returns:
        A dictionary of tag names and values associated with the resource
    """
    try:
        # Implementation to fetch resource tags
        # This could use Azure SDK or a database query
        tags = await fetch_resource_tags(resource_id)
        return json.dumps(tags)
    except Exception as e:
        return f"Error retrieving tags: {str(e)}"
```

### Customizing the Agent

To customize the agent's behavior:

1. Modify the system message in `AgentService._create_agent()` to change the agent's instructions and capabilities
2. Adjust the ReAct agent creation parameters in `create_react_agent()` to change the agent's reasoning approach
3. Update the model configuration in `app/core/config.py` to use different language models

#### System Message Customization

The system message defines the agent's personality, capabilities, and instructions:

```python
system_message = """You are a helpful and knowledgeable assistant with access to various tools. Your goal is to provide accurate and helpful responses to user questions by using the appropriate tools.

**You have access to the following tools:**
1. **SQL Database Tools**
2. **Document Retrieval Tool**

**When using SQL tools:**
- Always start by exploring the available tables using the `sql_db_list_tables` tool. 
- Then examine the schema of relevant tables using the `sql_db_schema` tool.
- Finally, use `sql_db_query` to run a query and get the answer.
...
"""
```

Guidelines for customizing the system message:

1. Keep instructions clear and concise
2. Provide specific guidance on tool selection
3. Include examples of good and bad behavior
4. Define the tone and style of responses
5. Set boundaries on what the agent should not do

#### Agent Parameters Customization

The agent creation function accepts several parameters that control behavior:

```python
agent = create_react_agent(
    model=self.llm,
    tools=self.tools,
    prompt=system_message,
    # checkpointer=self.memory,
)
```

Additional parameters can be added to customize behavior:

- `max_iterations`: Maximum number of reasoning steps
- `output_parser`: Custom parser for structuring output
- `handle_tool_errors`: Strategy for handling tool execution errors

### Adding New Data Sources

To add a new data source:

1. Create a new service class for the data source
2. Implement the necessary methods for retrieving data
3. Create a tool function that uses the service
4. Add the tool to the agent's tools list

#### Example: Adding a Time Series Database

```python
# 1. Create a service class
class TimeSeriesService:
    def __init__(self, connection_string: str):
        self.client = connect_to_timeseries_db(connection_string)
    
    async def query_metrics(self, metric: str, start_time: str, end_time: str) -> Dict:
        # Implementation to query time series data
        return await self.client.query(metric, start_time, end_time)

# 2. Register in dependency injection
def get_timeseries_service():
    return TimeSeriesService(settings.timeseries_connection)

# 3. Create a tool
@tool
async def query_time_series(metric: str, start_time: str, end_time: str) -> str:
    """
    Query time series metrics from our monitoring system.
    Use this tool when you need historical performance data or metrics.
    
    Args:
        metric: The name of the metric to query
        start_time: Start time in ISO format
        end_time: End time in ISO format
        
    Returns:
        Time series data for the requested metric and time range
    """
    service = get_timeseries_service()
    result = await service.query_metrics(metric, start_time, end_time)
    return json.dumps(result)

# 4. Add to AgentService
self.timeseries_tool = query_time_series
self.tools = self.sql_tools + [self.retriver_tool, self.timeseries_tool]
```

## Performance Optimization

### Query Efficiency

To improve database query performance:

1. Use appropriate indexes in your database
2. Optimize the SQL queries generated by the agent
3. Consider caching frequently accessed data

#### Database Indexing

For tables that are frequently queried:

```sql
-- Example: Add indexes to commonly queried columns
CREATE INDEX idx_resources_name ON resources(name);
CREATE INDEX idx_costs_date ON costs(date);
CREATE INDEX idx_resources_type ON resources(resource_type);
```

#### Query Generation Optimization

To help the agent generate more efficient queries:

1. Update the system message with query efficiency guidelines
2. Implement a query review step in the agent's workflow
3. Add a post-processing filter for generated queries

Example system message addition:
```
When generating SQL queries:
- Use appropriate WHERE clauses to filter data early
- Select only necessary columns
- Limit result sets when appropriate
- Use joins efficiently by checking for proper relationships
- Consider using aggregation in the database rather than in post-processing
```

#### Result Caching

For frequently accessed data that doesn't change often:

```python
from functools import lru_cache

class CachingService:
    @lru_cache(maxsize=100)
    async def get_table_schema(self, table_name: str) -> str:
        # Implementation to get schema
        return schema
```

### Memory Management

The agent can maintain conversation memory:

1. Uncomment the memory-related code in `AgentService.__init__` and `process_question()`
2. Implement persistence for the memory if needed
3. Consider memory pruning for long conversations

#### Memory Implementation

```python
from langgraph.checkpoint.memory import MemorySaver

class AgentService:
    def __init__(self, indexer: IndexerService):
        # Other initialization code...
        self.memory = MemorySaver()
        self.agent_executor = self._create_agent()
        
    async def process_question(self, question: str, thread_id: str = None) -> Dict[str, Any]:
        if not thread_id:
            thread_id = "default"
            
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            messages = [("human", question)]
            result = await self.agent_executor.ainvoke(
                {"messages": messages}, 
                config
            )
            return result["messages"][-1].content
        except Exception as e:
            # Error handling
```

#### Persistent Memory

For persistent memory across application restarts:

```python
from langgraph.checkpoint.sqlite import SqliteSaver

class AgentService:
    def __init__(self, indexer: IndexerService):
        # Create a persistent memory store
        self.memory = SqliteSaver("memory.db")
        # Rest of initialization
```

#### Memory Pruning

For managing long conversations:

```python
def prune_memory(thread_id: str, max_messages: int = 10):
    """Prune the conversation history to keep only recent messages."""
    # Implementation to retrieve memory
    # Truncate to max_messages
    # Save back to memory store
```

## Testing

### Unit Tests

Run unit tests with:

```bash
pytest tests/unit/
```

#### Writing Effective Unit Tests

Example unit test for the AgentService:

```python
import pytest
from unittest.mock import MagicMock, patch
from app.services.agent import AgentService
from app.services.indexer import IndexerService

@pytest.fixture
def mock_indexer():
    indexer = MagicMock(spec=IndexerService)
    indexer.vector_store = MagicMock()
    return indexer

@pytest.fixture
def agent_service(mock_indexer):
    with patch('app.services.agent.SQLDatabase'), \
         patch('app.services.agent.SQLDatabaseToolkit'), \
         patch('app.services.agent.create_react_agent'):
        return AgentService(mock_indexer)

def test_process_question(agent_service):
    # Mock the agent executor
    agent_service.agent_executor.ainvoke = MagicMock()
    agent_service.agent_executor.ainvoke.return_value = {
        "messages": [("ai", "Test response")]
    }
    
    # Test the method
    result = await agent_service.process_question("Test question")
    
    # Assertions
    assert result == "Test response"
    agent_service.agent_executor.ainvoke.assert_called_once()
```

### Integration Tests

Run integration tests with:

```bash
pytest tests/integration/
```

#### Writing Integration Tests

Example integration test that tests the API:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_agent_endpoint():
    response = client.post(
        "/v1/agent",
        json={"question": "What tables are in the database?"}
    )
    assert response.status_code == 200
    assert isinstance(response.text, str)
    assert len(response.text) > 0
```

### Test Coverage

Generate test coverage reports with:

```bash
pytest --cov=app tests/
```

To generate a detailed HTML coverage report:

```bash
pytest --cov=app --cov-report=html tests/
```

#### Coverage Goals

Aim for these coverage targets:
- Core services: >90% coverage
- API endpoints: >85% coverage
- Utility functions: >80% coverage
- Overall: >85% coverage

## Deployment

### Docker Deployment

A Dockerfile is provided for containerized deployment:

```bash
docker build -t sql-chat-agent .
docker run -p 8000:8000 --env-file .env sql-chat-agent
```

#### Docker Compose Setup

For a complete deployment with dependencies:

```yaml
# docker-compose.yml
version: '3'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    depends_on:
      - db
      
  db:
    image: postgres:14
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: azure_data
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Cloud Deployment

For cloud deployment, consider:

1. Azure App Service
2. Azure Container Instances
3. Kubernetes

#### Azure App Service Deployment

1. Create an App Service Plan:
   ```bash
   az appservice plan create --name sqlchat-plan --resource-group myResourceGroup --sku B1 --is-linux
   ```

2. Create a Web App:
   ```bash
   az webapp create --resource-group myResourceGroup --plan sqlchat-plan --name sqlchat-app --deployment-container-image-name your-acr.azurecr.io/sql-chat-agent:latest
   ```

3. Configure environment variables:
   ```bash
   az webapp config appsettings set --resource-group myResourceGroup --name sqlchat-app --settings @env.json
   ```

#### Kubernetes Deployment

1. Create Kubernetes manifests:

   **deployment.yaml**:
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: sql-chat-agent
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: sql-chat-agent
     template:
       metadata:
         labels:
           app: sql-chat-agent
       spec:
         containers:
         - name: sql-chat-agent
           image: your-registry/sql-chat-agent:latest
           ports:
           - containerPort: 8000
           envFrom:
           - configMapRef:
               name: sql-chat-config
           - secretRef:
               name: sql-chat-secrets
   ```

   **service.yaml**:
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: sql-chat-service
   spec:
     selector:
       app: sql-chat-agent
     ports:
     - port: 80
       targetPort: 8000
     type: ClusterIP
   ```

   **ingress.yaml**:
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: sql-chat-ingress
   spec:
     rules:
     - host: sqlchat.example.com
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: sql-chat-service
               port:
                 number: 80
   ```

2. Apply the manifests:
   ```bash
   kubectl apply -f kubernetes/
   ```

### Monitoring

Set up monitoring using:

1. Application logs in the `logs` directory
2. Azure Application Insights
3. Prometheus and Grafana

#### Azure Application Insights Integration

1. Add Application Insights to your project:
   ```bash
   pip install opencensus-ext-azure
   ```

2. Configure in code:
   ```python
   from opencensus.ext.azure.log_exporter import AzureLogHandler

   logger.addHandler(AzureLogHandler(
       connection_string='InstrumentationKey=00000000-0000-0000-0000-000000000000')
   )
   ```

#### Prometheus Metrics

1. Add Prometheus metrics to FastAPI:
   ```bash
   pip install prometheus-fastapi-instrumentator
   ```

2. Configure in code:
   ```python
   from prometheus_fastapi_instrumentator import Instrumentator

   def create_application():
       application = FastAPI(...)
       Instrumentator().instrument(application).expose(application)
       return application
   ```

## Security Considerations

1. **API Security**: Implement authentication and authorization

   Example using FastAPI security:
   ```python
   from fastapi.security import APIKeyHeader
   from fastapi import Security, HTTPException, Depends

   api_key_header = APIKeyHeader(name="X-API-Key")

   async def get_api_key(api_key: str = Security(api_key_header)):
       if api_key != settings.api_key:
           raise HTTPException(status_code=403, detail="Invalid API Key")
       return api_key

   @router.post("", dependencies=[Depends(get_api_key)])
   async def agent(request: AgentProcessingRequest, agent: AgentService = Depends(get_agent)):
       # Endpoint implementation
   ```

2. **Database Access**: Use read-only credentials for the database

   Example connection string setup:
   ```
   DATABASE=postgresql://readonly_user:password@host:port/dbname
   ```

   Ensure the database user has only SELECT permissions:
   ```sql
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
   REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM readonly_user;
   ```

3. **Environment Variables**: Securely manage environment variables

   Use a secrets management service in production:
   ```python
   from azure.keyvault.secrets import SecretClient
   from azure.identity import DefaultAzureCredential

   credential = DefaultAzureCredential()
   client = SecretClient(vault_url="https://your-vault.vault.azure.net/", credential=credential)
   
   # Get a secret
   api_key = client.get_secret("openai-api-key").value
   ```

4. **Input Validation**: Validate all user inputs

   Use Pydantic for request validation:
   ```python
   class AgentProcessingRequest(BaseModel):
       question: str
       thread_id: Optional[str] = None
       
       @validator('question')
       def question_must_not_be_empty(cls, v):
           if not v.strip():
               raise ValueError('Question cannot be empty')
           return v
   ```

5. **Rate Limiting**: Implement rate limiting to prevent abuse

   Example using slowapi:
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address

   limiter = Limiter(key_func=get_remote_address)

   @router.post("")
   @limiter.limit("10/minute")
   async def agent(request: AgentProcessingRequest, agent: AgentService = Depends(get_agent)):
       # Endpoint implementation
   ```

## Advanced Features

### Conversation Memory

Implementing persistent conversation memory:

```python
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    messages = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# Usage in service
class ConversationService:
    def __init__(self):
        self.engine = create_engine(settings.database)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_conversation(self, conversation_id: str, user_id: str) -> List[Dict]:
        with self.Session() as session:
            conversation = session.query(Conversation).filter_by(id=conversation_id, user_id=user_id).first()
            if conversation:
                return json.loads(conversation.messages)
            return []
    
    def save_conversation(self, conversation_id: str, user_id: str, messages: List[Dict]):
        with self.Session() as session:
            conversation = session.query(Conversation).filter_by(id=conversation_id, user_id=user_id).first()
            if conversation:
                conversation.messages = json.dumps(messages)
                conversation.updated_at = datetime.datetime.utcnow()
            else:
                conversation = Conversation(
                    id=conversation_id,
                    user_id=user_id,
                    messages=json.dumps(messages)
                )
                session.add(conversation)
            session.commit()
```

### Query Analytics

Implementing query analytics to improve performance:

```python
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import json

Base = declarative_base()

class QueryAnalytics(Base):
    __tablename__ = "query_analytics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
class AnalyticsService:
    def __init__(self):
        self.engine = create_engine(settings.analytics_database)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def record_query(self, question: str, generated_sql: str, execution_time_ms: int, token_count: int = None):
        """Record analytics for a query."""
        with self.Session() as session:
            record = QueryAnalytics(
                question=question,
                generated_sql=generated_sql,
                execution_time_ms=execution_time_ms,
                token_count=token_count
            )
            session.add(record)
            session.commit()
    
    def get_performance_metrics(self, days: int = 7):
        """Get performance metrics for recent queries."""
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        with self.Session() as session:
            results = session.query(
                func.avg(QueryAnalytics.execution_time_ms),
                func.min(QueryAnalytics.execution_time_ms),
                func.max(QueryAnalytics.execution_time_ms),
                func.count(QueryAnalytics.id)
            ).filter(QueryAnalytics.timestamp >= cutoff).first()
            
            return {
                "avg_execution_time_ms": results[0],
                "min_execution_time_ms": results[1],
                "max_execution_time_ms": results[2],
                "query_count": results[3]
            }
``` 