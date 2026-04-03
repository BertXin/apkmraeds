import asyncio
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from typing import Optional

from app.config import settings


class S3Client:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            region_name=settings.S3_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.bucket = settings.S3_BUCKET

    async def upload_file(self, file_content: bytes, key: str, content_type: str = "application/vnd.android.package-archive") -> str:
        """上传文件到 S3"""
        try:
            await asyncio.to_thread(
                self.client.put_object,
                Bucket=self.bucket,
                Key=key,
                Body=file_content,
                ContentType=content_type,
            )
            return key
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")

    async def download_file(self, key: str, range_header: Optional[str] = None):
        """从 S3 下载文件，支持断点续传"""
        try:
            kwargs = {"Bucket": self.bucket, "Key": key}
            if range_header:
                kwargs["Range"] = range_header

            response = await asyncio.to_thread(self.client.get_object, **kwargs)
            return response
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise HTTPException(status_code=404, detail="File not found in S3")
            raise HTTPException(status_code=500, detail=f"S3 download failed: {str(e)}")

    async def delete_file(self, key: str) -> bool:
        """从 S3 删除文件"""
        try:
            await asyncio.to_thread(
                self.client.delete_object,
                Bucket=self.bucket,
                Key=key,
            )
            return True
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"S3 delete failed: {str(e)}")


s3_client = S3Client()