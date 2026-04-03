import asyncio
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db, APKFile
from app.s3 import s3_client

router = APIRouter(tags=["download"])


@router.get("/download/{file_id}")
async def download_apk(
    file_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """下载 APK 文件 (服务端代理 S3)"""
    # 查询文件信息
    apk_file = db.query(APKFile).filter(APKFile.id == file_id).first()
    if not apk_file:
        raise HTTPException(status_code=404, detail="File not found")

    # 获取 Range header (断点续传)
    range_header = request.headers.get("range")

    # 从 S3 获取文件
    s3_response = await s3_client.download_file(apk_file.s3_key, range_header)

    # 更新下载计数
    apk_file.download_count += 1
    db.commit()

    # 获取文件内容
    body = s3_response["Body"]
    content_length = s3_response["ContentLength"]

    # 使用 asyncio.to_thread 读取内容
    content = await asyncio.to_thread(body.read)

    # 准备响应头
    headers = {
        "Content-Disposition": f'attachment; filename="{apk_file.filename}"',
        "Content-Type": "application/vnd.android.package-archive",
        "Accept-Ranges": "bytes",
        "Content-Length": str(len(content)),
    }

    # 处理断点续传
    if range_header:
        headers["Content-Range"] = f"bytes 0-{len(content)-1}/{content_length}"
        status_code = 206
    else:
        status_code = 200

    return Response(
        content=content,
        status_code=status_code,
        headers=headers,
        media_type="application/vnd.android.package-archive",
    )