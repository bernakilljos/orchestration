"""CLIP 분류 v2 — 더 세분화 카테고리 (20개).

dribbble illustration 의 실제 분포에 맞춘 prompts.
character-etc 가 등 큰 폴더를 더 세분화.
"""
import time
from pathlib import Path

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT / "docs" / "screens" / "illustration"

CATEGORIES = {
    # 사람/캐릭터
    "human":          "a photo of real people, person, photographer",
    "character":      "a cartoon character, mascot, or stylized human figure illustration",
    "portrait":       "a portrait painting or drawing of a face",

    # 자연/생물
    "animal":         "an illustration of an animal, wildlife, pet, dog, cat, bird",
    "plant":          "an illustration of plants, flowers, trees, leaves, botanical",
    "scenery":        "a landscape, mountains, beach, sunset, city skyline, outdoor scene",

    # 음식/사물
    "food":           "an illustration of food, drink, meal, fruit, coffee",
    "transport":      "an illustration of a vehicle, car, ship, train, plane, rocket, transportation",
    "building":       "an illustration of architecture, building, house, structure",

    # 디지털-UI
    "chart":          "a chart, graph, data visualization, bar or line chart, dashboard",
    "icon":           "an icon set, app icon, symbol icons, glyph",
    "logo":           "a brand logo, wordmark, monogram, brand identity",
    "typography":     "typography poster, lettering, calligraphy, font specimen",
    "mockup":         "a phone or laptop product mockup, device mockup",
    "ui-screen":      "a user interface screen, app interface, dashboard interface design",
    "poster":         "a poster, banner, advertisement design, hero artwork",

    # 추상
    "pattern":        "a repeating pattern, texture, geometric tile, wallpaper",
    "gradient":       "an abstract gradient, color blend, soft color composition",
    "abstract-shape": "abstract geometric shapes, sphere, cube, fluid shapes, blobs",
    "3d":             "a 3D rendered illustration, 3D character, 3D object",

    "etc":            "miscellaneous illustration not matching other categories",
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

    # 모든 카테고리 폴더 (기존 + 신규)
    for cat in category_keys:
        (SRC_DIR / cat).mkdir(exist_ok=True)

    # 이미지 list — 기존 폴더 내 + root 둘 다 수집 (재분류)
    images = []
    for f in SRC_DIR.rglob("*"):
        if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            images.append(f)
    print(f"[total] {len(images)} images (재분류)", flush=True)

    summary = {k: 0 for k in category_keys}
    skipped = 0
    start = time.time()
    for i, img_path in enumerate(images, 1):
        try:
            img = Image.open(img_path).convert("RGB")
            inputs = processor(text=text_prompts, images=img, return_tensors="pt", padding=True)
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits_per_image
                probs = logits.softmax(dim=-1)
                best_idx = probs.argmax(dim=-1).item()
            cat = category_keys[best_idx]
            score = probs[0, best_idx].item()
            # 폴더로 이동 (현재 폴더와 다르면)
            target_dir = SRC_DIR / cat
            new_path = target_dir / img_path.name
            if img_path.resolve() != new_path.resolve():
                img_path.rename(new_path)
            summary[cat] += 1
            if i % 50 == 0 or i == len(images):
                elapsed = int(time.time() - start)
                rate = i / max(elapsed, 1)
                eta = int((len(images) - i) / max(rate, 0.1))
                print(f"  [{i}/{len(images)}] {cat} ({score:.2f}) - {elapsed}s - ETA {eta}s", flush=True)
        except Exception as e:
            skipped += 1
            print(f"  [FAIL] {img_path.name}: {type(e).__name__} {str(e)[:60]}", flush=True)
    elapsed = int(time.time() - start)
    print(f"\n[DONE] {sum(summary.values())} classified / {skipped} skipped / {elapsed}s", flush=True)
    print("\n=== 분류 결과 ===", flush=True)
    for k, v in sorted(summary.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}", flush=True)


if __name__ == "__main__":
    main()
