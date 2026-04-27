from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pathlib import Path

from app.database import init_db
from app.routers.upload import router as upload_router
from app.routers.download import router as download_router

# 初始化应用
app = FastAPI(
    title="APK 分发服务",
    description="上传 APK 到 S3，生成自定义域名下载链接",
    version="1.0.0",
)

# 初始化数据库
init_db()

# 注册路由
app.include_router(upload_router)
app.include_router(download_router)

# 模板目录
TEMPLATE_DIR = Path(__file__).parent / "templates"


@app.get("/", response_class=HTMLResponse)
async def index():
    """上传页面"""
    return HTMLResponse(content=(TEMPLATE_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/list", response_class=HTMLResponse)
async def file_list():
    """文件列表页面"""
    return HTMLResponse(content=(TEMPLATE_DIR / "list.html").read_text(encoding="utf-8"))


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}