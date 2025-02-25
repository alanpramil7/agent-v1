from app.utils.logger import logger
from app.models.agent import AgentProcessingRequest
from app.services.agent import AgentService
from fastapi import APIRouter, HTTPException, status, Depends
from app.api.dependency import get_agent

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("")
async def agent(
    request: AgentProcessingRequest,
    agent: AgentService = Depends(get_agent),
):
    logger.debug(f"Generating response for user question: {request.question}")
    try:
        return await agent.process_question(request.question)

    except Exception as e:
        logger.error(f"Error in processing user question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing user request: {e}",
        )
