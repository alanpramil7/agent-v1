from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.managed import IsLastStep, RemainingSteps


class AgentState(TypedDict):
    """State of the ReAct agent containing conversation history and step tracking."""

    # Store user and agent interaction.
    messages: Annotated[
        Sequence[BaseMessage],
        add_messages,
    ]
    next: str  # Next step from the supervisor agent
    is_last_step: IsLastStep  # MAX (25)
    remaining_steps: RemainingSteps
