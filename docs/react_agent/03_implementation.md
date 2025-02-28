# React Agent Implementation Guide

This guide provides detailed instructions on how to implement and use the React Agent in your project.

## Prerequisites

Before implementing React Agent, ensure you have:

1. **Required Packages**
   - LangChain
   - LangGraph
   - Required language model (e.g., GPT-4, Claude)
   - Python 3.7+

2. **Project Setup**
   - Python environment
   - Dependencies installed
   - Access to language model API

## Basic Implementation

### 1. Creating a React Agent

```python
from langchain_core.language_models import LanguageModelLike
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph

def create_react_agent(
    model: Union[str, LanguageModelLike],
    tools: Sequence[BaseTool],
    prompt: Optional[str] = None,
    checkpointer: Optional[Checkpointer] = None,
) -> StateGraph:
    # Initialize tool node
    tool_node = ToolNode(tools)
    
    # Bind tools to model
    model = model.bind_tools(tools)
    
    # Create workflow graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    
    # Add tools if available
    if tools:
        workflow.add_node("tools", tool_node)
        workflow.set_entry_point("agent")
        
    return workflow.compile(checkpointer=checkpointer)
```

### 2. Configuring State Management

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: IsLastStep
    remaining_steps: RemainingSteps
```

### 3. Setting Up Tool Integration

```python
# Define tool
@tool
def example_tool(query: str) -> str:
    """Tool description"""
    # Tool implementation
    return result

# Create tools list
tools = [example_tool]

# Create agent with tools
agent = create_react_agent(model, tools, prompt)
```

## Advanced Implementation

### 1. Custom Tool Creation

```python
from langchain_core.tools import BaseTool

class CustomTool(BaseTool):
    name = "custom_tool"
    description = "Tool description"
    
    def _run(self, query: str) -> str:
        # Implementation
        return result
        
    async def _arun(self, query: str) -> str:
        # Async implementation
        return result
```

### 2. Workflow Customization

```python
# Custom routing logic
def custom_router(state: AgentState) -> Union[str, list]:
    last_message = state["messages"][-1]
    if custom_condition:
        return END
    return [Send("tools", [tool_call])]

# Add custom routing
workflow.add_conditional_edges(
    "agent",
    custom_router,
    path_map=["tools", END],
)
```

### 3. State Management

```python
# Custom state handler
async def handle_state(state: AgentState, config: RunnableConfig) -> AgentState:
    # Process state
    return updated_state

# Add state handler
workflow.add_node("state_handler", handle_state)
```

## Integration Examples

### 1. Basic Question-Answering

```python
# Create agent
agent = create_react_agent(model, tools, prompt)

# Process question
async def process_question(question: str):
    messages = [("human", question)]
    result = await agent.ainvoke({"messages": messages})
    return result["messages"][-1].content
```

### 2. Interactive Chat System

```python
class ChatSystem:
    def __init__(self, model, tools, prompt):
        self.agent = create_react_agent(model, tools, prompt)
        
    async def chat(self, message: str, thread_id: str = "default"):
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 10
        }
        
        messages = [("human", message)]
        result = await self.agent.ainvoke(
            {"messages": messages},
            config
        )
        
        return result["messages"][-1].content
```

### 3. Streaming Responses

```python
async def stream_response(question: str, thread_id: str = "default"):
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 25
    }
    
    messages = [("human", question)]
    
    async for event in agent.astream({"messages": messages}, config):
        if "agent" in event:
            for message in event["agent"]["messages"]:
                if message.content:
                    yield message.content
```

## Best Practices

### 1. Tool Design
- Keep tools focused and single-purpose
- Provide clear descriptions
- Handle errors gracefully
- Include type hints

### 2. State Management
- Minimize state size
- Clear state between sessions
- Handle state persistence
- Monitor step limits

### 3. Error Handling
- Implement proper error catching
- Provide meaningful error messages
- Handle tool failures
- Manage recursion limits

### 4. Performance Optimization
- Use async where possible
- Implement caching
- Monitor resource usage
- Optimize tool execution

## Common Issues and Solutions

### 1. Tool Execution Failures
```python
try:
    result = await tool.ainvoke(args)
except Exception as e:
    return handle_tool_error(e)
```

### 2. State Management Issues
```python
def clean_state(state: AgentState) -> AgentState:
    # Clean and validate state
    return cleaned_state
```

### 3. Recursion Control
```python
if state["remaining_steps"] < minimum_required_steps:
    return handle_step_limitation()
```

## Next Steps

For detailed information about available tools and their workflow, proceed to the [Tools and Workflow](./04_tools_and_workflow.md) section. For API documentation, check the [API Reference](./05_api_reference.md). 