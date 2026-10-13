"""illustration keyword -> docs/screens/illustration/<sub>/<jpg> 留ㅼ튂.

鍮뚮뜑 (build-*-html-diagrams.py, design_word, design_ppt) 媛 梨뺥꽣 keyword 濡??몄텧:
    >>> from illustration_lookup import find
    >>> find("湲곕┛"  )  # -> '...illustration/animal/dribbble-XXX.jpg'
    >>> find("濡쒓렇???붾㈃")  # -> '...login/<jpg>'

?꾨왂:
1. ?쒓? keyword -> ?곷Ц 移댄뀒怨좊━ 留ㅽ븨 (?ъ쟾)
2. 移댄뀒怨좊━ ?대뜑?먯꽌 臾댁옉??jpg ?좏깮 (?먮뒗 hash 濡??쇨?)
3. 留ㅼ튂 ?놁쑝硫?illustration/etc/ ?먮뒗 None
"""
import hashlib
import os
import random
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCREENS = PROJECT_ROOT / "docs" / "screens"
ILLUSTRATION = SCREENS / "illustration"

# ?쒓? keyword -> illustration sub-移댄뀒怨좊━
KEYWORD_MAP = {
    # ?숇Ъ
    "?숇Ъ": "animal", "湲곕┛": "animal", "?ъ옄": "animal", "怨좎뼇??: "animal",
    "媛뺤븘吏": "animal", "??: "animal", "臾쇨퀬湲?: "animal", "怨?: "animal",
    "?먯댂??: "animal", "?좊겮": "animal", "?ъ슦": "animal",
    # ?щ엺/罹먮┃??
    "?щ엺": "character", "罹먮┃??: "character", "?몃Ъ": "portrait",
    "?": "character", "?꾨줈??: "portrait", "?꾨컮?": "avatar",
    # ?먯뿰
    "?앸Ъ": "plant", "苑?: "plant", "?섎Т": "plant", "??: "plant",
    "?띻꼍": "scenery", "??: "scenery", "諛붾떎": "scenery", "?섎뒛": "scenery",
    # ?뚯떇
    "?뚯떇": "food", "而ㅽ뵾": "food", "?뚮즺": "food", "怨쇱씪": "food",
    # ?댁넚
    "?먮룞李?: "transport", "鍮꾪뻾湲?: "transport", "湲곗감": "transport", "濡쒖폆": "transport",
    "?댁넚": "transport", "援먰넻": "transport",
    # 嫄대Ъ
    "嫄대Ъ": "building", "吏?: "building", "?꾪뙆??: "building", "嫄댁텞": "building",
    # 湲곗닠-UI
    "李⑦듃": "chart", "洹몃옒??: "chart", "?곗씠??: "chart", "?쒓컖??: "chart",
    "?꾩씠肄?: "icon", "濡쒓퀬": "logo", "??댄룷": "typography",
    "紐⑤컮??: "mockup", "?붾컮?댁뒪": "mockup", "?ㅻ쭏?명룿": "mockup",
    "UI": "ui-screen", "?붾㈃": "ui-screen", "?명꽣?섏씠??: "ui-screen",
    "?ъ뒪??: "poster", "諛곕꼫": "poster",
    # 異붿긽
    "?⑦꽩": "pattern", "?띿뒪泥?: "pattern", "踰쎌?": "pattern",
    "洹몃씪?곗씠??: "gradient", "而щ윭": "gradient",
    "?꾪삎": "abstract-shape", "異붿긽": "abstract-shape",
    "3D": "3d", "3d": "3d", "?낆껜": "3d",
    # etc ??遺꾨쪟
    "?ㅽ떚而?: "sticker", "諛곗?": "badge", "?먮뵒?좊━??: "editorial",
    "?숈꽌": "doodle", "?ㅼ?移?: "doodle",
    # UI 移댄뀒怨좊━ (illustration ??
    "濡쒓렇??: "login", "?뚯썝媛??: "signup", "寃곗젣": "checkout", "泥댄겕?꾩썐": "checkout",
    "??쒕낫??: "dashboard", "硫붾돱": "menu", "媛寃?: "pricing", "?붽툑": "pricing",
    "?⑤낫??: "onboarding", "??: "form", "寃??: "search", "?ㅼ젙": "settings",
    "?뚮┝": "notification", "404": "404", "?ㅻ쪟": "404",
}

# ?곷Ц keyword (fallback)
EN_KEYWORD = {
    "giraffe": "animal", "cat": "animal", "dog": "animal", "bird": "animal",
    "person": "character", "people": "character", "team": "character",
    "flower": "plant", "tree": "plant",
    "car": "transport", "plane": "transport",
    "house": "building", "building": "building",
    "chart": "chart", "graph": "chart", "dashboard": "dashboard",
    "icon": "icon", "logo": "logo", "typography": "typography",
    "mobile": "mockup", "device": "mockup",
    "pattern": "pattern", "gradient": "gradient", "abstract": "abstract-shape",
    "3d": "3d", "3D": "3d",
    "login": "login", "signup": "signup", "checkout": "checkout",
    "pricing": "pricing", "onboarding": "onboarding", "form": "form",
    "menu": "menu", "settings": "settings", "search": "search",
}


def _resolve_category(keyword: str) -> Optional[str]:
    """keyword (???? -> category name ?먮뒗 None."""
    kw = keyword.lower().strip()
    # ?뺥솗??留ㅼ튂 ?곗꽑
    if kw in KEYWORD_MAP:
        return KEYWORD_MAP[kw]
    if kw in EN_KEYWORD:
        return EN_KEYWORD[kw]
    # 遺遺?留ㅼ튂 (keyword 媛 dict ?댄쐶 ?ы븿)
    for k, v in KEYWORD_MAP.items():
        if k in kw or kw in k:
            return v
    for k, v in EN_KEYWORD.items():
        if k in kw or kw in k:
            return v
    return None


