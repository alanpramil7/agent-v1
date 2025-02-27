"""
Website Models

This module defines the data models for website-related API requests and responses.
These models validate incoming requests to ensure they contain valid URLs
before being processed by the website service.
"""

from pydantic import BaseModel, Field, HttpUrl


class WebsiteProcessingRequest(BaseModel):
    """
    Model for website processing requests.

    Validates that the provided URL is in a valid format (using Pydantic's HttpUrl type)
    before being processed by the website service.
    """

    url: HttpUrl = Field(..., description="URL of the website to be processed.")

    class Config:
        """Pydantic configuration settings"""

        json_schema_extra = {"example": {"url": "https://example.com"}}
