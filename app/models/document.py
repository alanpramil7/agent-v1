from fastapi import UploadFile
from pydantic import BaseModel


class DocumentProcessRequest(BaseModel):
    file: UploadFile
