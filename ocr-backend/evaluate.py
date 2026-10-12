import os
import json
import easyocr
import jiwer
from PIL import Image
import numpy as np
from main import sort_and_merge_lines

DATASET_DIR = "dataset_feedback"
UPLOAD_DIR = "uploads"

def evaluate_test_set():
    reader = easyocr.Reader(['fa', 'en'], gpu=False)
    
    if not os.path.exists(DATASET_DIR):
        print("پوشه داده‌های تست یافت نشد.")
        return

    json_files = [f for f in os.listdir(DATASET_DIR) if f.endswith('.json')]
    
    if not json_files:
        print("هیچ نمونه تستی یافت نشد.")
        return

    total_cer = 0.0
    total_wer = 0.0
    count = 0

    print("=" * 60)
    print("ارزیابی واقعی عملکرد سیستم OCR روی نمونه‌های تست")
    print("=" * 60)

    for file_name in json_files:
        with open(os.path.join(DATASET_DIR, file_name), 'r', encoding='utf-8') as f:
            data = json.load(f)

        image_path = os.path.join(UPLOAD_DIR, f"{data['image_id']}.jpg")
        reference_text = data['corrected_text']

        if not os.path.exists(image_path) or not reference_text.strip():
            continue

        image = Image.open(image_path).convert('RGB')
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
        
        hypothesis_text = sort_and_merge_lines(results)

        cer = jiwer.cer(reference_text, hypothesis_text)
        wer = jiwer.wer(reference_text, hypothesis_text)

        total_cer += cer
        total_wer += wer
        count += 1

        print(f"شناسه تصویر: {data['image_id']}")
        print(f"CER: {round(cer, 4)} | WER: {round(wer, 4)}")
        print("-" * 60)

    if count > 0:
        avg_cer = round(total_cer / count, 4)
        avg_wer = round(total_wer / count, 4)
        accuracy = max(0.0, round((1.0 - avg_cer) * 100, 2))
        
        print(f"\n📊 نتایج نهایی ارزیابی:")
        print(f"تعداد نمونه‌ها: {count}")
        print(f"میانگین CER: {avg_cer}")
        print(f"میانگین WER: {avg_wer}")
        print(f"دقت تخمینی: {accuracy}%")
    print("=" * 60)

if __name__ == "__main__":
    evaluate_test_set()