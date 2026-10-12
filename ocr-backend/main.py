import os
import uuid
import io
import json
import numpy as np
from PIL import Image
import easyocr
import jiwer
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, OCRFeedbackDB

app = FastAPI(title="Enterprise Offline OCR System")

# محدود کردن CORS جهت رعایت اصول امنیتی
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# بارگذاری مدل پایتون در حافظه
reader = easyocr.Reader(['fa', 'en'], gpu=False)

UPLOAD_DIR = "uploads"
DATASET_DIR = "dataset_feedback"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATASET_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class FeedbackRequest(BaseModel):
    image_id: str
    original_text: str
    corrected_text: str

def sort_and_merge_lines(results, y_threshold=20):
    if not results:
        return ""
    
    boxes = []
    for item in results:
        bbox, text, prob = item
        top_left = bbox[0]
        x, y = top_left[0], top_left[1]
        boxes.append({'x': x, 'y': y, 'text': text, 'prob': prob})
    
    boxes.sort(key=lambda b: b['y'])
    
    lines = []
    current_line = [boxes[0]]
    
    for box in boxes[1:]:
        if abs(box['y'] - current_line[0]['y']) < y_threshold:
            current_line.append(box)
        else:
            current_line.sort(key=lambda b: b['x'], reverse=True)
            lines.append(" ".join([b['text'] for b in current_line]))
            current_line = [box]
            
    if current_line:
        current_line.sort(key=lambda b: b['x'], reverse=True)
        lines.append(" ".join([b['text'] for b in current_line]))
        
    return "\n".join(lines)

@app.post("/api/ocr")
async def process_ocr(file: UploadFile = File(...)):
    try:
        image_id = str(uuid.uuid4())
        file_bytes = await file.read()
        
        file_path = os.path.join(UPLOAD_DIR, f"{image_id}.jpg")
        with open(file_path, "wb") as f:
            f.write(file_bytes)
            
        image = Image.open(io.BytesIO(file_bytes)).convert('RGB')
        
        # ریسایز به 1000px جهت حفظ جزئیات متون ریز تذکره و مدارک
        max_dim = 1000
        if max(image.size) > max_dim:
            image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            
        img_np = np.array(image)
        
        results = reader.readtext(
            img_np, 
            decoder='greedy', 
            detail=1, 
            canvas_size=1000, 
            mag_ratio=1.0
        )
        
        extracted_text = sort_and_merge_lines(results)
        
        return {
            "image_id": image_id,
            "extracted_text": extracted_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def save_feedback(data: FeedbackRequest, db: Session = Depends(get_db)):
    try:
        # محاسبه دقیق و واقعی CER و WER بر اساس اختلاف متن اصلی و متن ویرایش‌شده
        cer = jiwer.cer(data.original_text, data.corrected_text) if data.original_text else 0.0
        wer = jiwer.wer(data.original_text, data.corrected_text) if data.original_text else 0.0
        cer = round(float(cer), 4)
        wer = round(float(wer), 4)

        db_entry = OCRFeedbackDB(
            image_id=data.image_id,
            original_text=data.original_text,
            corrected_text=data.corrected_text,
            cer=cer,
            wer=wer
        )
        db.add(db_entry)
        db.commit()

        # ذخیره جفت‌داده تصویر و متن تصحیح‌شده برای فرآیند Fine-Tuning
        json_path = os.path.join(DATASET_DIR, f"{data.image_id}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "image_id": data.image_id,
                "original_text": data.original_text,
                "corrected_text": data.corrected_text,
                "cer": cer,
                "wer": wer
            }, f, ensure_ascii=False, indent=2)

        return {"status": "success", "cer": cer, "wer": wer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    feedbacks = db.query(OCRFeedbackDB).all()
    total_samples = len(feedbacks)
    
    if total_samples == 0:
        return {
            "total_samples": 0,
            "avg_cer": 0.0,
            "accuracy_percentage": 100.0
        }
        
    avg_cer = sum(f.cer for f in feedbacks) / total_samples
    accuracy = max(0.0, round((1.0 - avg_cer) * 100, 2))
    
    return {
        "total_samples": total_samples,
        "avg_cer": round(avg_cer, 4),
        "accuracy_percentage": accuracy
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)