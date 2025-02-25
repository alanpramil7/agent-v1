from pydantic import BaseModel, Field, HttpUrl


class WebsiteProcessingRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL of the website to be processed.")
