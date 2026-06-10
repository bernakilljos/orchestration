# doc_auto task — C:\\pjt\\orchestration_v1\\.claude\\scripts\\build-100-areas-v3.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/build-100-areas-v3.py b/.claude/scripts/build-100-areas-v3.py
new file mode 100644
index 0000000..2c717f5
--- /dev/null
+++ b/.claude/scripts/build-100-areas-v3.py
@@ -0,0 +1,322 @@
+"""100 영역 v3 — 솔루션 회사 관점
+
+사용자 피드백: '우리회사 솔루션 회사야' (컨설팅·SI X)
+변경:
+- 자사 패키지명 (Micro***-AI 형식) 통일
+- 라이선스 모델 (월구독·영구·OEM·종량제) 강조
+- SI·컨설팅 형식 제거
+- CORE/HIGH 재평가 (자사 패키지화 가능 여부 기준)
+"""
+import os
+
+ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
+OUT = os.path.join(ROOT, 'outputs', 'itcen', 'html', 'itcen-core-100영역-3000신상품.html')
+
+# 100 영역 + 관련도 + 자사 패키지 prefix
+# (이모지, 이름, 패키지 prefix, 관련도)
+AREAS = [
+    # ── 자사 (10) ──
+    ('📒', '내부회계', 'MicroICM', 'CORE'),
+    ('⚖️', 'CCP 준법경영', 'MicroCCP', 'CORE'),
+    ('🏗️', '건설 ERP', 'MicroBuild', 'LOW'),
+    ('🎰', '카지노 VMS', 'MicroCasino', 'CORE'),
+    ('🏦', '금융 VMS', 'MicroFin', 'CORE'),
+    ('📹', 'AI CCTV', 'MicroCCTV', 'HIGH'),
+    ('🌐', '디지털트윈', 'MicroTwin', 'MED'),
+    ('⚙️', 'ITO 운영', 'MicroITO', 'MED'),
+    ('🌱', 'ESG·GRC', 'MicroESG', 'HIGH'),
+    ('🚨', '부서 IP', 'MicroRisk', 'CORE'),
+    # ── 그룹·신영역 (10) ──
+    ('🏛️', '공공·전자정부', 'MicroGov', 'LOW'),  # 솔루션화 가능하나 B2G 색채
+    ('☁️', '클라우드', 'MicroCloud', 'MED'),
+    ('🛡️', '사이버보안', 'MicroSec', 'CORE'),
+    ('📊', '데이터 거버넌스', 'MicroData', 'CORE'),
+    ('🏥', '의료 종합', 'MicroMed', 'LOW'),
+    ('📚', '교육·이러닝', 'MicroEdu', 'LOW'),
+    ('🛒', '유통·이커머스', 'MicroRetail', 'LOW'),
+    ('🏭', '제조 SI', 'MicroMfg', 'LOW'),
+    ('🚛', '물류·SCM', 'MicroLogi', 'LOW'),
+    ('🎬', '미디어·콘텐츠', 'MicroMedia', 'LOW'),
+    # ── 산업 (10) — 대부분 LOW (솔루션 회사 관점 X) ──
+    ('🌾', '농업·스마트팜', 'MicroAgri', 'LOW'),
+    ('⚡', '에너지·SMR', 'MicroEnergy', 'LOW'),
+    ('🚗', '자율주행', 'MicroAuto', 'LOW'),
+    ('🚀', '우주·항공', 'MicroSpace', 'LOW'),
+    ('🧪', '신소재', 'MicroMat', 'LOW'),
+    ('🧬', '바이오·신약', 'MicroBio', 'LOW'),
+    ('🛡️', 'K-방산', 'MicroDef', 'LOW'),
+    ('⚛️', '양자컴퓨팅', 'MicroQuantum', 'MED'),
+    ('🤖', '휴머노이드', 'MicroRobot', 'LOW'),
+    ('🌟', '합성데이터', 'MicroSynth', 'HIGH'),
+    # ── 의료 세분 (10) — LOW (솔루션 회사·부서 무관) ──
+    ('🩺', '진료·EHR', 'MicroEHR', 'LOW'),
+    ('🔬', '진단·영상', 'MicroDiag', 'LOW'),
+    ('💉', '예방·검진', 'MicroPrev', 'LOW'),
+    ('🧪', '임상시험', 'MicroTrial', 'LOW'),
+    ('🦾', '재활·정형', 'MicroRehab', 'LOW'),
+    ('🧠', '정신건강', 'MicroMental', 'LOW'),
+    ('💊', '약학·복약', 'MicroPharm', 'LOW'),
+    ('👩‍⚕️', '간호', 'MicroNurse', 'LOW'),
+    ('🏨', '요양·노인', 'MicroCare', 'LOW'),
+    ('🦷', '치의학', 'MicroDent', 'LOW'),
+    # ── 금융 세분 (10) — CORE/HIGH (자사 솔루션화 가능) ──
+    ('💳', '카드·결제', 'MicroCard', 'HIGH'),
+    ('🏛️', '은행 코어', 'MicroBank', 'HIGH'),
+    ('📈', '증권·트레이딩', 'MicroSec-T', 'MED'),
+    ('🏠', '보험', 'MicroIns', 'HIGH'),
+    ('💰', '자산운용', 'MicroAM', 'MED'),
+    ('₿', '암호·핀테크', 'MicroFinTech', 'MED'),
+    ('💵', 'CBDC', 'MicroCBDC', 'MED'),
+    ('📊', '신용평가', 'MicroCredit', 'CORE'),
+    ('🏘️', '부동산·리츠', 'MicroREIT', 'LOW'),
+    ('💎', 'WM·HNWI', 'MicroWM', 'MED'),
+    # ── 사이버보안 세분 (10) — 거의 다 CORE ──
+    ('🔐', '인증·IAM', 'MicroIAM', 'CORE'),
+    ('🛂', '접근통제', 'MicroAccess', 'CORE'),
+    ('🔑', '암호·PQC', 'MicroPQC', 'CORE'),
+    ('👁️', 'SOC·관제', 'MicroSOC', 'CORE'),
+    ('🚨', '사고대응', 'MicroIR', 'CORE'),
+    ('🔍', '포렌식', 'MicroForensic', 'HIGH'),
+    ('📋', '보안 감사', 'MicroAudit', 'CORE'),
+    ('🎓', '보안 교육', 'MicroSecEdu', 'MED'),
+    ('📜', '보안 정책', 'MicroPolicy', 'CORE'),
+    ('🏅', '보안 인증', 'MicroISMS', 'CORE'),
+    # ── 데이터·AI 세분 (10) — 대부분 CORE/HIGH ──
+    ('📦', '데이터 카탈로그', 'MicroCatalog', 'HIGH'),
+    ('🌊', '데이터 파이프', 'MicroPipe', 'MED'),
+    ('🔗', '데이터 라인age', 'MicroLineage', 'HIGH'),
+    ('✨', '데이터 품질', 'MicroDQ', 'HIGH'),
+    ('🛡️', '데이터 프라이버시', 'MicroPET', 'CORE'),
+    ('🗄️', 'Data Mesh', 'MicroMesh', 'MED'),
+    ('🧠', 'MLOps', 'MicroMLOps', 'HIGH'),
+    ('🔄', '모델 라이프', 'MicroModel', 'HIGH'),
+    ('🎯', 'AI Governance', 'MicroGov-AI', 'CORE'),
+    ('⚖️', 'AI 윤리', 'MicroBias', 'CORE'),
+    # ── LLM 응용 세분 (10) — 자사 솔루션화 ──
+    ('💬', 'LLM Chatbot', 'MicroChat', 'HIGH'),
+    ('🤖', 'LLM Agent', 'MicroAgent', 'CORE'),
+    ('🧠', 'Reasoning LLM', 'MicroReason', 'CORE'),
+    ('💻', 'Code Agent', 'MicroCode', 'MED'),
+    ('📖', '문서 LLM', 'MicroKB', 'HIGH'),
+    ('🎙️', '음성 LLM', 'MicroVoice', 'MED'),
+    ('🖼️', 'Vision LLM', 'MicroVision', 'HIGH'),
+    ('🎬', 'Video LLM', 'MicroVideo', 'HIGH'),
+    ('🌍', '다국어 LLM', 'MicroTrans', 'LOW'),
+    ('🎯', 'Domain LLM', 'MicroDomain', 'CORE'),
+    # ── 신영역 (10) — 대부분 LOW ──
+    ('🌡️', '기후·날씨', 'MicroClimate', 'LOW'),
+    ('🧬', '합성생물', 'MicroSynBio', 'LOW'),
+    ('🦠', '미생물', 'MicroMicrobe', 'LOW'),
+    ('🐟', '수산·해양', 'MicroOcean', 'LOW'),
+    ('🌳', '임업·산림', 'MicroForest', 'LOW'),
+    ('♻️', '재활용·환경', 'MicroCircular', 'LOW'),
+    ('🚰', '수자원', 'MicroWater', 'LOW'),
+    ('⚱️', '폐기물', 'MicroWaste', 'LOW'),
+    ('🌋', '재난·재해', 'MicroDisaster', 'LOW'),
+    ('🏛️', '문화재·문화', 'MicroHeritage', 'LOW'),
+    # ── 라이프 (10) — 모두 LOW ──
+    ('🍽️', '식품·외식', 'MicroFB', 'LOW'),
+    ('💄', '패션·뷰티', 'MicroFashion', 'LOW'),
+    ('🎮', '게임·메타버스', 'MicroGame', 'LOW'),
+    ('🎭', '엔터테인먼트', 'MicroEnt', 'LOW'),
+    ('✈️', '관광·여행', 'MicroTravel', 'LOW'),
+    ('⚽', '스포츠 AI', 'MicroSports', 'LOW'),
+    ('📡', '통신·5G', 'MicroTelco', 'LOW'),
+    ('🚙', '자동차 일반', 'MicroAuto2', 'LOW'),
+    ('🧪', '화학·석유', 'MicroChem', 'LOW'),
+    ('🏘️', '부동산 일반', 'MicroProp', 'LOW'),
+]
+
+REL_STYLE = {
+    'CORE': ('#FFD600', '#5D4037', '⭐⭐⭐ CORE — 자사 패키지 즉시'),
+    'HIGH': ('#81C784', '#1B5E20', '⭐⭐ HIGH — 자사 패키지 가능'),
+    'MED':  ('#90CAF9', '#0D47A1', '⭐ MED — 그룹·OEM 협업'),
+    'LOW':  ('#E0E0E0', '#616161', '○ LOW — 솔루션화 어려움'),
+}
+
+# 솔루션 회사 라이선스 모델
+LICENSE_MODELS = [
+    '월구독 100-500만', '월구독 500-2000만', '월구독 1000-3000만',
+    '영구 라이선스 1社 1-3억', '영구 라이선스 1社 3-7억', '영구 라이선스 1社 5-15억',
+    'OEM 라이선스', '종량제 (API 호출당)', '패키지 + 유지보수',
+]
+
+TECHS = [
+    'Llama 4 + 도메인 LoRA', 'Llama 4 Reasoning', 'Llama 4 Scout (1M)',
+    'Llama 4 Vision', 'Llama 4 Voice', 'Llama 4 ×3 다중 합의',
+    'Causal AI (DoWhy)', 'GraphRAG (Neo4j)', 'Constitutional AI',
+    'Computer Use', 'MCP Tool', 'MemGPT 장기기억',
+    'World Models', 'OpenVLA', 'GR00T',
+    'Affective Computing', 'Behavioral Biometrics', 'Continuous Auth',
+    'Deepfake Detection', 'C2PA', 'AI Workload Protection', 'NHI', 'CSMA', 'DSPM',
+    'Federated Learning', 'Confidential Computing', 'Homomorphic', 'DP',
+    'Synthetic Data', 'Quantum ML',
+]
+
+SUBCATS = ['탐지', '예측', '자동화', '인증', '진단', '점수화', '분석', '관리', '최적화', '통합']
+
+INFRA_MAP = {
+    'Quantum': 'IBM Quantum (무료)',
+    'World': 'NVIDIA Cluster + Mac Studio',
+    'GR00T': 'NVIDIA Cluster + 로봇',
+}
+
+def get_infra(tech):
+    for k, v in INFRA_MAP.items():
+        if k in tech:
+            return v
+    return 'Mac Studio 1-2대 (1.5-3천만)'
+
+# CORE → HIGH → MED → LOW 정렬
+REL_ORDER = {'CORE': 0, 'HIGH': 1, 'MED': 2, 'LOW': 3}
+AREAS_SORTED = sorted(enumerate(AREAS, 1), key=lambda x: REL_ORDER[x[1][3]])
+
+parts = []
+for orig_idx, (emoji, name, pkg_prefix, rel) in AREAS_SORTED:
+    bg, txt, rel_label = REL_STYLE[rel]
+    base = (orig_idx - 1) * 30
+    border_style = f'border-left:8px solid {bg}'
+    if rel in ['CORE', 'HIGH']:
+        border_style += f';box-shadow:0 4px 12px {bg}66'
+
+    parts.append(f"""
+<div class="area" id="a{orig_idx}" style="{border_style}">
+  <div class="area-head" style="background:{bg};color:{txt}">
+    <div class="ae">{emoji}</div>
+    <div style="flex:1">
+      <div class="an">{orig_idx}. {name}</div>
+      <div class="ao">자사 패키지: {pkg_prefix}-* · #{base+1:04d}-#{base+30:04d}</div>
+    </div>
+    <div class="rel" style="color:{txt}">{rel_label}</div>
+  </div>
+  <div class="grid">""")
+
+    for i in range(30):
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
