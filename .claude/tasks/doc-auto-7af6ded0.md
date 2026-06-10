# doc_auto task — C:\\pjt\\orchestration_v1\\.claude\\scripts\\add-how-to-100.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/add-how-to-100.py b/.claude/scripts/add-how-to-100.py
new file mode 100644
index 0000000..d12ee2a
--- /dev/null
+++ b/.claude/scripts/add-how-to-100.py
@@ -0,0 +1,168 @@
+"""100 신상품 HTML 에 각 카드별 '어떻게 구현할지' 박스 일괄 삽입"""
+import re, os
+
+path = os.path.join(
+    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
+    'outputs', 'itcen', 'html', 'itcen-core-100신상품.html'
+)
+
+# 100개 신상품 어떻게 (1~100)
+HOW = {
+    # ─── 영역 1: 내부회계 ───
+    1: ('o3 API 또는 Claude Extended Thinking 활용', 'MicroICM-C 156 RCM 매핑 데이터 학습', '감사보고서 템플릿 자동 생성', '3개월 PoC + 6개월 통합'),
+    2: ('DoWhy·Causica 오픈소스 통합', '한국 분식·횡령 사례 인과그래프 구축', 'MicroICM-C 거래 데이터 연결', '4개월 PoC, 1년 정식'),
+    3: ('Haiku-validator hook 구현 — Sonnet 1차 → Haiku 2차 재검토', 'confidence < 0.7 자동 재시도', '156 RCM 항목별 합의 점수 저장', '1-2개월 (orchestration_v1 패턴 그대로 이식)'),
+    4: ('Neo4j Community 무료 + LLM entity 추출', '결재-거래-회계 그래프 자동 구축', 'Cypher 쿼리로 다중 hop 분석', '3개월 PoC'),
+    5: ('IBM Quantum Network 무료 가입', 'Qiskit ML VQC 학습 (8 features)', 'MicroICM-C 거래 데이터 익명화 후 학습', '6개월 PoC (양자 우위 측정)'),
+    6: ('Gretel·Mostly AI 무료 tier', '익명화된 부정 사례 → 합성 100만건 생성', 'AI 학습데이터 폭증 → 정확도 ↑', '2개월'),
+    7: ('GPT-4o/Claude 4 Voice API', 'MicroICM-C 데이터 자연어 인터페이스', '"분식 의심 보여줘" 음성 응답', '2개월 (API 통합만)'),
+    8: ('GPT-4 Vision/Claude Vision', '영수증·송장 OCR + 자동 회계 입력', 'PDF·이미지 → MicroICM-C 자동 import', '3개월'),
+    9: ('Flower 오픈소스 + 그룹사 협업', '각 계열사 데이터는 자기 서버에 유지', '가중치만 중앙 합산', '6개월 PoC (3社 시작)'),
+    10: ('Claude Computer Use + MicroICM-C 직접 조작', 'Reflexion 루프로 분식 24/7 자동 감시', 'Slack/이메일 자동 보고', '6개월 (안정성 검증)'),
+
+    # ─── 영역 2: CCP 준법 ───
+    11: ('Llama 3·Llama 4 base + LoRA fine-tune', '한국 법규·사규·금감원 가이드 데이터셋', 'GPU 1대 (수백만원), 1-2개월 학습', '3개월 PoC'),
+    12: ('Microsoft GraphRAG OSS 통합', '사규·법규·판례 PDF → LLM 추출 그래프', 'Cypher 자동 질의 변환', '4개월'),
+    13: ('failure-mode.md 패턴 그대로 이식', '사규·법규를 .md 헌법 파일로 변환', 'PreToolUse hook 자동 차단 (위반 시)', '1-2개월'),
+    14: ('Perplexity Enterprise API 또는 자체 RAG', '법무부·금감원·KISA RSS 모니터링', '변경 즉시 영향 분석 LLM 호출', '2개월'),
+    15: ('Claude Opus 4.7 (1M context) API', '계약서 전문 단일 호출 분석', '위험 조항·누락 자동 표시', '1개월 (API only)'),
+    16: ('Federated + 익명화 + Multi-Agent', '제보 → 익명화 → 3 AI 합의 평가', '제보자 보호 + 객관 검증', '4개월'),
+    17: ('GraphRAG + Causal AI 결합', '거래 그래프에서 다중 hop cycle 자동 탐지', '금감원 STR/SAR 자동 보고서', '6개월'),
+    18: ('Generative AI + OFAC·UN 제재 DB 통합', '실시간 제재 대상 자동 스크리닝', '분기 보고서 자동 생성', '3개월'),
+    19: ('Anthropic SAE 도구 또는 Captum (PyTorch)', 'AI 모델 의사결정 회로 분석', '모델 카드 + EU AI Act 보고서 자동', '6개월'),
+    20: ('Computer Use + RPA 통합', '컴플라이언스 화면 자율 점검', '증거 수집·캡쳐·보고서 자동', '4개월'),
+
+    # ─── 영역 3: 건설 ERP ───
+    21: ('NVIDIA Cosmos 라이선스 (Free Research)', '건설 ERP BIM 데이터 import', 'Cosmos 로 사고 시뮬 영상 생성', '6개월 PoC'),
+    22: ('OpenVLA 오픈소스 + AI CCTV 영상', '작업자 행동 학습 (PPE·자세·동선)', '실시간 위험 알람 (Edge AI Chip)', '6개월'),
+    23: ('Apple Vision Pro 또는 Microsoft HoloLens 2', '디지털트윈 → AR 오버레이', '현장 작업자 가이드 앱', '4-6개월'),
+    24: ('Skydio·DJI 드론 + Vision Transformer', '대형 현장 자율 순찰 경로 학습', '도난·침입 실시간 감지', '6개월'),
+    25: ('LiDAR 센서 (Velodyne) + 디지털트윈', '주 1회 3D 스캔 자동 → BIM 비교', '진척 자동 검수·정산 자동화', '6개월'),
+    26: ('DoWhy 인과 그래프 + 사고 사례 DB', '사고 원인 자동 추론 (PEER·SAFER 표준)', '예방 권고 자동 보고서', '4개월'),
+    27: ('Claude 1M context + 1년 ERP 데이터', '공정·자재·인력 통합 분석', '사고·지연 예측 알림', '3개월'),
+    28: ('GraphCast 오픈소스 + 기상청 API', '주간 날씨 자동 통합', '공정 자동 조정 알람', '2개월'),
+    29: ('MatterGen API (Microsoft) 통합', '신소재 추천 + 비용·내구성 ML', '시공 전 소재 비교 보고서', '4개월'),
+    30: ('Boston Dynamics Spot 또는 ANYbotics', 'NVIDIA GR00T API 통합', '현장 자율 검사·보고', '12개월 (안정성 검증)'),
+
+    # ─── 영역 4: 카지노 VMS ───
+    31: ('Hume AI EVI 3 API 라이선스', 'CCTV 음성·얼굴 영상 실시간 분석', 'VMS 출입 데이터 연동 알람', '4개월'),
+    32: ('RT-2 또는 Pi0 영상 학습', '딜러·플레이어 행동 패턴 학습', '공모 의심 자동 알람', '6개월'),
+    33: ('IBM Quantum + 게임 결과 통계', 'Variational Quantum Classifier 학습', '조작 패턴 분류', '6개월'),
+    34: ('Idemia·Suprema 생체 인식 SDK', 'VMS 출입에 다중 생체 통합', 'VIP 블랙리스트 즉시 차단', '3개월'),
+    35: ('GraphRAG + 카지노 자금 흐름', '칩 구매·환전·송금 그래프', 'STR/SAR 자동 보고', '5개월'),
+    36: ('iOS·Android 네이티브 앱 + Claude API', 'VIP 호스트 실시간 가이드', 'VMS 데이터 연동', '3개월'),
+    37: ('실시간 영상 + 음성 + 결과 통합 분석', 'GPT-4o 또는 Gemini 2.5 멀티모달', '온라인 카지노 직판', '6개월'),
+    38: ('행동 패턴 + 도박중독 임상 데이터', 'Hume + 자체 분류기 결합', '강원랜드 공익 협업 (수가 인정)', '6개월'),
+    39: ('Claude 1M context + 1년 게임 데이터', '패턴 예측 + 운영 최적화 보고서', 'CEO·임원 대시보드', '3개월'),
+    40: ('한국 9社 검증 → 동남아 영업 (마카오·필리핀·싱가포르)', 'OEM 통합 영업 채널 구축', '글로벌 매출 폭증', '12개월 (해외 진출)'),
+
+    # ─── 영역 5: 금융 VMS ───
+    41: ('BioCatch SDK 또는 자체 (타이핑·마우스 패턴)', 'VMS 로그인 시작 → 세션 내내 검증', '이상 행동 시 step-up 인증', '4개월'),
+    42: ('Reality Defender·Hive API 통합', '콜센터·영업점 영상·음성 실시간', '2026 보이스피싱법 의무 대응', '3개월'),
+    43: ('NIST PQC 표준 (ML-KEM·ML-DSA) 도입', '기존 RSA·ECC 인벤토리 + 단계 전환', 'KISA 가이드 준수', '12-18개월 (대규모)'),
+    44: ('Codex+Gemini+Haiku 다중 합의 패턴', '1차 FDS 모델 → 2차 LLM 검토', '거짓양성 50% ↓ 실측', '6개월'),
+    45: ('Pindrop SDK + 콜센터 통합', '실시간 음성 위조·이상 신호 알람', '24/7 자동 차단', '4개월'),
+    46: ('UEBA + Continuous Auth 결합', '직원 행동 패턴 + 상시 인증 통합', '내부자 위협 차세대', '6개월'),
+    47: ('Llama 3 + 한국 금융 데이터 LoRA', '한국형 BloombergGPT 자체', '신용평가 + 대안 데이터', '12개월'),
+    48: ('한국은행 CBDC SDK (2027 예정)', '결제 인프라 SI', '은행·결제사 직판', '12-24개월'),
+    49: ('Constitutional AI + 금감원 규제 RSS', '규제 변경 자동 추적 + 헌법화', 'AI 결정 자동 준수 검증', '4개월'),
+    50: ('한국 행동신용평가소 — KCB·NICE 식', 'UEBA 점수 표준화·라이선싱', '보험·HR·IAM 3 시장 직판', '12개월 (표준 lobby)'),
+
+    # ─── 영역 6: AI CCTV ───
+    51: ('NVIDIA Cosmos World Model 라이선스', 'AI CCTV 영상 학습', '미래 예측 모듈', '6개월'),
+    52: ('OpenVLA 또는 RT-2 적용', '"침입 의심" 자연어 알람', '자율 판단 보고서', '6개월'),
+    53: ('GPT-4o·Gemini 2.5 멀티모달 검색', '"빨간 모자 사람" 자연어 영상 검색', '대형 시설 효율 ↑', '3개월'),
+    54: ('Crowd Analytics SDK + 이태원 사례 학습', '밀집도 임계 자동 알람', '행안부·지자체 입찰', '6개월'),
+    55: ('열화상 카메라 + 멀티모달 LLM', '화재·연기 조기 탐지', '소방청·산림청 입찰', '6개월'),
+    56: ('VLA + PPE 데이터셋 학습', '산업현장 안전 모니터링', '산안법 의무 직판', '4개월'),
+    57: ('Hume EVI + 매장 CCTV', '고객 만족도·이탈 자동 분석', '유통·매장 직판', '4개월'),
+    58: ('개인정보 마스킹 ML 모델 + Privacy API', '얼굴·번호판 자동 익명화', '개인정보위 의무 대응', '3개월'),
+    59: ('Hailo·NVIDIA Jetson 통합', 'CCTV 자체 추론 (Edge)', '클라우드 의존 X', '6개월 (HW 통합)'),
+    60: ('Dedrone·DroneShield OEM', 'CCTV + 안티드론 통합 관제', '국방·국가시설 입찰', '6개월'),
+
+    # ─── 영역 7: 디지털 트윈 ───
+    61: ('NVIDIA Cosmos World Foundation API', '디지털트윈 데이터 학습', '시나리오 무한 생성', '12개월 (대형 SI)'),
+    62: ('NVIDIA Isaac Sim 통합', '시뮬 → 실제 로봇 transfer', '학습 비용 ↓', '12개월'),
+    63: ('NVIDIA GR00T + 디지털트윈', '휴머노이드 가상 학습', '현대·삼성 SI', '12-18개월'),
+    64: ('Bentley iTwin + LH 협업', '도시 디지털트윈', 'B2G 대형 SI', '24개월'),
+    65: ('두산에너빌리티·SK SMR + AI 운영', '원전 디지털트윈', 'B2B 대형 SI', '24개월'),
+    66: ('Siemens NX + NVIDIA Omniverse 통합', '스마트팩토리 SI', '대기업 제조 직판', '12-18개월'),
+    67: ('Apple Vision Pro SDK + Unity', 'VR 가상 관제실', '관제·교육 직판', '6개월'),
+    68: ('디지털트윈 데이터 익명화·라이선싱', '글로벌 AI 회사 직판', '데이터 마켓플레이스', '12개월'),
+    69: ('GraphCast + 탄소 디지털트윈', 'CCUS 최적화', 'ESG 의무사 직판', '6개월'),
+    70: ('한화·LIG 협업', '국방 시뮬레이션 SI', '방위사업청 발주', '24개월'),
+
+    # ─── 영역 8: ITO ───
+    71: ('Claude Computer Use + MCP', '운영 작업 자율 처리', '기존 ITO 고객 직판', '6개월'),
+    72: ('Palo Alto·Wiz AI OEM 한국 1호', 'MSP 운영 체계', '월구독', '6개월 (파트너십)'),
+    73: ('Astrix·Oasis 통합', 'AI 에이전트 신원 관리', 'AI 도입 기업', '3개월'),
+    74: ('Cilium·Falco·Pixie 운영', '커널 레벨 관측', '대기업 IT 직판', '6개월'),
+    75: ('Fortinet·Cisco SCA OEM', '분산 보안 표준 SI', '멀티클라우드 기업', '12개월'),
+    76: ('Cyera·Sentra OEM', '데이터 위치·민감도 추적', '개인정보 의무사', '6개월'),
+    77: ('CloudHealth·Vantage·자체 ML', 'AWS·Azure·GCP 비용 최적화', '절감액 20% 수수료', '3개월'),
+    78: ('Pure·NetApp + AI ML 자동 복구', '장애 자동 진단·복구', '금융·공공 직판', '6-12개월'),
+    79: ('ISMS-P·금감원 자동 매핑', '규제 준수 자동 점검', '금융·공공 직판', '6개월'),
+    80: ('자체 탄소 측정 + 보고 SaaS', '데이터센터 탄소·EU CBAM 대응', '대기업 IT', '4개월'),
+
+    # ─── 영역 9: ESG·GRC ───
+    81: ('GraphCast + 탄소 디지털트윈', 'CCUS·NetZero 최적화', '대기업 ESG 직판', '6개월'),
+    82: ('Claude·GPT 생성형 + ESG 템플릿', '분기·연간 보고서 자동 생성', '상장사 의무 대응', '3개월'),
+    83: ('ISO 42001 한국 인증 기관 인증', 'AI 라이프사이클 자동 audit', '인증 컨설팅', '12개월'),
+    84: ('Fairlearn·Aequitas OSS', 'AI 편향 자동 측정', 'EU AI Act 의무 충족', '4개월'),
+    85: ('SHAP·LIME·Captum 통합', 'AI 결정 설명 자동 보고서', 'EU 2027 의무', '4개월'),
+    86: ('LangChain + 공급망 데이터', '협력사 ESG 평가 자동', '대기업 직판', '6개월'),
+    87: ('자체 탄소 산정 + IPCC 표준', 'Scope 1·2·3 자동', '상장사 의무', '6개월'),
+    88: ('IoT 센서 + AI 분석', '물·자원 최적화', '제조 대기업', '6개월'),
+    89: ('K-ETS 거래 시스템 + AI 거래', '탄소권 가격 예측', '탄소 배출 기업', '12개월'),
+    90: ('Cyber Resilience Score 자체 표준', '회복력 점수화·정기 audit', '보험사 협업', '6개월'),
+
+    # ─── 영역 10: 부서 IP ───
+    91: ('8 카테고리 자동 audit 도구 자체 개발', 'KISA·금감원·개인정보위 표준 lobby', '한국 K-Standard 등록', '24개월 (표준 등록)'),
+    92: ('KISA 양자보안 가이드 협력', '한국 양자보안 표준 자체 제정', '인증·교육 사업', '24-36개월'),
+    93: ('한국 ISO 42001 1호 인증 사업자', 'EU AI Act 컨설팅 패키지', '인증 + 컨설팅', '12개월'),
+    94: ('KCB·NICE 식 한국 행동신용평가소 신설', '점수 모델·라이선싱 IP', '보험·HR·IAM 직판', '24개월 (lobby)'),
+    95: ('Llama 4 base + 한국 금융·회계 LoRA', '자체 도메인 LLM', 'API + on-premise', '12개월'),
+    96: ('Gretel·Mostly AI 패턴 자체 구축', '한국 산업 합성데이터 마켓', '글로벌 AI 회사 직판', '12개월'),
+    97: ('Flower OSS 컨소시엄 운영', '은행·금융권 공동 부정탐지', '은행연합회 협업', '18개월'),
+    98: ('휴머노이드 보안 표준 자체 제정', '도입 기업 인증 사업', '현대·삼성 협업', '24개월'),
+    99: ('Anthropic·OpenAI 안전 연구 협력', 'AGI 거버넌스 자문 회사', '대기업·정부 자문', '24-36개월'),
+    100: ('KISA·금융보안원 등록 정식 과정', '부서 노하우 교육·자격증 발급', '수강료 + 자격증료', '12-18개월'),
+}
+
+with open(path, 'r', encoding='utf-8') as f:
+    html = f.read()
+
+# 각 카드의 card-what 다음에 card-how 박스 삽입
+# 패턴: <div class="card-num">N</div> ... <div class="card-what">...</div>
+def inject_how(match):
+    num_str = match.group(1)
+    num = int(num_str)
+    what_text = match.group(2)
+    if num not in HOW:
+        return match.group(0)
+    h = HOW[num]
+    how_html = f'<div class="card-how"><strong>🔧 어떻게:</strong> ① {h[0]} → ② {h[1]} → ③ {h[2]} <span style="color:#888">(기간 {h[3]})</span></div>'
+    return f'<div class="card-num">{num_str}</div>' + match.group(0).split(f'<div class="card-num">{num_str}</div>')[1].replace(f'<div class="card-what">{what_text}</div>', f'<div class="card-what">{what_text}</div>\n      {how_html}')
+
+# 정규식: card-num N + card-what 텍스트 매칭
+pattern = re.compile(r'<div class="card-num">(\d+)</div>.*?<div class="card-what">(.*?)</div>', re.DOTALL)
+
+# 각 매치마다 직접 처리
+def replace(m):
+    num = int(m.group(1))
+    what = m.group(2)
+    full = m.group(0)
+    if num not in HOW:
+        return full
+    h = HOW[num]
+    how_html = (f'<div class="card-how"><strong>🔧 어떻게:</strong> '
+                f'① {h[0]} → ② {h[1]} → ③ {h[2]} '
+                f'<span style="color:#888">(기간 {h[3]})</span></div>')
+    return full + '\n      ' + how_html
+
+new_html = pattern.sub(replace, html)
+with open(path, 'w', encoding='utf-8') as f:
+    f.write(new_html)
+
+count = new_html.count('🔧 어떻게')
+print(f'Injected 어떻게 boxes: {count}')
```

## Action
1. 변경된 public API 추출 (함수·클래스·exports)
2. CHANGELOG.md `[Unreleased]` 섹션에 entry 추가:
   - Added/Changed/Fixed/Removed/Security 분류
3. README.md 의 API 섹션 갱신 (있을 시)
4. docs/api/<module>.md 갱신 (있을 시)

## Constraints
- 기존 entry 덮어쓰기 X (append)
- 자동 commit X (사용자 review 대기)
- 내부 helper 변경 skip (public API 만)
