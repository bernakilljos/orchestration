# PPT Overflow Verification Report

- Source: `C:\pjt\orchestration_v1\outputs\ppt-plugins\html-source\png-output`
- Total slides: 40
- Suspect (>10% edge dark): **1**
- Threshold: bottom + right band 30px, dark = RGB < 80

## All slides

| slide | bottom | right | suspect |
|-------|-------:|------:|:-------:|
| slide-01.png | 0.000 | 0.000 | [OK] |
| slide-02.png | 0.000 | 0.000 | [OK] |
| slide-02a.png | 0.000 | 0.000 | [OK] |
| slide-02b.png | 0.000 | 0.000 | [OK] |
| slide-02c.png | 0.000 | 0.000 | [OK] |
| slide-02d.png | 0.000 | 0.000 | [OK] |
| slide-02e.png | 0.000 | 0.000 | [OK] |
| slide-02f.png | 0.000 | 0.000 | [OK] |
| slide-03.png | 0.000 | 0.000 | [OK] |
| slide-03a.png | 0.000 | 0.000 | [OK] |
| slide-03b.png | 0.000 | 0.000 | [OK] |
| slide-03c.png | 0.000 | 0.000 | [OK] |
| slide-04.png | 0.000 | 0.000 | [OK] |
| slide-05.png | 0.000 | 0.000 | [OK] |
| slide-05a.png | 0.324 | 0.000 | [!] YES |
| slide-06.png | 0.000 | 0.000 | [OK] |
| slide-06a.png | 0.000 | 0.000 | [OK] |
| slide-06b.png | 0.000 | 0.000 | [OK] |
| slide-07.png | 0.000 | 0.000 | [OK] |
| slide-08.png | 0.000 | 0.000 | [OK] |
| slide-08a.png | 0.000 | 0.000 | [OK] |
| slide-09.png | 0.000 | 0.000 | [OK] |
| slide-10.png | 0.000 | 0.000 | [OK] |
| slide-11.png | 0.000 | 0.000 | [OK] |
| slide-12.png | 0.000 | 0.000 | [OK] |
| slide-12a.png | 0.000 | 0.000 | [OK] |
| slide-12b.png | 0.000 | 0.000 | [OK] |
| slide-12c.png | 0.000 | 0.000 | [OK] |
| slide-13.png | 0.000 | 0.000 | [OK] |
| slide-13a.png | 0.000 | 0.000 | [OK] |
| slide-13b.png | 0.000 | 0.000 | [OK] |
| slide-14.png | 0.000 | 0.000 | [OK] |
| slide-14a.png | 0.000 | 0.000 | [OK] |
| slide-14b.png | 0.000 | 0.000 | [OK] |
| slide-14c.png | 0.000 | 0.000 | [OK] |
| slide-14d.png | 0.000 | 0.000 | [OK] |
| slide-14e.png | 0.000 | 0.000 | [OK] |
| slide-14f.png | 0.000 | 0.000 | [OK] |
| slide-14g.png | 0.000 | 0.000 | [OK] |
| slide-15.png | 0.000 | 0.000 | [OK] |

## Suspect slides — Claude OCR 직접 확인 권장

- **slide-05a.png** — bottom 0.324, right 0.000

**다음 액션:**
```python
# Claude 가 의심 slides를 Read tool 로 직접 OCR
Read('C:\pjt\orchestration_v1\outputs\ppt-plugins\html-source\png-output/slide-05a.png')
```