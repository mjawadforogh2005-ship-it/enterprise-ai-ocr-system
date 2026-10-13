import os
import random
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import arabic_reshaper

try:
    from bidi import get_display
except ImportError:
    from bidi.algorithm import get_display

WIN_FONTS = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
FONT_DIRS = [WIN_FONTS, "/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/noto", "/usr/share/fonts/truetype/liberation"]
FA_FONT_NAMES = ["tahoma.ttf", "arial.ttf", "times.ttf", "segoeui.ttf", "calibri.ttf", "DejaVuSans.ttf", "NotoSansArabic-Regular.ttf"]
EN_FONT_NAMES = FA_FONT_NAMES + ["verdana.ttf", "georgia.ttf", "cour.ttf", "LiberationSerif-Regular.ttf"]

FA_WORDS = ["کتاب", "مدرسه", "دانشگاه", "سیستم", "برنامه", "اطلاعات", "کاربر", "تصویر", "متن", "زبان",
            "هوش", "مصنوعی", "دقت", "مدل", "آموزش", "داده", "سند", "قرارداد", "شهر", "کابل", "افغانستان",
            "خانه", "زندگی", "آرامش", "خداوند", "انسان", "کار", "زمان", "فایل", "رایانه", "شبکه", "پروژه",
            "ارزیابی", "بهبود", "نتیجه", "گزارش", "مدیریت", "امنیت", "رمز", "عبور", "صفحه", "ورود", "خروج",
            "شماره", "تاریخ", "تولد", "نام", "پدر", "ولایت", "ملی", "هویت", "کارت", "اداره", "وزارت", "مالی",
            "بانک", "حساب", "پرداخت", "خدمات", "چاپ", "گزینه", "مجموعه", "پژوهش", "ژنرال", "گفتگو"]
FA_JOIN = ["و", "در", "به", "از", "برای", "با", "که", "این", "یک"]
EN_WORDS = ["system", "document", "agreement", "university", "student", "residence", "regulations", "safety",
            "access", "control", "energy", "water", "building", "service", "report", "model", "training",
            "accuracy", "image", "text", "language", "machine", "learning", "data", "user", "feedback",
            "project", "network", "security", "password", "account", "payment", "ministry", "national",
            "identity", "card", "date", "birth", "name", "father", "province", "official", "section",
            "provide", "maintain", "clean", "common", "property", "damage", "repair", "equipment"]
EN_JOIN = ["of", "the", "and", "for", "with", "in", "to", "a"]
FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def find_fonts(names):
    found = []
    for d in FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p) and p not in found:
                found.append(p)
    return found


def fa_sentence(rng, n):
    parts = []
    for i in range(n):
        parts.append(rng.choice(FA_WORDS))
        if i < n - 1 and rng.random() < 0.3:
            parts.append(rng.choice(FA_JOIN))
    if rng.random() < 0.2:
        parts.append("".join(rng.choice(FA_DIGITS) for _ in range(rng.randint(2, 6))))
    return " ".join(parts)


def en_sentence(rng, n):
    parts = []
    for i in range(n):
        parts.append(rng.choice(EN_WORDS))
        if i < n - 1 and rng.random() < 0.3:
            parts.append(rng.choice(EN_JOIN))
    text = " ".join(parts)
    if rng.random() < 0.3:
        text = text.capitalize()
    if rng.random() < 0.2:
        text += " " + "".join(rng.choice("0123456789") for _ in range(rng.randint(2, 6)))
    return text


def make_line(rng):
    r = rng.random()
    if r < 0.45:
        return fa_sentence(rng, rng.randint(3, 7)), "fa"
    if r < 0.8:
        return en_sentence(rng, rng.randint(3, 7)), "en"
    words = fa_sentence(rng, rng.randint(3, 6)).split()
    words.insert(rng.randint(0, len(words)), rng.choice(EN_WORDS))
    return " ".join(words), "fa"


def visual(text, kind):
    if kind == "fa":
        return get_display(arabic_reshaper.reshape(text))
    return text


def render_line(text, kind, font_path, size, rng):
    font = ImageFont.truetype(font_path, size)
    shown = visual(text, kind)
    probe = ImageDraw.Draw(Image.new("L", (10, 10)))
    box = probe.textbbox((0, 0), shown, font=font)
    pad_x = rng.randint(8, 20)
    pad_y = rng.randint(6, 14)
    w = box[2] - box[0] + 2 * pad_x
    h = box[3] - box[1] + 2 * pad_y
    bg = rng.randint(225, 255)
    fg = rng.randint(0, 70)
    img = Image.new("L", (w, h), bg)
    ImageDraw.Draw(img).text((pad_x - box[0], pad_y - box[1]), shown, font=font, fill=fg)
    return img


def augment(img, rng):
    if rng.random() < 0.4:
        img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.3, 1.0)))
    arr = np.array(img).astype(np.float32)
    arr += np.random.default_rng(rng.randint(0, 10**9)).normal(0, rng.uniform(1, 8), arr.shape)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    out = Image.fromarray(arr)
    if rng.random() < 0.3:
        out = out.rotate(rng.uniform(-1.2, 1.2), expand=True, fillcolor=int(np.median(arr)))
    return out


def make_page(rng, fa_fonts, en_fonts):
    n_lines = rng.randint(3, 6)
    size = rng.randint(24, 40)
    lines = []
    for _ in range(n_lines):
        text, kind = make_line(rng)
        fonts = fa_fonts if kind == "fa" else en_fonts
        lines.append((text, kind, render_line(text, kind, rng.choice(fonts), size, rng)))
    width = max(max(im.width for _, _, im in lines) + 40, 700)
    height = sum(im.height for _, _, im in lines) + 40 + 6 * len(lines)
    page = Image.new("L", (width, height), rng.randint(235, 255))
    y = 20
    for text, kind, im in lines:
        x = width - im.width - 20 if kind == "fa" else 20
        page.paste(im, (x, y))
        y += im.height + 6
    return page, lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--count", type=int, default=30)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--crops", action="store_true")
    args = ap.parse_args()

    fa_fonts = find_fonts(FA_FONT_NAMES)
    en_fonts = find_fonts(EN_FONT_NAMES)
    if not fa_fonts or not en_fonts:
        raise SystemExit("هیچ فونتی پیدا نشد")
    print("فونت‌های فارسی:", [os.path.basename(f) for f in fa_fonts])
    print("فونت‌های انگلیسی:", [os.path.basename(f) for f in en_fonts])

    rng = random.Random(args.seed)
    img_dir = os.path.join(args.out, "images")
    lbl_dir = os.path.join(args.out, "labels")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(lbl_dir, exist_ok=True)
    crop_dir = os.path.join(args.out, "crops")
    gt_rows = []
    if args.crops:
        os.makedirs(crop_dir, exist_ok=True)

    for i in range(1, args.count + 1):
        name = f"syn{args.seed}_{i:04d}"
        page, lines = make_page(rng, fa_fonts, en_fonts)
        augment(page, rng).save(os.path.join(img_dir, name + ".png"))
        with open(os.path.join(lbl_dir, name + ".txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(t for t, _, _ in lines))
        if args.crops:
            for k, (text, kind, im) in enumerate(lines):
                crop_name = f"{name}_{k}.png"
                augment(im, rng).save(os.path.join(crop_dir, crop_name))
                gt_rows.append(f"crops/{crop_name}\t{text}")

    if args.crops:
        with open(os.path.join(args.out, "gt.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(gt_rows))
    print("تمام شد:", args.out)


if __name__ == "__main__":
    main()