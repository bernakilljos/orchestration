# LMS & E-learning 공통 도구모음 (80+ tools)

> **용도**: 온라인 교육·강의·학습 플랫폼 구축 시 참고
> **범위**: LMS 플랫폼 ~ 인증서 ~ AI 튜터 ~ 한국 교육 서비스
> **관리**: orchestration_v1 reference (sync 대상 아님)

---

## 1. LMS 플랫폼 (Learning Management System)

| 도구 | 언어 | 특징 | 라이선스 | 설치 |
|------|------|------|---------|------|
| **Moodle** | PHP | 오픈소스 LMS (전 세계 300M 사용자), 활성 커뮤니티 | AGPL | `docker run -d moodle:latest` |
| **Canvas LMS** | Ruby on Rails | 클라우드 기반, 교육기관 인기 (MIT, Stanford), API 풍부 | Proprietary | API: `canvas.instructure.com` |
| **Open edX** | Python/Django | edX 재단 오픈소스, MOOC 플랫폼 기반 | AGPL | `docker-compose up -d` |
| **Chamilo** | PHP | Moodle 보다 경량, SCORM 완벽 지원 | LGPL | `docker run chamilo/chamilo:latest` |
| **ILIAS** | PHP | 독일발 LMS, 기업 교육 강점 | AGPL | `docker run ilias/ilias` |
| **Sakai** | Java | 한국 대학 다수 도입 (서울대 등), 커뮤니티 판 활성 | AGPL | `docker run sakai/sakai` |
| **NextCloud Schooltool** | PHP | 파일공유 + 교실 관리 (경량) | AGPL | `docker run nextcloud:latest` |
| **Dokeos (구 Chamilo 호환)** | PHP | SCORM/LTI 호환, 코스 마이그레이션 가능 | LGPL | 상용 호스팅 |

---

## 2. 코스 빌더 (Course Authoring)

| 도구 | 형태 | 특징 | 가격 | API |
|------|------|------|------|-----|
| **Teachable** | SaaS | 노코드 코스 빌더, 결제 통합 완벽, 초보자 친화 | $99/월+ | REST API |
| **Thinkific** | SaaS | 워드프레스 같은 UX, 한국 에이전시 많음 | $79/월+ | REST + Zapier |
| **Podia** | SaaS | 디지털상품 + 커뮤니티 번들, 콘텐츠 크리에이터 선호 | $39/월+ | Webhook |
| **Kajabi** | SaaS | 이메일 마케팅 + 코스 + 애플리케이션 올인원 | $119/월+ | REST API |
| **LearnDash** | WordPress 플러그인 | WordPress 기반 (WooCommerce 통합), 한국 많음 | $199/년+ | PHP Hooks, REST API |
| **LifterLMS** | WordPress 플러그인 | WordPress 경량 LMS, 드래그앤드롭 | $99/년+ | REST API |
| **Udemy for Business** | SaaS | 수백만 강의 라이브러리, B2B 엔터프라이즈 | 요청 시 | API 제한적 |
| **Skillshare** | SaaS | 크리에이티브 강의 특화, 구독 모델 | 협력사만 | 제한적 |

### 설치 예 (WordPress LearnDash)
```bash
# WordPress + LearnDash + WooCommerce 스택
docker run -d --name wordpress wordpress:latest -e WORDPRESS_DB_HOST=mysql:3306
# 플러그인 설치: LearnDash, WooCommerce, Elementor
wp plugin install learndash --activate
wp plugin install woocommerce --activate
```

---

## 3. SCORM & xAPI (표준화된 학습 추적)

| 표준 | 용도 | 특징 | npm/pip | 설명 |
|------|------|------|---------|------|
| **SCORM 1.2 / 2004** | LMS 콘텐츠 호환성 | "학습 객체"의 시작/종료/점수/시간 추적 | `scorm-parser` (npm) | LMS ↔ 강의 콘텐츠 표준 (ADDIE 모델) |
| **xAPI (Tin Can)** | 광범위 학습 데이터 | SCORM 보다 유연, 모바일·offline 추적 | `tincan.js` (npm) | "I did X" 문장형 학습 추적 |
| **cmi5** | xAPI 위의 표준화 | SCORM 규정준수 + xAPI 유연성 | `cmi5.js` (npm) | 차세대 SCORM (AICC 컨소시엄) |
| **LTI** | LMS 통합 | "Single Sign-On + 콘텐츠 심임" (Canvas ↔ 외부 도구) | `ltijs` (npm) | 교실 관리 + 콘텐츠 상호 운용성 |

