"""ITcen 공모전 제출용 Excel 생성.

4 시트:
  1. ROI 매트릭스 (분류·top 추천·근거)
  2. 100 아이디어 (카테고리·번호·제목·설명·ROI 분류)
  3. 제출 양식 (빈칸 템플릿)
  4. BMC 예시 — 가장 유망한 #2 sLLM 회의록·법무문서 자동 요약·태깅
"""
from __future__ import annotations
import sys
import subprocess
from pathlib import Path
from datetime import date

# openpyxl 자동 install
try:
    import openpyxl  # noqa: F401
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "openpyxl"], check=True)
    import openpyxl  # noqa: F401

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = PROJECT_ROOT / "outputs" / "itcen"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / f"itcen-proposal-{date.today().isoformat()}.xlsx"

# ───────── 스타일 ─────────
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(name="맑은 고딕", bold=True, size=11, color="FFFFFF")
CAT_FILL = PatternFill("solid", fgColor="D9E2F3")
CAT_FONT = Font(name="맑은 고딕", bold=True, size=11, color="1F4E79")
NORMAL = Font(name="맑은 고딕", size=10)
THIN = Side(border_style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

wb = Workbook()

# ═══════════════════════════════════════════════════════════
# Sheet 1: ROI 매트릭스
# ═══════════════════════════════════════════════════════════
ws = wb.active
ws.title = "1.ROI매트릭스"

ROI_MATRIX = [
    ("즉시 매출 (6~12개월)",
     "#2 sLLM 회의록 / #11 ZTN 자동정책 / #41 FDS GNN / #91 사내 RAG / #92 회의록 액션 / #1 멀티모달 지식포털",
     "한국 대기업 PoC 단계. ITcen SI 레퍼런스 활용. 객단가 3~10억", "★★★★★"),
    ("단기 PoC → 1년 매출",
     "#17 IAM 최소권한 / #18 SOAR AI / #22 예지보전 / #23 이탈예측 / #42 AML SAR",
     "금융·제조 정기 발주. ITcen 보안 사업부 직결", "★★★★"),
    ("중장기 R&D (정부매칭)",
     "#71 FHE / #72 PQC / #73 QKD / #75 CBDC",
     "과기정통부·KISA 과제 매칭. 양자 키워드와 시너지", "★★★"),
    ("B2G 공공입찰 강점",
     "#33 CCTV 군중 / #54 화재 영상 / #66 그린빌딩 / #68 산림위성 / #15 컨테이너 / #19 ICS/OT",
     "행정안전부·산림청·환경부 발주", "★★★★"),
    ("글로벌 수출 가능",
     "#71 FHE / #72 PQC / #82 V2X / #88 자율주행 익명화",
     "미·EU 규제 대응. K-방산·자동차 OEM 협력", "★★★"),
    ("레드오션 — 제외 추천",
     "#6 온보딩 / #28 데이터품질 / #34 주차장 / #56 임상시험",
     "이미 포화·B2C·해외 대형사 점유", "✗"),
    ("시너지 (사용자 기존 4개 확장)",
     "리스크 → #41·#42·#48 / 양자 → #71·#72·#73 / 피지컬 → #11·#54·#33 / 행동위험 → #59·#89·#13",
     "같은 PoC 묶어서 컨소시엄화 가능", "★★★★★"),
]

ws["A1"] = "ITcen 공모전 — 100 아이디어 ROI 매트릭스"
ws["A1"].font = Font(name="맑은 고딕", bold=True, size=14, color="1F4E79")
ws.merge_cells("A1:D1")

headers = ["분류", "Top 추천", "근거", "추천 강도"]
for col, h in enumerate(headers, 1):
    c = ws.cell(row=3, column=col, value=h)
    c.fill = HEADER_FILL
    c.font = HEADER_FONT
    c.alignment = CENTER
    c.border = BORDER

for i, (cls, picks, reason, star) in enumerate(ROI_MATRIX, 4):
    ws.cell(row=i, column=1, value=cls).font = CAT_FONT
    ws.cell(row=i, column=1).fill = CAT_FILL
    ws.cell(row=i, column=2, value=picks).font = NORMAL
    ws.cell(row=i, column=3, value=reason).font = NORMAL
    ws.cell(row=i, column=4, value=star).font = NORMAL
    for col in range(1, 5):
        ws.cell(row=i, column=col).alignment = WRAP
        ws.cell(row=i, column=col).border = BORDER

ws.column_dimensions["A"].width = 25
ws.column_dimensions["B"].width = 55
ws.column_dimensions["C"].width = 40
ws.column_dimensions["D"].width = 12
for i in range(4, 4 + len(ROI_MATRIX)):
    ws.row_dimensions[i].height = 50

# ═══════════════════════════════════════════════════════════
# Sheet 2: 100 아이디어
# ═══════════════════════════════════════════════════════════
ws2 = wb.create_sheet("2.100아이디어")

IDEAS = [
    # (번호, 카테고리, 제목, ROI 분류, 예상 객단가, 추천)
    ("A. AI·LLM 응용", [
        (1, "멀티모달 RAG 기반 사내 지식포털 (PDF/도면/영상 통합 검색)", "즉시 매출", "3~8억", "★★★★★"),
        (2, "도메인 fine-tune sLLM 회의록·법무문서 자동 요약·태깅", "즉시 매출", "5~10억", "★★★★★"),
        (3, "AI 코드 리뷰 봇 (보안·라이선스·성능 3축 동시 평가)", "즉시 매출", "2~5억", "★★★★"),
        (4, "음성 에이전트 콜센터 — 통화 중 실시간 컴플라이언스 위반 감지", "단기 PoC", "3~7억", "★★★★"),
        (5, "이미지+텍스트 멀티에이전트 보험 손해사정 자동화", "단기 PoC", "5~12억", "★★★★"),
        (6, "신입 온보딩 AI 튜터 — 사내 시스템 사용법 대화형 학습", "레드오션", "1~3억", "★★"),
        (7, "RAG 기반 RFP·제안서 자동 생성 (과거 사례 검색 + 생성)", "즉시 매출", "2~5억", "★★★★"),
        (8, "AI 영업기회 스코어링 — CRM·이메일·미팅 자동 점수화", "단기 PoC", "2~4억", "★★★"),
        (9, "멀티 에이전트 회계 마감 자동화 (분개·증빙·세무 협업)", "단기 PoC", "3~6억", "★★★★"),
        (10, "임원 대시보드 자연어 질의 (한 줄 질문 → 차트·인사이트)", "즉시 매출", "2~5억", "★★★★"),
    ]),
    ("B. 사이버보안 심화", [
        (11, "Zero Trust 네트워크 자동 정책 생성 (이상 트래픽 학습)", "즉시 매출", "5~15억", "★★★★★"),
        (12, "SBOM 자동 감사 — OSS 취약 의존성 PR 자동 차단", "단기 PoC", "2~4억", "★★★"),
        (13, "AI 기반 피싱메일 탐지 (멀티모달 + 평판 점수)", "단기 PoC", "2~5억", "★★★★"),
        (14, "데이터 유출 DLP — 클립보드·USB·메신저 실시간 마스킹", "단기 PoC", "3~7억", "★★★★"),
        (15, "컨테이너 런타임 이상행위 탐지 (eBPF + ML)", "B2G", "5~10억", "★★★★"),
        (16, "패스키 전사 도입 마이그레이션 도구 (패스워드 폐기)", "단기 PoC", "2~4억", "★★★"),
        (17, "클라우드 IAM 최소권한 자동 추천 (Access Analyzer + LLM)", "단기 PoC", "3~6억", "★★★★"),
        (18, "AI 침해사고 자동 분류·플레이북 실행 (SOAR + LLM)", "단기 PoC", "5~12억", "★★★★★"),
        (19, "ICS/OT 산업제어망 침입탐지 (Modbus/DNP3 파싱)", "B2G", "8~20억", "★★★★"),
        (20, "AI 생성 코드 보안 검증 — Copilot 산출물 자동 SAST", "단기 PoC", "2~4억", "★★★"),
    ]),
    ("C. 데이터·예측", [
        (21, "수요예측 + 자동 발주 (식자재·소모품)", "단기 PoC", "2~5억", "★★★"),
        (22, "설비 예지보전 — 진동·온도 시계열 이상 탐지", "단기 PoC", "5~12억", "★★★★★"),
        (23, "이탈고객 예측 + 맞춤 retention 캠페인 자동화", "단기 PoC", "2~5억", "★★★★"),
        (24, "매출 cohort 분석 자동 리포트 (월간 자동 송부)", "단기 PoC", "1~3억", "★★★"),
        (25, "A/B 테스트 자동 설계·해석 (베이지안)", "단기 PoC", "1~3억", "★★"),
        (26, "데이터 카탈로그 + 의미 검색 (자연어 → 테이블)", "즉시 매출", "3~7억", "★★★★"),
        (27, "합성 데이터 생성 (개인정보 비식별 학습용)", "단기 PoC", "2~5억", "★★★"),
        (28, "데이터 품질 모니터링 (Great Expectations + 알림)", "레드오션", "1~3억", "★★"),
        (29, "KPI 이상 자동 진단 (drill-down + 원인 LLM 설명)", "단기 PoC", "2~5억", "★★★★"),
        (30, "외부데이터 통합 ELT 자동화 (날씨·환율·뉴스)", "단기 PoC", "1~3억", "★★★"),
    ]),
    ("D. IoT·엣지·스마트시티", [
        (31, "공장 디지털 트윈 + 실시간 동기화 (BACnet/MQTT)", "B2G", "10~30억", "★★★★"),
        (32, "스마트 빌딩 에너지 최적화 (예측 HVAC 제어)", "B2G", "5~15억", "★★★★"),
        (33, "도시 CCTV 군중 밀집·이상행동 알림", "B2G", "5~15억", "★★★★★"),
        (34, "주차장 빈자리 예측 + 동적 요금", "레드오션", "2~5억", "★★"),
        (35, "스마트 가로등 (조도·인구 흐름 기반 자동 조절)", "B2G", "5~10억", "★★★"),
        (36, "환경센서 실시간 대기질 지도 + 시민 알림", "B2G", "3~7억", "★★★"),
        (37, "엣지 AI 카메라 — 산업안전 PPE 미착용 탐지", "단기 PoC", "3~7억", "★★★★"),
        (38, "농업 IoT — 작물 병해충 조기 탐지 + 처방", "B2G", "2~5억", "★★★"),
        (39, "스마트 폐기물 — 적재량 센서 + 수거 경로 최적화", "B2G", "3~6억", "★★★"),
        (40, "물류창고 자율로봇 작업 스케줄러", "단기 PoC", "8~20억", "★★★★"),
    ]),
    ("E. 핀테크·금융 리스크", [
        (41, "AI 이상거래 탐지 (FDS) — 그래프 신경망 기반", "즉시 매출", "5~15억", "★★★★★"),
        (42, "자금세탁방지(AML) 트랜잭션 자동 SAR 작성", "단기 PoC", "5~12억", "★★★★"),
        (43, "신용평가 대안데이터 (소셜·통신·결제 패턴)", "단기 PoC", "3~7억", "★★★"),
        (44, "ESG 채권 신용 리스크 모델", "중장기 R&D", "2~5억", "★★★"),
        (45, "보험사기 탐지 + 자동 조사 메모", "단기 PoC", "3~7억", "★★★★"),
        (46, "마이데이터 자산 통합 + 개인화 자문", "단기 PoC", "2~5억", "★★★"),
        (47, "환율 헤지 자동 추천 (수출입 기업용)", "단기 PoC", "1~3억", "★★"),
        (48, "컴플라이언스 규제 변경 자동 추적·영향 분석", "즉시 매출", "3~7억", "★★★★"),
        (49, "카드사 한도 동적 조정 (실시간 거래 패턴)", "단기 PoC", "3~7억", "★★★"),
        (50, "P2P 정산 자동화 (가맹점·세무)", "단기 PoC", "2~5억", "★★★"),
    ]),
    ("F. 헬스·안전·재난", [
        (51, "의료영상 AI 1차 판독 + 우선순위 큐", "단기 PoC", "5~15억", "★★★★"),
        (52, "환자 동선 추적 (응급실 체류 최적화)", "B2G", "3~7억", "★★★"),
        (53, "산업현장 낙상 탐지 (스마트워치 + 카메라)", "단기 PoC", "3~7억", "★★★★"),
        (54, "화재·연기 영상 조기탐지 (CCTV 분석)", "B2G", "5~15억", "★★★★★"),
        (55, "응급실 환자분류(triage) AI 보조", "B2G", "3~7억", "★★★"),
        (56, "임상시험 환자 매칭 자동화", "레드오션", "2~5억", "★★"),
        (57, "만성질환 원격 모니터링 (혈압·혈당 데이터)", "B2G", "3~7억", "★★★"),
        (58, "정신건강 챗봇 (CBT 기반 + 위기 감지)", "단기 PoC", "1~3억", "★★"),
        (59, "재난 SNS 분석 (실시간 피해 지도)", "B2G", "3~7억", "★★★★"),
        (60, "화학물질 누출 시뮬레이션 + 대피경로 안내", "B2G", "3~7억", "★★★"),
    ]),
    ("G. ESG·기후·에너지", [
        (61, "Scope 1·2·3 탄소배출 자동 산정 + 보고서", "즉시 매출", "3~7억", "★★★★"),
        (62, "RE100 재생에너지 추적 + 거래 (PPA 자동화)", "단기 PoC", "5~12억", "★★★"),
        (63, "전력수요 예측 + DR 자동참여", "단기 PoC", "3~7억", "★★★"),
        (64, "폐기물 분류 영상 AI (재활용 라인)", "B2G", "2~5억", "★★★"),
        (65, "공급망 ESG 평가 — 협력사 자동 스코어링", "단기 PoC", "2~5억", "★★★★"),
        (66, "그린 빌딩 인증 자동 모니터링 (LEED·G-SEED)", "B2G", "2~5억", "★★★"),
        (67, "친환경 물류 경로 (탄소 최소 라우팅)", "단기 PoC", "2~5억", "★★★"),
        (68, "산림 위성 모니터링 (불법벌채·산불 위험)", "B2G", "5~12억", "★★★★"),
        (69, "수질 IoT 센서 + 예측 모델 (정수장)", "B2G", "3~7억", "★★★"),
        (70, "마이크로 그리드 자동 운영 (P2P 전력거래)", "중장기 R&D", "3~7억", "★★★"),
    ]),
    ("H. 양자·차세대 컴퓨팅", [
        (71, "동형암호(FHE) 의료데이터 분석 PoC", "글로벌 수출", "5~15억", "★★★★★"),
        (72, "양자내성암호(PQC) 전환 도구 (CRYPTO inventory + roadmap)", "글로벌 수출", "5~12억", "★★★★★"),
        (73, "양자키분배(QKD) 백본 + 고전 채널 하이브리드", "중장기 R&D", "10~30억", "★★★★"),
        (74, "분산 신원(DID) 사원증 + 자격증명", "단기 PoC", "3~7억", "★★★"),
        (75, "CBDC 시범 결제 인프라", "중장기 R&D", "10~30억", "★★★★"),
        (76, "영지식증명(zk-SNARK) 본인인증 (KYC 비공개)", "중장기 R&D", "3~7억", "★★★"),
        (77, "컨피덴셜 컴퓨팅 (Intel TDX/SEV) 멀티테넌트 분석", "단기 PoC", "5~12억", "★★★★"),
        (78, "뉴로모픽 칩 엣지 추론 PoC", "중장기 R&D", "5~12억", "★★★"),
        (79, "광컴퓨팅 행렬연산 가속 (생성AI 학습 비용 절감)", "중장기 R&D", "10~30억", "★★★"),
        (80, "DNA 스토리지 장기 보관 PoC", "중장기 R&D", "3~7억", "★★"),
    ]),
    ("I. 자율주행·모빌리티", [
        (81, "자율주행 시뮬레이션 시나리오 자동 생성 (LLM + 3D)", "단기 PoC", "5~12억", "★★★★"),
        (82, "V2X 통신 보안 (인증서 자동 발급·폐기)", "글로벌 수출", "5~15억", "★★★★"),
        (83, "화물 트럭 군집주행 (Platooning) 운영 플랫폼", "중장기 R&D", "10~30억", "★★★"),
        (84, "배송 라스트마일 로봇 운영 시스템", "단기 PoC", "5~12억", "★★★"),
        (85, "드론 배송 항로 + 공역 관리", "B2G", "5~12억", "★★★"),
        (86, "도심항공교통(UAM) 관제 시뮬레이션", "중장기 R&D", "10~30억", "★★★"),
        (87, "전기차 충전 동적 가격·예약", "단기 PoC", "3~7억", "★★★"),
        (88, "자율주행 사고 데이터 익명화·공유 표준", "글로벌 수출", "3~7억", "★★★★"),
        (89, "운전자 졸음·산만 모니터링 (in-cabin AI)", "단기 PoC", "3~7억", "★★★★"),
        (90, "공유 모빌리티 수요 예측 + 차량 재배치", "단기 PoC", "2~5억", "★★★"),
    ]),
    ("J. 디지털 워크·RPA·플랫폼", [
        (91, "사내 RAG 사이드킥 (Slack/Teams 통합)", "즉시 매출", "2~5억", "★★★★★"),
        (92, "AI 회의록 + 액션아이템 자동 할당 (Jira/Linear)", "즉시 매출", "2~5억", "★★★★★"),
        (93, "노코드 워크플로우 빌더 (AI 자동 자동화 제안)", "단기 PoC", "3~7억", "★★★"),
        (94, "사내 챗봇 → 멀티에이전트 컨시어지 (HR·IT·총무 통합)", "단기 PoC", "3~7억", "★★★★"),
        (95, "코드 → 다이어그램 자동 (아키텍처 시각화)", "단기 PoC", "1~3억", "★★★"),
        (96, "인보이스 OCR + ERP 자동 입력 + 승인 라우팅", "단기 PoC", "2~5억", "★★★★"),
        (97, "사내 API 마켓플레이스 (자동 카탈로그·소비량 분석)", "단기 PoC", "2~5억", "★★★"),
        (98, "개발자 생산성 분석 (DORA 지표 + LLM 진단)", "단기 PoC", "1~3억", "★★★"),
        (99, "사이트 신뢰성 (SRE) — incident timeline 자동 생성", "단기 PoC", "2~5억", "★★★"),
        (100, "디지털 트윈 + LLM 자연어 운영 콘솔 (한 문장으로 조작)", "중장기 R&D", "5~12억", "★★★★"),
    ]),
]

ws2["A1"] = "ITcen 공모전 — 100 아이디어 전체 리스트"
ws2["A1"].font = Font(name="맑은 고딕", bold=True, size=14, color="1F4E79")
ws2.merge_cells("A1:F1")

headers2 = ["번호", "카테고리", "제목·핵심", "ROI 분류", "예상 객단가", "추천 강도"]
for col, h in enumerate(headers2, 1):
    c = ws2.cell(row=3, column=col, value=h)
    c.fill = HEADER_FILL
    c.font = HEADER_FONT
    c.alignment = CENTER
    c.border = BORDER

row = 4
for cat, items in IDEAS:
    # 카테고리 row
    cc = ws2.cell(row=row, column=1, value=cat)
    cc.fill = CAT_FILL
    cc.font = CAT_FONT
    cc.alignment = Alignment(horizontal="left", vertical="center")
    ws2.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
    cc.border = BORDER
    row += 1
    for num, title, roi, price, star in items:
        ws2.cell(row=row, column=1, value=num).font = NORMAL
        ws2.cell(row=row, column=2, value=cat[:1]).font = NORMAL
        ws2.cell(row=row, column=3, value=title).font = NORMAL
        ws2.cell(row=row, column=4, value=roi).font = NORMAL
        ws2.cell(row=row, column=5, value=price).font = NORMAL
        ws2.cell(row=row, column=6, value=star).font = NORMAL
        for col in range(1, 7):
            ws2.cell(row=row, column=col).alignment = WRAP
            ws2.cell(row=row, column=col).border = BORDER
        row += 1

ws2.column_dimensions["A"].width = 8
ws2.column_dimensions["B"].width = 8
ws2.column_dimensions["C"].width = 60
ws2.column_dimensions["D"].width = 18
ws2.column_dimensions["E"].width = 14
ws2.column_dimensions["F"].width = 12
ws2.freeze_panes = "A4"

# ═══════════════════════════════════════════════════════════
# Sheet 3: 제출 양식 (빈칸)
# ═══════════════════════════════════════════════════════════
ws3 = wb.create_sheet("3.제출양식")

ws3["A1"] = "ITcen 공모전 — 참가 신청 양식"
ws3["A1"].font = Font(name="맑은 고딕", bold=True, size=14, color="1F4E79")
ws3.merge_cells("A1:B1")

FORM_FIELDS = [
    ("팀명", "*필수", ""),
    ("소속 부서", "*필수", "예: 기술혁신본부"),
    ("팀원 수", "*필수", "예: 3명"),
    ("사업 분야", "*필수", "예: AI 기반 고객서비스 자동화, 스마트팩토리 플랫폼 등"),
    ("팀원 이름", "*필수", "예: 홍길동, 김철수, 이영희"),
    ("연락처 이메일", "*필수", "team@itcen.com"),
    ("프로젝트 제목", "*필수", "아이디어의 핵심을 담은 제목"),
    ("아이디어 설명", "*필수", "해결하려는 문제, 제안하는 솔루션, 핵심 기능"),
    ("기대 효과", "선택", "사업적 효과·성과"),
    ("아이디어 제안서 URL", "선택", "https://docs.google.com/... 또는 https://github.com/..."),
    ("아이디어 제안서 파일", "선택", "PPT·PPTX·PDF (최대 10MB)"),
    ("목업 URL", "선택", "https://www.figma.com/... 또는 데모 사이트"),
    ("BMC 문서 URL", "선택", "Google Slides·Notion·Figma 공유 링크"),
    ("BMC 파일", "선택", "PDF·PPT·PPTX·PNG·JPG (최대 10MB)"),
    ("수정용 4자리 PIN", "*필수", "추후 제출 결과물 수정 시 사용"),
]

ws3.cell(row=3, column=1, value="항목").fill = HEADER_FILL
ws3.cell(row=3, column=1).font = HEADER_FONT
ws3.cell(row=3, column=2, value="필수 여부").fill = HEADER_FILL
ws3.cell(row=3, column=2).font = HEADER_FONT
ws3.cell(row=3, column=3, value="입력 / 안내").fill = HEADER_FILL
ws3.cell(row=3, column=3).font = HEADER_FONT
for col in range(1, 4):
    ws3.cell(row=3, column=col).alignment = CENTER
    ws3.cell(row=3, column=col).border = BORDER

for i, (label, req, hint) in enumerate(FORM_FIELDS, 4):
    ws3.cell(row=i, column=1, value=label).font = CAT_FONT
    ws3.cell(row=i, column=1).fill = CAT_FILL
    ws3.cell(row=i, column=2, value=req).font = NORMAL
    ws3.cell(row=i, column=3, value=hint).font = NORMAL
    for col in range(1, 4):
        ws3.cell(row=i, column=col).alignment = WRAP
        ws3.cell(row=i, column=col).border = BORDER

ws3.column_dimensions["A"].width = 25
ws3.column_dimensions["B"].width = 12
ws3.column_dimensions["C"].width = 60

# ═══════════════════════════════════════════════════════════
# Sheet 4: BMC 예시 (#2 sLLM 회의록·법무문서 자동 요약·태깅)
# ═══════════════════════════════════════════════════════════
ws4 = wb.create_sheet("4.BMC예시-2번")

ws4["A1"] = "BMC 예시 — #2 도메인 fine-tune sLLM 회의록·법무문서 자동 요약·태깅"
ws4["A1"].font = Font(name="맑은 고딕", bold=True, size=14, color="1F4E79")
ws4.merge_cells("A1:B1")

ws4["A2"] = "ROI: 즉시 매출 (6~12개월) · 객단가 5~10억 · 추천 ★★★★★"
ws4["A2"].font = Font(name="맑은 고딕", italic=True, size=10, color="555555")
ws4.merge_cells("A2:B2")

BMC = [
    ("01 핵심 파트너 (Key Partners)",
     "• Anthropic / OpenAI (foundation 모델 라이선스)\n"
     "• 국내 LLM 스타트업 (KT Mi:dm, Naver HyperCLOVA X — 한국어 도메인)\n"
     "• 법무법인 (학습 데이터 + 도메인 검증)\n"
     "• 한국전자통신연구원 (ETRI) — 평가 표준\n"
     "• 클라우드 (AWS Bedrock / Azure OpenAI / NCP CLOVA Studio)"),
    ("02 핵심 활동 (Key Activities)",
     "• 도메인 데이터 수집·익명화 (회의록·계약서·판결문)\n"
     "• sLLM fine-tune (LoRA/QLoRA, 8B~13B 모델)\n"
     "• RAG 인덱스 구축 (회사별 격리)\n"
     "• 정확도·환각률 정기 평가 (벤치마크)\n"
     "• SI 통합 (Office 365, Confluence, Jira, 사내 ERP)\n"
     "• 컴플라이언스 인증 (ISMS-P, K-FSI)"),
    ("03 핵심 자원 (Key Resources)",
     "• 한국어 도메인 데이터셋 (500K+ 회의록, 100K+ 법무문서)\n"
     "• GPU 인프라 (학습용 A100/H100, 추론용 L4)\n"
     "• ML 엔지니어 + 법무·언어 전문가\n"
     "• ITcen 그룹 사 보안·SI 인력 (300+ 명)\n"
     "• 기존 고객 레퍼런스 (금융권·공공기관)"),
    ("04 가치 제안 (Value Propositions)",
     "• 회의록 작성 시간 80% 절감 (1시간 회의 → 5분 검토)\n"
     "• 계약서 핵심 리스크 자동 추출·태깅 (검토 누락 방지)\n"
     "• 한국어·법률 도메인 특화 (범용 GPT-4 대비 정확도 +25%)\n"
     "• On-premise / VPC 격리 (민감정보 외부 유출 방지)\n"
     "• ISMS-P / 클라우드보안인증 (CSAP) 호환"),
    ("05 고객 관계 (Customer Relationships)",
     "• B2B 직접 영업 (CIO/CTO 대상)\n"
     "• 연 단위 SaaS 라이선스 + SI 통합 비용\n"
     "• 전담 고객지원팀 (CSM) — 분기 정기 리뷰\n"
     "• 사용자 피드백 기반 모델 재학습 (RLHF)\n"
     "• 사용자 커뮤니티·교육 (반기 컨퍼런스)"),
    ("06 채널 (Channels)",
     "• ITcen 그룹 영업망 (위즈노바 / 시큐어 / 클라우드 자회사)\n"
     "• 공공 조달 (나라장터·디지털서비스몰)\n"
     "• 파트너 SI (삼성SDS·LG CNS·SK C&C 컨소시엄)\n"
     "• 디지털 마케팅 (LinkedIn·산업별 컨퍼런스)\n"
     "• Microsoft·Google·AWS 마켓플레이스 listing"),
    ("07 고객 세그먼트 (Customer Segments)",
     "• 1차: 대형 금융권 (은행·증권·보험 — 회의록 + 컴플라이언스)\n"
     "• 2차: 법무법인 + 기업 법무팀 (계약서 검토)\n"
     "• 3차: 공공기관 (회의록 의무 작성)\n"
     "• 4차: 대기업 R&D·기술기획 (특허·기술 문서)\n"
     "• 5차: 컨설팅펌·회계법인 (인사이트 추출)"),
    ("08 비용 구조 (Cost Structure)",
     "• 모델 학습 GPU 비용 (월 5천만~1억)\n"
     "• 추론 인프라 (월 3천만~7천만, 사용량 비례)\n"
     "• Foundation 모델 라이선스 (Anthropic/OpenAI)\n"
     "• ML 엔지니어 인건비 (10명 × 1.2억 = 12억/년)\n"
     "• 보안·컴플라이언스 인증 (연 5천만)\n"
     "• 영업·마케팅 (연 매출 15%)"),
    ("09 수익 흐름 (Revenue Streams)",
     "• 연간 SaaS 라이선스 (사용자 1000명 × 30만원 = 3억/사)\n"
     "• 초기 SI 통합 비용 (사당 2~5억)\n"
     "• 도메인 fine-tune 추가 비용 (사당 1~3억)\n"
     "• On-premise 라이선스 (사당 5~15억, 3년)\n"
     "• API 사용량 과금 (외부 호출 1k 당 5만원)\n"
     "• 컨설팅·교육 (시간당 50만)"),
]

ws4.cell(row=4, column=1, value="9 항목").fill = HEADER_FILL
ws4.cell(row=4, column=1).font = HEADER_FONT
ws4.cell(row=4, column=2, value="내용").fill = HEADER_FILL
ws4.cell(row=4, column=2).font = HEADER_FONT
for col in range(1, 3):
    ws4.cell(row=4, column=col).alignment = CENTER
    ws4.cell(row=4, column=col).border = BORDER

for i, (title, body) in enumerate(BMC, 5):
    ws4.cell(row=i, column=1, value=title).font = CAT_FONT
    ws4.cell(row=i, column=1).fill = CAT_FILL
    ws4.cell(row=i, column=1).alignment = Alignment(vertical="top", wrap_text=True)
    ws4.cell(row=i, column=2, value=body).font = NORMAL
    ws4.cell(row=i, column=2).alignment = WRAP
    for col in range(1, 3):
        ws4.cell(row=i, column=col).border = BORDER
    ws4.row_dimensions[i].height = 100

ws4.column_dimensions["A"].width = 30
ws4.column_dimensions["B"].width = 90

# ═══════════════════════════════════════════════════════════
# 저장
# ═══════════════════════════════════════════════════════════
wb.save(OUT_FILE)
print(f"✅ 생성 완료: {OUT_FILE}")
print(f"   파일 크기: {OUT_FILE.stat().st_size / 1024:.1f} KB")
print(f"   시트: 1.ROI매트릭스 / 2.100아이디어 / 3.제출양식 / 4.BMC예시-2번")
