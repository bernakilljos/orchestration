# Task: video-restore.py 고도화 구현

## Goal
`tools/video-restore.py`를 실제 프로덕션 수준으로 고도화한다.
현재 기본 틀만 있고, CodeFormer/Real-ESRGAN 연동이 pip fallback 수준이다.
완전한 동작 + 에러 핸들링 + 진행률 표시가 필요하다.

## Assigned Agent
- Implementer: **Codex** (1차 구현)
- Reviewer: **Gemini** (검증)
- Final: **Claude** (보완/고도화)

## 현재 파일 위치
- `tools/video-restore.py` (기존 파일 수정)

## 기술 스택
- Python 3.8+, CodeFormer, Real-ESRGAN, FFmpeg, PyTorch (CUDA/CPU)

## 구현 요구사항

### 1. --check / --install 모드
- `--check`: Python, GPU(nvidia-smi), FFmpeg, CodeFormer, Real-ESRGAN 체크
- `--install`: 미설치 항목 자동 설치 (git clone + pip + 모델 다운로드)

### 2. 동영상 파이프라인
```
Step 1: FFmpeg → frame_%06d.png + audio.aac
Step 2: CodeFormer → 얼굴 복원 (inference_codeformer.py 또는 모듈 import)
Step 3: Real-ESRGAN → 업스케일 (inference_realesrgan.py 또는 pip)
Step 4: FFmpeg → 프레임 + 오디오 → 출력 (libx264, crf=17)
```

### 3. 이미지 단건: photo.jpg → photo_restored.jpg

### 4. 진행률: tqdm (없으면 커스텀 프로그레스바)

### 5. GPU OOM 대응: FP16 → tile 줄이�� → CPU fallback

### 6. CLI
```
video-restore.py input.mp4 [-o out.mp4] [-w 0.5] [--scale 4]
  [--face-only] [--upscale-only] [--fps 24] [--gpu 0]
  [--keep-temp] [--model anime] [--install] [--check]
```

## Allowed Files
- `tools/video-restore.py` (modify only)

## Prohibited
- 하드코딩, Windows 비호환, 한글 파일명 깨짐

## Acceptance Criteria
- [ ] `--check` 정상
- [ ] `--install` 자동 설치
- [ ] 동영상 4단계 파이프라인
- [ ] 이미지 단건
- [ ] 진행률 표시
- [ ] GPU OOM fallback
- [ ] --face-only / --upscale-only
- [ ] 한글 파일명 안전

## Completion Report
`docs/implementation-report.md`
