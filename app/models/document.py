"""
Document Models

This module defines the data models for document-related API requests and responses.
These models validate document uploads and ensure they meet the required format
before being processed by the document service.
"""

from fastapi import UploadFile
from pydantic import BaseModel, Field


class DocumentProcessRequest(BaseModel):
    """
    Model for document processing requests.

    This model is used for document upload validation. It ensures that
    a file is included in the request before processing by the document service.

    Note: Since FastAPI's UploadFile is used directly in the endpoint function
    parameter, this model is primarily for documentation purposes.
    """

    file: UploadFile = Field(
        ..., description="The document file to be processed and indexed."
    )

    class Config:
        """Pydantic configuration settings"""

        arbitrary_types_allowed = True  # Required for UploadFile type
