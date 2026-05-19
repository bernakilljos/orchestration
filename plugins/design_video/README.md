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

## 의존성
- **플러그인**: `exec_orch`, `mcp_media`
- **Python**: realesrgan, opencv-python, noisereduce, demucs, moviepy
- **CLI**: ffmpeg, whisper
