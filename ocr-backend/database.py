import os
import datetime
import urllib.parse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = urllib.parse.quote_plus(os.getenv("DB_PASSWORD", ""))
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ocr_db")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class OCRFeedbackDB(Base):
    __tablename__ = "ocr_feedback"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(String, index=True)
    original_text = Column(String)
    corrected_text = Column(String)
    cer = Column(Float)
    wer = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

Base.metadata.create_all(bind=engine)