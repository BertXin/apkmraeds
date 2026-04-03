from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class APKFile(Base):
    __tablename__ = "apk_files"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    filename = Column(String, nullable=False)
    s3_key = Column(String, nullable=False, unique=True)
    size = Column(Integer, nullable=False)
    version_name = Column(String, nullable=True)
    version_code = Column(String, nullable=True)
    upload_time = Column(DateTime, default=datetime.utcnow)
    download_count = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "size": self.size,
            "version_name": self.version_name,
            "version_code": self.version_code,
            "upload_time": self.upload_time.isoformat() if self.upload_time else None,
            "download_count": self.download_count,
            "download_url": f"{settings.BASE_URL}/download/{self.id}",
        }


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()