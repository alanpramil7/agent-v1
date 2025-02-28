# API Reference

This document provides detailed API documentation for the React Agent system.

## Core Components

### AgentState

```python
class AgentState(TypedDict):
    """State management for React Agent."""
    
    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: IsLastStep
    remaining_steps: RemainingSteps
```

#### Fields
- `messages`: Sequence of messages in the conversation
- `is_last_step`: Boolean indicating if current step is last
- `remaining_steps`: Number of remaining execution steps

### StateGraph

```python
class StateGraph:
    """Graph-based workflow management."""
    
    def __init__(self, state_type: Type[TypedDict]):
        """Initialize state graph."""
        
    def add_node(self, name: str, node: Any):
        """Add node to graph."""
        
    def add_edge(self, start: str, end: str):
        """Add edge between nodes."""
        
    def compile(self, **kwargs) -> Any:
        """Compile graph into executable form."""
```

### BaseTool

```python
class BaseTool:
    """Base class for tool implementation."""
    
    name: str
    description: str
    
    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Synchronous execution."""
        
    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        """Asynchronous execution."""
```

## Core Functions

### create_react_agent

```python
def create_react_agent(
    model: Union[str, LanguageModelLike],
    tools: Sequence[BaseTool],
    prompt: Optional[str] = None,
    checkpointer: Optional[Checkpointer] = None,
) -> StateGraph:
    """
    Create a React Agent instance.
    
    Args:
        model: Language model to use
        tools: List of tools to integrate
        prompt: System prompt
        checkpointer: State persistence handler
        
    Returns:
        Compiled state graph
    """
```

### process_question

```python
async def process_question(
    question: str,
    thread_id: Optional[str] = None
) -> Any:
    """
    Process user question.
    
    Args:
        question: User's question
        thread_id: Conversation thread ID
        
    Returns:
        Agent's response
    """
```

### stream_question

```python
async def stream_question(
    question: str,
    thread_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Stream response to user question.
    
    Args:
        question: User's question
        thread_id: Conversation thread ID
        
    Yields:
        Response chunks
    """
```

## Tool APIs

### SQLDatabaseToolkit

```python
class SQLDatabaseToolkit:
    """SQL database interaction toolkit."""
    
    def __init__(self, db: SQLDatabase, llm: Any):
        """Initialize toolkit."""
        
    def get_tools(self) -> List[BaseTool]:
        """Get SQL tools."""
```

### DocumentRetrieverTool

```python
@tool
async def retrieve_documents(query: str) -> str:
    """
    Retrieve relevant documents.
    
    Args:
        query: Search query
        
    Returns:
        Retrieved documents
    """
```

## Configuration Types

### ToolConfig

```python
class ToolConfig(TypedDict):
    """Tool configuration type."""
    
    name: str
    description: str
    parameters: Dict[str, Dict[str, Any]]
```

### RunnableConfig

```python
class RunnableConfig(TypedDict):
    """Execution configuration type."""
    
    configurable: Dict[str, Any]
    recursion_limit: int
```

## Message Types

### BaseMessage

```python
class BaseMessage:
    """Base message type."""
    
    content: str
    additional_kwargs: Dict[str, Any]
```

### AIMessage

```python
class AIMessage(BaseMessage):
    """AI-generated message type."""
    
    tool_calls: Optional[List[ToolCall]]
```

### ToolMessage

```python
class ToolMessage(BaseMessage):
    """Tool execution result message type."""
    
    tool_name: str
    tool_args: Dict[str, Any]
```

## Tool Call Types

### ToolCall

```python
class ToolCall(TypedDict):
    """Tool call specification."""
    
    name: str
    arguments: Dict[str, Any]
```

## Utility Types

### Checkpointer

```python
class Checkpointer:
    """State persistence interface."""
    
    async def save(self, state: Any):
        """Save state."""
        
    async def load(self) -> Any:
        """Load state."""
```

### IsLastStep

```python
class IsLastStep(TypedDict):
    """Step limitation type."""
    
    is_last: bool
```

### RemainingSteps

```python
class RemainingSteps(TypedDict):
    """Step counter type."""
    
    remaining: int
```

## Error Types

### ToolExecutionError

```python
class ToolExecutionError(Exception):
    """Tool execution error."""
    
    tool_name: str
    error_message: str
```

### StateError

```python
class StateError(Exception):
    """State management error."""
    
    state_type: str
    error_message: str
```

## Constants

```python
# System defaults
DEFAULT_RECURSION_LIMIT: int = 25
DEFAULT_THREAD_ID: str = "default"

# Tool configuration
MAX_TOOL_STEPS: int = 10
TOOL_TIMEOUT: int = 30

# State management
MAX_MESSAGES: int = 100
MAX_MESSAGE_LENGTH: int = 4096
```

## Usage Examples

### Basic Agent Creation

```python
# Create agent
agent = create_react_agent(
    model="gpt-4",
    tools=[tool1, tool2],
    prompt="System prompt"
)

# Process question
response = await agent.process_question("User question")
```

### Streaming Response

```python
# Stream response
async for chunk in agent.stream_question("User question"):
    print(chunk)
```

### Tool Integration

```python
# Create custom tool
@tool
def custom_tool(arg: str) -> str:
    return process_arg(arg)

# Add to agent
agent = create_react_agent(
    model="gpt-4",
    tools=[custom_tool]
)
```

### State Management

```python
# Create checkpointer
checkpointer = MemoryCheckpointer()

# Create agent with state persistence
agent = create_react_agent(
    model="gpt-4",
    tools=[tool1],
    checkpointer=checkpointer
)
``` 