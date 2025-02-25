from pydantic import BaseModel, Field


class AgentProcessingRequest(BaseModel):
    question: str = Field(..., desciption="User question")
