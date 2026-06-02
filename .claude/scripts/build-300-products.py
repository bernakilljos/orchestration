"""ITCEN CORE × Llama 4 — 300 신상품 HTML 자동 생성

30 영역 × 10 신상품 = 300
모두 Llama 4 (오픈소스·자체 운영) base
인프라: Mac Studio M3 Ultra 512GB 명시
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'outputs', 'itcen', 'html', 'itcen-core-300신상품.html')

# 30 영역 × 10 신상품
# 각 신상품: (이름, 접목기술, 무엇, 어떻게, 인프라, 대상, 매출)

AREAS = [
    # ───── 영역 1: 내부회계 (10) ─────
    ('📒', '1. 내부회계 (MicroICM-C 1위)', '국내 1위 · 156 RCM · 현대·LX·하림 등 보유', [
        ('MicroICM-Reasoning', 'Llama 4 + Reasoning', '분식·횡령 사고 과정 자동 추론·감사보고서 생성', 'Llama 4 + RCM 매핑 LoRA · 보고서 템플릿', 'Mac Studio 1대 (1.5천만)', '현대 계열사 1000+', '1社 1-3억'),
        ('MicroICM-Causal', 'DoWhy 인과 추론', '분식의 진짜 원인 (감독·시스템·의도) 자동 식별', 'DoWhy OSS + 인과 그래프 자체 구축', 'Mac Studio 1대', '금융·공공 GRC', '1社 2-5억'),
        ('MicroICM-Critique', 'Llama 4 ×2 검증', '156 통제 1차→2차 검토 합의·거짓양성 50%↓', 'Llama 4 ×2 hook·confidence < 0.7 재시도', 'Mac Studio 1대', '전 기존 고객', '월 100-500만'),
        ('MicroICM-Graph', 'GraphRAG (Neo4j)', '결재-거래-회계 그래프 다중 hop 횡령 추적', 'Neo4j 무료 + Llama 4 entity 추출', 'Mac Studio 1대 + Neo4j', '대기업·금융', '1社 3-7억'),
        ('MicroICM-Quantum', 'IBM Quantum ML', '거래 양자 최적화 부정탐지', 'IBM Quantum Network 무료 + Qiskit', 'IBM Quantum (Cloud)', '금융권', '1社 5억+'),
        ('MicroICM-Synthetic', 'Gretel 합성데이터', '부정 사례 합성 100만건·개인정보 0', 'Gretel 무료 tier + 자체 generator', 'Mac Studio 1대', '금감원 의무사', '컨설팅'),
        ('MicroICM-Voice', 'Llama 4 Voice', '"분식 의심 보여줘" 음성 질의·답변', 'Llama 4 + Whisper STT + TTS', 'Mac Studio 1대', '경영진·임원', '월 50만/사용자'),
        ('MicroICM-Vision', 'Llama 4 Vision', '영수증·송장 OCR + 자동 회계 입력', 'Llama 4 Multimodal + 회계 LoRA', 'Mac Studio 2대', '중견기업', '1社 1-2억'),
        ('MicroICM-Federated', 'Flower OSS', '여러 그룹사 데이터 안 모으고 학습', 'Flower 무료 + 각 사 자체 서버', '각 사 1대씩', '그룹사·컨소시엄', '월구독'),
        ('MicroICM-Agent', 'Llama 4 + Agentic', 'AI 자율 감사 봇·24/7 모니터·보고', 'Llama 4 + LangGraph + MicroICM 통합', 'Mac Studio 2대', '대기업 그룹', '월 1000-3000만'),
    ]),
    # ───── 영역 2: CCP 준법 (10) ─────
    ('⚖️', '2. CCP 준법경영 (EPM·Compliance 1위)', 'EPM·Compliance 1위 · ISO 42001 base', [
        ('MicroCCP-LLM', 'Llama 4 + 도메인 LoRA', '한국 법규·사규 특화 LLM·회사별 fine-tune', 'Llama 4 + 법규 데이터 LoRA', 'Mac Studio 1대', '1000+ CCP 사', '1社 5천만-2억'),
        ('MicroCCP-GraphRAG', 'GraphRAG', '사규·법규·판례·위반사례 그래프', 'Microsoft GraphRAG OSS', 'Mac Studio 1대 + Neo4j', '금융·공공', '1社 3-5억'),
        ('MicroCCP-Constitutional', 'Constitutional AI', '사규를 헌법으로 박고 AI 자동 준수', 'failure-mode.md 패턴 + PreToolUse hook', 'Mac Studio 1대', 'AI 도입 기업', '1社 2-4억'),
        ('MicroCCP-Watcher', 'AI Search', '법규 변경 24/7 자동 추적·영향 분석', '자체 RSS + Llama 4', 'Mac Studio 1대', '대기업·금융', '월 200-500만'),
        ('MicroCCP-Contract', 'Llama 4 Scout (1M)', '계약서 전문 단일 분석·위험 조항 발견', 'Llama 4 Scout 1M context', 'Mac Studio 2대', '법무팀·임원실', '월 100-300만'),
        ('MicroCCP-Whistle', 'Multi-Agent + Privacy', '제보 익명화·다중 AI 검토', 'Llama 4 ×3 + 차등프라이버시', 'Mac Studio 2대', '대기업', '1社 1-3억'),
        ('MicroCCP-AML', 'GraphRAG + Causal', '자금세탁 다중 hop 자동 추적·금감원 보고', 'Neo4j + DoWhy + Llama 4', 'Mac Studio 2대 + Neo4j', '금융 의무', '1社 5-10억'),
        ('MicroCCP-Sanction', 'Generative AI', 'OFAC·UN 제재 자동 스크리닝·보고서', 'Llama 4 + 제재 DB 통합', 'Mac Studio 1대', '은행·증권·카드', '월 500만~'),
        ('MicroCCP-EU', 'Mech Interpretability', 'EU AI Act 의무 — AI 결정 설명·인증', 'SAE 도구 + Captum (PyTorch)', 'Mac Studio 2대', 'EU 수출 기업', '1社 3-8억'),
        ('MicroCCP-Audit', 'Llama 4 + Computer Use', '자율 컴플라이언스 점검·증거 수집', 'Llama 4 + Computer Use + RPA', 'Mac Studio 2대', '대기업·공공', '월 500-1500만'),
    ]),
    # ───── 영역 3: 건설 ERP (10) ─────
    ('🏗️', '3. 건설 ERP (국내 1위)', '건설업 표준 · 중대재해법 의무', [
        ('SmartConstruct-Cosmos', 'NVIDIA Cosmos', '가상 시공 시뮬·사고·붕괴 예측', 'NVIDIA Cosmos Free Research', 'Mac Studio 2대 + NVIDIA GPU 1', '50인+ 건설사', '1社 5천만-2억'),
        ('SmartConstruct-VLA', 'OpenVLA + AI CCTV', '작업자 자세·위험행동·PPE 미착용 감지', 'OpenVLA + Edge AI', 'Mac Studio 1대 + Edge', '1만+ 건설사', '월 50-200만'),
        ('SmartConstruct-AR', 'AR 디지털트윈', '스마트글래스 현장 가이드', 'Vision Pro + Unity', 'Vision Pro 10대 (5천만)', '중대형 건설사', '1社 1-3억'),
        ('SmartConstruct-Drone', 'AI 보안 드론', '대형 현장 자율 순찰', 'Skydio + Llama 4', 'Mac Studio 1대 + Skydio', '대규모 현장', '1현장 5-15억'),
        ('SmartConstruct-LiDAR', 'LiDAR 3D', '주간 3D 스캔·BIM 자동 업데이트', 'Velodyne + Open3D', 'Mac Studio 1대 + LiDAR', '대형 건설사', '1社 2-5억'),
        ('SmartConstruct-Causal', 'DoWhy 인과', '중대재해 인과 분석·예방 권고', 'DoWhy + 사고 사례 DB', 'Mac Studio 1대', '의무사', '월 100-300만'),
        ('SmartConstruct-Predict', 'Llama 4 Scout (1M)', '1년 공정 데이터 분석·예측', 'Llama 4 Scout 1M', 'Mac Studio 2대', '대기업 시공사', '1프로젝트 3-7억'),
        ('SmartConstruct-Weather', 'Climate AI', '날씨 자동 통합·공정 조정', 'GraphCast + 기상청 API', 'Mac Studio 1대', '옥외 시공', '월 50-200만'),
        ('SmartConstruct-Material', 'MatterGen', '신소재 추천·최적화', 'Microsoft MatterGen API', 'Mac Studio 1대', '건설사 R&D', '1社 1-3억'),
        ('SmartConstruct-Robot', 'Humanoid·Quadruped', '현장 자율 순찰·검사 로봇', 'Boston Dynamics Spot + Llama 4', 'Mac Studio 1대 + Spot', '대규모 현장', '1대 1-3억'),
    ]),
    # ───── 영역 4: 카지노 VMS (10) ─────
    ('🎰', '4. 카지노 VMS (9社 독점)', '강원랜드 + 외국인전용 9社', [
        ('CasinoVMS-Emotion', 'Llama 4 + 감정 LoRA', '딜러·플레이어 감정·중독 감지', 'Llama 4 + 감정 인식 LoRA', 'Mac Studio 2대', '9社 + 글로벌', '1社 5억+'),
        ('CasinoVMS-VLA', 'OpenVLA 의도 추론', '딜러-플레이어 공모·이상 행동', 'OpenVLA + CCTV', 'Mac Studio 1대 + Edge', '전 카지노', '1社 3-7억'),
        ('CasinoVMS-Quantum', 'IBM Quantum', '게임 결과 통계 양자 검증', 'IBM Quantum + Qiskit', 'IBM Quantum Cloud', '고급 카지노', '1社 5-10억'),
        ('CasinoVMS-Biometric', 'Multi-modal Biometric', '정맥·홍채·걸음 다중 인증', 'Idemia·Suprema SDK', 'Mac Studio 1대 + 생체장비', '외국인 카지노', '1社 3-5억'),
        ('CasinoVMS-AML', 'GraphRAG + Causal', '자금세탁 다중 hop 추적', 'Neo4j + DoWhy + Llama 4', 'Mac Studio 1대 + Neo4j', '금감원 의무', '월 300-1000만'),
        ('CasinoVMS-Mobile', 'Mobile Agent', 'VIP 호스트 실시간 가이드', 'Llama 4 + 모바일 앱', '클라우드 + Mac Studio', 'VIP룸', '월 100-500만'),
        ('CasinoVMS-Stream', 'Llama 4 Multimodal', '온라인 카지노 실시간 통합 분석', 'Llama 4 Vision + Audio', 'Mac Studio 3대', '온라인 카지노', '월 1000만+'),
        ('CasinoVMS-Addict', 'Behavioral + Emotion', '도박중독 조기 경보', 'Llama 4 + 임상 데이터 LoRA', 'Mac Studio 1대', '강원랜드·정부', 'B2G 1-3억'),
        ('CasinoVMS-Predict', 'Llama 4 Scout (1M)', '1년 게임 데이터 예측·운영 최적', 'Llama 4 Scout 1M', 'Mac Studio 2대', '경영진', '1社 2-5억'),
        ('CasinoVMS-Global', 'OEM 통합', '한국 9社 검증 → 글로벌 진출', '영업·OEM 채널 구축', '각 국가 1대', '아시아 100+', '1社 5-15억'),
    ]),
    # ───── 영역 5: 금융 VMS (10) ─────
    ('🏦', '5. 금융 VMS', '은행·증권·카드사 30+', [
        ('FinVMS-Behavioral', 'Behavioral Biometrics', '타이핑·마우스·걸음 상시 인증', 'BioCatch SDK 또는 자체', 'Mac Studio 1대', '은행·증권', '1社 2-5억'),
        ('FinVMS-Deepfake', 'Deepfake Detection', '보이스피싱·AI 합성 위조 탐지', 'Reality Defender API', 'Mac Studio 1대', '전 금융사', '1社 3-7억'),
        ('FinVMS-PQC', 'PQC 마이그레이션', 'NIST 의무 양자내성암호 전환', '자체 + KISA 가이드', '컨설팅 인력만', '전 대기업', '1社 1-3억'),
        ('FinVMS-FDS', 'Llama 4 ×3 합의', '다중 AI 부정거래·거짓양성 50%↓', 'Llama 4 ×3 hook', 'Mac Studio 3대', '은행·카드사', '1社 5-10억'),
        ('FinVMS-Voice', 'Llama 4 + Voice', '콜센터 음성 위조·이상 탐지', 'Llama 4 + Pindrop OEM', 'Mac Studio 1대', '은행 콜센터', '월 300-1000만'),
        ('FinVMS-Insider', 'UEBA + Continuous Auth', '내부자 위협 차세대', 'Llama 4 + 행동 패턴 LoRA', 'Mac Studio 1대', '금융·보험', '1社 3-7억'),
        ('FinVMS-Credit', 'Llama 4 + 금융 LoRA', '한국형 BloombergGPT·대안 데이터', 'Llama 4 + 금융 데이터 LoRA', 'Mac Studio 2대', '은행·핀테크', '월 500만~'),
        ('FinVMS-CBDC', 'CBDC + AI 결제', '한국은행 디지털화폐 인프라 SI', '한은 SDK + 자체 운영', 'Mac Studio 5대 클러스터', '은행·결제', '1社 10-30억'),
        ('FinVMS-Regtech', 'Constitutional AI', '금감원 규제 자동 추적·헌법화', 'failure-mode 패턴', 'Mac Studio 1대', '전 금융사', '월 300-700만'),
        ('FinVMS-Bureau', 'UEBA + Multi-Agent', '한국 행동신용평가소', '점수 모델 IP + 라이선스', 'Mac Studio 3대', '보험·HR·IAM', '영구 라이선스'),
    ]),
    # ───── 영역 6: AI CCTV (10) ─────
    ('📹', '6. AI 지능형 CCTV', '영상 분석', [
        ('SmartCCTV-World', 'NVIDIA Cosmos', '물리법칙 학습·미래 예측', 'Cosmos Free Research', 'Mac Studio 2대 + GPU', '기존+신규', '월 100-300만'),
        ('SmartCCTV-VLA', 'OpenVLA', '자율 추론·자연어 알람', 'OpenVLA + Llama 4', 'Mac Studio 1대 + Edge', '공공·금융', '1社 1-3억'),
        ('SmartCCTV-Search', 'Llama 4 Multimodal', '자연어 영상 검색', 'Llama 4 Vision', 'Mac Studio 2대', '대형 시설', '월 100-500만'),
        ('SmartCCTV-Crowd', 'Crowd Analytics', '밀집도·이상 행동·조기 경보', '자체 SDK + Llama 4', 'Mac Studio 1대', '행안부·지자체', 'B2G 5-20억'),
        ('SmartCCTV-Fire', 'Multimodal + 열화상', '화재·연기 조기 탐지', 'Llama 4 + 열화상 카메라', 'Mac Studio 1대 + 열화상', '소방청·산림청', 'B2G 5-15억'),
        ('SmartCCTV-Safety', 'VLA + PPE', '산업현장 안전 모니터링', 'OpenVLA + Edge AI', 'Mac Studio 1대 + Edge', '제조·건설', '1社 3-8억'),
        ('SmartCCTV-Mood', 'Llama 4 + 감정', '매장 고객 만족도·VOC 자동', 'Llama 4 + 감정 LoRA', 'Mac Studio 1대', '유통·매장', '월 100-500만'),
        ('SmartCCTV-Privacy', 'Privacy ML', '얼굴·번호판 자동 마스킹', '자체 마스킹 모델', 'Mac Studio 1대', '공공·기업', '월 50-200만'),
        ('SmartCCTV-Edge', 'Edge AI Chip', 'CCTV 자체 추론·저전력', 'Hailo + Jetson', 'Edge 칩 (대당 100만)', '분산 시설', '대당 100-300만'),
        ('SmartCCTV-Drone', 'Drone Detection', 'CCTV + 안티드론 통합', 'Dedrone + Llama 4', 'Mac Studio 1대 + 드론센서', '국방·국가시설', 'B2G 10-30억'),
    ]),
    # ───── 영역 7: 디지털트윈 (10) ─────
    ('🌐', '7. 디지털 트윈', '제조·건설·인프라', [
        ('DigitalTwin-Cosmos', 'NVIDIA Cosmos', '물리법칙 자동 학습·시나리오 생성', 'Cosmos World Foundation', 'NVIDIA Cluster (1억)', '현대·기아·삼성·SK', '1社 50-100억'),
        ('DigitalTwin-Sim2Real', 'NVIDIA Isaac', '시뮬→실제 transfer·학습비 1/100', 'Isaac Sim', 'NVIDIA Cluster', '로봇·자율시스템 사', '1프로젝트 10-30억'),
        ('DigitalTwin-Humanoid', 'NVIDIA GR00T', '휴머노이드 가상 학습', 'GR00T + 디지털트윈', 'NVIDIA Cluster', '현대·삼성', '1社 20-50억'),
        ('DigitalTwin-City', '도시 디지털트윈', '서울·부산 등 도시 SI', 'Bentley iTwin + LH 협업', 'Mac Studio 5대 + NVIDIA', '지자체·LH', 'B2G 30-100억'),
        ('DigitalTwin-Energy', 'SMR + 디지털트윈', '소형 원전 AI 운영', '두산·SK 협업', 'Mac Studio 5대', '원전·에너지', '50-200억'),
        ('DigitalTwin-Factory', 'Industrial Metaverse', '스마트팩토리 SI', 'Siemens + Omniverse', 'Mac Studio 3대 + NVIDIA', '제조 대기업', '1공장 10-50억'),
        ('DigitalTwin-VR', 'Spatial Computing', 'VR 가상 관제실', 'Vision Pro + Unity', 'Vision Pro 10대 + Mac Studio', '관제·교육', '1社 3-10억'),
        ('DigitalTwin-Train', 'Synthetic Data', '학습데이터 라이선싱', '디지털트윈 → 데이터 마켓', 'Mac Studio 3대', '글로벌 AI 회사', '데이터 라이선스'),
        ('DigitalTwin-Climate', 'Climate AI', '탄소 디지털트윈', 'GraphCast + 자체', 'Mac Studio 2대', '대기업 ESG', '1社 3-10억'),
        ('DigitalTwin-Defense', '국방 시뮬레이션', 'K-방산 무기·전장 시뮬', '한화·LIG 협업', 'NVIDIA Cluster + 보안', '방위사업청', '50-150억'),
    ]),
    # ───── 영역 8: ITO 운영 (10) ─────
    ('⚙️', '8. ITO (IT 아웃소싱)', 'IT 운영 위탁', [
        ('ITO-Agentic', 'Llama 4 + Agentic', '24/7 자율 운영·사람 1명 = 100배', 'Llama 4 + LangGraph + MCP', 'Mac Studio 2대', '기존 ITO 고객', '월 1000-3000만'),
        ('ITO-Workload', 'AI Workload Protection', 'AI 모델·데이터 보호 MSP', 'Palo Alto·Wiz OEM', 'Mac Studio 1대 + 클라우드', 'AI 도입 기업', '월 500-2000만'),
        ('ITO-NHI', 'NHI', 'AI 에이전트·서비스계정 신원', 'Astrix·Oasis OEM', 'Mac Studio 1대', 'AI 도입 기업', '월 200-1000만'),
        ('ITO-eBPF', 'eBPF Cilium', '커널 레벨 관측·보안', 'Cilium·Falco OSS', 'Mac Studio 1대', '대기업 IT', '1社 3-10억'),
        ('ITO-CSMA', 'Cybersecurity Mesh', '분산 보안 표준 SI', 'Fortinet·Cisco OEM', 'Mac Studio 2대', '멀티클라우드', '1社 5-15억'),
        ('ITO-DSPM', 'DSPM', '데이터 위치·민감도 추적', 'Cyera·Sentra OEM', 'Mac Studio 1대', '개인정보 의무', '월 300-1000만'),
        ('ITO-FinOps', 'AI Cloud Cost', '클라우드 비용 자동 최적화', 'CloudHealth + 자체 ML', 'Mac Studio 1대', '클라우드 사용사', '절감액 20%'),
        ('ITO-DR', 'AI DR', '장애 자동 진단·복구', '자체 ML + AIOps', 'Mac Studio 2대', '금융·공공', '1社 5-20억'),
        ('ITO-Compliance', '자동 규제', 'ISMS-P·금감원 자동 준수', '자체 규제 매핑', 'Mac Studio 1대', '금융·공공', '월 200-500만'),
        ('ITO-Green', '탄소 측정', 'DC 탄소 측정·EU CBAM', '자체 측정 SaaS', 'Mac Studio 1대', '대기업 IT', '월 100-300만'),
    ]),
    # ───── 영역 9: ESG·GRC (10) ─────
    ('🌱', '9. ESG·GRC', 'ESG·거버넌스', [
        ('ESG-GRC-Climate', 'Climate AI', '탄소 디지털트윈·CCUS 최적화', 'GraphCast + 자체', 'Mac Studio 2대', '대기업 ESG', '1社 3-10억'),
        ('ESG-GRC-Report', 'Llama 4 + 생성형', '보고서 자동 작성', 'Llama 4 + ESG 템플릿', 'Mac Studio 1대', '상장사', '월 200-500만'),
        ('ESG-GRC-ISO42001', 'ISO 42001', 'AI 라이프사이클 audit', '자체 audit 도구', 'Mac Studio 1대', 'AI 도입 1000+', '1社 1-5억'),
        ('ESG-GRC-Bias', 'Fairlearn', 'AI 편향 자동 감사', 'Fairlearn OSS', 'Mac Studio 1대', '금융·HR·AI', '1社 1-3억'),
        ('ESG-GRC-Explain', 'SHAP·LIME', 'AI 결정 설명 자동', 'SHAP + Captum', 'Mac Studio 1대', '고위험 AI 사용', '1社 2-5억'),
        ('ESG-GRC-Supply', 'LangChain + 공급망', '협력사 ESG 평가', 'Llama 4 + 공급망 DB', 'Mac Studio 2대', '대기업', '월 300-1000만'),
        ('ESG-GRC-Scope3', '탄소 자동 산정', 'Scope 1·2·3 자동·정규 의무', '자체 + IPCC 표준', 'Mac Studio 1대', '상장사', '월 200-500만'),
        ('ESG-GRC-Water', 'IoT + Water AI', '물·자원 최적화', 'IoT 센서 + 자체 ML', 'Mac Studio 1대 + IoT', '제조 대기업', '월 100-300만'),
        ('ESG-GRC-Carbon', 'K-ETS + AI', '탄소권 거래 최적화', '자체 거래 예측 모델', 'Mac Studio 1대', '탄소 배출사', '1社 5-15억'),
        ('ESG-GRC-Risk', 'Cyber Resilience', '회복력 점수화·정기 audit', '자체 표준', 'Mac Studio 1대', '대기업·보험사', '월 500-1500만'),
    ]),
    # ───── 영역 10: 부서 IP (10) ─────
    ('🚨', '10. 부서 IP (신규 한국 표준)', '행동위험 외 신영역 K-Standard', [
        ('AI Risk Lighthouse', '8 카테고리 audit', '한국 K-Standard 후보', '자체 8 카테고리 도구', 'Mac Studio 1대', '5,000 대기업', '영구 5,000억'),
        ('K-Quantum Standard', 'PQC + 양자보안 표준', '한국 양자보안 표준 인증', 'KISA 협력 + 자체', '컨설팅 인력', '금융·국방·공공', '영구 인증료'),
        ('AI 거버넌스 컨설팅', 'ISO 42001 + EU AI Act', '한국 1호 인증 사업자', '인증 + 컨설팅', '컨설팅 인력', 'AI 도입 모든', '1社 3-10억'),
        ('행동신용평가소', 'UEBA + Multi-Agent', 'KCB식 행동신용평가소', '점수 모델·라이선스', 'Mac Studio 3대', '보험·HR·IAM', '영구 라이선스'),
        ('한국형 BloombergGPT', 'Llama 4 + 금융 LoRA', '자체 도메인 LLM', 'Llama 4 + 금융 데이터 LoRA', 'Mac Studio 2대', '금융·회계', '월 500만~'),
        ('Synthetic Data 마켓', '합성데이터 라이선싱', '한국 산업 데이터 마켓', '자체 + Gretel 패턴', 'Mac Studio 3대', '글로벌 AI 회사', '데이터 라이선스'),
        ('Federated Consortium', 'Flower 컨소시엄', '금융 공동 부정탐지', 'Flower OSS', '각 은행 1대씩', '은행연합회', '월구독'),
        ('휴머노이드 보안 인증', '디지털트윈 + 보안', '한국 휴머노이드 보안 표준', '자체 표준', 'Mac Studio 2대', '현대·삼성', '인증 5천만-3억'),
        ('AGI 거버넌스 자문', 'Mech Interp + 안전', '한국 AGI 안전 자문', '자체 연구 + Anthropic 협력', '연구 인력', '대기업·정부', '시간당 자문료'),
        ('K-AI Academy', 'AI 교육·자격증', 'KISA 등록 정식 과정', '교육 콘텐츠 + LMS', 'Mac Studio 1대', '전 한국 기업', '수강료+자격증'),
    ]),
    # ───── 영역 11: 공공·전자정부 (ENTEC 협업) ─────
    ('🏛️', '11. 공공·전자정부 (ENTEC 협업)', '전자정부 1위', [
        ('Gov-LLM', 'Llama 4 + 행정 LoRA', '공공기관 행정 특화 LLM', 'Llama 4 + 행정 데이터 LoRA', 'Mac Studio 2대', '중앙·지방 정부', 'B2G 5-30억'),
        ('Gov-Chatbot', 'Llama 4 + 민원', '24/7 민원 응대 자동화', 'Llama 4 + RAG', 'Mac Studio 1대', '지자체·공공', '1기관 1-3억'),
        ('Gov-Doc', 'Llama 4 + Vision', '공문·법령 OCR·자동 분류', 'Llama 4 Multimodal', 'Mac Studio 1대', '중앙부처', '1기관 2-5억'),
        ('Gov-Voice', 'Llama 4 Voice', '음성 민원 자동 처리', 'Llama 4 + STT/TTS', 'Mac Studio 1대', '120 다산콜·129 보건', 'B2G 3-10억'),
        ('Gov-Predict', 'Llama 4 Scout (1M)', '정책 영향 분석·예측', 'Llama 4 Scout', 'Mac Studio 2대', '정책기획·국회', 'B2G 5-15억'),
        ('Gov-Audit', 'Constitutional AI', '공직 감사 자동화·청렴 검증', '자체 헌법화', 'Mac Studio 1대', '감사원·국정원', 'B2G 3-10억'),
        ('Gov-Disaster', 'Multimodal + Climate', '재난 자동 모니터·대응', 'GraphCast + Llama 4 Vision', 'Mac Studio 2대', '행안부·소방청', 'B2G 10-30억'),
        ('Gov-Welfare', 'Llama 4 + 복지', '복지 사각지대 자동 발굴', 'Llama 4 + 복지 데이터', 'Mac Studio 1대', '보건복지부', 'B2G 5-15억'),
        ('Gov-Tax', 'GraphRAG + 세무', '세무·탈세 자동 탐지', 'Neo4j + Llama 4', 'Mac Studio 2대 + Neo4j', '국세청·관세청', 'B2G 10-30억'),
        ('Gov-Identity', 'Behavioral Biometrics', '공공 디지털 신원', 'BioCatch + FIDO2', 'Mac Studio 1대', '행안부·KISA', 'B2G 5-15억'),
    ]),
    # ───── 영역 12: 클라우드 (CTS·CLOIT 협업) ─────
    ('☁️', '12. 클라우드 네이티브 (CTS·CLOIT 협업)', 'Google Cloud Partner', [
        ('Cloud-AI-Native', 'Llama 4 + K8s', 'AI 네이티브 컨테이너 운영', 'Llama 4 + Kubernetes', 'Mac Studio 3대 + K8s', '대기업 IT', '1社 5-15억'),
        ('Cloud-Migration', 'AI 마이그레이션', '온프레→클라우드 자동', 'Llama 4 + 마이그레이션 도구', 'Mac Studio 1대 + Cloud', '대기업', '1社 5-30억'),
        ('Cloud-Multi', 'Llama 4 + Multi-cloud', 'AWS·Azure·GCP 통합', '자체 추상화', 'Mac Studio 2대', '글로벌 기업', '월 1000만+'),
        ('Cloud-Cost', 'AI FinOps', '비용 자동 최적화', 'CloudHealth + 자체', 'Mac Studio 1대', '클라우드 사용사', '절감액 20%'),
        ('Cloud-Sec', 'CSPM/CIEM', '클라우드 보안 자동', 'Wiz·Lacework OEM', 'Mac Studio 1대', '클라우드 사용사', '월 500-2000만'),
        ('Cloud-DR', 'AI Disaster Recovery', '클라우드 장애 자동 복구', '자체 + AIOps', 'Mac Studio 2대', '금융·공공', '1社 5-20억'),
        ('Cloud-Edge', 'Edge Computing', '엣지·CDN 자동 운영', 'Cloudflare·Fastly + 자체', 'Mac Studio 1대', '글로벌 기업', '월 500만+'),
        ('Cloud-Serverless', 'Llama 4 + Serverless', 'AI 서버리스 자동화', 'Lambda·Cloud Run + Llama', 'Mac Studio 1대', 'SW 회사', '월 200-1000만'),
        ('Cloud-K8s-AI', 'AIOps Kubernetes', 'K8s AI 자율 운영', 'Llama 4 + K8s 운영', 'Mac Studio 2대', '대기업 IT', '월 500-1500만'),
        ('Cloud-SovEU', 'Sovereign Cloud', '국가 데이터 주권 클라우드', '자체 + 정부 협력', 'Mac Studio 5대', '국가·금융', 'B2G 30-100억'),
    ]),
    # ───── 영역 13: 사이버보안 (PNS 협업) ─────
    ('🛡️', '13. 사이버보안 (PNS 협업)', '사이버보안 전문', [
        ('Sec-SOC', 'Llama 4 + Multi-Agent', '24/7 자율 SOC 운영', 'Llama 4 ×3 + SOAR', 'Mac Studio 3대', '금융·대기업', '1社 10-30억'),
        ('Sec-XDR', 'XDR + AI', '통합 탐지·대응', 'CrowdStrike·SentinelOne OEM', 'Mac Studio 1대', '대기업', '월 1000-3000만'),
        ('Sec-ZeroTrust', 'Zero Trust', 'ZTNA 자동 정책', 'Zscaler·Cato OEM', 'Mac Studio 2대', '금융·공공', '1社 5-15억'),
        ('Sec-Adv-ML', 'Adversarial ML Defense', 'AI 모델 공격 방어', 'Robust Intelligence OEM', 'Mac Studio 1대', 'AI 사용 기업', '1社 3-10억'),
        ('Sec-Prompt', 'Prompt Injection Defense', '직원 LLM 보호', 'Lakera·Aim OEM', 'Mac Studio 1대', 'AI 도입 기업', '월 300-1000만'),
        ('Sec-Threat', 'Threat Intelligence', '위협 인텔리전스 AI', 'CrowdStrike + Llama 4', 'Mac Studio 1대', '금융·공공', '월 500-2000만'),
        ('Sec-Hunt', 'Threat Hunting AI', '자율 위협 사냥', 'Llama 4 + SIEM', 'Mac Studio 2대', '대기업', '월 500-1500만'),
        ('Sec-IR', 'Incident Response AI', '침해 자동 분석·대응', 'Llama 4 + SOAR', 'Mac Studio 2대', '금융·공공', '1社 5-15억'),
        ('Sec-Anti-Drone', 'Drone Detection', '드론 탐지·요격', 'Dedrone·DroneShield', 'Mac Studio 1대 + 센서', '국방·공항', 'B2G 10-30억'),
        ('Sec-OT', 'OT/ICS Security', '산업제어망 보안', 'Claroty·Nozomi OEM', 'Mac Studio 1대', '제조·에너지', '1社 5-15억'),
    ]),
    # ───── 영역 14: 데이터·AI 거버넌스 ─────
    ('📊', '14. 데이터·AI 거버넌스', '데이터 관리·AI 라이프사이클', [
        ('Data-Catalog', 'Llama 4 + Catalog', 'AI 자동 데이터 카탈로그', 'Llama 4 + Collibra OEM', 'Mac Studio 1대', '대기업', '월 300-1000만'),
        ('Data-Lineage', 'Graph DB', '데이터 흐름 자동 추적', 'Neo4j + Llama 4', 'Mac Studio 1대 + Neo4j', '금융·공공', '1社 3-10억'),
        ('Data-Quality', 'AI Data Quality', '데이터 품질 자동 점검', 'Great Expectations + Llama 4', 'Mac Studio 1대', 'DW 사용사', '월 200-500만'),
        ('Data-Privacy', 'PET 통합', '개인정보 자동 보호', 'Differential Privacy + Confidential', 'Mac Studio 1대', '개인정보 의무', '1社 2-5억'),
        ('Data-Mesh', 'Data Mesh AI', '분산 데이터 거버넌스', 'Databricks + Llama 4', 'Mac Studio 2대', '대기업', '1社 5-15억'),
        ('Data-Vector', 'Vector DB', '임베딩 검색 인프라', 'ChromaDB·Pinecone', 'Mac Studio 1대', 'AI 도입 기업', '월 200-1000만'),
        ('Data-Anonymize', '익명화 자동', '자동 익명화·가명화', '자체 마스킹 + Privacy ML', 'Mac Studio 1대', '의무 기업', '1社 1-3억'),
        ('Data-Sovereignty', '데이터 주권', '국가 데이터 주권 관리', '자체 + 정부 협력', 'Mac Studio 2대', '공공·금융', 'B2G 5-20억'),
        ('Data-Marketplace', '데이터 마켓플레이스', '한국 산업 데이터 거래', 'Snowflake·Databricks + 자체', 'Mac Studio 3대', '데이터 사용·공급', '거래 수수료'),
        ('Data-Synthetic', 'Synthetic Data', '합성 데이터 자동 생성', 'Gretel + 자체', 'Mac Studio 1대', '개인정보 의무', '1社 1-3억'),
    ]),
    # ───── 영역 15: 의료·헬스케어 ─────
    ('🏥', '15. 의료·헬스케어', 'AI 진료·진단', [
        ('Med-Scribe', 'Llama 4 Voice', 'EHR 자동 작성·녹음 → 진료기록', 'Llama 4 + Whisper', 'Mac Studio 1대', '병원·의원', '월 100-500만'),
        ('Med-Image', 'Llama 4 Vision', '영상 판독 보조', 'Llama 4 Vision + 의료 데이터', 'Mac Studio 2대', '영상의학과', '1社 3-10억'),
        ('Med-Triage', 'Llama 4 + 응급', '응급 환자 분류 AI', 'Llama 4 + ESI 표준', 'Mac Studio 1대', '응급실', '1병원 2-5억'),
        ('Med-Pathology', 'Llama 4 + 병리', '병리 영상 분석', 'Llama 4 Vision + 병리 LoRA', 'Mac Studio 2대', '대학병원', '1社 3-10억'),
        ('Med-Genome', 'Genomic AI', '유전체 분석 AI', 'AlphaFold 3 + 자체', 'Mac Studio 3대 + GPU', '대학·제약', '1프로젝트 5-30억'),
        ('Med-Wearable', 'Wearable Monitor', '24/7 건강 모니터', 'Llama 4 + Apple Watch SDK', 'Mac Studio 1대 + iOS', '환자·보험', '월 1-5만'),
        ('Med-Chatbot', 'Llama 4 + 의학 LoRA', '의학 챗봇 (의사 보조)', 'Llama 4 + 의학 데이터', 'Mac Studio 1대', '병원·의원', '월 200-500만'),
        ('Med-Mental', 'Affective Computing', '정신건강 자동 진단·코칭', 'Llama 4 + 감정 LoRA', 'Mac Studio 1대', '정신건강·보험', '월 100-300만'),
        ('Med-Drug-Inter', 'GraphRAG + 약물', '약물 상호작용 자동', 'Neo4j + 약물 DB', 'Mac Studio 1대 + Neo4j', '병원·약국', '월 200-500만'),
        ('Med-Compliance', 'GRC 의료', '의료기관 규정 준수', 'Constitutional AI + 의료법', 'Mac Studio 1대', '병원·요양원', '월 300-1000만'),
    ]),
    # ───── 영역 16: 교육·이러닝 ─────
    ('📚', '16. 교육·이러닝', 'AI 튜터·학습 분석', [
        ('Edu-Tutor', 'Llama 4 + 교육 LoRA', '개인 맞춤 AI 튜터', 'Llama 4 + 교과 데이터 LoRA', 'Mac Studio 1대', '학원·온라인 교육', '월 200-1000만'),
        ('Edu-Grading', 'Llama 4 + 채점', '주관식 자동 채점', 'Llama 4 + 평가 모델', 'Mac Studio 1대', 'EBS·메가스터디', '1社 1-3억'),
        ('Edu-Analytics', 'Learning Analytics', '학습 분석·예측', 'Llama 4 + LMS 데이터', 'Mac Studio 1대', '대학·기업교육', '1社 1-3억'),
        ('Edu-Voice', 'Llama 4 Voice', '음성 인터랙티브 학습', 'Llama 4 + STT/TTS', 'Mac Studio 1대', '어학·국어', '월 100-500만'),
        ('Edu-Vision', 'Llama 4 Vision', '필기·교재 OCR·자동 채점', 'Llama 4 Multimodal', 'Mac Studio 1대', '학교·학원', '월 50-300만'),
        ('Edu-Knowledge', 'GraphRAG', '지식 그래프 학습', 'Neo4j + Llama 4', 'Mac Studio 1대 + Neo4j', '대학·MOOC', '1社 2-5억'),
        ('Edu-Coding', 'Code Agent', '코딩 학습 AI', 'Llama 4 + 코드 LoRA', 'Mac Studio 1대', '코딩 학원', '월 100-500만'),
        ('Edu-VR', 'Spatial Computing', 'VR 교육 환경', 'Vision Pro + Unity', 'Vision Pro + Mac Studio', '대학·실습교육', '1대 5천만'),
        ('Edu-Adaptive', 'Adaptive Learning', '적응형 학습 경로', 'Llama 4 + 강화학습', 'Mac Studio 1대', 'EBS·메가', '1社 2-5억'),
        ('Edu-Compliance', 'AI 교육 컴플라이언스', 'AI 교육 윤리·인증', 'ISO 42001 자체', '컨설팅 인력', 'AI 교육 기업', '1社 1-3억'),
    ]),
    # ───── 영역 17: 유통·이커머스 ─────
    ('🛒', '17. 유통·이커머스', 'AI 추천·결제·매장', [
        ('Retail-Reco', 'Llama 4 + 추천', '개인 맞춤 추천', 'Llama 4 + 행동 LoRA', 'Mac Studio 2대', '쿠팡·11번가·G마켓', '1社 5-15억'),
        ('Retail-Agent', 'Llama 4 + Agentic', 'AI 쇼핑 에이전트', 'Llama 4 + Browser-Use', 'Mac Studio 2대', '이커머스', '월구독'),
        ('Retail-Voice', 'Llama 4 Voice', '음성 쇼핑', 'Llama 4 + STT/TTS', 'Mac Studio 1대', 'AI 스피커', '월 100-500만'),
        ('Retail-Inventory', 'Demand Forecast', '재고 자동 예측·발주', 'Llama 4 Scout (1M)', 'Mac Studio 2대', '대형마트·도매', '1社 3-10억'),
        ('Retail-Store', 'Vision + IoT', '무인 매장 (Amazon Go 식)', 'Llama 4 Vision + 센서', 'Mac Studio 2대 + 센서', '편의점·매장', '1매장 5천만~'),
        ('Retail-Mood', 'Affective + CCTV', '고객 만족도·VOC', 'Llama 4 + 감정 LoRA + CCTV', 'Mac Studio 1대 + CCTV', '백화점·매장', '월 200-1000만'),
        ('Retail-Pricing', 'Dynamic Pricing', '동적 가격 자동 조정', 'Llama 4 + 가격 ML', 'Mac Studio 2대', '대형 유통', '1社 3-10억'),
        ('Retail-Marketing', 'Generative Marketing', 'AI 마케팅 자동화', 'Llama 4 + Generative', 'Mac Studio 2대', '마케팅·광고', '월 500-2000만'),
        ('Retail-Fraud', 'Multi-Agent FDS', '결제 사기 탐지', 'Llama 4 ×3', 'Mac Studio 3대', '결제·이커머스', '1社 5-15억'),
        ('Retail-Logistics', 'AI Logistics', '배송·물류 최적화', 'Llama 4 + 라우팅 ML', 'Mac Studio 2대', '쿠팡·이마트', '1社 3-10억'),
    ]),
    # ───── 영역 18: 제조 SI ─────
    ('🏭', '18. 제조 SI', '스마트 팩토리', [
        ('Mfg-Predict', 'Predictive Maintenance', '설비 예지보전', 'Llama 4 + 시계열 ML', 'Mac Studio 2대', '제조 대기업', '1공장 5-15억'),
        ('Mfg-Quality', 'Vision + Quality', '품질 검사 자동', 'Llama 4 Vision', 'Mac Studio 1대 + 카메라', '반도체·디스플레이', '1社 3-10억'),
        ('Mfg-Twin', 'Industrial Metaverse', '공장 디지털트윈', 'Siemens + Omniverse', 'Mac Studio 3대 + NVIDIA', '제조 대기업', '1공장 10-50억'),
        ('Mfg-Robot', 'Humanoid + 공장', '휴머노이드 + 공장 통합 SI', 'NVIDIA GR00T + Llama 4', 'NVIDIA Cluster', '현대·삼성·LG', '50-200억'),
        ('Mfg-Safety', 'VLA + PPE', '산업안전 모니터링', 'OpenVLA + CCTV', 'Mac Studio 1대 + Edge', '제조·건설', '1社 3-8억'),
        ('Mfg-OEE', 'OEE Analytics', '설비 효율 (OEE) 자동', 'Llama 4 + IoT', 'Mac Studio 1대 + IoT', '제조사', '1社 2-5억'),
        ('Mfg-Energy', 'Energy AI', '공장 에너지 최적화', 'Llama 4 + Energy ML', 'Mac Studio 1대', '대규모 공장', '1社 2-5억'),
        ('Mfg-Supply', 'Supply Chain AI', '공급망 위험 예측', 'GraphRAG + Llama 4', 'Mac Studio 2대 + Neo4j', '대기업 제조', '월 500-2000만'),
        ('Mfg-Material', 'MatterGen + R&D', '신소재 자동 발견', 'Microsoft MatterGen', 'Mac Studio 2대 + GPU', '소재 R&D', '1프로젝트 5-30억'),
        ('Mfg-Sustain', 'Carbon AI', '탄소 자동 측정·EU CBAM', '자체 측정 + IPCC', 'Mac Studio 1대', 'EU 수출 제조사', '월 300-1000만'),
    ]),
    # ───── 영역 19: 물류·SCM ─────
    ('🚛', '19. 물류·SCM', '공급망·운송 AI', [
        ('Logistics-Route', 'Route Optimization', '최적 배송 경로', 'Llama 4 + Routing ML', 'Mac Studio 1대', '쿠팡·CJ대한통운', '1社 3-10억'),
        ('Logistics-Warehouse', 'Warehouse AI', '창고 자동화', 'Symbotic + Llama 4', 'Mac Studio 2대 + 로봇', '대형 물류', '1社 10-30억'),
        ('Logistics-Forecast', 'Demand Forecast', '수요 예측', 'Llama 4 Scout', 'Mac Studio 2대', '유통·물류', '1社 2-5억'),
        ('Logistics-Tracking', 'IoT + Tracking', '실시간 화물 추적', 'IoT + Llama 4', 'Mac Studio 1대 + IoT', '운송사·고객', '월 500-2000만'),
        ('Logistics-Last', 'Last-mile', '라스트마일 로봇·드론', 'Drone + Llama 4', 'Mac Studio 1대 + 드론', '택배사', '대당 1-5억'),
        ('Logistics-Port', '항만·항공 AI', '항만·항공 자동화', 'Llama 4 + 항만 시스템', 'Mac Studio 2대', '인천공항·부산항', 'B2G 30-100억'),
        ('Logistics-Cold', 'Cold Chain AI', '저온 유통 자동 모니터', 'IoT + Llama 4', 'Mac Studio 1대 + IoT', '식품·의약품', '월 200-1000만'),
        ('Logistics-Customs', '관세·통관 AI', '자동 통관·관세 분류', 'Llama 4 + 관세법 LoRA', 'Mac Studio 1대', '수출입·물류', '월 300-1000만'),
        ('Logistics-Insurance', 'Cargo Insurance AI', '화물 보험 자동 평가', 'Llama 4 + 보험 LoRA', 'Mac Studio 1대', '보험사·물류', '월 200-1000만'),
        ('Logistics-Reverse', 'Reverse Logistics', '반품 자동 처리', 'Llama 4 + 반품 ML', 'Mac Studio 1대', '이커머스', '월 200-1000만'),
    ]),
    # ───── 영역 20: 미디어·콘텐츠 ─────
    ('🎬', '20. 미디어·콘텐츠', '영상·음악·생성형', [
        ('Media-Video', 'Text-to-Video', '광고·교육 영상 자동', 'Sora·Veo·Kling 활용', '클라우드 API', '기업 마케팅', '월 500-2000만'),
        ('Media-Music', 'Suno·Udio', 'AI 작곡·K-팝 라이선스', 'Suno API + 자체', 'Mac Studio 1대', '엔터·광고', '월 200-1000만'),
        ('Media-Voice', 'Voice Cloning', '성우 복제·다국어 더빙', 'ElevenLabs + 자체', 'Mac Studio 1대', '콘텐츠 회사', '월 200-1000만'),
        ('Media-Avatar', 'Digital Human', 'AI 아바타 (가상 진행자)', 'HeyGen·Synthesia OEM', '클라우드', '방송·교육', '월 500-2000만'),
        ('Media-Subtitle', 'Llama 4 + 자막', '자막 자동 + 번역', 'Llama 4 + Whisper', 'Mac Studio 1대', '유튜브·OTT', '월 100-500만'),
        ('Media-Shorts', 'Llama 4 + Shorts', '롱폼 → 쇼츠 자동', 'Llama 4 Vision + Edit', 'Mac Studio 1대', '크리에이터', '월 100-500만'),
        ('Media-Thumb', 'Llama 4 + 썸네일', '썸네일 A/B 자동 생성', 'Llama 4 Vision + Imagen', 'Mac Studio 1대', '유튜버', '월 50-300만'),
        ('Media-Watermark', 'C2PA + Deepfake', 'AI 생성물 표식 + 위조 탐지', 'Reality Defender + C2PA', 'Mac Studio 1대', '미디어·법무', '월 200-1000만'),
        ('Media-Live', 'Real-time Multimodal', '실시간 라이브 분석·자막', 'Llama 4 + Live API', 'Mac Studio 2대', '방송·이벤트', '1社 3-10억'),
        ('Media-VR', '8K/VR 콘텐츠', 'VR 콘텐츠 자동 생성', 'Vision Pro + Unity', 'Mac Studio 3대 + Vision Pro', 'VR 콘텐츠 회사', '1프로젝트 3-15억'),
    ]),
    # ───── 영역 21: 농업 ─────
    ('🌾', '21. 농업·스마트팜', '농업 AI', [
        ('Agri-Pest', 'Vision + 병해충', '병해충 자동 진단', 'Llama 4 Vision', 'Mac Studio 1대', '농가·농협', '월 50-200만'),
        ('Agri-Yield', 'Yield Predict', '수확량 예측', 'Llama 4 + 농업 데이터', 'Mac Studio 1대', '대농·농협', '1社 1-3억'),
        ('Agri-Auto', 'Autonomous Farming', '자율 농기계', 'John Deere + Llama 4', 'Mac Studio 1대 + 농기계', '대농', '대당 1-5억'),
        ('Agri-Greenhouse', 'Smart Greenhouse', '스마트팜 자동 운영', 'IoT + Llama 4', 'Mac Studio 1대 + IoT', '스마트팜 농가', '1社 1-3억'),
        ('Agri-Soil', 'Soil AI', '토양 분석·비료 최적', 'Llama 4 + 토양 데이터', 'Mac Studio 1대 + IoT', '농가·농진청', '1社 1-3억'),
        ('Agri-Water', 'Irrigation AI', '관개 자동 최적화', 'Llama 4 + IoT', 'Mac Studio 1대 + IoT', '농가', '월 50-200만'),
        ('Agri-Drone', 'Drone + Crop', '드론 작물 모니터링', 'Drone + Llama 4 Vision', 'Mac Studio 1대 + 드론', '대농', '대당 1-3억'),
        ('Agri-Weather', 'Climate AI 농업', '날씨 + 작물 영향', 'GraphCast + Llama 4', 'Mac Studio 1대', '농가·농협', '월 100-300만'),
        ('Agri-Vertical', '수직농업 AI', '수직농업 자동 운영', 'IoT + Llama 4', 'Mac Studio 1대 + IoT', '수직농업 회사', '1社 3-10억'),
        ('Agri-Genome', 'Plant Genomics', '식물 유전체 신품종', 'AlphaFold + 농업 LoRA', 'Mac Studio 3대 + GPU', '농진청·종자회사', '1프로젝트 5-30억'),
    ]),
    # ───── 영역 22: 에너지 ─────
    ('⚡', '22. 에너지·SMR', '발전·전력망', [
        ('Energy-SMR', 'SMR + AI', '소형 원전 AI 운영', '두산·SK 협업', 'Mac Studio 5대', '원전·에너지사', '50-200억'),
        ('Energy-Grid', 'Smart Grid AI', '전력망 자동 운영', 'Llama 4 + 전력 ML', 'Mac Studio 3대', '한전·발전사', 'B2G 30-100억'),
        ('Energy-Battery', 'Battery AI', '배터리 운영 최적', 'Llama 4 + 배터리 데이터', 'Mac Studio 2대', '에너지 저장사', '1社 3-15억'),
        ('Energy-Solar', 'Solar AI', '태양광 발전 예측·최적', 'Llama 4 + 기상 + 발전', 'Mac Studio 1대', '태양광 사업자', '월 200-1000만'),
        ('Energy-Wind', 'Wind AI', '풍력 발전 예측·최적', 'Llama 4 + 기상', 'Mac Studio 1대', '풍력 사업자', '월 200-1000만'),
        ('Energy-Cooling', 'DC Cooling AI', '데이터센터 냉각 최적', 'DeepMind cooling + 자체', 'Mac Studio 2대', 'DC 사업자', '1社 5-15억'),
        ('Energy-Trade', 'Energy Trading', 'AI 에너지 거래', 'Llama 4 + 거래 ML', 'Mac Studio 2대', '에너지 거래사', '1社 5-15억'),
        ('Energy-DERMS', 'DERMS AI', '분산 에너지 관리', 'Llama 4 + DER', 'Mac Studio 2대', '분산 발전사', '1社 3-10억'),
        ('Energy-EV', 'EV Charging AI', '전기차 충전 최적', 'Llama 4 + 충전망', 'Mac Studio 1대', 'EV 충전 사업', '월 300-1000만'),
        ('Energy-H2', 'Hydrogen AI', '수소 생산·운영 최적', 'Llama 4 + 수소 ML', 'Mac Studio 1대', '수소 사업자', '1社 3-10억'),
    ]),
    # ───── 영역 23: 자율주행 ─────
    ('🚗', '23. 자율주행·모빌리티', '자율주행 시스템', [
        ('Auto-Safety', 'AI 안전 인증', '자율주행 안전 평가·인증', '자체 + KISA', 'Mac Studio 2대', '현대·기아', '1회 5천만-3억'),
        ('Auto-Sim', 'Simulation', '자율주행 시뮬레이션', 'NVIDIA Cosmos + Isaac', 'NVIDIA Cluster', '현대·기아·SK', '1社 10-30억'),
        ('Auto-V2X', 'V2X Security', '차량-인프라 보안', '자체 + Llama 4', 'Mac Studio 2대', '자동차·통신', '1社 3-10억'),
        ('Auto-Behavior', 'Driver Behavior', '운전자 행동 분석', 'Llama 4 + 행동 LoRA', 'Mac Studio 1대', '보험사·자동차', '월 200-1000만'),
        ('Auto-Predict', 'Pedestrian Predict', '보행자 행동 예측', 'OpenVLA + 자율주행', 'Mac Studio 1대', '자동차사', '1社 3-10억'),
        ('Auto-Robotaxi', 'Robotaxi 운영', 'AI 로보택시 SI', 'Waymo·Tesla + 자체', 'Mac Studio 3대 + 클라우드', '카카오·SK', 'B2C SI'),
        ('Auto-Logistics', '자율 화물', '자율 화물 트럭', 'Embotech·Embark', 'Mac Studio 2대', '물류·운송', '대당 5-15억'),
        ('Auto-Drone', 'UAM 관제', '도시항공교통 관제', 'Llama 4 + 항공', 'Mac Studio 3대', '한국공항공사·KAI', 'B2G 30-100억'),
        ('Auto-MaaS', 'Mobility-as-a-Service', '통합 모빌리티 플랫폼', 'Llama 4 + 모빌리티', 'Mac Studio 2대', '카카오·티맵', '월 1000만+'),
        ('Auto-Insurance', '자율주행 보험', 'UBI·자율주행 보험 AI', 'Llama 4 + 보험 LoRA', 'Mac Studio 1대', '손해보험사', '1社 3-10억'),
    ]),
    # ───── 영역 24: 우주·항공 ─────
    ('🚀', '24. 우주·항공', '위성·우주선·발사', [
        ('Space-Satellite', '위성 자율 운영', 'Llama 4 + 위성 운영', 'Llama 4 + 위성 SDK', 'Mac Studio 3대', 'KARI·한화·LIG', 'B2G 50-200억'),
        ('Space-Comms', 'Starlink + AI', '위성 통신 자율', 'Starlink SDK + Llama 4', 'Mac Studio 2대', '글로벌·국방', 'B2G 30-100억'),
        ('Space-Earth', 'Earth Observation', '위성 영상 분석', 'Llama 4 Vision + 위성', 'Mac Studio 2대', '환경부·국토부', 'B2G 5-30억'),
        ('Space-Launch', 'Launch AI', '발사 운영 자율', 'SpaceX 식 + Llama 4', 'Mac Studio 3대', 'KARI·누리호', 'B2G 30-100억'),
        ('Space-Defense', '국방 우주', '국방 우주 AI', '자체 + 한화 협업', 'Mac Studio 3대 + 보안', '국방부·합참', 'B2G 50-200억'),
        ('Space-Mining', '우주 채굴 시뮬', '소행성·달 채굴 시뮬', 'NVIDIA Cosmos', 'NVIDIA Cluster', '연구·미래', '미래 R&D'),
        ('Space-HAPS', 'HAPS 통신', '성층권 통신 + AI', '자체 + 한국 군', 'Mac Studio 2대', '국방·통신', 'B2G 30-100억'),
        ('Space-NaaS', 'Network-as-a-Service', '위성 군집 AI', 'Llama 4 + 군집 운영', 'Mac Studio 3대', '글로벌 IoT', 'B2C SI'),
        ('Space-Tourism', '우주 관광 AI', 'AR/VR 우주 관광', 'Vision Pro + Unity', 'Mac Studio 2대 + Vision Pro', '관광·교육', '1프로젝트 5-15억'),
        ('Space-Insurance', '우주 보험', '위성·발사 보험', 'Llama 4 + 보험 LoRA', 'Mac Studio 1대', '보험사', '월 200-1000만'),
    ]),
    # ───── 영역 25: 신소재·반도체 ─────
    ('🧪', '25. 신소재·반도체', 'AI 신소재 발견', [
        ('Mat-MatterGen', 'MatterGen', '신소재 자동 발견', 'Microsoft MatterGen', 'Mac Studio 2대 + GPU', '소재 R&D', '1프로젝트 5-30억'),
        ('Mat-Battery', 'Battery Material', '배터리 신소재', 'MatterGen + 배터리 LoRA', 'Mac Studio 3대 + GPU', 'LG·삼성SDI·SK', '1프로젝트 10-50억'),
        ('Mat-Semi', '반도체 신소재', '반도체 신소재·EUV', 'MatterGen + 반도체', 'Mac Studio 3대 + GPU', '삼성·SK하이닉스', '1프로젝트 10-50억'),
        ('Mat-Solar', '태양광 신소재', '태양광 효율 신소재', 'MatterGen + 태양광', 'Mac Studio 2대', '태양광 회사', '1프로젝트 5-20억'),
        ('Mat-Polymer', '고분자 신소재', '플라스틱·고무 신소재', 'MatterGen + 고분자', 'Mac Studio 2대', '석유화학·제약', '1프로젝트 5-20억'),
        ('Mat-Quantum', '양자 신소재', '양자 컴퓨팅 신소재', '양자 + MatterGen', 'IBM Quantum + Mac', '연구·미래', '미래 R&D'),
        ('Mat-Catalyst', '촉매 AI', '산업 촉매 신소재', 'MatterGen + 촉매', 'Mac Studio 2대', '석유화학', '1프로젝트 3-10억'),
        ('Mat-Bio', '바이오 소재', '의료 임플란트 소재', 'MatterGen + 의료', 'Mac Studio 2대', '의료기기', '1프로젝트 3-10억'),
        ('Mat-Build', '건설 소재', '시멘트·강재 신소재', 'MatterGen + 건설', 'Mac Studio 2대', '건설사·소재사', '1프로젝트 3-10억'),
        ('Mat-Aero', '항공우주 소재', '경량·내열 신소재', 'MatterGen + 항공우주', 'Mac Studio 2대', 'KAI·한화', '1프로젝트 5-20억'),
    ]),
    # ───── 영역 26: 바이오·신약 ─────
    ('🧬', '26. 바이오·신약', 'AI 신약 개발', [
        ('Bio-AlphaFold', 'AlphaFold 3', '단백질 구조 예측', 'AlphaFold 3 API', 'Mac Studio 3대 + GPU', '제약·바이오', '1프로젝트 5-30억'),
        ('Bio-Drug-Design', 'Generative Drug', 'AI 신약 설계', 'Inceptive + Cradle', 'Mac Studio 3대 + GPU', '한미·셀트리온', '1프로젝트 10-50억'),
        ('Bio-Repurpose', '약물 재창출', '기존 약물 새 용도', 'Recursion + 자체', 'Mac Studio 2대', '제약사', '1프로젝트 3-15억'),
        ('Bio-Clinical', 'Clinical Trial', '임상시험 AI 최적', 'Llama 4 + 임상 LoRA', 'Mac Studio 2대', '제약·CRO', '1社 3-10억'),
        ('Bio-Genome', 'Genomic Privacy', '유전체 보호 분석', 'PET + 유전체', 'Mac Studio 2대', '유전체 회사', '1社 3-10억'),
        ('Bio-Diagnostics', 'AI Diagnostics', '진단 키트 + AI', 'Llama 4 + 진단', 'Mac Studio 1대', '진단·바이오', '1프로젝트 3-10억'),
        ('Bio-Vaccine', 'Vaccine Design', '백신 설계 AI', 'AlphaFold + 면역', 'Mac Studio 3대', '백신 회사', '1프로젝트 5-20억'),
        ('Bio-Animal', 'Veterinary AI', '동물 의약·진단', 'Llama 4 + 수의', 'Mac Studio 1대', '동물병원·축산', '월 100-500만'),
        ('Bio-Microbiome', 'Microbiome AI', '장내 미생물 분석', 'Llama 4 + 미생물', 'Mac Studio 1대', '바이오·식품', '1프로젝트 3-10억'),
        ('Bio-Synth', '합성생물학 AI', 'DNA 합성·디자인', 'Ginkgo + Llama 4', 'Mac Studio 3대', '합성생물 회사', '1프로젝트 5-20억'),
    ]),
    # ───── 영역 27: K-방산 ─────
    ('🛡️', '27. K-방산', '국방·무기 시스템', [
        ('Def-AntiDrone', 'Anti-Drone AI', '드론 탐지·요격', 'Dedrone + Llama 4', 'Mac Studio 2대 + 센서', '국방·공항·발전소', 'B2G 30-100억'),
        ('Def-Swarm', 'Drone Swarm', '드론 군집·자율 협업', 'Llama 4 + Swarm', 'Mac Studio 3대 + 드론', '국방부', 'B2G 50-200억'),
        ('Def-Sim', '전장 시뮬레이션', '전쟁 게임·작전 시뮬', 'NVIDIA Cosmos', 'NVIDIA Cluster + 보안', '합참·국방부', 'B2G 50-150억'),
        ('Def-CBR', 'CBRN AI', '화학·생물·방사능 탐지', 'Llama 4 + 센서', 'Mac Studio 2대 + 센서', '군·소방', 'B2G 30-80억'),
        ('Def-Cyber', '사이버 방어', '국방 사이버 자율 방어', 'Llama 4 + SOC', 'Mac Studio 3대 + 보안', '국방부·국정원', 'B2G 50-150억'),
        ('Def-Intel', '정보 인텔리전스', 'OSINT·HUMINT AI', 'Llama 4 + 정보', 'Mac Studio 3대 + 보안', '국정원·국방정보', 'B2G 30-100억'),
        ('Def-Unmanned', '무인 시스템', '무인 함정·UAV', 'Llama 4 + 무인기', 'Mac Studio 3대 + 보안', '한화·LIG·KAI', 'B2G 100-500억'),
        ('Def-Quantum', '양자 통신·암호', '국방 양자 통신', 'IBM Quantum + 자체', 'Mac Studio + 양자', '국정원·국방부', 'B2G 30-100억'),
        ('Def-PQC', 'PQC 마이그레이션', '국방 양자내성암호', 'NIST PQC + 자체', '컨설팅 인력', '국방부·국정원', 'B2G 30-100억'),
        ('Def-Export', 'K-방산 수출 AI', '수출 위험 평가·관리', 'Llama 4 + 수출', 'Mac Studio 2대', 'K-방산 빅3', '1社 3-10억'),
    ]),
    # ───── 영역 28: 양자컴퓨팅 ─────
    ('⚛️', '28. 양자컴퓨팅 응용', 'IBM Quantum 기반', [
        ('Q-Finance', '금융 양자 최적화', '거래 양자 최적·신용평가', 'IBM Quantum + 금융', 'IBM Quantum Cloud', '금융사', '1社 5-15억'),
        ('Q-Supply', '공급망 양자', '공급망 NP-hard 최적', 'IBM Quantum + 물류', 'IBM Quantum Cloud', '제조·물류', '1프로젝트 3-10억'),
        ('Q-Material', '신소재 양자 시뮬', '신소재 양자 화학', 'IBM Quantum + 화학', 'IBM Quantum Cloud', '소재 R&D', '1프로젝트 5-20억'),
        ('Q-Drug', '신약 양자', '신약 양자 도킹', 'IBM Quantum + 신약', 'IBM Quantum Cloud', '제약 R&D', '1프로젝트 5-20억'),
        ('Q-Crypto', '양자 암호', '양자 키 분배 (QKD)', 'IBM + KT·SKT 협업', 'Mac Studio + 양자', '금융·국방', 'B2G 30-100억'),
        ('Q-PQC', 'PQC 인벤토리', '양자내성암호 전환', 'NIST PQC + 자체', '컨설팅', '전 대기업', '1社 1-5억'),
        ('Q-Sensing', '양자 센싱', '자기장·중력 양자 센서', '연구 + 한국 군·국정원', '연구 인력', '국방·과학', 'B2G 30-100억'),
        ('Q-Sim', '양자 시뮬', '복잡계 양자 시뮬', 'IBM Quantum', 'IBM Quantum Cloud', '연구·기업 R&D', '1프로젝트 5-20억'),
        ('Q-ML', 'Quantum ML', '양자 ML 알고리즘', 'IBM Qiskit ML', 'IBM Quantum Cloud', 'AI·금융', '1프로젝트 3-10억'),
        ('Q-Edu', '양자 교육·인력', '양자 인력 양성', 'IBM Q Network 교육', '교육 인프라', '대학·기업', '교육 패키지'),
    ]),
    # ───── 영역 29: 휴머노이드·로봇 ─────
    ('🤖', '29. 휴머노이드·로봇', '로봇 + AI', [
        ('Robot-Patrol', '보안 순찰 로봇', '시설 자율 순찰', 'Boston Dynamics + Llama 4', 'Mac Studio + 로봇', '데이터센터·발전소', '대당 1-5억'),
        ('Robot-Factory', '공장 휴머노이드', '공장 작업 로봇', 'NVIDIA GR00T + 자체', 'NVIDIA + 로봇', '현대·삼성', '대당 3-10억'),
        ('Robot-Logistics', '물류 로봇', '창고·물류 로봇', 'Symbotic + Llama 4', 'Mac Studio + 로봇', '쿠팡·CJ', '대당 1-5억'),
        ('Robot-Care', '의료·돌봄 로봇', '환자·노인 돌봄', 'Llama 4 + 의료 LoRA + 로봇', 'Mac Studio + 로봇', '병원·요양원', '대당 3-10억'),
        ('Robot-Home', '가정 휴머노이드', '가정 보조 로봇', '1X·Figure + 자체', 'Mac Studio + 로봇', '고소득 가정', '대당 5천만~'),
        ('Robot-Construction', '건설 로봇', '건설현장 자율 검사', 'Spot + 자체', 'Mac Studio + Spot', '건설사', '대당 1-3억'),
        ('Robot-Police', '경찰 로봇', '경찰 순찰·치안', 'Spot + 한국 경찰 협업', 'Mac Studio + 로봇', '경찰청', 'B2G 5-30억'),
        ('Robot-Defense', '국방 로봇', '국방 무인 시스템', 'NVIDIA GR00T + 한화', 'NVIDIA + 보안', '국방부', 'B2G 30-100억'),
        ('Robot-Safety', '휴머노이드 보안 인증', '휴머노이드 보안·인증', '자체 표준', '컨설팅', '도입 기업', '인증료 5천만-3억'),
        ('Robot-Train', '로봇 학습 데이터', '로봇 학습 데이터 마켓', '디지털트윈 + Sim2Real', 'NVIDIA Cluster', '로봇 회사', '데이터 라이선스'),
    ]),
    # ───── 영역 30: 합성데이터·마켓 ─────
    ('🌟', '30. 합성데이터·신영역', '미래 사업', [
        ('Synth-Korea', '한국 합성 데이터', '한국 산업 데이터 마켓', '자체 + Gretel 패턴', 'Mac Studio 3대', '글로벌 AI 회사', '데이터 라이선스'),
        ('AGI-Adv', 'AGI 거버넌스', 'AGI 안전·자문', 'Anthropic 협력', '연구 인력', '대기업·정부', '시간당 자문료'),
        ('K-Edu', 'K-AI 교육·자격', 'KISA 등록 정식 과정', '교육 + 자격증', '교육 인프라', '전 한국 기업', '수강료+자격증'),
        ('Federated-Bank', '은행 컨소시엄', 'Flower 금융 컨소시엄', 'Flower OSS', '각 은행 1대', '은행연합회', '월구독'),
        ('NHI-Korea', 'AI 신원 관리 표준', 'AI 에이전트 신원 표준', '자체 + Astrix', 'Mac Studio 2대', 'AI 도입 기업', '월구독'),
        ('Sov-Cloud', 'Sovereign Cloud', '국가 데이터 주권', '자체 + 정부 협업', 'Mac Studio 5대', '국가·금융', 'B2G 30-100억'),
        ('OSS-Korea', '한국형 오픈소스 AI', 'Llama 4 한국 패키지', 'Llama 4 + 한국 LoRA', 'Mac Studio 2대', '한국 AI 사용사', '월구독'),
        ('Climate-K', '한국 기후 적응', '한국 기후 AI', 'GraphCast + 한국 기상', 'Mac Studio 2대', '농업·보험·건설', '월구독'),
        ('Brain-K', 'K-BCI 인증', '한국 BCI 보안 표준', '자체 표준', '컨설팅', '의료·연구', '인증료'),
        ('AI-Liability', 'AI 책임보험', 'AI 사고 책임 평가', 'Llama 4 + 보험', 'Mac Studio 1대', '보험사', '월구독'),
    ]),
]


# ───── HTML 생성 ─────
def card_html(num, name, tech, what, how, infra, target, rev, color_idx):
    return f"""
    <div class="card">
      <div class="card-head"><div class="card-num">{num}</div><div class="card-name">{name}</div></div>
      <div class="card-tech">🦙 {tech}</div>
      <div class="card-what">📋 {what}</div>
      <div class="card-how"><strong>🔧 어떻게:</strong> {how}</div>
      <div class="card-infra"><strong>💻 인프라:</strong> {infra}</div>
      <div class="card-meta"><span class="lbl">대상:</span><span>{target}</span><span class="rev">{rev}</span></div>
    </div>"""


COLORS = ['1976D2','7B1FA2','E64A19','388E3C','0288D1','9C27B0','455A64','9E9D24','558B2F','FFA000',
          '00838F','5D4037','827717','6A1B9A','C2185B','283593','00695C','EF6C00','BF360C','37474F',
          '1A237E','004D40','3E2723','311B92','880E4F','01579B','BF360C','0D47A1','4A148C','E65100']

cards_html_parts = []
prod_num = 0
for area_idx, (emoji, name, sub, items) in enumerate(AREAS):
    color = COLORS[area_idx % len(COLORS)]
    cards_html_parts.append(f"""
