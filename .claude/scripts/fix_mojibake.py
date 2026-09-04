"""
Fix UTF-8 -> CP949 -> UTF-8 mojibake (한글 깨짐 복원).
사용: python .claude/scripts/fix_mojibake.py <file1> [file2 ...]
"""
import sys
import shutil
from pathlib import Path

def try_unmojibake(text: str) -> tuple[str, int]:
    """깨진 텍스트를 한글로 복원 시도. 복원 글자 수 반환."""
    # UTF-8로 읽힌 텍스트를 cp949로 다시 인코딩 후 utf-8로 디코딩
    fixed_chars = []
    fixed_count = 0
    i = 0
    while i < len(text):
        ch = text[i]
        # 정상 한글 또는 ASCII는 그대로
        if ord(ch) < 128 or ('\uac00' <= ch <= '\ud7a3') or ('\u3131' <= ch <= '\u318e'):
            fixed_chars.append(ch)
            i += 1
            continue
        # 의심 문자 (mojibake 패턴) — 다음 N글자를 모아서 cp949 reverse 시도
        # 한 번에 6~12 byte 단위로 시도
        best = None
        for n in range(2, 14):
            chunk = text[i:i+n]
            try:
                # mojibake -> 원래 bytes -> 한글
                raw = chunk.encode('cp949', errors='strict')
                korean = raw.decode('utf-8', errors='strict')
                # 복원 결과가 정상 한글 범위인지 확인
                if all(('\uac00' <= c <= '\ud7a3') or ('\u3131' <= c <= '\u318e') or c in ' .,!?-()' for c in korean):
                    best = (korean, n)
                    break
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
        if best:
            fixed_chars.append(best[0])
            fixed_count += len(best[0])
            i += best[1]
        else:
            fixed_chars.append(ch)
            i += 1
    return ''.join(fixed_chars), fixed_count


def fix_file(path: Path, dry_run: bool = False) -> dict:
    raw = path.read_bytes()
    # BOM 제거
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    text = raw.decode('utf-8', errors='replace')
    # CRLF 보존
    crlf = '\r\n' in text
    fixed, count = try_unmojibake(text)
    if count == 0:
        return {"file": str(path), "fixed_chars": 0, "skipped": True}
    if dry_run:
        return {"file": str(path), "fixed_chars": count, "preview": fixed[:200]}
    # 백업 생성
    bak = path.with_suffix(path.suffix + '.mojibake-bak')
    shutil.copy2(path, bak)
    # 저장
    out_bytes = fixed.encode('utf-8')
    path.write_bytes(out_bytes)
    return {"file": str(path), "fixed_chars": count, "backup": str(bak)}


if __name__ == '__main__':
    args = sys.argv[1:]
    dry = '--dry' in args
    files = [a for a in args if not a.startswith('--')]
    for f in files:
        p = Path(f)
        if not p.exists():
            print(f"[skip] {f} (not found)")
            continue
        result = fix_file(p, dry_run=dry)
        print(result)
