# music_studio — 음악 스튜디오 — 녹음·작곡·믹싱·편곡·가사·MIDI·커버

> **Prefix**: `music_` | **버전**: 0.1 | **Status**: spec-only | **Phase**: 2

## ⚠️ 현재 상태

**spec-only** — 스펙 + 공통 헬퍼. 실구현은 플랫폼에서.

## 📋 커맨드 (10개)

- `/music_studio-record` — 실시간 녹음·멀티트랙 (마이크·라인 입력·24bit/48kHz)
- `/music_studio-compose` ⭐ 기본 — AI 작곡 (Suno·Udio·MusicGen) — 장르·BPM·키·길이 지정
- `/music_studio-arrange` — 편곡·코드 진행·섹션 구조 (verse·chorus·bridge)
- `/music_studio-lyrics` — 가사 작성 (주제·톤·운율·후크 라인)
- `/music_studio-mix` — 믹싱 — EQ·컴프·리버브·패닝 자동 적용
- `/music_studio-master` — 마스터링 — LUFS 정규화·라우드니스·스트리밍 대응
- `/music_studio-cover` — 커버곡 변형 — 보컬 변환·장르 스와프·reharm
- `/music_studio-midi` — MIDI 파일 조작 — 코드 추출·퀀타이즈·벨로시티 편집
- `/music_studio-stem` — 스템 분리 — 보컬/드럼/베이스/기타 (Spleeter·Demucs)
- `/music_studio-export` — 최종 출력 — WAV·MP3·FLAC·stem 패키지

## 🧠 스킬

- `skill-music-production` — 작곡·편곡 원칙 (코드 진행·장르 컨벤션·arrangement 원칙)
- `skill-music-mixing` — 믹싱·마스터링 가이드 (EQ·컴프·리버브·스트리밍 LUFS)
- `skill-music-copyright` — 저작권·샘플링·AI 생성물 법적 이슈 (공정 이용·라이선스)

## 🔗 의존성

- **플러그인**: `exec_orch`, `mcp_media`, `exec_voice`
- **MCP 권장**: FFmpeg·Whisper (mcp_media)
- **선택 API**: Suno·Udio·MusicGen (env: SUNO_API_KEY 등)

## 📝 참조

- 스펙: `SPEC.md`
- 아키텍처: `docs/architecture-patterns.md`
