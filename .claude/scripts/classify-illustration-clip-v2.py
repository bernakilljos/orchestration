"""CLIP 遺꾨쪟 v2 ?????몃텇??移댄뀒怨좊━ (20媛?.

dribbble illustration ???ㅼ젣 遺꾪룷??留욎텣 prompts.
character-etc 媛 ?????대뜑瑜????몃텇??
"""
import time
from pathlib import Path

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT / "docs" / "screens" / "illustration"

CATEGORIES = {
    # ?щ엺/罹먮┃??
    "human":          "a photo of real people, person, photographer",
    "character":      "a cartoon character, mascot, or stylized human figure illustration",
    "portrait":       "a portrait painting or drawing of a face",

    # ?먯뿰/?앸Ъ
    "animal":         "an illustration of an animal, wildlife, pet, dog, cat, bird",
    "plant":          "an illustration of plants, flowers, trees, leaves, botanical",
    "scenery":        "a landscape, mountains, beach, sunset, city skyline, outdoor scene",

    # ?뚯떇/?щЪ
    "food":           "an illustration of food, drink, meal, fruit, coffee",
    "transport":      "an illustration of a vehicle, car, ship, train, plane, rocket, transportation",
    "building":       "an illustration of architecture, building, house, structure",

    # ?붿???UI
    "chart":          "a chart, graph, data visualization, bar or line chart, dashboard",
    "icon":           "an icon set, app icon, symbol icons, glyph",
    "logo":           "a brand logo, wordmark, monogram, brand identity",
    "typography":     "typography poster, lettering, calligraphy, font specimen",
    "mockup":         "a phone or laptop product mockup, device mockup",
    "ui-screen":      "a user interface screen, app interface, dashboard interface design",
    "poster":         "a poster, banner, advertisement design, hero artwork",

    # 異붿긽
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

    # 紐⑤뱺 移댄뀒怨좊━ ?대뜑 (湲곗〈 + ?좉퇋)
    for cat in category_keys:
        (SRC_DIR / cat).mkdir(exist_ok=True)

    # ?대?吏 list ??湲곗〈 ?대뜑 ??+ root ?????섏쭛 (?щ텇瑜?
    images = []
    for f in SRC_DIR.rglob("*"):
        if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            images.append(f)
    print(f"[total] {len(images)} images (?щ텇瑜?", flush=True)

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
            # ?대뜑濡??대룞 (?꾩옱 ?대뜑? ?ㅻⅤ硫?
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
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            skipped += 1
            print(f"  [FAIL] {img_path.name}: {type(e).__name__} {str(e)[:60]}", flush=True)
    elapsed = int(time.time() - start)
    print(f"\n[DONE] {sum(summary.values())} classified / {skipped} skipped / {elapsed}s", flush=True)
    print("\n=== 遺꾨쪟 寃곌낵 ===", flush=True)
    for k, v in sorted(summary.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}", flush=True)


if __name__ == "__main__":
    main()

