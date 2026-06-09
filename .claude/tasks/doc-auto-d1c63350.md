# doc_auto task — C:\\work\\orchestration_v1\\.claude\\scripts\\make-itcen-proposal.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/make-itcen-proposal.py b/.claude/scripts/make-itcen-proposal.py
new file mode 100644
index 0000000..991eb1e
--- /dev/null
+++ b/.claude/scripts/make-itcen-proposal.py
@@ -0,0 +1,424 @@
+"""ITcen 공모전 제출용 Excel 생성.
+
+4 시트:
+  1. ROI 매트릭스 (분류·top 추천·근거)
+  2. 100 아이디어 (카테고리·번호·제목·설명·ROI 분류)
+  3. 제출 양식 (빈칸 템플릿)
+  4. BMC 예시 — 가장 유망한 #2 sLLM 회의록·법무문서 자동 요약·태깅
+"""
+from __future__ import annotations
+import sys
+import subprocess
+from pathlib import Path
+from datetime import date
+
+# openpyxl 자동 install
+try:
+    import openpyxl  # noqa: F401
+except ImportError:
+    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "openpyxl"], check=True)
+    import openpyxl  # noqa: F401
+
+from openpyxl import Workbook
+from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
+from openpyxl.utils import get_column_letter
+
+PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
+OUT_DIR = PROJECT_ROOT / "outputs" / "itcen"
+OUT_DIR.mkdir(parents=True, exist_ok=True)
+OUT_FILE = OUT_DIR / f"itcen-proposal-{date.today().isoformat()}.xlsx"
+
+# ───────── 스타일 ─────────
+HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
+HEADER_FONT = Font(name="맑은 고딕", bold=True, size=11, color="FFFFFF")
+CAT_FILL = PatternFill("solid", fgColor="D9E2F3")
+CAT_FONT = Font(name="맑은 고딕", bold=True, size=11, color="1F4E79")
+NORMAL = Font(name="맑은 고딕", size=10)
+THIN = Side(border_style="thin", color="BFBFBF")
+BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
+WRAP = Alignment(wrap_text=True, vertical="top")
+CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
+
+wb = Workbook()
+
+# ═══════════════════════════════════════════════════════════
+# Sheet 1: ROI 매트릭스
+# ═══════════════════════════════════════════════════════════
+ws = wb.active
+ws.title = "1.ROI매트릭스"
+
+ROI_MATRIX = [
+    ("즉시 매출 (6~12개월)",
+     "#2 sLLM 회의록 / #11 ZTN 자동정책 / #41 FDS GNN / #91 사내 RAG / #92 회의록 액션 / #1 멀티모달 지식포털",
+     "한국 대기업 PoC 단계. ITcen SI 레퍼런스 활용. 객단가 3~10억", "★★★★★"),
+    ("단기 PoC → 1년 매출",
+     "#17 IAM 최소권한 / #18 SOAR AI / #22 예지보전 / #23 이탈예측 / #42 AML SAR",
+     "금융·제조 정기 발주. ITcen 보안 사업부 직결", "★★★★"),
+    ("중장기 R&D (정부매칭)",
+     "#71 FHE / #72 PQC / #73 QKD / #75 CBDC",
+     "과기정통부·KISA 과제 매칭. 양자 키워드와 시너지", "★★★"),
+    ("B2G 공공입찰 강점",
+     "#33 CCTV 군중 / #54 화재 영상 / #66 그린빌딩 / #68 산림위성 / #15 컨테이너 / #19 ICS/OT",
+     "행정안전부·산림청·환경부 발주", "★★★★"),
+    ("글로벌 수출 가능",
+     "#71 FHE / #72 PQC / #82 V2X / #88 자율주행 익명화",
+     "미·EU 규제 대응. K-방산·자동차 OEM 협력", "★★★"),
+    ("레드오션 — 제외 추천",
+     "#6 온보딩 / #28 데이터품질 / #34 주차장 / #56 임상시험",
+     "이미 포화·B2C·해외 대형사 점유", "✗"),
+    ("시너지 (사용자 기존 4개 확장)",
+     "리스크 → #41·#42·#48 / 양자 → #71·#72·#73 / 피지컬 → #11·#54·#33 / 행동위험 → #59·#89·#13",
+     "같은 PoC 묶어서 컨소시엄화 가능", "★★★★★"),
+]
+
+ws["A1"] = "ITcen 공모전 — 100 아이디어 ROI 매트릭스"
+ws["A1"].font = Font(name="맑은 고딕", bold=True, size=14, color="1F4E79")
+ws.merge_cells("A1:D1")
+
+headers = ["분류", "Top 추천", "근거", "추천 강도"]
+for col, h in enumerate(headers, 1):
+    c = ws.cell(row=3, column=col, value=h)
+    c.fill = HEADER_FILL
+    c.font = HEADER_FONT
+    c.alignment = CENTER
+    c.border = BORDER
+
+for i, (cls, picks, reason, star) in enumerate(ROI_MATRIX, 4):
+    ws.cell(row=i, column=1, value=cls).font = CAT_FONT
+    ws.cell(row=i, column=1).fill = CAT_FILL
+    ws.cell(row=i, column=2, value=picks).font = NORMAL
+    ws.cell(row=i, column=3, value=reason).font = NORMAL
+    ws.cell(row=i, column=4, value=star).font = NORMAL
+    for col in range(1, 5):
+        ws.cell(row=i, column=col).alignment = WRAP
+        ws.cell(row=i, column=col).border = BORDER
+
+ws.column_dimensions["A"].width = 25
+ws.column_dimensions["B"].width = 55
+ws.column_dimensions["C"].width = 40
+ws.column_dimensions["D"].width = 12
+for i in range(4, 4 + len(ROI_MATRIX)):
+    ws.row_dimensions[i].height = 50
+
+# ═══════════════════════════════════════════════════════════
+# Sheet 2: 100 아이디어
+# ═══════════════════════════════════════════════════════════
+ws2 = wb.create_sheet("2.100아이디어")
+
+IDEAS = [
+    # (번호, 카테고리, 제목, ROI 분류, 예상 객단가, 추천)
+    ("A. AI·LLM 응용", [
+        (1, "멀티모달 RAG 기반 사내 지식포털 (PDF/도면/영상 통합 검색)", "즉시 매출", "3~8억", "★★★★★"),
+        (2, "도메인 fine-tune sLLM 회의록·법무문서 자동 요약·태깅", "즉시 매출", "5~10억", "★★★★★"),
+        (3, "AI 코드 리뷰 봇 (보안·라이선스·성능 3축 동시 평가)", "즉시 매출", "2~5억", "★★★★"),
+        (4, "음성 에이전트 콜센터 — 통화 중 실시간 컴플라이언스 위반 감지", "단기 PoC", "3~7억", "★★★★"),
+        (5, "이미지+텍스트 멀티에이전트 보험 손해사정 자동화", "단기 PoC", "5~12억", "★★★★"),
+        (6, "신입 온보딩 AI 튜터 — 사내 시스템 사용법 대화형 학습", "레드오션", "1~3억", "★★"),
+        (7, "RAG 기반 RFP·제안서 자동 생성 (과거 사례 검색 + 생성)", "즉시 매출", "2~5억", "★★★★"),
+        (8, "AI 영업기회 스코어링 — CRM·이메일·미팅 자동 점수화", "단기 PoC", "2~4억", "★★★"),
+        (9, "멀티 에이전트 회계 마감 자동화 (분개·증빙·세무 협업)", "단기 PoC", "3~6억", "★★★★"),
+        (10, "임원 대시보드 자연어 질의 (한 줄 질문 → 차트·인사이트)", "즉시 매출", "2~5억", "★★★★"),
+    ]),
+    ("B. 사이버보안 심화", [
+        (11, "Zero Trust 네트워크 자동 정책 생성 (이상 트래픽 학습)", "즉시 매출", "5~15억", "★★★★★"),
+        (12, "SBOM 자동 감사 — OSS 취약 의존성 PR 자동 차단", "단기 PoC", "2~4억", "★★★"),
+        (13, "AI 기반 피싱메일 탐지 (멀티모달 + 평판 점수)", "단기 PoC", "2~5억", "★★★★"),
+        (14, "데이터 유출 DLP — 클립보드·USB·메신저 실시간 마스킹", "단기 PoC", "3~7억", "★★★★"),
+        (15, "컨테이너 런타임 이상행위 탐지 (eBPF + ML)", "B2G", "5~10억", "★★★★"),
+        (16, "패스키 전사 도입 마이그레이션 도구 (패스워드 폐기)", "단기 PoC", "2~4억", "★★★"),
+        (17, "클라우드 IAM 최소권한 자동 추천 (Access Analyzer + LLM)", "단기 PoC", "3~6억", "★★★★"),
+        (18, "AI 침해사고 자동 분류·플레이북 실행 (SOAR + LLM)", "단기 PoC", "5~12억", "★★★★★"),
+        (19, "ICS/OT 산업제어망 침입탐지 (Modbus/DNP3 파싱)", "B2G", "8~20억", "★★★★"),
+        (20, "AI 생성 코드 보안 검증 — Copilot 산출물 자동 SAST", "단기 PoC", "2~4억", "★★★"),
+    ]),
+    ("C. 데이터·예측", [
+        (21, "수요예측 + 자동 발주 (식자재·소모품)", "단기 PoC", "2~5억", "★★★"),
+        (22, "설비 예지보전 — 진동·온도 시계열 이상 탐지", "단기 PoC", "5~12억", "★★★★★"),
+        (23, "이탈고객 예측 + 맞춤 retention 캠페인 자동화", "단기 PoC", "2~5억", "★★★★"),
+        (24, "매출 cohort 분석 자동 리포트 (월간 자동 송부)", "단기 PoC", "1~3억", "★★★"),
+        (25, "A/B 테스트 자동 설계·해석 (베이지안)", "단기 PoC", "1~3억", "★★"),
+        (26, "데이터 카탈로그 + 의미 검색 (자연어 → 테이블)", "즉시 매출", "3~7억", "★★★★"),
+        (27, "합성 데이터 생성 (개인정보 비식별 학습용)", "단기 PoC", "2~5억", "★★★"),
+        (28, "데이터 품질 모니터링 (Great Expectations + 알림)", "레드오션", "1~3억", "★★"),
+        (29, "KPI 이상 자동 진단 (drill-down + 원인 LLM 설명)", "단기 PoC", "2~5억", "★★★★"),
+        (30, "외부데이터 통합 ELT 자동화 (날씨·환율·뉴스)", "단기 PoC", "1~3억", "★★★"),
+    ]),
+    ("D. IoT·엣지·스마트시티", [
+        (31, "공장 디지털 트윈 + 실시간 동기화 (BACnet/MQTT)", "B2G", "10~30억", "★★★★"),
+        (32, "스마트 빌딩 에너지 최적화 (예측 HVAC 제어)", "B2G", "5~15억", "★★★★"),
+        (33, "도시 CCTV 군중 밀집·이상행동 알림", "B2G", "5~15억", "★★★★★"),
+        (34, "주차장 빈자리 예측 + 동적 요금", "레드오션", "2~5억", "★★"),
+        (35, "스마트 가로등 (조도·인구 흐름 기반 자동 조절)", "B2G", "5~10억", "★★★"),
+        (36, "환경센서 실시간 대기질 지도 + 시민 알림", "B2G", "3~7억", "★★★"),
+        (37, "엣지 AI 카메라 — 산업안전 PPE 미착용 탐지", "단기 PoC", "3~7억", "★★★★"),
+        (38, "농업 IoT — 작물 병해충 조기 탐지 + 처방", "B2G", "2~5억", "★★★"),
+        (39, "스마트 폐기물 — 적재량 센서 + 수거 경로 최적화", "B2G", "3~6억", "★★★"),
+        (40, "물류창고 자율로봇 작업 스케줄러", "단기 PoC", "8~20억", "★★★★"),
+    ]),
+    ("E. 핀테크·금융 리스크", [
+        (41, "AI 이상거래 탐지 (FDS) — 그래프 신경망 기반", "즉시 매출", "5~15억", "★★★★★"),
+        (42, "자금세탁방지(AML) 트랜잭션 자동 SAR 작성", "단기 PoC", "5~12억", "★★★★"),
+        (43, "신용평가 대안데이터 (소셜·통신·결제 패턴)", "단기 PoC", "3~7억", "★★★"),
+        (44, "ESG 채권 신용 리스크 모델", "중장기 R&D", "2~5억", "★★★"),
+        (45, "보험사기 탐지 + 자동 조사 메모", "단기 PoC", "3~7억", "★★★★"),
+        (46, "마이데이터 자산 통합 + 개인화 자문", "단기 PoC", "2~5억", "★★★"),
+        (47, "환율 헤지 자동 추천 (수출입 기업용)", "단기 PoC", "1~3억", "★★"),
+        (48, "컴플라이언스 규제 변경 자동 추적·영향 분석", "즉시 매출", "3~7억", "★★★★"),
+        (49, "카드사 한도 동적 조정 (실시간 거래 패턴)", "단기 PoC", "3~7억", "★★★"),
+        (50, "P2P 정산 자동화 (가맹점·세무)", "단기 PoC", "2~5억", "★★★"),
+    ]),
+    ("F. 헬스·안전·재난", [
+        (51, "의료영상 AI 1차 판독 + 우선순위 큐", "단기 PoC", "5~15억", "★★★★"),
+        (52, "환자 동선 추적 (응급실 체류 최적화)", "B2G", "3~7억", "★★★"),
+        (53, "산업현장 낙상 탐지 (스마트워치 + 카메라)", "단기 PoC", "3~7억", "★★★★"),
+        (54, "화재·연기 영상 조기탐지 (CCTV 분석)", "B2G", "5~15억", "★★★★★"),
+        (55, "응급실 환자분류(triage) AI 보조", "B2G", "3~7억", "★★★"),
+        (56, "임상시험 환자 매칭 자동화", "레드오션", "2~5억", "★★"),
+        (57, "만성질환 원격 모니터링 (혈압·혈당 데이터)", "B2G", "3~7억", "★★★"),
+        (58, "정신건강 챗봇 (CBT 기반 + 위기 감지)", "단기 PoC", "1~3억", "★★"),
+        (59, "재난 SNS 분석 (실시간 피해 지도)", "B2G", "3~7억", "★★★★"),
+        (60, "화학물질 누출 시뮬레이션 + 대피경로 안내", "B2G", "3~7억", "★★★"),
+    ]),
+    ("G. ESG·기후·에너지", [
+        (61, "Scope 1·2·3 탄소배출 자동 산정 + 보고서", "즉시 매출", "3~7억", "★★★★"),
+        (62, "RE100 재생에너지 추적 + 거래 (PPA 자동화)", "단기 PoC", "5~12억", "★★★"),
+        (63, "전력수요 예측 + DR 자동참여", "단기 PoC", "3~7억", "★★★"),
+        (64, "폐기물 분류 영상 AI (재활용 라인)", "B2G", "2~5억", "★★★"),
+        (65, "공급망 ESG 평가 — 협력사 자동 스코어링", "단기 PoC", "2~5억", "★★★★"),
+        (66, "그린 빌딩 인증 자동 모니터링 (LEED·G-SEED)", "B2G", "2~5억", "★★★"),
+        (67, "친환경 물류 경로 (탄소 최소 라우팅)", "단기 PoC", "2~5억", "★★★"),
+        (68, "산림 위성 모니터링 (불법벌채·산불 위험)", "B2G", "5~12억", "★★★★"),
+        (69, "수질 IoT 센서 + 예측 모델 (정수장)", "B2G", "3~7억", "★★★"),
+        (70, "마이크로 그리드 자동 운영 (P2P 전력거래)", "중장기 R&D", "3~7억", "★★★"),
+    ]),
+    ("H. 양자·차세대 컴퓨팅", [
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