### SCORM 플레이어 (npm)
```bash
npm install scorm-cloud-xapi  # Rustici Software 클라우드 기반
npm install scorm-player      # 오픈소스 SCORM 플레이어
npm install tincan-player     # xAPI 기반 플레이어
```

### Python xAPI 클라이언트
```bash
pip install tincan            # TinCan 라이브러리
pip install xapi-py           # xAPI 강화판
```

---

## 4. 퀴즈 & 평가 도구

| 도구 | 형태 | 특징 | API | 한국 |
|------|------|------|-----|------|
| **H5P** | 오픈소스 | 60+ 콘텐츠 유형 (퀴즈, 비디오 상호작용 등), 모든 LMS 통합 가능 | REST API, Webhook | 한국 에이전시 多 |
| **Quizlet** | SaaS | 클래시 + 모바일, 학생 자율학습 강점 | REST API | 국내 고등학생 必 |
| **Kahoot!** | SaaS | 게임형 퀴즈 (라이브 + 자가 페이스), 참여도 극대 | REST API | 학원/학교 인기 |
| **Google Forms** | SaaS | 무료, 엑셀 자동 저장, 학급 관리 X | Apps Script | 국내 교사 多 |
| **Typeform** | SaaS | 아름다운 UI, conditional logic, 하지만 교육용 아님 | REST API | 설문 전문 |
| **Testportal** | 웹 | SCORM 완벽 호환, 시간제한, 점수 즉시 조회 | API 제한적 | 기업 시험 |

### H5P npm
```bash
npm install h5p-core           # H5P 엔진
npm install h5p-editor-core    # 에디터
npm install h5p-express        # Express 통합
```

### Quizlet API
```bash
# REST API (학생 데이터만 접근)
curl https://api.quizlet.com/2.1/sets/{setId}?access_token=$TOKEN
```

---

## 5. 동영상 강의 플랫폼

| 도구 | 특징 | 스트리밍 | 분석 | 가격 |
|------|------|---------|------|------|
| **Vimeo OTT** | 프리미엄 화질, 자막, 오프라인 | HLS, DASH | 재생시간·완료율·클릭맵 | $75+/월 |
| **Wistia** | 비디오 마케팅 특화, 호버카드, CTA 삽입 | HLS, Hls.js | 히트맵, 클릭추적 | $99+/월 |
| **Loom** | 화면녹화 + 비디오 메시징, 간편 공유 | WebRTC | 기본 분석 | $12+/월 |
| **Panopto** | 기업/교육 LMS 강점, 자동 자막, 검색 가능 | RTMP | 정교한 분석 | 요청 시 |
| **Kaltura** | 대규모 미디어 플랫폼, 자막 자동생성 | HLS, Dash | 정교함 | 엔터프라이즈 |
| **YouTube / YouTube for Education** | 무료, 재플리스트, 댓글 | HLS | 기본 | 무료 |

### Vimeo API (Python)
```bash
pip install vimeo               # Vimeo 공식 SDK
curl https://api.vimeo.com/videos/{video_id}?access_token=$TOKEN
```

### Loom API
```bash
# 비디오 생성 및 메타데이터 조회
curl https://api.loom.com/api/user \
```

---

## 6. 화이트보드 & 협업 도구

| 도구 | 형태 | 실시간 협업 | 수출 | 교육용 |
|------|------|-----------|------|--------|
| **Excalidraw** | 오픈소스 | ✅ (협업링크) | SVG/PNG/JSON | ✅ 교실용 |
| **tldraw** | 오픈소스 | ✅ (구축 필요) | SVG/JSON | ✅ 자체 호스팅 |
| **Miro** | SaaS | ✅ (실시간) | PNG/PDF/SVG, API 내보내기 | ✅ 엔터프라이즈 |
| **FigJam** (Figma 일부) | SaaS | ✅ (실시간) | 디자인+보드 | ✅ 팀협업 |
| **Jamboard** (deprecated) | SaaS | ✅ Google Meet 통합 | Google Drive → PDF | ✅ 학교 |
| **OneNote** | 클라우드 | ✅ (MSOffice 통합) | ONETNOTE, PDF | ✅ 교실 공책 |

### Excalidraw 호스팅
```bash
# 자체 호스팅
docker run -d -p 80:3000 excalidraw/excalidraw:latest

# 또는 npm
npm install @excalidraw/excalidraw
npm install excalidraw-cli
```

### Miro API
```bash
npm install @mirohq/miro-api   # 보드, 위젯 관리
curl https://api.miro.com/v2/boards \
```

