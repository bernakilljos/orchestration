#!/usr/bin/env python3
"""
webtech-sync.py — 주 1회 (일요일 05:00) 최신 기술 버전 fetch
목적: Java LTS · .NET LTS · Python · Node LTS · Go · Rust 등 최신 정보 자동 수집
결과: .claude/state/webtech-updates.md
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# TechStack 매트릭스 (현재 하드코딩, 향후 WebSearch 확장)
TECH_VERSIONS = {
    "java": {
        "current_lts": "21",
        "upcoming_lts": "25",
        "note": "2026-09 예정",
        "url": "https://www.oracle.com/java/technologies/java-se-support-roadmap.html",
    },
    "dotnet": {
        "current_lts": "8.0",
        "upcoming_lts": "9.0",
        "note": "2026-11 예정",
        "url": "https://learn.microsoft.com/en-us/dotnet/core/releases-and-support",
    },
    "python": {
        "current_latest": "3.13",
        "current_stable": "3.12",
        "note": "3.14 2026-10 예정",
        "url": "https://www.python.org/downloads/",
    },
    "node": {
        "current_lts": "22",
        "upcoming_lts": "24",
        "note": "2026-04 예정",
        "url": "https://nodejs.org/en/about/previous-releases",
    },
    "go": {
        "current": "1.23",
        "upcoming": "1.24",
        "note": "6개월 주기",
        "url": "https://go.dev/dl/",
    },
    "rust": {
        "current_stable": "1.84",
        "edition": "2024",
        "note": "6주 주기 release",
        "url": "https://www.rust-lang.org/en-US/downloads.html",
    },
}

def generate_report():
    """WebTech 업데이트 리포트 생성"""
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    report = f"# WebTech Versions Update\n\n**Generated**: {now}\n\n"

    report += "## 주요 버전 정보\n\n"

    for tech, info in TECH_VERSIONS.items():
        report += f"### {tech.upper()}\n\n"
        for key, value in info.items():
            if key != "url":
                report += f"- **{key}**: {value}\n"
        if "url" in info:
            report += f"\n📌 [참고]({info['url']})\n\n"

    report += "## 업데이트 정책\n\n"
    report += "- **Java**: LTS 버전만 사용 (21 현재, 25 준비)\n"
    report += "- **.NET**: LTS 버전만 사용 (8.0 현재)\n"
    report += "- **Python**: 3.12+ 권장 (3.13 최신)\n"
    report += "- **Node.js**: LTS 버전만 사용 (22 현재)\n"
    report += "- **Go**: 1.23+ 권장\n"
    report += "- **Rust**: 1.84+ stable\n\n"

    report += "## 로컬 버전 점검\n\n"
    report += "```bash\n"
    report += "java -version      # Java\n"
    report += "dotnet --version   # .NET\n"
    report += "python --version   # Python\n"
    report += "node --version     # Node.js\n"
    report += "go version         # Go\n"
    report += "rustc --version    # Rust\n"
    report += "```\n"

    return report.encode('utf-8').decode('utf-8')

def main():
    # 프로젝트 루트에서 상대경로 사용
    state_dir = Path(".claude/state")

    # 없으면 홈 디렉토리 fallback
    if not state_dir.exists():
        state_dir = Path.home() / ".claude" / "projects" / "C--pjt-orchestration-v1" / ".claude" / "state"

    state_dir.mkdir(parents=True, exist_ok=True)

    output_file = state_dir / "webtech-updates.md"

    report = generate_report()

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[webtech-sync] OK {output_file}")
    print(f"[webtech-sync] 주요 버전: Java 21 LTS · .NET 8.0 · Python 3.13 · Node 22 LTS · Go 1.23 · Rust 1.84")

if __name__ == "__main__":
    main()
