"""CLIP — UI 카테고리들 (signup·checkout·login·dashboard 등) sub 분류.

각 카테고리당 5 sub: dark-theme / light-theme / mobile / minimalist / illustrative.
"""
import time
from pathlib import Path

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

ROOT = Path(__file__).resolve().parent.parent.parent
SCREENS = ROOT / "docs" / "screens"

UI_CATS = ["signup", "checkout", "login", "dashboard", "menu", "pricing",
           "onboarding", "form", "search", "settings", "profile",
           "notification", "404", "color-typo", "template"]

CATEGORIES = {
    "dark":         "a dark mode UI design with black or dark navy background",
    "light":        "a light mode UI design with white or cream background",
    "mobile":       "a mobile phone UI screen, vertical mobile interface",
    "minimalist":   "a minimalist clean UI design with lots of whitespace",
    "illustrative": "a UI screen with illustrations, characters, or 3D elements",
    "colorful":     "a colorful vibrant UI design with bright colors and gradients",
}


def main():
    model_name = "openai/clip-vit-base-patch32"
    print(f"[load] {model_name}", flush=True)
    t0 = time.time()
    processor = CLIPProcessor.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name)
    model.eval()
    print(f"[load] {int(time.time() - t0)}s", flush=True)

    text_prompts = list(CATEGORIES.values())
    category_keys = list(CATEGORIES.keys())

    grand_total = 0
    grand_start = time.time()
    grand_summary = {k: 0 for k in category_keys}

    for ui_cat in UI_CATS:
        src = SCREENS / ui_cat
        if not src.exists():
            continue
        # sub 폴더 생성
        for sub in category_keys:
            (src / sub).mkdir(exist_ok=True)
        # 이미지 list (sub 폴더 제외)
        images = []
        for f in src.iterdir():
            if f.is_file() and f.suffix.lower() in (".jpg",".jpeg",".png",".webp"):
                images.append(f)
        if not images:
            continue
        print(f"\n=== {ui_cat}: {len(images)} images ===", flush=True)
        summary = {k: 0 for k in category_keys}
        start = time.time()
        for i, img_path in enumerate(images, 1):
            try:
                img = Image.open(img_path).convert("RGB")
                inputs = processor(text=text_prompts, images=img, return_tensors="pt", padding=True)
                with torch.no_grad():
                    outputs = model(**inputs)
                    probs = outputs.logits_per_image.softmax(dim=-1)
                    best_idx = probs.argmax(dim=-1).item()
                cat = category_keys[best_idx]
                new_path = src / cat / img_path.name
                img_path.rename(new_path)
                summary[cat] += 1
                grand_summary[cat] += 1
                if i % 50 == 0 or i == len(images):
                    elapsed = int(time.time() - start)
                    print(f"  [{i}/{len(images)}] {cat} · {elapsed}s", flush=True)
            except Exception as e:
                print(f"  [FAIL] {img_path.name}: {type(e).__name__}", flush=True)
        grand_total += len(images)
        print(f"  {ui_cat}: " + " · ".join(f"{k}={v}" for k,v in summary.items()), flush=True)

    elapsed = int(time.time() - grand_start)
    print(f"\n[DONE] {grand_total} classified / {elapsed}s", flush=True)
    print("\n=== 전체 sub 합계 ===", flush=True)
    for k, v in sorted(grand_summary.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}", flush=True)


if __name__ == "__main__":
    main()
