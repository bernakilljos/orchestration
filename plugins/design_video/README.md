# design_video — 영상·이미지·오디오 복원 + 편집 + 실시간 스트리밍

> **Prefix**: `design_` | **버전**: 2.0 | **Status**: stable | **Phase**: 0

## Phase 3: 미디어 복원·생성

### 커맨드
- `/video-restore` — 90년대~2000년대 저화질 영상 → 고화질 복원 (VHS/Hi8 지원)
- `/image-restore` — 이미지 복원 (초해상도·얼굴·컬러화·배경제거)
- `/audio-restore` — 오디오 복원 (노이즈제거·대역확장·스템분리·AI작곡)
- `/video-edit` — 영상 편집 (자르기·합치기·자막)
- `/video-subtitle` — 자막 자동 생성 (Whisper + 번역)
- `/video-template` — 유튜브 인트로·아웃트로 템플릿
- `/video-shorts` — 롱폼 → 쇼츠 자동 추출
- `/video-thumbnail` — 썸네일 A/B 3안 자동 생성

### 핵심 도구
| 영역 | 도구 | 용도 |
|------|------|------|
| 영상 초해상도 | Real-ESRGAN, BasicVSR++ | 480p→4K |
| 프레임 보간 | RIFE, FILM | 15fps→60fps |
| 얼굴 복원 | CodeFormer, GFP-GAN | 흐릿한 얼굴 재생성 |
| 컬러화 | DeOldify, DDColor | 흑백→컬러 |
| 노이즈 제거 | FFmpeg hqdn3d, FastDVDnet | 그레인·노이즈 제거 |
| 오디오 복원 | noisereduce, VoiceFixer | 잡음 제거·음질 향상 |
| 스템 분리 | Demucs, Spleeter | 보컬/드럼/베이스 분리 |
| AI 작곡 | MusicGen, Bark | 텍스트→음악·음성 |

## Phase 4: 실시간 스트리밍

### 커맨드
- `/realtime-setup` — WebSocket·SSE·WebRTC 환경 구성

### 레퍼런스
- `references/realtime-streaming-toolkit.md`

## 상세 스펙

### 목표

- 영상 편집 — 자막·쇼츠·썸네일 (유튜브 수익화 직결)

### 스킬 스펙

#### `skill-video-remotion`

Remotion 프로그래매틱 영상 (design_ppt 에서 이관)

#### `skill-video-retention`

시청지속률 높이는 편집 패턴

### 구현 체크리스트 (플랫폼)

- [ ] 멱등성
- [ ] `--dry-run` 실동작
- [ ] 입력 검증
- [ ] 에러 복구
- [ ] Rate limit (지수백오프)
- [ ] 시크릿 `.env` 로드
- [ ] JSON 구조화 로그

### 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 커맨드 인식 안 됨 | sync 미실행 | `bash .claude/scripts/sync-plugins.sh` |
| 환경변수 누락 | `.env` 미설정 | `.env.example` 복사 후 값 입력 |
| API 호출 실패 | 쿼터·네트워크·토큰 | `scripts/common.sh` 의 retry 로직 확인 |
| 한글 깨짐 | 인코딩 | `.claude/hooks/check-mojibake.sh` 가 차단. UTF-8 로 재저장 |
| 드라이런 실패 | 인자 미지원 | `is_dry_run "$@"` 헬퍼 검사 |

## 의존성
- **플러그인**: `exec_orch`, `mcp_media`
- **Python**: realesrgan, opencv-python, noisereduce, demucs, moviepy
- **CLI**: ffmpeg, whisper
- **참조**: `docs/architecture-patterns.md`, `.claude/rules/file-naming.md`, `.claude/rules/skill-design.md`, `.claude/rules/plugin-structure.md`