---

## 7. 코딩 교육 & 실습 환경

| 도구 | 형태 | 언어 | 교실 기능 | 설치 |
|------|------|------|----------|------|
| **CodeSandbox** | SaaS | JS, TS, Vue, React, Next.js 등 | ✅ (소셜 기능 제한) | https://codesandbox.io |
| **StackBlitz** | SaaS | Node.js + 브라우저 IDE | ✅ (팀 워크스페이스) | https://stackblitz.com |
| **Replit** | SaaS | 100+ 언어, 협업, 호스팅 포함 | ✅ (교실 + 숙제) | https://replit.com/teams |
| **Judge0** | 오픈소스 | 60+ 언어 (C, Python, Java 등) | ❌ (API 기반) | `docker run -d judge0/judge0:latest` |
| **Codewars** | SaaS | 다양한 언어 kata (문제), 랭킹 | ✅ (워리어 갤럽) | API: https://www.codewars.com/api |
| **LeetCode** | SaaS | 알고리즘 특화, 면접 준비 | ❌ (개인학습) | Premium API 제한적 |
| **HackerRank** | SaaS | 기술 평가 + 학습, 채용공고 연결 | ✅ (기업 교실) | API: https://www.hackerrank.com |
| **GitHub Classroom** | SaaS (GitHub) | Git 기반 과제, 자동 채점 | ✅ (교실+과제 자동화) | 무료 (GitHub) |

### Replit 교실 API
```bash
pip install replit             # Python SDK
curl https://replit.com/api/teams/{teamId}/members \
```

### Judge0 설치 및 사용
```bash
# Docker Compose
docker run -d \
  --name judge0_db -e POSTGRES_PASSWORD=judge0 postgres:latest
docker run -d \
  --name judge0_api \
  --link judge0_db \
  judge0/judge0:latest

# Python 클라이언트
pip install judge0-api
curl https://judge0.com/api/submissions \
  -d '{"language_id": 71, "source_code": "print(\"hello\")"}'  # Python3
```

### GitHub Classroom
```bash
# 자동화 (GitHub CLI)
gh classroom create --name "CS101"
gh classroom add-assignment --name "Assignment1"
# 자동 채점: GitHub Actions 워크플로우
cat > .github/workflows/autograder.yml << EOF
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: python test_solution.py
EOF
```

---

## 8. AI 튜터 & 적응형 학습

| 도구 | 특징 | 기술 | API | 한국 |
|------|------|------|-----|------|
| **Khan Academy** | 무료 콘텐츠 라이브러리 (수학, 과학, 역사) | 학습 진행도 추적 | REST API (제한적) | 영어 중심 |
| **Khan Academy Mastery System** | 각 학생별 맞춤 학습 경로 | ML 기반 진도율 예측 | API (학교 구독) | 구독 필요 |
| **Duolingo** | 언어학습 게이미피케이션 | Spaced repetition, AI 문법 교정 | REST API | 앱 기반 |
| **Quizlet** (AI 강화) | 학생 생성 학습세트 + AI 튜터링 | GPT 기반 설명, 문제 생성 | REST API | 국내 활성 |
| **Coursera** | MOOC 플랫폼 + 학위, 자격증 | Peer 리뷰, 머신러닝 기반 추천 | API 제한적 | 일부 한국어 |
| **edX** | 대학 강의 (MIT, Harvard 등) | Open edX (오픈소스) | 직접 호스팅 | STEM 중심 |
| **Tutor.com** | 실시간 온라인 튜터링 | AI 매칭 + 사람 튜터 | API 없음 | 영어 중심 |
| **Squirrel AI** | 중국발 AI 적응형 튜터 | 딥러닝 기반 맞춤 경로 | API 제한 | 중국/동아시아 |

### Khan Academy API (Python)
```bash
pip install khan-api           # 비공식 라이브러리
curl https://www.khanacademy.org/api/internal/user \
```

### Duolingo API
```bash
pip install duolingo           # 비공식 라이브러리
# 공식 API 없음 (학교/기업 협력사만)
```

---

## 9. 인증서 & 배지 발급

