from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UploadResponse(BaseModel):
    id: str
    filename: str
    size: int
    download_url: str
    message: str


class FileInfo(BaseModel):
    id: str
    filename: str
    size: int
    version_name: Optional[str] = None
    version_code: Optional[str] = None
    upload_time: Optional[datetime] = None
    download_count: int
    download_url: str


class FileListResponse(BaseModel):
    files: list[FileInfo]
    total: int


class DeleteResponse(BaseModel):
    message: str
    id: str