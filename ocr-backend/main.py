import os
import uuid
import io
import numpy as np
from PIL import Image
import easyocr
import jiwer
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, OCRFeedbackDB

app = FastAPI(title="Enterprise Ultra-Fast Offline OCR System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

print("⏳ Loading Fast EasyOCR Model (Fa + En)...")
reader = easyocr.Reader(['fa', 'en'], gpu=False)
print("✅ EasyOCR Reader Loaded Successfully!")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class FeedbackModel(BaseModel):
    image_id: str
    original_text: str
    corrected_text: str

def sort_and_merge_lines(results, line_threshold=20):
    """مرتب‌سازی دقیق سطرها و ادغام کلمات هم‌سطر از راست به چپ برای زبان فارسی"""
    if not results:
        return ""

    boxes = []
    for item in results:
        bbox, text, prob = item
        top_left_x = bbox[0][0]
        top_left_y = bbox[0][1]
        bottom_right_y = bbox[2][1]
        center_y = (top_left_y + bottom_right_y) / 2
        
        boxes.append({
            'x': top_left_x,
            'y': center_y,
            'text': text.strip()
        })

    boxes.sort(key=lambda b: b['y'])

    lines = []
    current_line = []

    for box in boxes:
        if not current_line:
            current_line.append(box)
        else:
            if abs(box['y'] - current_line[0]['y']) <= line_threshold:
                current_line.append(box)
            else:
                current_line.sort(key=lambda b: b['x'], reverse=True)
                line_text = " ".join([b['text'] for b in current_line])
                lines.append(line_text)
                current_line = [box]

    if current_line:
        current_line.sort(key=lambda b: b['x'], reverse=True)
        line_text = " ".join([b['text'] for b in current_line])
        lines.append(line_text)

    return "\n".join(lines)

@app.post("/api/ocr")
async def process_ocr(file: UploadFile = File(...)):
    try:
        image_id = str(uuid.uuid4())
        file_bytes = await file.read()
        
        pil_image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        
        max_dimension = 600
        if max(pil_image.size) > max_dimension:
            pil_image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
        img_np = np.array(pil_image)
        
        file_path = os.path.join(UPLOADS_DIR, f"{image_id}.jpg")
        pil_image.save(file_path, "JPEG", quality=85)
            
    
        results = reader.readtext(
            img_np, 
            detail=1, 
            paragraph=False,
            canvas_size=640,
            mag_ratio=1.0
        )
   
        final_text = sort_and_merge_lines(results)

        return {
            "image_id": image_id,
            "image_path": file_path,
            "extracted_text": final_text.strip() if final_text.strip() else "متنی تشخیص داده نشد."
        }
    except Exception as e:
        print(f"Error in Processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def save_feedback(data: FeedbackModel, db: Session = Depends(get_db)):
    try:
        cer_score = jiwer.cer(data.corrected_text, data.original_text) if data.corrected_text else 0.0
        wer_score = jiwer.wer(data.corrected_text, data.original_text) if data.corrected_text else 0.0
        
        feedback_entry = OCRFeedbackDB(
            id=data.image_id,
            image_path=os.path.join(UPLOADS_DIR, f"{data.image_id}.jpg"),
            original_text=data.original_text,
            corrected_text=data.corrected_text,
            cer_score=round(cer_score, 4),
            wer_score=round(wer_score, 4)
        )
        
        db.merge(feedback_entry)
        db.commit()
            
        return {
            "status": "success",
            "message": "بازخورد با موفقیت ثبت شد.",
            "cer": round(cer_score, 4),
            "wer": round(wer_score, 4)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics")
def get_metrics(db: Session = Depends(get_db)):
    records = db.query(OCRFeedbackDB).all()
    if not records:
        return {"total_samples": 0, "avg_cer": 0.0, "avg_wer": 0.0, "accuracy_percentage": 100.0}
    
    total_cer = sum(r.cer_score for r in records)
    total_wer = sum(r.wer_score for r in records)
    count = len(records)
    
    avg_cer = total_cer / count
    avg_wer = total_wer / count
    accuracy = round(max(0, (1 - avg_cer) * 100), 2)
    
    return {
        "total_samples": count,
        "avg_cer": round(avg_cer, 4),
        "avg_wer": round(avg_wer, 4),
        "accuracy_percentage": accuracy
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)