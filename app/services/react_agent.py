from typing import Literal, Optional, Sequence, Union, cast

from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.managed import IsLastStep, RemainingSteps
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer, Send
from langgraph.utils.runnable import RunnableCallable
from typing_extensions import Annotated, TypedDict


class AgentState(TypedDict):
    """
    The state of the ReAct agent.

    This state is passed between nodes in the agent's graph and contains:
    - messages: The conversation history
    - is_last_step: Flag indicating if the current step is the last step
    - remaining_steps: The number of remaining steps before the agent stops
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: IsLastStep
    remaining_steps: RemainingSteps


def create_react_agent(
    model: Union[str, LanguageModelLike],
    tools: Sequence[BaseTool],
    prompt: str = None,
    checkpointer: Optional[Checkpointer] = None,
    store: Optional[BaseStore] = None,
    name: Optional[str] = None,
) -> StateGraph:
    """
    Creates a ReAct agent using LangGraph and LangChain components.

    Args:
        model: The language model to use, either as a string or LanguageModelLike object.
        tools: A sequence of tools the agent can use.
        prompt: An optional system prompt to prepend to the conversation.
        checkpointer: Optional checkpointer for saving/restoring state.

    Returns:
        A compiled StateGraph representing the ReAct agent.
    """
    tool_node = ToolNode(tools)
    tool_classes = list(tool_node.tools_by_name.values())
    tool_calling_enabled = len(tools) > 0

    model = model.bind_tools(tools)
    system_message = SystemMessage(content=prompt)
    prompt_runnable = RunnableCallable(
        lambda state: [system_message] + state["messages"]
    )
    model_runnable = prompt_runnable | model

    should_return_direct = {t.name for t in tool_classes if t.return_direct}

    async def call_model(state: AgentState, config: RunnableConfig) -> AgentState:
        response = cast(AIMessage, await model_runnable.ainvoke(state, config))
        response.name = name
        has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
        all_tools_return_direct = (
            all(call["name"] in should_return_direct for call in response.tool_calls)
            if has_tool_calls
            else False
        )
        if (
            (
                "remaining_steps" not in state
                and state.get("is_last_step", False)
                and has_tool_calls
            )
            or (
                "remaining_steps" in state
                and state["remaining_steps"] < 1
                and all_tools_return_direct
            )
            or (
                "remaining_steps" in state
                and state["remaining_steps"] < 2
                and has_tool_calls
            )
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

    if not tool_calling_enabled:
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.set_entry_point("agent")
        return workflow.compile(
            checkpointer=checkpointer,
            debug=True,
        )

    def should_continue(state: AgentState) -> Union[str, list]:
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return END
        tool_calls = [
            tool_node.inject_tool_args(call, state, store)
            for call in last_message.tool_calls
        ]
        return [Send("tools", [tool_call]) for tool_call in tool_calls]

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        path_map=["tools", END],
    )

    def route_tool_responses(state: AgentState) -> Literal["agent", "__end__"]:
        for m in reversed(state["messages"]):
            if not isinstance(m, ToolMessage):
                break
            if m.name in should_return_direct:
                return END
        return "agent"

    if should_return_direct:
        workflow.add_conditional_edges("tools", route_tool_responses)
    else:
        workflow.add_edge("tools", "agent")

    return workflow.compile(
        checkpointer=checkpointer,
        debug=True,
    )