| 도구 | 형식 | 추적성 | 가격 | 통합 |
|------|------|--------|------|------|
| **Credly** | 디지털 배지 + 인증서 | Blockchain 검증 (Accredible과 다름) | $1-2/배지 | Salesforce, Canvas LMS |
| **Accredible** | 블록체인 인증서 | 위변조 방지, 공개 검증 | $5-10/인증서 | Moodle, Canvas |
| **Badgr** | Open Badges 표준 | 오픈 표준, 자체호스팅 가능 | 오픈소스 무료 | 모든 LMS |
| **Open Badges** | 표준 형식 (JSON-LD) | 이동 가능 배지 (LinkedIn 등으로 공유) | 오픈 표준 | 모든 플랫폼 호환 |
| **Youracclaim** (Credly 인수) | 취업 배지 | LinkedIn 직접 추가 | Credly 동일 | HR 연계 |
| **Google Career Certificates** | 구글 자격증 | Coursera 호스팅 | 무료/유료 혼합 | Coursera API |

### Badgr 자체 호스팅
```bash
# Docker
docker run -d \
  --name badgr \
  -e DB_NAME=badgr \
  -e DB_USER=badgr \
  badgr/badgr-server:latest

# Open Badges JSON 예
{
  "name": "Python 기초 이수",
  "description": "Python 입문 과정 완료",
  "image": "https://example.com/badge.png",
  "criteria": "점수 70점 이상"
}
```

### Credly API
```bash
curl https://api.credly.com/v1/organizations/{orgId}/badges \
```

---

## 10. 한국 교육 플랫폼 & API

| 서비스 | 용도 | API | 특징 |
|--------|------|-----|------|
| **EBS (교육방송)** | 초중고 강의 (무료) | REST API | 수능, 교과 영상 |
| **K-MOOC** | 대학수준 온라인 강좌 | API (제한적) | MOOC (교육부) |
| **학점은행제** | 비학위→학위 변환 | 국가평생교육진흥원 API | 학점 인정 |
| **한국교육학술정보원 (KERIS)** | 교육통계, 기관정보 | 공공데이터포털 API | 학교·학과 데이터 |
| **커넥츠** | 한국 온라인 강의 플랫폼 | 자체 API | 직업훈련 특화 |
| **잡코리아 러닝** | 직업교육 + 채용연계 | API 제한 | HR 통합 |
| **폴라리스 오피스 교육용** | 한글, 스프레드시트 협업 | API 없음 | Office 호환 |
| **라이브 아카데미** | 유튜브 기반 한국 영어교육 | 없음 | 크리에이터 모델 |

### EBS API (공공데이터포털)
```bash
# 공공데이터포털에서 인증키 신청 필요
curl "http://www.ebslang.co.kr/api/search?apiKey=$API_KEY&query=영어" \
  -H "Accept: application/json"
```

### 학점은행제 조회
```bash
# 국가평생교육진흥원 API (한국평생교육진흥원)
curl "https://api.nile.or.kr/credit/course?searchType=subjectName&subjectName=파이썬" \
```

### KERIS 교육통계
```bash
# 공공데이터포털 (한국교육학술정보원)
curl "https://kosis.kr/openapi/Param/statisticsParameterData?method=getList&apiKey=$API_KEY" \
  -d "orgId=101&tblId=DT_1CO002"
```

---

## 11. 종합 비교 표

| 기준 | LMS 추천 | 코스빌더 추천 | 평가 추천 | 실습 추천 | 비디오 추천 |
|------|---------|-------------|---------|---------|-----------|
| **무료** | Moodle, Open edX | LearnDash + WP | Google Forms, H5P | Judge0, GitHub Classroom | YouTube |
| **한국 친화적** | Moodle, Sakai, Chamilo | LearnDash, Thinkific | Quizlet, H5P | Replit, GitHub Classroom | Vimeo |
| **엔터프라이즈** | Canvas LMS, Sakai | Kajabi, Podia | Kahoot Enterprise | HackerRank, Judge0 Cloud | Panopto, Kaltura |
| **AI 강점** | Open edX (LMS framework) | Teachable (자동추천) | Quizlet AI, Khan Academy | Replit AI (최신) | Loom (스크린분석) |
| **SCORM 호환** | 모두 (H5P도 지원) | Chamilo, Dokeos | H5P 필수 | 대부분 미지원 | 미지원 |

---

## 참조

- **SCORM 표준**: https://scorm.com/
- **xAPI 스펙**: https://xapi.com/
- **LTI**: https://www.imsglobal.org/activity/learning-tools-interoperability
- **H5P 콘텐츠**: https://h5p.org/
- **Khan Academy 데이터**: https://www.khanacademy.org/api
- **Moodle Plugin Directory**: https://moodle.org/plugins/
- **EBS API 신청**: https://www.data.go.kr/
- **GitHub Classroom 가이드**: https://classroom.github.com/