def _category_dir(category: str) -> Optional[Path]:
    """category -> ?ㅼ젣 ?대뜑 path (illustration sub ?곗꽑, 洹??ㅼ쓬 docs/screens/ 移댄뀒怨좊━)."""
    # 1. illustration sub
    sub = ILLUSTRATION / category
    if sub.exists() and any(sub.iterdir()):
        return sub
    # 2. docs/screens/<category>
    main = SCREENS / category
    if main.exists() and any(main.iterdir()):
        return main
    return None


CUSTOM_DIR = SCREENS / "custom"


def _custom_match(keyword: str) -> Optional[str]:
    """docs/screens/custom/ ?먯꽌 keyword 留ㅼ튂 (?ъ슜??ChatGPT ?먮뒗 Pollinations ?앹꽦)."""
    if not CUSTOM_DIR.exists():
        return None
    kw_lower = keyword.lower().replace(" ", "-")
    for f in CUSTOM_DIR.iterdir():
        if not f.is_file():
            continue
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        if kw_lower in f.stem.lower():
            return str(f)
    return None


def find(keyword: str, deterministic: bool = True,
         auto_generate: bool = False, brand_cluster: Optional[str] = None) -> Optional[str]:
    """keyword -> 留ㅼ튂?섎뒗 jpg ?덈?寃쎈줈.

    留ㅼ튂 ?곗꽑?쒖쐞:
    1. docs/screens/custom/<keyword-*>.jpg (?ъ슜??import ?먮뒗 ?댁쟾 Pollinations ?앹꽦)
    2. docs/screens/illustration/<sub>/ ?먮뒗 UI 移댄뀒怨좊━
    3. auto_generate=True 硫?Pollinations.ai ?먮룞 ?몄텧 -> custom/ ???

    Args:
        keyword: ?쒓? ?먮뒗 ?곷Ц 寃?됱뼱
        deterministic: True 硫?hash 湲곕컲 ?쇨? ?좏깮
        auto_generate: 留ㅼ튂 ?놁쑝硫?Pollinations ?먮룞 ?몄텧
        brand_cluster: warm-editorial/dark-minimal/etc ??style hint

    Returns:
        jpg ?덈?寃쎈줈 ?먮뒗 None
    """
    # 1. custom/ ?곗꽑
    custom = _custom_match(keyword)
    if custom:
        return custom

    # 2. illustration/ + UI 移댄뀒怨좊━
    category = _resolve_category(keyword)
    if category:
        dir_path = _category_dir(category)
        if dir_path:
            images = []
            for ext in (".jpg", ".jpeg", ".png", ".webp"):
                images.extend(sorted(dir_path.rglob(f"*{ext}")))
            if images:
                if deterministic:
                    h = int(hashlib.md5(keyword.encode("utf-8")).hexdigest(), 16)
                    return str(images[h % len(images)])
                return str(random.choice(images))

    # 3. auto-generate (Pollinations.ai) ??臾대즺, 30珥??뺣룄
    if auto_generate:
        try:
            import sys as _sys
            _sys.path.insert(0, str(Path(__file__).parent))
            from pollinations_client import generate_to_file
            # ?쒓? keyword -> ?곷Ц prompt ?먮룞 蹂닿컯
            prompt = f"{keyword}, flat design illustration, clean modern style"
            return generate_to_file(prompt, keyword, brand_cluster=brand_cluster)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            return None

    return None


def find_many(keyword: str, count: int = 3) -> list:
    """count 媛쒖쓽 jpg 寃쎈줈 list 諛섑솚 (遺議깊븯硫??덈뒗 留뚰겮)."""
    category = _resolve_category(keyword)
    if not category:
        return []
    dir_path = _category_dir(category)
    if not dir_path:
        return []
    images = []
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        images.extend(sorted(dir_path.rglob(f"*{ext}")))
    if not images:
        return []
    h = int(hashlib.md5(keyword.encode("utf-8")).hexdigest(), 16)
    out = []
    for i in range(min(count, len(images))):
        out.append(str(images[(h + i) % len(images)]))
    return out


def stats() -> dict:
    """illustration ?대뜑 + UI 移댄뀒怨좊━ jpg 移댁슫??"""
    out = {}
    for sub in ILLUSTRATION.iterdir():
        if sub.is_dir():
            count = sum(1 for _ in sub.rglob("*.jpg")) + \
                    sum(1 for _ in sub.rglob("*.png")) + \
                    sum(1 for _ in sub.rglob("*.webp"))
            if count > 0:
                out[f"illustration/{sub.name}"] = count
    for ui_cat in ("login", "signup", "checkout", "dashboard", "menu", "pricing",
                    "onboarding", "form", "search", "settings", "profile",
                    "notification", "404", "color-typo", "template"):
        cat_path = SCREENS / ui_cat
        if cat_path.exists():
            count = sum(1 for _ in cat_path.rglob("*.jpg"))
            if count > 0:
                out[ui_cat] = count
    return out


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) > 1:
        kw = " ".join(sys.argv[1:])
        result = find(kw)
        print(f"keyword: {kw}")
        print(f"result: {result}")
        if result:
            print(f"size: {os.path.getsize(result) // 1024} KB")
    else:
        print(json.dumps(stats(), ensure_ascii=False, indent=2))

