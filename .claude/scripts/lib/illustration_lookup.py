"""illustration keyword → docs/screens/illustration/<sub>/<jpg> 매치.

빌더 (build-*-html-diagrams.py, design_word, design_ppt) 가 챕터 keyword 로 호출:
    >>> from illustration_lookup import find
    >>> find("기린"  )  # → '...illustration/animal/dribbble-XXX.jpg'
    >>> find("로그인 화면")  # → '...login/<jpg>'

전략:
1. 한글 keyword → 영문 카테고리 매핑 (사전)
2. 카테고리 폴더에서 무작위 jpg 선택 (또는 hash 로 일관)
3. 매치 없으면 illustration/etc/ 또는 None
"""
import hashlib
import os
import random
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCREENS = PROJECT_ROOT / "docs" / "screens"
ILLUSTRATION = SCREENS / "illustration"

# 한글 keyword → illustration sub-카테고리
KEYWORD_MAP = {
    # 동물
    "동물": "animal", "기린": "animal", "사자": "animal", "고양이": "animal",
    "강아지": "animal", "새": "animal", "물고기": "animal", "곰": "animal",
    "원숭이": "animal", "토끼": "animal", "여우": "animal",
    # 사람/캐릭터
    "사람": "character", "캐릭터": "character", "인물": "portrait",
    "팀": "character", "프로필": "portrait", "아바타": "avatar",
    # 자연
    "식물": "plant", "꽃": "plant", "나무": "plant", "잎": "plant",
    "풍경": "scenery", "산": "scenery", "바다": "scenery", "하늘": "scenery",
    # 음식
    "음식": "food", "커피": "food", "음료": "food", "과일": "food",
    # 운송
    "자동차": "transport", "비행기": "transport", "기차": "transport", "로켓": "transport",
    "운송": "transport", "교통": "transport",
    # 건물
    "건물": "building", "집": "building", "아파트": "building", "건축": "building",
    # 기술·UI
    "차트": "chart", "그래프": "chart", "데이터": "chart", "시각화": "chart",
    "아이콘": "icon", "로고": "logo", "타이포": "typography",
    "모바일": "mockup", "디바이스": "mockup", "스마트폰": "mockup",
    "UI": "ui-screen", "화면": "ui-screen", "인터페이스": "ui-screen",
    "포스터": "poster", "배너": "poster",
    # 추상
    "패턴": "pattern", "텍스처": "pattern", "벽지": "pattern",
    "그라데이션": "gradient", "컬러": "gradient",
    "도형": "abstract-shape", "추상": "abstract-shape",
    "3D": "3d", "3d": "3d", "입체": "3d",
    # etc 후 분류
    "스티커": "sticker", "배지": "badge", "에디토리얼": "editorial",
    "낙서": "doodle", "스케치": "doodle",
    # UI 카테고리 (illustration 외)
    "로그인": "login", "회원가입": "signup", "결제": "checkout", "체크아웃": "checkout",
    "대시보드": "dashboard", "메뉴": "menu", "가격": "pricing", "요금": "pricing",
    "온보딩": "onboarding", "폼": "form", "검색": "search", "설정": "settings",
    "알림": "notification", "404": "404", "오류": "404",
}

# 영문 keyword (fallback)
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
    """keyword (한·영) → category name 또는 None."""
    kw = keyword.lower().strip()
    # 정확한 매치 우선
    if kw in KEYWORD_MAP:
        return KEYWORD_MAP[kw]
    if kw in EN_KEYWORD:
        return EN_KEYWORD[kw]
    # 부분 매치 (keyword 가 dict 어휘 포함)
    for k, v in KEYWORD_MAP.items():
        if k in kw or kw in k:
            return v
    for k, v in EN_KEYWORD.items():
        if k in kw or kw in k:
            return v
    return None


def _category_dir(category: str) -> Optional[Path]:
    """category → 실제 폴더 path (illustration sub 우선, 그 다음 docs/screens/ 카테고리)."""
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
    """docs/screens/custom/ 에서 keyword 매치 (사용자 ChatGPT 또는 Pollinations 생성)."""
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
    """keyword → 매치되는 jpg 절대경로.

    매치 우선순위:
    1. docs/screens/custom/<keyword-*>.jpg (사용자 import 또는 이전 Pollinations 생성)
    2. docs/screens/illustration/<sub>/ 또는 UI 카테고리
    3. auto_generate=True 면 Pollinations.ai 자동 호출 → custom/ 저장

    Args:
        keyword: 한글 또는 영문 검색어
        deterministic: True 면 hash 기반 일관 선택
        auto_generate: 매치 없으면 Pollinations 자동 호출
        brand_cluster: warm-editorial/dark-minimal/etc — style hint

    Returns:
        jpg 절대경로 또는 None
    """
    # 1. custom/ 우선
    custom = _custom_match(keyword)
    if custom:
        return custom

    # 2. illustration/ + UI 카테고리
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

    # 3. auto-generate (Pollinations.ai) — 무료, 30초 정도
    if auto_generate:
        try:
            import sys as _sys
            _sys.path.insert(0, str(Path(__file__).parent))
            from pollinations_client import generate_to_file
            # 한글 keyword → 영문 prompt 자동 보강
            prompt = f"{keyword}, flat design illustration, clean modern style"
            return generate_to_file(prompt, keyword, brand_cluster=brand_cluster)
        except Exception as e:
            return None

    return None


def find_many(keyword: str, count: int = 3) -> list:
    """count 개의 jpg 경로 list 반환 (부족하면 있는 만큼)."""
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
    """illustration 폴더 + UI 카테고리 jpg 카운트."""
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
