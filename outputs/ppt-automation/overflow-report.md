# PPT Overflow Verification Report

- Source: `C:\pjt\orchestration_v1\outputs\ppt-automation\html-source\png-output`
- Total slides: 12
- Suspect (>10% edge dark): **1**
- Threshold: bottom + right band 30px, dark = RGB < 80

## All slides

| slide | bottom | right | suspect |
|-------|-------:|------:|:-------:|
| slide-01.png | 0.000 | 0.000 | [OK] |
| slide-02.png | 0.000 | 0.000 | [OK] |
| slide-03.png | 0.000 | 0.000 | [OK] |
| slide-04.png | 0.000 | 0.000 | [OK] |
| slide-05.png | 0.000 | 0.000 | [OK] |
| slide-06.png | 0.360 | 0.000 | [!] YES |
| slide-07.png | 0.000 | 0.000 | [OK] |
| slide-08.png | 0.000 | 0.000 | [OK] |
| slide-09.png | 0.000 | 0.000 | [OK] |
| slide-10.png | 0.000 | 0.000 | [OK] |
| slide-11.png | 0.000 | 0.000 | [OK] |
| slide-12.png | 0.000 | 0.000 | [OK] |

## Suspect slides — Claude OCR 직접 확인 권장

- **slide-06.png** — bottom 0.360, right 0.000

**다음 액션:**
```python
# Claude 가 의심 slides를 Read tool 로 직접 OCR
Read('C:\pjt\orchestration_v1\outputs\ppt-automation\html-source\png-output/slide-06.png')
```