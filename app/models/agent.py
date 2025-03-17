"""
Agent Request Models

This module defines the data models for agent-related API requests and responses.
These models validate incoming requests to ensure they contain the required data
in the correct format before being processed by the agent service.
"""

from pydantic import BaseModel, Field


class AgentProcessingRequest(BaseModel):
    """
    Model for agent processing requests.

    Represents a user's question to be processed by the AI agent.
    This model validates that the question is provided in the request.
    """

    user_id: str = Field(..., description="User ID")
    conversation_id: str = Field(..., description="Conversation ID")
    question: str = Field(..., description="User question to be processed by the agent")

    class Config:
        """Pydantic configuration settings"""

        json_schema_extra = {
            "example": {
                "user_id": "default",
                "conversation_id": "default",
                "question": "What are the key features of Azure Virtual Machines?",
            }
        }
