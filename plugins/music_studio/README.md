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

## 상세 스펙

### 기술 스택 (플랫폼 구현 시)

| 영역 | 도구 |
|---|---|
| 오디오 처리 | FFmpeg · sox · librosa |
| AI 작곡 | Suno API · Udio · MusicGen · Stable Audio |
| 스템 분리 | Demucs · Spleeter |
| MIDI | mido · pretty_midi · music21 |
| 믹싱 | pedalboard (Spotify) · pyo |
| 마스터링 | LUFS 측정 (pyloudnorm) |

### 구현 체크리스트 (플랫폼)

- [ ] 멱등성 (같은 시드·입력 = 같은 출력)
- [ ] `--dry-run` 실동작
- [ ] 저작권 경고 자동 출력 (AI 생성물)
- [ ] LUFS 자동 정규화 (-14 LUFS 기본)
- [ ] WAV/MP3/FLAC 다중 출력
- [ ] 시크릿 `.env` (Suno·Udio API)
- [ ] JSON 로그

### 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| ffmpeg 없음 | 미설치 | `/mcp_media-install` |
| Suno API 실패 | 쿼터·인증 | `.env` SUNO_API_KEY 확인 |
| LUFS 과다 | 마스터 과압 | `-14 LUFS` 목표 재조정 |
| 스템 분리 실패 | Demucs 모델 미다운 | 초회 실행 시 자동 다운로드 대기 |

## 📝 참조

- 아키텍처: `docs/architecture-patterns.md`
- `plugins/exec_voice/` (STT·TTS 연계)
- `plugins/mcp_media/` (FFmpeg 설치)
