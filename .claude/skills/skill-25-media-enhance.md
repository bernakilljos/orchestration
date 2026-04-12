# Skill 25: Media Enhance (미디어 화질/품질 개선)

## 목적
동영상, 오디오, 이미지, PDF, PPT 파일의 화질/음질을 AI로 개선한다.
CLI + Streamlit GUI 이중 인터페이스 제공.

## 트리거
- "화질 개선", "media enhance", "업스케일", "노이즈 제거"
- "동영상 복원", "오디오 개선", "PDF 화질", "PPT 이미지 개선"

## 지원 파일 + 처리 방법

### 동영상 (mp4, avi, mkv, wmv, asf, mov)
```
도구: FFmpeg + Real-ESRGAN + CodeFormer + GFPGAN
파이프라인:
  1. FFmpeg → 프레임 분리 + 오디오 추출
  2. CodeFormer → 얼굴 복원 (정면/비스듬)
  3. GFPGAN → 보조 얼굴 복원 (CodeFormer 미감지 보완)
  4. Real-ESRGAN → 해상도 업스케일
  5. FFmpeg → 프레임 합성 + 오디오 복원

얼굴 감지 전략 (중요):
  - detection_model: YOLOv5l (기본) → 옆모습 감지율 높음
  - 정면 얼굴: CodeFormer w=0.5 (품질 우선)
  - 옆모습/비스듬: CodeFormer w=0.7 (원본 보존 우선)
  - 미감지 얼굴: GFPGAN fallback
  - 얼굴별 fidelity 차등 적용:
    - 주요 인물 (화면 중앙, 큰 얼굴): w=0.3~0.5
    - 보조 인물 (화면 가장자리, 작은 얼굴): w=0.7~0.9
    - 옆모습/뒷모습: w=0.8+ (과도한 복원 방지)
```

### 오디오 (mp3, wav, flac, aac, ogg)
```
도구: demucs, noisereduce, pydub, librosa
파이프라인:
  1. noisereduce → 배경 노이즈 제거
  2. demucs → 음성/악기 분리 (선택)
  3. librosa → 이퀄라이저/노멀라이즈
  4. pydub → 비트레이트 변환 + 출력
```

### 이미지 (jpg, png, bmp, webp)
```
도구: Real-ESRGAN + CodeFormer
파이프라인:
  1. CodeFormer → 얼굴 복원
  2. Real-ESRGAN → 업스케일 (2x/4x)
  3. 일괄 처리 지원 (폴더 단위)
```

### PDF (스캔 문서)
```
도구: PyMuPDF(fitz) + Real-ESRGAN + pytesseract
파이프라인:
  1. PDF → 페이지별 이미지 추출
  2. Real-ESRGAN → 이미지 업스케일
  3. pytesseract → OCR (텍스트 검색 가능하게)
  4. 이미지 + OCR 텍스트 → PDF 재조립
```

### PPT/PPTX
```
도구: python-pptx + Real-ESRGAN
파이프라인:
  1. 슬라이드에서 이미지 추출
  2. Real-ESRGAN → 업스케일
  3. 개선된 이미지 → 슬라이드에 재삽입
  4. 원본 레이아웃 유지
```

## CLI 인터페이스
```bash
python media-enhance.py input.mp4                    # 자동 감지
python media-enhance.py input.mp4 -o output.mp4      # 출력 경로
python media-enhance.py folder/ --batch              # 폴더 일괄
python media-enhance.py audio.mp3 --denoise          # 노이즈 제거
python media-enhance.py scan.pdf --ocr               # OCR 포함
python media-enhance.py pres.pptx                    # PPT 이미지 개선
python media-enhance.py --gui                        # Streamlit GUI
python media-enhance.py --install                    # 의존성 설치
python media-enhance.py --check                      # 환경 체크
```

## GUI (Streamlit)
```bash
streamlit run media-enhance-gui.py
```
```
┌─────────────────────────────────────────┐
│  Media Enhance Tool                     │
├─────────────────────────────────────────┤
│  📁 파일 선택: [Browse...]              │
│  📂 또는 폴더: [Browse...]              │
│                                         │
│  유형: ○동영상 ○오디오 ○이미지 ○PDF ○PPT │
│                                         │
│  옵션:                                  │
│    업스케일: [2x ▼]                     │
│    얼굴 복원: [✓]  fidelity: [0.7]     │
│    노이즈 제거: [✓]                     │
│    OCR: [✓]                             │
│                                         │
│  [▶ 처리 시작]                          │
│                                         │
│  ████████░░░░░░  52% (3/6 files)       │
│  현재: video.mp4 - 프레임 복원 중...    │
└─────────────────────────────────────────┘
```

## 한글 경로 대응
```python
# OpenCV가 한글 경로를 못 읽는 문제 해결
# 1. 임시 영문 경로로 복사
# 2. 처리
# 3. 결과를 원본 경로로 이동
# 4. 임시 폴더 삭제
TEMP_DIR = os.path.join(tempfile.gettempdir(), "media_enhance_tmp")
```

## 출력 규칙
```
입력: C:\work\photo.jpg
출력: C:\work\photo_enhanced.jpg

입력: C:\work\video.mp4
출력: C:\work\video_enhanced.mp4

입력: C:\work\folder\ (일괄)
출력: C:\work\folder_enhanced\ (전체)
```

## 프로젝트 구조
```
tools/media-enhance/
├── media-enhance.py        # CLI 메인
├── media-enhance-gui.py    # Streamlit GUI
├── enhancers/
│   ├── __init__.py
│   ├── video.py            # 동영상 처리
│   ├── audio.py            # 오디오 처리
│   ├── image.py            # 이미지 처리
│   ├── pdf.py              # PDF 처리
│   └── pptx.py             # PPT 처리
├── utils/
│   ├── __init__.py
│   ├── path_helper.py      # 한글 경로 대응
│   ├── progress.py         # 진행률 표시
│   └── gpu.py              # GPU/CUDA 감지
├── requirements.txt
└── setup.py
```

## 환경 조건
```
필수: Python 3.8+, FFmpeg
GPU:  자동 감지 (nvidia-smi → CUDA 버전 확인 → 맞는 PyTorch 설치)
      없으면 CPU fallback (느리지만 동작)
기존: CodeFormer (tools/video-restore/CodeFormer 자동 탐색)
```

## MCP 연동
- tools/video-restore.py 의 CodeFormer/Real-ESRGAN 재사용
- skill-22 (remotion): 개선된 미디어를 영상에 삽입
