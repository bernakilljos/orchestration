"""CLIP v3 — illustration/etc 330 만 더 세분화 재분류."""
import time
from pathlib import Path

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT / "docs" / "screens" / "illustration" / "etc"

CATEGORIES = {
    "avatar":        "an avatar profile picture, head bust portrait icon",
    "sticker":       "a sticker, fun emoji sticker, decorative sticker design",
    "badge":         "a badge, award, achievement seal, ribbon emblem",
    "spot-illust":   "a small spot illustration, decorative illustration, hand-drawn vignette",
    "editorial":     "an editorial magazine illustration with composition and storytelling",
    "infographic":   "an infographic with text labels, arrows, multiple sections explaining a concept",
    "doodle":        "a doodle sketch, line drawing, hand-drawn cartoon",
    "art-piece":     "a fine art painting, surreal artwork, gallery art piece",
    "color-palette": "a color palette with multiple color swatches displayed",
    "device-mockup": "a phone, laptop, tablet, smartwatch device mockup with screen",
    "background":    "a textured or photographic background image, blurred backdrop",
    "neon":          "a neon sign, glowing light effect, electric neon graphic",
    "stilllife":     "a still life arrangement, props composition, decorative objects",
    "etc":           "uncategorized miscellaneous graphic",
}


def main():
    if not SRC_DIR.exists():
        print(f"no etc folder: {SRC_DIR}", flush=True)
        return
    model_name = "openai/clip-vit-base-patch32"
    print(f"[load] {model_name}", flush=True)
    t0 = time.time()
    processor = CLIPProcessor.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name)
    model.eval()
    print(f"[load] {int(time.time() - t0)}s", flush=True)

    text_prompts = list(CATEGORIES.values())
    category_keys = list(CATEGORIES.keys())
    parent = SRC_DIR.parent
    for cat in category_keys:
        if cat != "etc":
            (parent / cat).mkdir(exist_ok=True)

    images = [f for f in SRC_DIR.iterdir() if f.is_file() and f.suffix.lower() in (".jpg",".jpeg",".png",".webp")]
    print(f"[etc total] {len(images)}", flush=True)

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
            score = probs[0, best_idx].item()
            # etc 는 그대로 두고, 그 외는 sibling 폴더로 이동
            if cat != "etc":
                new_path = parent / cat / img_path.name
                img_path.rename(new_path)
            summary[cat] += 1
            if i % 50 == 0 or i == len(images):
                elapsed = int(time.time() - start)
                eta = int((len(images) - i) / max(i/max(elapsed,1), 0.1))
                print(f"  [{i}/{len(images)}] {cat} ({score:.2f}) · {elapsed}s · ETA {eta}s", flush=True)
        except Exception as e:
            print(f"  [FAIL] {img_path.name}: {type(e).__name__} {str(e)[:60]}", flush=True)
    elapsed = int(time.time() - start)
    print(f"\n[DONE] {elapsed}s", flush=True)
    print("\n=== etc 재분류 결과 ===", flush=True)
    for k, v in sorted(summary.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}", flush=True)


if __name__ == "__main__":
    main()
