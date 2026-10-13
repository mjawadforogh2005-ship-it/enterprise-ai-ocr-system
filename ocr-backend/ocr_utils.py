import re
import numpy as np
from PIL import Image

_RTL = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
_LTR = re.compile(r"[A-Za-z]")

def _is_rtl_line(texts):
    joined = " ".join(texts)
    rtl = len(_RTL.findall(joined))
    ltr = len(_LTR.findall(joined))
    return rtl >= ltr

def sort_and_merge_lines(results, overlap_ratio=0.5):
    if not results:
        return ""

    boxes = []
    for bbox, text, prob in results:
        text = text.strip()
        if not text:
            continue
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        boxes.append({
            "x": (min(xs) + max(xs)) / 2,
            "top": min(ys),
            "bottom": max(ys),
            "text": text,
        })

    if not boxes:
        return ""

    boxes.sort(key=lambda b: (b["top"] + b["bottom"]) / 2)

    lines = []
    current = [boxes[0]]
    for box in boxes[1:]:
        top = sum(b["top"] for b in current) / len(current)
        bottom = sum(b["bottom"] for b in current) / len(current)
        overlap = min(bottom, box["bottom"]) - max(top, box["top"])
        smaller = min(bottom - top, box["bottom"] - box["top"])
        if smaller > 0 and overlap >= smaller * overlap_ratio:
            current.append(box)
        else:
            lines.append(current)
            current = [box]
    lines.append(current)

    output = []
    for line in lines:
        rtl = _is_rtl_line([b["text"] for b in line])
        line.sort(key=lambda b: b["x"], reverse=rtl)
        output.append(" ".join(b["text"] for b in line))

    return "\n".join(output)

def ocr_image(reader, image, max_dim=1000):
    image = image.convert("RGB")
    if max(image.size) > max_dim:
        resample_filter = getattr(getattr(Image, 'Resampling', Image), 'LANCZOS', Image.LANCZOS)
        image.thumbnail((max_dim, max_dim), resample_filter)
    results = reader.readtext(
        np.array(image),
        decoder="greedy",
        detail=1,
        canvas_size=max_dim,
        mag_ratio=1.0,
    )
    return sort_and_merge_lines(results)