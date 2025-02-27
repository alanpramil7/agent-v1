from typing import Optional, Sequence, Union, cast

from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.managed import IsLastStep, RemainingSteps
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer, Send
from rich import print
from typing_extensions import Annotated, TypedDict


class AgentState(TypedDict):
    """State of the ReAct agent containing conversation history and step tracking."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: IsLastStep
    remaining_steps: RemainingSteps


def create_react_agent(
    model: Union[str, LanguageModelLike],
    tools: Sequence[BaseTool],
    prompt: Optional[str] = None,
    checkpointer: Optional[Checkpointer] = None,
) -> StateGraph:
    """Creates a ReAct agent using LangGraph and LangChain components."""
    # Setup tools
    debug: bool = False
    store: BaseStore = None
    tool_node = ToolNode(tools)
    print("*" * 20, "Tools", "*" * 20)
    print(tool_node)
    tool_calling_enabled = bool(tools)
    model = model.bind_tools(tools)

    current_model_call = 1

    def debug_print_messages(messages):
        nonlocal current_model_call
        if messages:
            print("*" * 20, f"Model call {current_model_call} with message", "*" * 20)
            print(messages)
        current_model_call += 1
        return messages

    # Create system message and model chain
    system_message = SystemMessage(content=prompt or "")
    model_runnable = (
        (lambda state: [system_message] + state["messages"])
        # | RunnableLambda(debug_print_messages)
        | model
    )

    async def call_model(state: AgentState, config: RunnableConfig) -> AgentState:
        response = cast(AIMessage, await model_runnable.ainvoke(state, config))

        # Check if we need to stop due to step limitations
        has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
        if (state.get("is_last_step", False) and has_tool_calls) or (
            "remaining_steps" in state
            and state["remaining_steps"] < (1 if not has_tool_calls else 2)
        ):
            return {
                "messages": [
                    AIMessage(
                        id=response.id,
                        content="Sorry, need more steps to process this request.",
                    )
                ]
            }
        return {"messages": [response]}

    # Create workflow graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)

    # If no tools, create a simple agent-only workflow
    if not tool_calling_enabled:
        workflow.set_entry_point("agent")
        return workflow.compile(checkpointer=checkpointer, debug=debug)

    # Add tool node and setup workflow with tools
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")

    # Define tool execution logic
    def should_continue(state: AgentState) -> Union[str, list]:
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return END
        tool_calls = [
            tool_node.inject_tool_args(call, state, store)
            for call in last_message.tool_calls
        ]
        return [Send("tools", [tool_call]) for tool_call in tool_calls]

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        path_map=["tools", END],
    )

    # Check for direct return tools
    direct_return_tools = {
        t.name
        for t in tool_node.tools_by_name.values()
        if getattr(t, "return_direct", False)
    }

    # If there are tools that should return directly, add conditional routing
    if direct_return_tools:

        def route_tool_responses(state: AgentState):
            for msg in reversed(state["messages"]):
                if not isinstance(msg, ToolMessage):
                    break
                if msg.name in direct_return_tools:
                    return END
            return "agent"

        workflow.add_conditional_edges("tools", route_tool_responses)
    else:
        workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=checkpointer, debug=debug)
