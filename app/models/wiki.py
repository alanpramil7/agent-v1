from pydantic import BaseModel, Field


class WikiProcessingRequest(BaseModel):
    organization: str = Field(default="cloudcadi", description="Organization name")
    project: str = Field(default="azure-cloudcadi-v2", description="Project name")
    wikiIdentifier: str = Field(
        default="azure-cloudcadi-v2.wiki", description="Wiki Identifier"
    )


class WikiPage(BaseModel):
    page_path: str
    content: str
    remote_url: str
