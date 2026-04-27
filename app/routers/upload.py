import os
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import zipfile
import io

from app.database import get_db, APKFile
from app.models import UploadResponse, FileListResponse, FileInfo, DeleteResponse, ReplaceResponse
from app.s3 import s3_client
from app.config import settings

router = APIRouter(prefix="/api", tags=["api"])


def verify_token(authorization: Optional[str] = Header(None)):
    """验证上传 Token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    if token != settings.UPLOAD_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    return token


def extract_apk_version(file_content: bytes) -> tuple[Optional[str], Optional[str]]:
    """从 APK 中提取版本信息"""
    try:
        with zipfile.ZipFile(io.BytesIO(file_content)) as zf:
            # 尝试读取 AndroidManifest.xml (二进制格式，需要解析)
            # 简单实现：返回 None，后续可以用 androguard 等库解析
            return None, None
    except Exception:
        return None, None


@router.post("/upload", response_model=UploadResponse)
async def upload_apk(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    """上传 APK 文件"""
    # 验证文件扩展名
    if not file.filename or not file.filename.lower().endswith(".apk"):
        raise HTTPException(status_code=400, detail="Only APK files are allowed")

    # 读取文件内容
    content = await file.read()
    file_size = len(content)

    # 验证文件大小
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds limit")

    # 提取版本信息
    version_name, version_code = extract_apk_version(content)

    # 检查是否已有同名文件，有则覆盖
    existing = db.query(APKFile).filter(APKFile.filename == file.filename).first()

    if existing:
        # 删除旧 S3 文件
        await s3_client.delete_file(existing.s3_key)

        # 上传新文件到 S3（保持同一个 file_id）
        new_s3_key = f"apk/{existing.id}/{file.filename}"
        await s3_client.upload_file(content, new_s3_key)

        # 更新数据库记录
        existing.s3_key = new_s3_key
        existing.size = file_size
        existing.version_name = version_name
        existing.version_code = version_code
        existing.upload_time = datetime.utcnow()
        db.commit()

        return UploadResponse(
            id=existing.id,
            filename=file.filename,
            size=file_size,
            download_url=f"{settings.BASE_URL}/download/{existing.id}",
            message="File replaced",
        )

    # 新文件
    file_id = str(uuid.uuid4())
    s3_key = f"apk/{file_id}/{file.filename}"

    await s3_client.upload_file(content, s3_key)

    apk_file = APKFile(
        id=file_id,
        filename=file.filename,
        s3_key=s3_key,
        size=file_size,
        version_name=version_name,
        version_code=version_code,
    )
    db.add(apk_file)
    db.commit()

    return UploadResponse(
        id=file_id,
        filename=file.filename,
        size=file_size,
        download_url=f"{settings.BASE_URL}/download/{file_id}",
        message="Upload successful",
    )


@router.get("/files", response_model=FileListResponse)
async def list_files(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    """列出所有已上传的文件"""
    files = db.query(APKFile).order_by(APKFile.upload_time.desc()).all()
    return FileListResponse(
        files=[FileInfo(**f.to_dict()) for f in files],
        total=len(files),
    )


@router.delete("/files/{file_id}", response_model=DeleteResponse)
async def delete_file(
    file_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    """删除文件"""
    apk_file = db.query(APKFile).filter(APKFile.id == file_id).first()
    if not apk_file:
        raise HTTPException(status_code=404, detail="File not found")

    # 从 S3 删除
    await s3_client.delete_file(apk_file.s3_key)

    # 从数据库删除
    db.delete(apk_file)
    db.commit()

    return DeleteResponse(message="File deleted", id=file_id)


@router.put("/files/{file_id}/replace", response_model=ReplaceResponse)
async def replace_file(
    file_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    """替换已有文件，保持下载链接不变"""
    apk_file = db.query(APKFile).filter(APKFile.id == file_id).first()
    if not apk_file:
        raise HTTPException(status_code=404, detail="File not found")

    if not file.filename or not file.filename.lower().endswith(".apk"):
        raise HTTPException(status_code=400, detail="Only APK files are allowed")

    content = await file.read()
    file_size = len(content)

    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds limit")

    # 删除旧 S3 文件
    await s3_client.delete_file(apk_file.s3_key)

    # 上传新文件到 S3（保持同一个 file_id）
    new_s3_key = f"apk/{file_id}/{file.filename}"
    await s3_client.upload_file(content, new_s3_key)

    # 提取版本信息
    version_name, version_code = extract_apk_version(content)

    # 更新数据库记录
    apk_file.filename = file.filename
    apk_file.s3_key = new_s3_key
    apk_file.size = file_size
    apk_file.version_name = version_name
    apk_file.version_code = version_code
    apk_file.upload_time = datetime.utcnow()
    db.commit()

    return ReplaceResponse(
        id=file_id,
        filename=file.filename,
        size=file_size,
        download_url=f"{settings.BASE_URL}/download/{file_id}",
        message="File replaced successfully",
    )