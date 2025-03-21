"""
Agent Processing API Endpoints

This module provides endpoints for interacting with the AI agent.
It allows clients to submit questions for processing by the agent
and receive responses, including streaming responses for real-time feedback.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependency import get_agent
from app.models.agent import AgentProcessingRequest
from app.services.agent import AgentService
from app.utils.logger import logger

# Agent-specific router with appropriate tags and prefix
router = APIRouter(prefix="/agent", tags=["agent"])


@router.post(
    "/stream",
    summary="Stream a response from the agent",
    description="Submit a question to be processed by the AI agent and receive a streaming response",
)
async def stream_agent(
    request: AgentProcessingRequest,
    agent: AgentService = Depends(get_agent),
):
    """
    Process a question using the AI agent and stream the response.

    This endpoint accepts a question from the client, processes it using
    the AI agent, and returns a streaming response for real-time feedback.

    Args:
        request: The agent processing request containing the question
        agent: AgentService dependency for processing the question

    Returns:
        StreamingResponse: A streaming response with the agent's answer

    Raises:
        HTTPException: If processing encounters an error
    """
    try:
        # Return a streaming response
        return StreamingResponse(
            agent.stream_question(
                request.conversation_id,
                request.question,
            ),
            media_type="text/plain",
        )
    except Exception as e:
        logger.error(f"Error streaming response to question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error streaming response: {str(e)}",
        )
