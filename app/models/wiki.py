"""
Wiki Models

This module defines the data models for wiki-related API requests and responses.
These models validate wiki processing requests and define the structure for wiki
page data returned from external services.
"""

from pydantic import BaseModel, Field


class WikiProcessingRequest(BaseModel):
    """
    Model for wiki processing requests.

    Validates required information about a wiki to be processed, including
    organization name, project name, and wiki identifier. Default values are
    provided to simplify common use cases.
    """

    organization: str = Field(
        default="", description="Organization name containing the wiki"
    )
    project: str = Field(default="", description="Project name containing the wiki")
    wikiIdentifier: str = Field(
        default="", description="Unique identifier for the wiki"
    )

    class Config:
        """Pydantic configuration settings"""

        json_schema_extra = {
            "example": {
                "organization": "cloudcadi",
                "project": "azure-cloudcadi-v2",
                "wikiIdentifier": "azure-cloudcadi-v2.wiki",
            }
        }


class WikiPage(BaseModel):
    """
    Model representing a wiki page.

    Contains the path, content, and remote URL of a wiki page retrieved
    from an external wiki service (e.g., Azure DevOps Wiki).
    """

    page_path: str = Field(..., description="Path to the wiki page")
    content: str = Field(..., description="Content of the wiki page")
    remote_url: str = Field(..., description="Remote URL of the wiki page")
