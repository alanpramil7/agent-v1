from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.managed import IsLastStep, RemainingSteps


class AgentState(TypedDict):
    """State of the ReAct agent containing conversation history and step tracking."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    next: str
    is_last_step: IsLastStep
    remaining_steps: RemainingSteps
