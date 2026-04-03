import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # S3 配置
    S3_BUCKET: str = os.getenv("S3_BUCKET", "")
    S3_REGION: str = os.getenv("S3_REGION", "ap-northeast-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")

    # 认证
    UPLOAD_TOKEN: str = os.getenv("UPLOAD_TOKEN", "")

    # 服务配置
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/apk.db")

    # 上传配置
    MAX_FILE_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS: set = {".apk"}

    @property
    def s3_endpoint(self) -> str:
        return f"https://{self.S3_BUCKET}.s3.{self.S3_REGION}.amazonaws.com"


settings = Settings()