<div class="area" id="area{area_idx+1}" style="border-left-color:#{color}">
  <div class="area-head" style="background:linear-gradient(90deg,#{color},#{color}AA)">
    <div class="area-emoji">{emoji}</div>
    <div class="area-info"><div class="area-name">{name}</div><div class="area-old">{sub}</div></div>
  </div>
  <div class="grid">""")
    for item in items:
        prod_num += 1
        prod_name, tech, what, how, infra, target, rev = item
        cards_html_parts.append(card_html(prod_num, prod_name, tech, what, how, infra, target, rev, area_idx))
    cards_html_parts.append("  </div>\n</div>")

# 목차 생성
nav_html = '\n'.join([f'  <a href="#area{i+1}" style="display:block;color:#0D47A1;padding:2px 6px;font-size:10.5px">{a[0]} {a[1]}</a>' for i, a in enumerate(AREAS)])

HTML = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>ITCEN CORE × Llama 4 — 300 신상품 카탈로그</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'맑은 고딕','Malgun Gothic',-apple-system,sans-serif;background:#F5F5F0;padding:24px;line-height:1.6;font-size:13px}}
  .hero{{background:linear-gradient(135deg,#0D2A4D,#1565C0);color:#fff;padding:28px 36px;border-radius:14px;margin-bottom:24px;box-shadow:0 6px 18px rgba(13,42,77,.2)}}
  .hero h1{{font-size:28px;margin-bottom:6px}}
  .hero h2{{font-size:15px;opacity:.92;margin-bottom:12px}}
  .hero .msg{{background:rgba(255,255,255,.15);padding:12px 16px;border-radius:8px;font-size:13.5px;line-height:1.7}}
  .hero .msg strong{{color:#FFC107}}

  .nav{{position:fixed;top:20px;right:20px;background:#fff;border-radius:10px;padding:12px;box-shadow:0 3px 10px rgba(0,0,0,.15);font-size:11px;max-height:85vh;overflow-y:auto;border:1px solid #DDD;z-index:100;width:220px}}
  .nav strong{{display:block;margin-bottom:6px;color:#0D47A1}}
  .nav a:hover{{background:#E3F2FD}}

  .area{{background:#fff;border-radius:12px;padding:22px 26px;margin-bottom:22px;box-shadow:0 3px 10px rgba(0,0,0,.06);border-left:8px solid #0D47A1}}
  .area-head{{padding:14px 20px;border-radius:10px;margin:-22px -26px 16px;color:#fff;display:flex;align-items:center;gap:14px}}
  .area-emoji{{font-size:36px;flex-shrink:0;background:#fff;width:60px;height:60px;border-radius:12px;display:flex;align-items:center;justify-content:center}}
  .area-name{{font-size:20px;font-weight:700}}
  .area-old{{font-size:12px;opacity:.95;margin-top:2px}}

  .grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}
  .card{{background:#FAFBFC;border:1px solid #E0E0E0;border-left:4px solid #0D47A1;border-radius:8px;padding:12px 14px}}
  .card-head{{display:flex;align-items:center;gap:8px;margin-bottom:6px}}
  .card-num{{background:#0D47A1;color:#fff;width:28px;height:28px;border-radius:50%;text-align:center;line-height:28px;font-weight:700;font-size:12px;flex-shrink:0}}
  .card-name{{font-weight:700;color:#0D47A1;font-size:13.5px}}
  .card-tech{{font-size:11px;color:#7B1FA2;margin-bottom:4px;font-weight:600}}
  .card-what{{font-size:11.5px;color:#444;line-height:1.65;margin-bottom:5px}}
  .card-how{{background:#FFF8E1;border-left:3px solid #FFA000;padding:5px 9px;border-radius:4px;font-size:10.5px;color:#5D4037;line-height:1.55;margin-bottom:5px}}
  .card-how strong{{color:#E65100}}
  .card-infra{{background:#E3F2FD;border-left:3px solid #1976D2;padding:5px 9px;border-radius:4px;font-size:10.5px;color:#0D47A1;margin-bottom:5px}}
  .card-infra strong{{color:#0D47A1}}
  .card-meta{{font-size:10.5px;color:#666;display:flex;gap:8px;flex-wrap:wrap;margin-top:5px;padding-top:5px;border-top:1px dashed #E0E0E0}}
  .card-meta .lbl{{font-weight:700;color:#1565C0}}
  .card-meta .rev{{background:#E8F5E9;color:#1B5E20;padding:1px 8px;border-radius:6px;font-weight:700}}

  .footer{{text-align:center;margin-top:30px;padding:20px;color:#888;font-size:11.5px;border-top:1px solid #DDD;line-height:1.8}}
</style>
</head>
<body>

<div class="nav">
  <strong>📋 300 신상품 목차 (30 영역)</strong>
{nav_html}
</div>

<div class="hero">
  <h1>🎯 ITCEN CORE × Llama 4 — 300 신상품 카탈로그</h1>
  <h2>30 영역 × 각 10 신상품 = 300 사업 아이디어 · 모든 LLM 부분 Llama 4 자체 운영</h2>
  <div class="msg">
    <strong>📌 형식:</strong> 각 신상품 = 신기술 + 무엇 + <strong>어떻게</strong> + <strong>인프라</strong> + 대상 + 매출<br>
    <strong style="color:#FFC107">⭐ LLM 모두 Llama 4 (오픈소스·자체 운영)</strong> — API 비용 0·데이터 유출 X·한국 도메인 LoRA 자유<br>
    <strong style="color:#FFC107">💻 자체 인프라:</strong> Mac Studio M3 Ultra 512GB Unified Memory (약 1,500만원/대) — Llama 4 70B 양자화 운영. 작은 PoC=1대, 중간=2-3대, 대규모=5대+ NVIDIA Cluster 보조<br>
    행동위험분석 외 ITCEN CORE 사업 영역 + 신영역 30개 모두 cover. 총 300 신상품.
  </div>
</div>

{''.join(cards_html_parts)}

<div class="footer">
  ITCEN CORE × Llama 4 — 300 신상품 (30 영역 × 10) · 자체 운영 인프라 명시<br>
  작성: 2026-06-02 · 행동위험분석 외 ITCEN 자사 솔루션 + 신영역 확장<br>
  모든 신상품: Llama 4 자체 운영 (API 비용 0) + Mac Studio 인프라 (1,500만원/대) 명시
</div>

</body>
</html>"""

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(HTML)
print(f'Wrote: {OUT}')
print(f'Total products: {prod_num}')
print(f'Total areas: {len(AREAS)}')
