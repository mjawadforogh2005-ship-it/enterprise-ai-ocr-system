import os
import sys
import json
import easyocr
import jiwer
from PIL import Image
from ocr_utils import ocr_image

IMG_DIR = os.path.join("test_set", "images")
LBL_DIR = os.path.join("test_set", "labels")
OUT_DIR = "eval_results"
EXTS = (".jpg", ".jpeg", ".png")


def norm(text):
    return " ".join(text.split())


def run(tag):
    reader = easyocr.Reader(["fa", "en"], gpu=False)
    rows = []
    for name in sorted(os.listdir(IMG_DIR)):
        stem, ext = os.path.splitext(name)
        if ext.lower() not in EXTS:
            continue
        label_path = os.path.join(LBL_DIR, stem + ".txt")
        if not os.path.exists(label_path):
            continue
        with open(label_path, encoding="utf-8") as f:
            reference = norm(f.read())
        if not reference:
            continue
        hypothesis = norm(ocr_image(reader, Image.open(os.path.join(IMG_DIR, name))))
        cer = float(jiwer.cer(reference, hypothesis))
        wer = float(jiwer.wer(reference, hypothesis))
        rows.append({"image": name, "cer": round(cer, 4), "wer": round(wer, 4)})
        print(f"{name}: CER={cer:.4f} WER={wer:.4f}")

    if not rows:
        print("هیچ نمونه‌ای پیدا نشد")
        return

    summary = {
        "tag": tag,
        "samples": len(rows),
        "avg_cer": round(sum(r["cer"] for r in rows) / len(rows), 4),
        "avg_wer": round(sum(r["wer"] for r in rows) / len(rows), 4),
        "details": rows,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, f"{tag}.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n{tag}: samples={summary['samples']} CER={summary['avg_cer']} WER={summary['avg_wer']}")


def compare(tag_a, tag_b):
    with open(os.path.join(OUT_DIR, f"{tag_a}.json"), encoding="utf-8") as f:
        a = json.load(f)
    with open(os.path.join(OUT_DIR, f"{tag_b}.json"), encoding="utf-8") as f:
        b = json.load(f)
    print(f"{'':10}{tag_a:>12}{tag_b:>12}")
    print(f"{'CER':10}{a['avg_cer']:>12}{b['avg_cer']:>12}")
    print(f"{'WER':10}{a['avg_wer']:>12}{b['avg_wer']:>12}")


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "compare":
        compare(sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 2:
        run(sys.argv[1])
    else:
        print("python evaluate.py <tag>  یا  python evaluate.py compare <tagA> <tagB>")