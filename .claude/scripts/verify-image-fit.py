"""verify-image-fit.py — docs/screens/arch-kor/*.png 의 비율을 페이지 비율과 비교.

teaching-doc.md § 페이지 fit 사전검증 자동화.
hook-09-ocr-verify.sh 에서 build-*-diagrams.py 호출 후 발동.

PASS: PNG 비율이 페이지 비율 (landscape 0.69 ± 0.05) 안
FAIL: 비율 불일치 -> docx 에서 짤림 또는 빈 공간
"""
import sys
import io
from pathlib import Path

# Windows 콘솔 cp949 회피
try:
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except (AttributeError, Exception):
    pass

try:
    from PIL import Image
except ImportError:
    print("[SKIP] Pillow not installed - pip install Pillow")
    sys.exit(0)

ROOT = Path(__file__).resolve().parent.parent.parent
TARGET = ROOT / "docs" / "screens" / "arch-kor"

# 산출물별 페이지 비율 (margin 제외, h/w) — 확장 가능
RATIOS = {
    # === 문서 (A4 기본) ===
    "docx-portrait":     1.46,    # 8.27×11.69 -> 사용 6.5×9.5
    "docx-landscape":    0.69,    # 11.69×8.27 -> 사용 9.5×6.6
    "pdf-portrait":      1.41,    # A4
    "pdf-landscape":     0.71,    # A4
    # === A3 / A5 / Letter ===
    "a3-portrait":       1.41,
    "a3-landscape":      0.71,
    "a5-portrait":       1.41,
    "a5-landscape":      0.71,
    "letter-portrait":   1.29,    # 8.5×11
    "letter-landscape":  0.77,
    # === 슬라이드 ===
    "pptx-16:9":         0.54,    # 13.33×7.5 -> 사용 12.5×6.7
    "pptx-4:3":          0.71,    # 10×7.5
    "google-slides":     0.54,    # 16:9
    "keynote":           0.54,    # 16:9
    # === 전자책 ===
    "epub-portrait":     1.50,    # 6×9 in
    "kindle":            1.60,    # 표준
    # === 영상 ===
    "video-16:9":        0.5625,  # 1920×1080 YouTube
    "video-9:16":        1.78,    # 1080×1920 Shorts/Reels
    "video-1:1":         1.0,     # 정사각 Instagram
    "youtube-thumbnail": 0.5625,  # 1280×720
    # === 소셜 ===
    "instagram-square":  1.0,
    "instagram-story":   1.78,    # 9:16
    "instagram-portrait": 1.25,   # 4:5
    "facebook-cover":    0.524,   # 820×312
    "twitter-card":      0.563,   # 1200×675
    "linkedin-post":     1.0,     # 1:1 권장
    "tiktok":            1.78,    # 9:16
    # === 인쇄-기타 ===
    "business-card":     0.572,   # 89×51mm
    "poster-a2":         1.41,
    "card-3:2":          0.667,
}
TOLERANCE = 0.05

# 동적 산출물 자동 등록 — 사용자 액션 0 (RATIOS_USER.json 으로 확장 가능)
import os, json
USER_RATIOS = Path(__file__).parent.parent / "state" / "fit-ratios-user.json"
if USER_RATIOS.exists():
    try:
        with open(USER_RATIOS, encoding="utf-8") as f:
            RATIOS.update(json.load(f))
    except Exception:
        pass

# 기본: docx landscape (현재 lecture 빌더). 다른 산출물은 FIT_TARGET=<key>
EXPECTED_KEY = os.environ.get("FIT_TARGET", "docx-landscape")
EXPECTED = RATIOS.get(EXPECTED_KEY, 0.69)


def auto_register_ratio(name: str, width: int, height: int) -> None:
    """빌더 script 가 호출해서 RATIOS 동적 등록.

    예: from verify_image_fit import auto_register_ratio
        auto_register_ratio("my-custom-doc", 1600, 1100)
    """
    USER_RATIOS.parent.mkdir(parents=True, exist_ok=True)
    cur = {}
    if USER_RATIOS.exists():
        try:
            with open(USER_RATIOS, encoding="utf-8") as f:
                cur = json.load(f)
        except Exception:
            pass
    cur[name] = round(height / width, 4)
    with open(USER_RATIOS, "w", encoding="utf-8") as f:
        json.dump(cur, f, ensure_ascii=False, indent=2)

if not TARGET.exists():
    print(f"[SKIP] {TARGET} 없음")
    sys.exit(0)

problems = []
warnings = []
ok = 0
total = 0
for png in sorted(TARGET.glob("*.png")):
    total += 1
    try:
        with Image.open(png) as im:
            w, h = im.size
    except Exception as e:
        problems.append((png.name, f"PIL 오류: {e}"))
        continue
    ratio = h / w
    diff = abs(ratio - EXPECTED)

    # FAIL: 비율 큰 차이 (짤림 또는 빈 공간 ↑)
    if diff > TOLERANCE:
        problems.append((png.name, f"비율 {ratio:.2f} vs 기대 {EXPECTED:.2f} (차이 {diff:.2f}) — 짤림/여백 위험"))
        continue

    # WARN: 추가 검증 (빈 여백-콘텐츠 부족)
    # 매우 작은 PNG = 콘텐츠 부족 (예: width < 800 px)
    if w < 900:
        warnings.append((png.name, f"width {w}px 작음 — 정보 부족 또는 폰트 비율 ↓"))
    # 매우 큰 PNG = docx 에서 글씨 작아 보임 (해상도 ↑ 좋음 + 화면 표시 ↓)
    elif w > 2000:
        warnings.append((png.name, f"width {w}px 과대 — docx 박힐 때 화면 글씨 작음"))

    ok += 1

if problems:
    print(f"[FAIL] image-fit 검증 — {len(problems)}/{total} 비율 불일치")
    for name, msg in problems[:5]:
        print(f"  - {name}: {msg}")
    if len(problems) > 5:
        print(f"  ... {len(problems) - 5} more")
    print()
    print("권장: PNG viewport 비율을 페이지 비율과 일치시켜 재생성 (FIT_TARGET 환경변수)")
    sys.exit(2)

if warnings:
    print(f"[WARN] image-fit 검증 — {ok}/{total} PASS, 단 {len(warnings)} 경고")
    for name, msg in warnings[:5]:
        print(f"  - {name}: {msg}")
    sys.exit(0)

print(f"[PASS] image-fit 검증 — {ok}/{total} 모두 통과 (비율 {EXPECTED:.2f} ± {TOLERANCE})")
sys.exit(0)
