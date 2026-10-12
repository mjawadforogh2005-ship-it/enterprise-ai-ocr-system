import os
import urllib.parse
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# رمز عبور شما به همراه کاراکتر خاص #
raw_password = "2026#"

# انکود کردن پسورد جهت جلوگیری از خطای parse آدرس در SQLAlchemy
encoded_password = urllib.parse.quote_plus(raw_password)

# ساخت آدرس اتصال دقیق به دیتابیس ocr_db
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql://postgres:{encoded_password}@localhost:5432/ocr_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class OCRFeedbackDB(Base):
    __tablename__ = "ocr_feedback"

    id = Column(String, primary_key=True, index=True)
    image_path = Column(String, nullable=False)
    original_text = Column(String, nullable=True)
    corrected_text = Column(String, nullable=True)
    cer_score = Column(Float, default=0.0)
    wer_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)