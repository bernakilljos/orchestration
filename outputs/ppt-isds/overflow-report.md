# PPT Overflow Verification Report

- Source: `C:\pjt\orchestration_v1\outputs\ppt-isds\html-source\png-output`
- Total slides: 10
- Suspect (>10% edge dark): **2**
- Threshold: bottom + right band 30px, dark = RGB < 80

## All slides

| slide | bottom | right | suspect |
|-------|-------:|------:|:-------:|
| slide-01.png | 1.000 | 0.953 | [!] YES |
| slide-02.png | 0.000 | 0.000 | [OK] |
| slide-03.png | 0.000 | 0.000 | [OK] |
| slide-04.png | 0.000 | 0.000 | [OK] |
| slide-05.png | 0.000 | 0.000 | [OK] |
| slide-06.png | 0.000 | 0.000 | [OK] |
| slide-07.png | 0.000 | 0.000 | [OK] |
| slide-08.png | 0.000 | 0.000 | [OK] |
| slide-09.png | 0.000 | 0.000 | [OK] |
| slide-10.png | 1.000 | 0.953 | [!] YES |

## Suspect slides — Claude OCR 직접 확인 권장

- **slide-01.png** — bottom 1.000, right 0.953
- **slide-10.png** — bottom 1.000, right 0.953

**다음 액션:**
```python
# Claude 가 의심 slides를 Read tool 로 직접 OCR
Read('C:\pjt\orchestration_v1\outputs\ppt-isds\html-source\png-output/slide-01.png')
Read('C:\pjt\orchestration_v1\outputs\ppt-isds\html-source\png-output/slide-10.png')
```