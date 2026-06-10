# doc_auto task — C:\\pjt\\orchestration_v1\\.claude\\scripts\\build-300-products.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/build-300-products.py b/.claude/scripts/build-300-products.py
new file mode 100644
index 0000000..1b84488
--- /dev/null
+++ b/.claude/scripts/build-300-products.py
@@ -0,0 +1,521 @@
+"""ITCEN CORE × Llama 4 — 300 신상품 HTML 자동 생성
+
+30 영역 × 10 신상품 = 300
+모두 Llama 4 (오픈소스·자체 운영) base
+인프라: Mac Studio M3 Ultra 512GB 명시
+"""
+import os
+
+ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
+OUT = os.path.join(ROOT, 'outputs', 'itcen', 'html', 'itcen-core-300신상품.html')
+
+# 30 영역 × 10 신상품
+# 각 신상품: (이름, 접목기술, 무엇, 어떻게, 인프라, 대상, 매출)
+
+AREAS = [
+    # ───── 영역 1: 내부회계 (10) ─────
+    ('📒', '1. 내부회계 (MicroICM-C 1위)', '국내 1위 · 156 RCM · 현대·LX·하림 등 보유', [
+        ('MicroICM-Reasoning', 'Llama 4 + Reasoning', '분식·횡령 사고 과정 자동 추론·감사보고서 생성', 'Llama 4 + RCM 매핑 LoRA · 보고서 템플릿', 'Mac Studio 1대 (1.5천만)', '현대 계열사 1000+', '1社 1-3억'),
+        ('MicroICM-Causal', 'DoWhy 인과 추론', '분식의 진짜 원인 (감독·시스템·의도) 자동 식별', 'DoWhy OSS + 인과 그래프 자체 구축', 'Mac Studio 1대', '금융·공공 GRC', '1社 2-5억'),
+        ('MicroICM-Critique', 'Llama 4 ×2 검증', '156 통제 1차→2차 검토 합의·거짓양성 50%↓', 'Llama 4 ×2 hook·confidence < 0.7 재시도', 'Mac Studio 1대', '전 기존 고객', '월 100-500만'),
+        ('MicroICM-Graph', 'GraphRAG (Neo4j)', '결재-거래-회계 그래프 다중 hop 횡령 추적', 'Neo4j 무료 + Llama 4 entity 추출', 'Mac Studio 1대 + Neo4j', '대기업·금융', '1社 3-7억'),
+        ('MicroICM-Quantum', 'IBM Quantum ML', '거래 양자 최적화 부정탐지', 'IBM Quantum Network 무료 + Qiskit', 'IBM Quantum (Cloud)', '금융권', '1社 5억+'),
+        ('MicroICM-Synthetic', 'Gretel 합성데이터', '부정 사례 합성 100만건·개인정보 0', 'Gretel 무료 tier + 자체 generator', 'Mac Studio 1대', '금감원 의무사', '컨설팅'),
+        ('MicroICM-Voice', 'Llama 4 Voice', '"분식 의심 보여줘" 음성 질의·답변', 'Llama 4 + Whisper STT + TTS', 'Mac Studio 1대', '경영진·임원', '월 50만/사용자'),
+        ('MicroICM-Vision', 'Llama 4 Vision', '영수증·송장 OCR + 자동 회계 입력', 'Llama 4 Multimodal + 회계 LoRA', 'Mac Studio 2대', '중견기업', '1社 1-2억'),
+        ('MicroICM-Federated', 'Flower OSS', '여러 그룹사 데이터 안 모으고 학습', 'Flower 무료 + 각 사 자체 서버', '각 사 1대씩', '그룹사·컨소시엄', '월구독'),
+        ('MicroICM-Agent', 'Llama 4 + Agentic', 'AI 자율 감사 봇·24/7 모니터·보고', 'Llama 4 + LangGraph + MicroICM 통합', 'Mac Studio 2대', '대기업 그룹', '월 1000-3000만'),
+    ]),
+    # ───── 영역 2: CCP 준법 (10) ─────
+    ('⚖️', '2. CCP 준법경영 (EPM·Compliance 1위)', 'EPM·Compliance 1위 · ISO 42001 base', [
+        ('MicroCCP-LLM', 'Llama 4 + 도메인 LoRA', '한국 법규·사규 특화 LLM·회사별 fine-tune', 'Llama 4 + 법규 데이터 LoRA', 'Mac Studio 1대', '1000+ CCP 사', '1社 5천만-2억'),
+        ('MicroCCP-GraphRAG', 'GraphRAG', '사규·법규·판례·위반사례 그래프', 'Microsoft GraphRAG OSS', 'Mac Studio 1대 + Neo4j', '금융·공공', '1社 3-5억'),
+        ('MicroCCP-Constitutional', 'Constitutional AI', '사규를 헌법으로 박고 AI 자동 준수', 'failure-mode.md 패턴 + PreToolUse hook', 'Mac Studio 1대', 'AI 도입 기업', '1社 2-4억'),
+        ('MicroCCP-Watcher', 'AI Search', '법규 변경 24/7 자동 추적·영향 분석', '자체 RSS + Llama 4', 'Mac Studio 1대', '대기업·금융', '월 200-500만'),
+        ('MicroCCP-Contract', 'Llama 4 Scout (1M)', '계약서 전문 단일 분석·위험 조항 발견', 'Llama 4 Scout 1M context', 'Mac Studio 2대', '법무팀·임원실', '월 100-300만'),
+        ('MicroCCP-Whistle', 'Multi-Agent + Privacy', '제보 익명화·다중 AI 검토', 'Llama 4 ×3 + 차등프라이버시', 'Mac Studio 2대', '대기업', '1社 1-3억'),
+        ('MicroCCP-AML', 'GraphRAG + Causal', '자금세탁 다중 hop 자동 추적·금감원 보고', 'Neo4j + DoWhy + Llama 4', 'Mac Studio 2대 + Neo4j', '금융 의무', '1社 5-10억'),
+        ('MicroCCP-Sanction', 'Generative AI', 'OFAC·UN 제재 자동 스크리닝·보고서', 'Llama 4 + 제재 DB 통합', 'Mac Studio 1대', '은행·증권·카드', '월 500만~'),
+        ('MicroCCP-EU', 'Mech Interpretability', 'EU AI Act 의무 — AI 결정 설명·인증', 'SAE 도구 + Captum (PyTorch)', 'Mac Studio 2대', 'EU 수출 기업', '1社 3-8억'),
+        ('MicroCCP-Audit', 'Llama 4 + Computer Use', '자율 컴플라이언스 점검·증거 수집', 'Llama 4 + Computer Use + RPA', 'Mac Studio 2대', '대기업·공공', '월 500-1500만'),
+    ]),
+    # ───── 영역 3: 건설 ERP (10) ─────
+    ('🏗️', '3. 건설 ERP (국내 1위)', '건설업 표준 · 중대재해법 의무', [
+        ('SmartConstruct-Cosmos', 'NVIDIA Cosmos', '가상 시공 시뮬·사고·붕괴 예측', 'NVIDIA Cosmos Free Research', 'Mac Studio 2대 + NVIDIA GPU 1', '50인+ 건설사', '1社 5천만-2억'),
+        ('SmartConstruct-VLA', 'OpenVLA + AI CCTV', '작업자 자세·위험행동·PPE 미착용 감지', 'OpenVLA + Edge AI', 'Mac Studio 1대 + Edge', '1만+ 건설사', '월 50-200만'),
+        ('SmartConstruct-AR', 'AR 디지털트윈', '스마트글래스 현장 가이드', 'Vision Pro + Unity', 'Vision Pro 10대 (5천만)', '중대형 건설사', '1社 1-3억'),
+        ('SmartConstruct-Drone', 'AI 보안 드론', '대형 현장 자율 순찰', 'Skydio + Llama 4', 'Mac Studio 1대 + Skydio', '대규모 현장', '1현장 5-15억'),
+        ('SmartConstruct-LiDAR', 'LiDAR 3D', '주간 3D 스캔·BIM 자동 업데이트', 'Velodyne + Open3D', 'Mac Studio 1대 + LiDAR', '대형 건설사', '1社 2-5억'),
+        ('SmartConstruct-Causal', 'DoWhy 인과', '중대재해 인과 분석·예방 권고', 'DoWhy + 사고 사례 DB', 'Mac Studio 1대', '의무사', '월 100-300만'),
+        ('SmartConstruct-Predict', 'Llama 4 Scout (1M)', '1년 공정 데이터 분석·예측', 'Llama 4 Scout 1M', 'Mac Studio 2대', '대기업 시공사', '1프로젝트 3-7억'),
+        ('SmartConstruct-Weather', 'Climate AI', '날씨 자동 통합·공정 조정', 'GraphCast + 기상청 API', 'Mac Studio 1대', '옥외 시공', '월 50-200만'),
+        ('SmartConstruct-Material', 'MatterGen', '신소재 추천·최적화', 'Microsoft MatterGen API', 'Mac Studio 1대', '건설사 R&D', '1社 1-3억'),
+        ('SmartConstruct-Robot', 'Humanoid·Quadruped', '현장 자율 순찰·검사 로봇', 'Boston Dynamics Spot + Llama 4', 'Mac Studio 1대 + Spot', '대규모 현장', '1대 1-3억'),
+    ]),
+    # ───── 영역 4: 카지노 VMS (10) ─────
+    ('🎰', '4. 카지노 VMS (9社 독점)', '강원랜드 + 외국인전용 9社', [
+        ('CasinoVMS-Emotion', 'Llama 4 + 감정 LoRA', '딜러·플레이어 감정·중독 감지', 'Llama 4 + 감정 인식 LoRA', 'Mac Studio 2대', '9社 + 글로벌', '1社 5억+'),
+        ('CasinoVMS-VLA', 'OpenVLA 의도 추론', '딜러-플레이어 공모·이상 행동', 'OpenVLA + CCTV', 'Mac Studio 1대 + Edge', '전 카지노', '1社 3-7억'),
+        ('CasinoVMS-Quantum', 'IBM Quantum', '게임 결과 통계 양자 검증', 'IBM Quantum + Qiskit', 'IBM Quantum Cloud', '고급 카지노', '1社 5-10억'),
+        ('CasinoVMS-Biometric', 'Multi-modal Biometric', '정맥·홍채·걸음 다중 인증', 'Idemia·Suprema SDK', 'Mac Studio 1대 + 생체장비', '외국인 카지노', '1社 3-5억'),
+        ('CasinoVMS-AML', 'GraphRAG + Causal', '자금세탁 다중 hop 추적', 'Neo4j + DoWhy + Llama 4', 'Mac Studio 1대 + Neo4j', '금감원 의무', '월 300-1000만'),
+        ('CasinoVMS-Mobile', 'Mobile Agent', 'VIP 호스트 실시간 가이드', 'Llama 4 + 모바일 앱', '클라우드 + Mac Studio', 'VIP룸', '월 100-500만'),
+        ('CasinoVMS-Stream', 'Llama 4 Multimodal', '온라인 카지노 실시간 통합 분석', 'Llama 4 Vision + Audio', 'Mac Studio 3대', '온라인 카지노', '월 1000만+'),
+        ('CasinoVMS-Addict', 'Behavioral + Emotion', '도박중독 조기 경보', 'Llama 4 + 임상 데이터 LoRA', 'Mac Studio 1대', '강원랜드·정부', 'B2G 1-3억'),
+        ('CasinoVMS-Predict', 'Llama 4 Scout (1M)', '1년 게임 데이터 예측·운영 최적', 'Llama 4 Scout 1M', 'Mac Studio 2대', '경영진', '1社 2-5억'),
+        ('CasinoVMS-Global', 'OEM 통합', '한국 9社 검증 → 글로벌 진출', '영업·OEM 채널 구축', '각 국가 1대', '아시아 100+', '1社 5-15억'),
+    ]),
+    # ───── 영역 5: 금융 VMS (10) ─────
+    ('🏦', '5. 금융 VMS', '은행·증권·카드사 30+', [
+        ('FinVMS-Behavioral', 'Behavioral Biometrics', '타이핑·마우스·걸음 상시 인증', 'BioCatch SDK 또는 자체', 'Mac Studio 1대', '은행·증권', '1社 2-5억'),
+        ('FinVMS-Deepfake', 'Deepfake Detection', '보이스피싱·AI 합성 위조 탐지', 'Reality Defender API', 'Mac Studio 1대', '전 금융사', '1社 3-7억'),
+        ('FinVMS-PQC', 'PQC 마이그레이션', 'NIST 의무 양자내성암호 전환', '자체 + KISA 가이드', '컨설팅 인력만', '전 대기업', '1社 1-3억'),
+        ('FinVMS-FDS', 'Llama 4 ×3 합의', '다중 AI 부정거래·거짓양성 50%↓', 'Llama 4 ×3 hook', 'Mac Studio 3대', '은행·카드사', '1社 5-10억'),
+        ('FinVMS-Voice', 'Llama 4 + Voice', '콜센터 음성 위조·이상 탐지', 'Llama 4 + Pindrop OEM', 'Mac Studio 1대', '은행 콜센터', '월 300-1000만'),
+        ('FinVMS-Insider', 'UEBA + Continuous Auth', '내부자 위협 차세대', 'Llama 4 + 행동 패턴 LoRA', 'Mac Studio 1대', '금융·보험', '1社 3-7억'),
+        ('FinVMS-Credit', 'Llama 4 + 금융 LoRA', '한국형 BloombergGPT·대안 데이터', 'Llama 4 + 금융 데이터 LoRA', 'Mac Studio 2대', '은행·핀테크', '월 500만~'),
+        ('FinVMS-CBDC', 'CBDC + AI 결제', '한국은행 디지털화폐 인프라 SI', '한은 SDK + 자체 운영', 'Mac Studio 5대 클러스터', '은행·결제', '1社 10-30억'),
+        ('FinVMS-Regtech', 'Constitutional AI', '금감원 규제 자동 추적·헌법화', 'failure-mode 패턴', 'Mac Studio 1대', '전 금융사', '월 300-700만'),
+        ('FinVMS-Bureau', 'UEBA + Multi-Agent', '한국 행동신용평가소', '점수 모델 IP + 라이선스', 'Mac Studio 3대', '보험·HR·IAM', '영구 라이선스'),
+    ]),
+    # ───── 영역 6: AI CCTV (10) ─────
+    ('📹', '6. AI 지능형 CCTV', '영상 분석', [
+        ('SmartCCTV-World', 'NVIDIA Cosmos', '물리법칙 학습·미래 예측', 'Cosmos Free Research', 'Mac Studio 2대 + GPU', '기존+신규', '월 100-300만'),
+        ('SmartCCTV-VLA', 'OpenVLA', '자율 추론·자연어 알람', 'OpenVLA + Llama 4', 'Mac Studio 1대 + Edge', '공공·금융', '1社 1-3억'),
+        ('SmartCCTV-Search', 'Llama 4 Multimodal', '자연어 영상 검색', 'Llama 4 Vision', 'Mac Studio 2대', '대형 시설', '월 100-500만'),
+        ('SmartCCTV-Crowd', 'Crowd Analytics', '밀집도·이상 행동·조기 경보', '자체 SDK + Llama 4', 'Mac Studio 1대', '행안부·지자체', 'B2G 5-20억'),
+        ('SmartCCTV-Fire', 'Multimodal + 열화상', '화재·연기 조기 탐지', 'Llama 4 + 열화상 카메라', 'Mac Studio 1대 + 열화상', '소방청·산림청', 'B2G 5-15억'),
+        ('SmartCCTV-Safety', 'VLA + PPE', '산업현장 안전 모니터링', 'OpenVLA + Edge AI', 'Mac Studio 1대 + Edge', '제조·건설', '1社 3-8억'),
+        ('SmartCCTV-Mood', 'Llama 4 + 감정', '매장 고객 만족도·VOC 자동', 'Llama 4 + 감정 LoRA', 'Mac Studio 1대', '유통·매장', '월 100-500만'),
+        ('SmartCCTV-Privacy', 'Privacy ML', '얼굴·번호판 자동 마스킹', '자체 마스킹 모델', 'Mac Studio 1대', '공공·기업', '월 50-200만'),
+        ('SmartCCTV-Edge', 'Edge AI Chip', 'CCTV 자체 추론·저전력', 'Hailo + Jetson', 'Edge 칩 (대당 100만)', '분산 시설', '대당 100-300만'),
+        ('SmartCCTV-Drone', 'Drone Detection', 'CCTV + 안티드론 통합', 'Dedrone + Llama 4', 'Mac Studio 1대 + 드론센서', '국방·국가시설', 'B2G 10-30억'),
+    ]),
+    # ───── 영역 7: 디지털트윈 (10) ─────
+    ('🌐', '7. 디지털 트윈', '제조·건설·인프라', [
+        ('DigitalTwin-Cosmos', 'NVIDIA Cosmos', '물리법칙 자동 학습·시나리오 생성', 'Cosmos World Foundation', 'NVIDIA Cluster (1억)', '현대·기아·삼성·SK', '1社 50-100억'),
+        ('DigitalTwin-Sim2Real', 'NVIDIA Isaac', '시뮬→실제 transfer·학습비 1/100', 'Isaac Sim', 'NVIDIA Cluster', '로봇·자율시스템 사', '1프로젝트 10-30억'),
+        ('DigitalTwin-Humanoid', 'NVIDIA GR00T', '휴머노이드 가상 학습', 'GR00T + 디지털트윈', 'NVIDIA Cluster', '현대·삼성', '1社 20-50억'),
+        ('DigitalTwin-City', '도시 디지털트윈', '서울·부산 등 도시 SI', 'Bentley iTwin + LH 협업', 'Mac Studio 5대 + NVIDIA', '지자체·LH', 'B2G 30-100억'),
+        ('DigitalTwin-Energy', 'SMR + 디지털트윈', '소형 원전 AI 운영', '두산·SK 협업', 'Mac Studio 5대', '원전·에너지', '50-200억'),
+        ('DigitalTwin-Factory', 'Industrial Metaverse', '스마트팩토리 SI', 'Siemens + Omniverse', 'Mac Studio 3대 + NVIDIA', '제조 대기업', '1공장 10-50억'),
+        ('DigitalTwin-VR', 'Spatial Computing', 'VR 가상 관제실', 'Vision Pro + Unity', 'Vision Pro 10대 + Mac Studio', '관제·교육', '1社 3-10억'),
+        ('DigitalTwin-Train', 'Synthetic Data', '학습데이터 라이선싱', '디지털트윈 → 데이터 마켓', 'Mac Studio 3대', '글로벌 AI 회사', '데이터 라이선스'),
+        ('DigitalTwin-Climate', 'Climate AI', '탄소 디지털트윈', 'GraphCast + 자체', 'Mac Studio 2대', '대기업 ESG', '1社 3-10억'),
+        ('DigitalTwin-Defense', '국방 시뮬레이션', 'K-방산 무기·전장 시뮬', '한화·LIG 협업', 'NVIDIA Cluster + 보안', '방위사업청', '50-150억'),
+    ]),
+    # ───── 영역 8: ITO 운영 (10) ─────
+    ('⚙️', '8. ITO (IT 아웃소싱)', 'IT 운영 위탁', [
+        ('ITO-Agentic', 'Llama 4 + Agentic', '24/7 자율 운영·사람 1명 = 100배', 'Llama 4 + LangGraph + MCP', 'Mac Studio 2대', '기존 ITO 고객', '월 1000-3000만'),
+        ('ITO-Workload', 'AI Workload Protection', 'AI 모델·데이터 보호 MSP', 'Palo Alto·Wiz OEM', 'Mac Studio 1대 + 클라우드', 'AI 도입 기업', '월 500-2000만'),
+        ('ITO-NHI', 'NHI', 'AI 에이전트·서비스계정 신원', 'Astrix·Oasis OEM', 'Mac Studio 1대', 'AI 도입 기업', '월 200-1000만'),
+        ('ITO-eBPF', 'eBPF Cilium', '커널 레벨 관측·보안', 'Cilium·Falco OSS', 'Mac Studio 1대', '대기업 IT', '1社 3-10억'),
+        ('ITO-CSMA', 'Cybersecurity Mesh', '분산 보안 표준 SI', 'Fortinet·Cisco OEM', 'Mac Studio 2대', '멀티클라우드', '1社 5-15억'),
+        ('ITO-DSPM', 'DSPM', '데이터 위치·민감도 추적', 'Cyera·Sentra OEM', 'Mac Studio 1대', '개인정보 의무', '월 300-1000만'),
+        ('ITO-FinOps', 'AI Cloud Cost', '클라우드 비용 자동 최적화', 'CloudHealth + 자체 ML', 'Mac Studio 1대', '클라우드 사용사', '절감액 20%'),
+        ('ITO-DR', 'AI DR', '장애 자동 진단·복구', '자체 ML + AIOps', 'Mac Studio 2대', '금융·공공', '1社 5-20억'),
+        ('ITO-Compliance', '자동 규제', 'ISMS-P·금감원 자동 준수', '자체 규제 매핑', 'Mac Studio 1대', '금융·공공', '월 200-500만'),
+        ('ITO-Green', '탄소 측정', 'DC 탄소 측정·EU CBAM', '자체 측정 SaaS', 'Mac Studio 1대', '대기업 IT', '월 100-300만'),
+    ]),
+    # ───── 영역 9: ESG·GRC (10) ─────
+    ('🌱', '9. ESG·GRC', 'ESG·거버넌스', [
+        ('ESG-GRC-Climate', 'Climate AI', '탄소 디지털트윈·CCUS 최적화', 'GraphCast + 자체', 'Mac Studio 2대', '대기업 ESG', '1社 3-10억'),
+        ('ESG-GRC-Report', 'Llama 4 + 생성형', '보고서 자동 작성', 'Llama 4 + ESG 템플릿', 'Mac Studio 1대', '상장사', '월 200-500만'),
+        ('ESG-GRC-ISO42001', 'ISO 42001', 'AI 라이프사이클 audit', '자체 audit 도구', 'Mac Studio 1대', 'AI 도입 1000+', '1社 1-5억'),
+        ('ESG-GRC-Bias', 'Fairlearn', 'AI 편향 자동 감사', 'Fairlearn OSS', 'Mac Studio 1대', '금융·HR·AI', '1社 1-3억'),
+        ('ESG-GRC-Explain', 'SHAP·LIME', 'AI 결정 설명 자동', 'SHAP + Captum', 'Mac Studio 1대', '고위험 AI 사용', '1社 2-5억'),
+        ('ESG-GRC-Supply', 'LangChain + 공급망', '협력사 ESG 평가', 'Llama 4 + 공급망 DB', 'Mac Studio 2대', '대기업', '월 300-1000만'),
+        ('ESG-GRC-Scope3', '탄소 자동 산정', 'Scope 1·2·3 자동·정규 의무', '자체 + IPCC 표준', 'Mac Studio 1대', '상장사', '월 200-500만'),
+        ('ESG-GRC-Water', 'IoT + Water AI', '물·자원 최적화', 'IoT 센서 + 자체 ML', 'Mac Studio 1대 + IoT', '제조 대기업', '월 100-300만'),
+        ('ESG-GRC-Carbon', 'K-ETS + AI', '탄소권 거래 최적화', '자체 거래 예측 모델', 'Mac Studio 1대', '탄소 배출사', '1社 5-15억'),
+        ('ESG-GRC-Risk', 'Cyber Resilience', '회복력 점수화·정기 audit', '자체 표준', 'Mac Studio 1대', '대기업·보험사', '월 500-1500만'),
+    ]),
+    # ───── 영역 10: 부서 IP (10) ─────
+    ('🚨', '10. 부서 IP (신규 한국 표준)', '행동위험 외 신영역 K-Standard', [
+        ('AI Risk Lighthouse', '8 카테고리 audit', '한국 K-Standard 후보', '자체 8 카테고리 도구', 'Mac Studio 1대', '5,000 대기업', '영구 5,000억'),
+        ('K-Quantum Standard', 'PQC + 양자보안 표준', '한국 양자보안 표준 인증', 'KISA 협력 + 자체', '컨설팅 인력', '금융·국방·공공', '영구 인증료'),
+        ('AI 거버넌스 컨설팅', 'ISO 42001 + EU AI Act', '한국 1호 인증 사업자', '인증 + 컨설팅', '컨설팅 인력', 'AI 도입 모든', '1社 3-10억'),
+        ('행동신용평가소', 'UEBA + Multi-Agent', 'KCB식 행동신용평가소', '점수 모델·라이선스', 'Mac Studio 3대', '보험·HR·IAM', '영구 라이선스'),
+        ('한국형 BloombergGPT', 'Llama 4 + 금융 LoRA', '자체 도메인 LLM', 'Llama 4 + 금융 데이터 LoRA', 'Mac Studio 2대', '금융·회계', '월 500만~'),
+        ('Synthetic Data 마켓', '합성데이터 라이선싱', '한국 산업 데이터 마켓', '자체 + Gretel 패턴', 'Mac Studio 3대', '글로벌 AI 회사', '데이터 라이선스'),
+        ('Federated Consortium', 'Flower 컨소시엄', '금융 공동 부정탐지', 'Flower OSS', '각 은행 1대씩', '은행연합회', '월구독'),
+        ('휴머노이드 보안 인증', '디지털트윈 + 보안', '한국 휴머노이드 보안 표준', '자체 표준', 'Mac Studio 2대', '현대·삼성', '인증 5천만-3억'),
+        ('AGI 거버넌스 자문', 'Mech Interp + 안전', '한국 AGI 안전 자문', '자체 연구 + Anthropic 협력', '연구 인력', '대기업·정부', '시간당 자문료'),
+        ('K-AI Academy', 'AI 교육·자격증', 'KISA 등록 정식 과정', '교육 콘텐츠 + LMS', 'Mac Studio 1대', '전 한국 기업', '수강료+자격증'),
+    ]),
+    # ───── 영역 11: 공공·전자정부 (ENTEC 협업) ─────
+    ('🏛️', '11. 공공·전자정부 (ENTEC 협업)', '전자정부 1위', [
+        ('Gov-LLM', 'Llama 4 + 행정 LoRA', '공공기관 행정 특화 LLM', 'Llama 4 + 행정 데이터 LoRA', 'Mac Studio 2대', '중앙·지방 정부', 'B2G 5-30억'),
+        ('Gov-Chatbot', 'Llama 4 + 민원', '24/7 민원 응대 자동화', 'Llama 4 + RAG', 'Mac Studio 1대', '지자체·공공', '1기관 1-3억'),
+        ('Gov-Doc', 'Llama 4 + Vision', '공문·법령 OCR·자동 분류', 'Llama 4 Multimodal', 'Mac Studio 1대', '중앙부처', '1기관 2-5억'),
+        ('Gov-Voice', 'Llama 4 Voice', '음성 민원 자동 처리', 'Llama 4 + STT/TTS', 'Mac Studio 1대', '120 다산콜·129 보건', 'B2G 3-10억'),
+        ('Gov-Predict', 'Llama 4 Scout (1M)', '정책 영향 분석·예측', 'Llama 4 Scout', 'Mac Studio 2대', '정책기획·국회', 'B2G 5-15억'),
+        ('Gov-Audit', 'Constitutional AI', '공직 감사 자동화·청렴 검증', '자체 헌법화', 'Mac Studio 1대', '감사원·국정원', 'B2G 3-10억'),
+        ('Gov-Disaster', 'Multimodal + Climate', '재난 자동 모니터·대응', 'GraphCast + Llama 4 Vision', 'Mac Studio 2대', '행안부·소방청', 'B2G 10-30억'),
+        ('Gov-Welfare', 'Llama 4 + 복지', '복지 사각지대 자동 발굴', 'Llama 4 + 복지 데이터', 'Mac Studio 1대', '보건복지부', 'B2G 5-15억'),
+        ('Gov-Tax', 'GraphRAG + 세무', '세무·탈세 자동 탐지', 'Neo4j + Llama 4', 'Mac Studio 2대 + Neo4j', '국세청·관세청', 'B2G 10-30억'),
+        ('Gov-Identity', 'Behavioral Biometrics', '공공 디지털 신원', 'BioCatch + FIDO2', 'Mac Studio 1대', '행안부·KISA', 'B2G 5-15억'),
+    ]),
+    # ───── 영역 12: 클라우드 (CTS·CLOIT 협업) ─────
+    ('☁️', '12. 클라우드 네이티브 (CTS·CLOIT 협업)', 'Google Cloud Partner', [
+        ('Cloud-AI-Native', 'Llama 4 + K8s', 'AI 네이티브 컨테이너 운영', 'Llama 4 + Kubernetes', 'Mac Studio 3대 + K8s', '대기업 IT', '1社 5-15억'),
+        ('Cloud-Migration', 'AI 마이그레이션', '온프레→클라우드 자동', 'Llama 4 + 마이그레이션 도구', 'Mac Studio 1대 + Cloud', '대기업', '1社 5-30억'),
+        ('Cloud-Multi', 'Llama 4 + Multi-cloud', 'AWS·Azure·GCP 통합', '자체 추상화', 'Mac Studio 2대', '글로벌 기업', '월 1000만+'),
+        ('Cloud-Cost', 'AI FinOps', '비용 자동 최적화', 'CloudHealth + 자체', 'Mac Studio 1대', '클라우드 사용사', '절감액 20%'),
+        ('Cloud-Sec', 'CSPM/CIEM', '클라우드 보안 자동', 'Wiz·Lacework OEM', 'Mac Studio 1대', '클라우드 사용사', '월 500-2000만'),
+        ('Cloud-DR', 'AI Disaster Recovery', '클라우드 장애 자동 복구', '자체 + AIOps', 'Mac Studio 2대', '금융·공공', '1社 5-20억'),
+        ('Cloud-Edge', 'Edge Computing', '엣지·CDN 자동 운영', 'Cloudflare·Fastly + 자체', 'Mac Studio 1대', '글로벌 기업', '월 500만+'),
+        ('Cloud-Serverless', 'Llama 4 + Serverless', 'AI 서버리스 자동화', 'Lambda·Cloud Run + Llama', 'Mac Studio 1대', 'SW 회사', '월 200-1000만'),
+        ('Cloud-K8s-AI', 'AIOps Kubernetes', 'K8s AI 자율 운영', 'Llama 4 + K8s 운영', 'Mac Studio 2대', '대기업 IT', '월 500-1500만'),
+        ('Cloud-SovEU', 'Sovereign Cloud', '국가 데이터 주권 클라우드', '자체 + 정부 협력', 'Mac Studio 5대', '국가·금융', 'B2G 30-100억'),
+    ]),
+    # ───── 영역 13: 사이버보안 (PNS 협업) ─────
+    ('🛡️', '13. 사이버보안 (PNS 협업)', '사이버보안 전문', [
+        ('Sec-SOC', 'Llama 4 + Multi-Agent', '24/7 자율 SOC 운영', 'Llama 4 ×3 + SOAR', 'Mac Studio 3대', '금융·대기업', '1社 10-30억'),
+        ('Sec-XDR', 'XDR + AI', '통합 탐지·대응', 'CrowdStrike·SentinelOne OEM', 'Mac Studio 1대', '대기업', '월 1000-3000만'),
+        ('Sec-ZeroTrust', 'Zero Trust', 'ZTNA 자동 정책', 'Zscaler·Cato OEM', 'Mac Studio 2대', '금융·공공', '1社 5-15억'),
+        ('Sec-Adv-ML', 'Adversarial ML Defense', 'AI 모델 공격 방어', 'Robust Intelligence OEM', 'Mac Studio 1대', 'AI 사용 기업', '1社 3-10억'),
+        ('Sec-Prompt', 'Prompt Injection Defense', '직원 LLM 보호', 'Lakera·Aim OEM', 'Mac Studio 1대', 'AI 도입 기업', '월 300-1000만'),
+        ('Sec-Threat', 'Threat Intelligence', '위협 인텔리전스 AI', 'CrowdStrike + Llama 4', 'Mac Studio 1대', '금융·공공', '월 500-2000만'),
+        ('Sec-Hunt', 'Threat Hunting AI', '자율 위협 사냥', 'Llama 4 + SIEM', 'Mac Studio 2대', '대기업', '월 500-1500만'),
+        ('Sec-IR', 'Incident Response AI', '침해 자동 분석·대응', 'Llama 4 + SOAR', 'Mac Studio 2대', '금융·공공', '1社 5-15억'),
+        ('Sec-Anti-Drone', 'Drone Detection', '드론 탐지·요격', 'Dedrone·DroneShield', 'Mac Studio 1대 + 센서', '국방·공항', 'B2G 10-30억'),
+        ('Sec-OT', 'OT/ICS Security', '산업제어망 보안', 'Claroty·Nozomi OEM', 'Mac Studio 1대', '제조·에너지', '1社 5-15억'),
+    ]),
+    # ───── 영역 14: 데이터·AI 거버넌스 ─────
+    ('📊', '14. 데이터·AI 거버넌스', '데이터 관리·AI 라이프사이클', [
+        ('Data-Catalog', 'Llama 4 + Catalog', 'AI 자동 데이터 카탈로그', 'Llama 4 + Collibra OEM', 'Mac Studio 1대', '대기업', '월 300-1000만'),
+        ('Data-Lineage', 'Graph DB', '데이터 흐름 자동 추적', 'Neo4j + Llama 4', 'Mac Studio 1대 + Neo4j', '금융·공공', '1社 3-10억'),
+        ('Data-Quality', 'AI Data Quality', '데이터 품질 자동 점검', 'Great Expectations + Llama 4', 'Mac Studio 1대', 'DW 사용사', '월 200-500만'),
+        ('Data-Privacy', 'PET 통합', '개인정보 자동 보호', 'Differential Privacy + Confidential', 'Mac Studio 1대', '개인정보 의무', '1社 2-5억'),
+        ('Data-Mesh', 'Data Mesh AI', '분산 데이터 거버넌스', 'Databricks + Llama 4', 'Mac Studio 2대', '대기업', '1社 5-15억'),
+        ('Data-Vector', 'Vector DB', '임베딩 검색 인프라', 'ChromaDB·Pinecone', 'Mac Studio 1대', 'AI 도입 기업', '월 200-1000만'),
+        ('Data-Anonymize', '익명화 자동', '자동 익명화·가명화', '자체 마스킹 + Privacy ML', 'Mac Studio 1대', '의무 기업', '1社 1-3억'),
+        ('Data-Sovereignty', '데이터 주권', '국가 데이터 주권 관리', '자체 + 정부 협력', 'Mac Studio 2대', '공공·금융', 'B2G 5-20억'),
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
