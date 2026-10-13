"""시스템 사양 자동 감지 — GPU VRAM 기준 LLM 설치 분기.

기준 (현 노트북 Intel Iris Xe 1GB 기준 10배):
- GPU ≥ 10GB & RAM ≥ 32GB -> full (Ollama Llama 8B + RAG)
- GPU ≥ 6GB  & RAM ≥ 16GB -> lite (Ollama Gemma 2B + RAG)
- else                       -> rag_only (RAG 만, LLM = Claude API)

결과: ~/.claude/cache/system-tier.json 에 캐시.
"""
import sys
import os
import json
import subprocess
import shutil
from pathlib import Path

CACHE_PATH = Path.home() / ".claude" / "cache" / "system-tier.json"
CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

# LLM 설치 한계 (이 노트북 1GB GPU 의 10배)
LLM_FULL_MIN_VRAM_GB = 10
LLM_FULL_MIN_RAM_GB = 32
LLM_LITE_MIN_VRAM_GB = 6
LLM_LITE_MIN_RAM_GB = 16


def detect_gpu_vram_gb() -> float:
    """GPU VRAM (GB) 감지 — Windows wmic + nvidia-smi fallback."""
    # nvidia-smi (정확)
    if shutil.which("nvidia-smi"):
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=10,
            )
            mb = max((int(line.strip()) for line in r.stdout.strip().splitlines() if line.strip()), default=0)
            return mb / 1024
        except Exception:
            pass
    # Windows wmic (integrated GPU)
    try:
        r = subprocess.run(
            ["wmic", "path", "win32_VideoController", "get", "AdapterRAM"],
            capture_output=True, text=True, timeout=10,
        )
        bytes_max = 0
        for line in r.stdout.strip().splitlines()[1:]:
            line = line.strip()
            if line.isdigit():
                bytes_max = max(bytes_max, int(line))
        return bytes_max / (1024**3)
    except Exception:
        return 0.0


def detect_ram_gb() -> float:
    try:
        import psutil
        return psutil.virtual_memory().total / (1024**3)
    except ImportError:
        return 0.0


def detect() -> dict:
    vram = detect_gpu_vram_gb()
    ram = detect_ram_gb()

    if vram >= LLM_FULL_MIN_VRAM_GB and ram >= LLM_FULL_MIN_RAM_GB:
        tier = "full"
        llm_install = "Ollama + Llama 3.1 8B"
    elif vram >= LLM_LITE_MIN_VRAM_GB and ram >= LLM_LITE_MIN_RAM_GB:
        tier = "lite"
        llm_install = "Ollama + Gemma 2 2B"
    else:
        tier = "rag_only"
        llm_install = "X (Claude API 사용)"

    result = {
        "tier": tier,
        "gpu_vram_gb": round(vram, 2),
        "ram_gb": round(ram, 2),
        "llm_install": llm_install,
        "rag_install": "ChromaDB + Voyage embedding (항상 설치)",
        "thresholds": {
            "full": f"VRAM ≥ {LLM_FULL_MIN_VRAM_GB}GB & RAM ≥ {LLM_FULL_MIN_RAM_GB}GB",
            "lite": f"VRAM ≥ {LLM_LITE_MIN_VRAM_GB}GB & RAM ≥ {LLM_LITE_MIN_RAM_GB}GB",
        },
    }
    CACHE_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    if "--force" in sys.argv:
        # 캐시 무시
        result = detect()
    elif CACHE_PATH.exists():
        # 캐시 사용
        result = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    else:
        result = detect()
    print(json.dumps(result, ensure_ascii=False, indent=2))
