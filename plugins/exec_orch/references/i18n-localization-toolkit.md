# i18n & Localization Toolkit

> **목적**: 다국어 지원 · 로케일 최적화 · 번역 관리 공통 도구 모음 (70+ 도구)
> **적용 범위**: 웹 애플리케이션 · 모바일 앱 · 데스크톱 · 문서 · 마이크로서비스
> **카테고리**: 10개 영역 · 번역 · 프레임워크 · 관리 · 로케일 · RTL · 폰트 · NLP

---

## 1. 기계 번역 API (Machine Translation)

### 주요 서비스 비교

| 서비스 | 언어 | 가격 | 품질 | API | 한국어 |
|---|---|---|---|---|---|
| **Google Translate API** | 130+ | $15/백만 자 | 높음 | REST · gRPC |  우수 |
| **DeepL API** | 30+ | €0.002/단어 (Pro) | 최고 (특히 문학) | REST |  우수 |
| **Microsoft Azure Translator** | 90+ | $15/백만 자 | 높음 | REST |  좋음 |
| **Amazon Translate** | 70+ | $15/백만 단위 | 높음 | AWS SDK · REST |  좋음 |
| **Naver Papago API** | 13 (한국 최적) | 무료 (일일 5만 자) | 최고 (한국어↔영어) | REST |  최고 |
| **Kakao i Translator** | 한국어↔주요 9언어 | 무료 (일일 10만 자) | 높음 | REST |  최고 |
| **Claude API (with i18n prompt)** | 모든 언어 | $3-15/백만 토큰 | 문맥 우수 | REST |  우수 |
| **Open Source: LibreTranslate** | 20+ | 자체호스트 무료 | 중간 | REST |  가능 |
| **Hugging Face Transformers** | 모든 언어 | 오픈소스 무료 | 모델 의존 | Python |  지원 |

### 한국어 최적화 전략
```bash
# 우선순위: Naver Papago (최고 품질) → Kakao i (백업) → Google (fallback)
# 라운드로빈으로 quota 분산

# 설치
npm install axios  # REST API 호출용
pip install google-cloud-translate  # Python Google
pip install deepl  # Python DeepL
```

---

## 2. i18n 프레임워크 (Frontend)

### 프레임워크별 비교

| 프레임워크 | 라이브러리 | 특징 | 파일 포맷 | 설치 |
|---|---|---|---|---|
| **React** | `react-i18next` | 훅 기반 · 성숙도 · Suspense 지원 | JSON · YAML | `npm install react-i18next i18next` |
| **React** (가벼움) | `i18next-http-backend` | 동적 로딩 · 성능 최적화 | JSON | `npm install i18next-http-backend` |
| **Vue 3** | `vue-i18n` | Composition API · 플러그인 · 로케일 스위칭 | JSON | `npm install vue-i18n@9` |
| **Next.js** | `next-intl` | App Router 네이티브 · 라우팅 통합 | JSON | `npm install next-intl` |
| **Next.js** (레거시) | `next-i18next` | Pages Router · SSR 지원 | JSON | `npm install next-i18next` |
| **Nuxt** | `@nuxtjs/i18n` | SSR · 라우팅 통합 · SEO | JSON | `npm install @nuxtjs/i18n` |
| **Angular** | `@ngx-translate/core` | 트리 셰이킹 · AOT 컴파일 | JSON | `npm install @ngx-translate/core` |
| **Svelte** | `svelte-i18n` | 리액티브 · 자동 스크립트 인젝션 | JSON | `npm install svelte-i18n` |
| **Vanilla JS** | `FormatJS` (Intl API) | 내장 `Intl` 확장 · 폴리필 | JSON | `npm install intl` |
| **Flutter** | `intl` package | Intl API 래퍼 · 로케일 데이터 | ARB | `flutter pub add intl` |
| **React Native** | `i18n-js` | 간단함 · 백그라운드 작업 | JSON | `npm install i18n-js` |

### 빠른 선택
- **React**: react-i18next (권장)
- **Vue**: vue-i18n
- **Next.js**: next-intl (App Router)
- **Angular**: @ngx-translate
- **가벼움**: vanilla Intl API + 간단한 JSON

---

## 3. 번역 관리 플랫폼 (TMS)

### 클라우드 기반 (팀 협업)

| 플랫폼 | 가격 | 특징 | 워크플로우 | 한국어 |
|---|---|---|---|---|
| **Crowdin** | 프로 $99/월 | 커뮤니티 번역자 · AI 제안 · 검증 | 자동 PR |  최고 |
| **Lokalise** | 팀 $99/월 | 개발자 친화 · CLI · Git sync | 자동 push |  우수 |
| **Phrase (구 Phraseapp)** | 엔터프라이즈 | 엔터프라이즈급 · 완벽한 번역 추적 | 고급 워크플로우 |  지원 |
| **Transifex** | 프로 $99/월 | 오픈소스 친화 · 커뮤니티 · AI | 자동 동기화 |  지원 |
| **POEditor** | 기본 무료 | 직관적 · 소규모 팀 · Slack 통합 | 수동 다운로드 |  지원 |
| **Weblate** | 셀프호스트 무료 | 오픈소스 · 커뮤니티 · AGPL | Git 기반 |  최고 |
| **Tolgee** | 무료 (호스팅 $49) | 개발자 친화 · In-context 번역 · API 우수 | 자동 commit |  지원 |
| **OneSky** | 기본 무료 | 간단함 · 앱 중심 · Slack 통합 | 자동 동기화 |  지원 |

### 선택 기준
| 시나리오 | 추천 |
|---|---|
| **스타트업** | Tolgee 또는 Crowdin (커뮤니티 활용) |
| **팀 협업** | Lokalise (개발자 친화) |
| **오픈소스** | Weblate (자체호스트) |
| **엔터프라이즈** | Phrase |
| **한국 중심** | Crowdin + Naver Papago (자동 초안) |

### 타이포그래피 가이드 (TMS 체크리스트)
```yaml
번역 검증:
  - 문자열 길이: 원본 대비 120-180% (언어별)
  - RTL (아랍어/히브리어): 자동 레이아웃 재정렬 확인
  - 숫자 형식: 1,234.56 (EN) vs 1.234,56 (DE)
  - 날짜 형식: MM/DD/YYYY (US) vs DD/MM/YYYY (EU) vs YYYY년 M월 D일 (KR)
  - 통화: $100 (USD) vs 100 EUR vs ₩100,000 (KRW)
  - 변수 ({name}, {count}): 누락·중복 감지
```

---

## 4. 로케일 & 날짜·시간·숫자 포매팅

### JavaScript 라이브러리

```bash
npm install date-fns day.js luxon intl-messageformat
```

| 라이브러리 | 용도 | 문법 | 크기 |
|---|---|---|---|
| **Intl API** (내장) | 날짜 · 숫자 · 통화 · 복수형 | `new Intl.DateTimeFormat('ko-KR')` | 0 (내장) |
| **date-fns** | 날짜 · 포매팅 · 로케일 파일 | `format(date, 'yyyy-MM-dd', { locale: ko })` | 14 KB (tree-shake) |
| **Day.js** | 경량 날짜 | `dayjs().locale('ko').format('YYYY-MM-DD')` | 2 KB |
| **Luxon** | 고급 날짜 · 타임존 · 기간 | `DateTime.now().setLocale('ko').toFormat('yyyy년 M월 d일')` | 40 KB |
| **numeral.js** | 숫자 포매팅 | `numeral(1234.56).format('0,0.00')` | 8 KB |
| **currency.js** | 통화 연산 | `new Currency(100, { symbol: '₩' })` | 3 KB |

### 한국어 특화 예제
```javascript
// 내장 Intl API
const formatter = new Intl.DateTimeFormat('ko-KR', {
  year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
});
console.log(formatter.format(new Date())); // "2026년 5월 20일 수요일"

// 숫자
const numFormatter = new Intl.NumberFormat('ko-KR', { style: 'currency', currency: 'KRW' });
console.log(numFormatter.format(100000)); // "₩100,000"

// 복수형 (한국어는 count 기반 분기만)
const msgFormatter = new Intl.PluralRules('ko-KR');
const rule = msgFormatter.select(5); // 항상 'other'
```

### Python 로케일 (백엔드)
```bash
pip install babel pytz pyarrow
```

```python
from babel.dates import format_date, format_currency
from babel.numbers import format_number

format_date(date(2026, 5, 20), locale='ko_KR')  # '2026년 5월 20일'
format_currency(100000, 'KRW', locale='ko_KR')  # '₩100,000'
format_number(1234567.89, locale='ko_KR')  # '1,234,567.89'
```

---

## 5. RTL (Right-to-Left) 지원

### RTL 언어
아랍어, 히브리어, 페르시아어, 우르두어 등

### CSS 자동화

```bash
npm install tailwindcss-rtl postcss-rtlcss
```

**Tailwind RTL 플러그인**:
```javascript
// tailwind.config.js
module.exports = {
  plugins: [require('tailwindcss-rtlcss')],
};

// 사용: dir="rtl" attribute on <html>
// Tailwind가 자동으로 margin-left → margin-right 변환
```

**PostCSS RTL**:
```javascript
// postcss.config.js
module.exports = {
  plugins: {
    'postcss-rtlcss': {}
  }
};
```

### HTML 구조
```html
<html dir="ltr" lang="en">  <!-- 또는 dir="rtl" lang="ar" -->
  <body>
    <nav><!-- 자동 flex-reverse --></nav>
    <main style="text-align: start;"><!-- start = left (LTR) / right (RTL) --></main>
  </body>
</html>
```

### 금지 사항
```css
/*  금지 */
.sidebar { margin-left: 20px; }

/*  허용 (RTL 안전) */
.sidebar { margin-inline-start: 20px; }
```

---

## 6. 다국어 폰트

### 웹 폰트 (Google Fonts + 특화)

| 폰트 | 지원 언어 | 용도 | 라이선스 |
|---|---|---|---|
| **Google Fonts: Noto Sans** | 140+ 언어 · CJK 포함 | 범용 · 모든 스크립트 | OFL |
| **Google Fonts: Roboto** | 라틴 · 그리스 · 키릴 | 서양 언어 표준 | Apache 2.0 |
| **Google Fonts: Noto Serif** | CJK · 동아시아 세리프 | 문서 · 출판 | OFL |
| **Pretendard** (한국) | 한글 · 라틴 · 기호 | 한글 최적화 (무료) | OFL |
| **IBM Plex** | 다국어 · 8가중치 | 기업용 · 높은 품질 | OFL |
| **Adobe Fonts** | 모든 언어 | 프로페셔널 · 유료 | Adobe Fonts 라이선스 |
| **Noto Sans JP** | 일본어 + 라틴 | 일본 최적화 | OFL |
| **Source Han Sans** | 한중일 + 라틴 | CJK 전문 | OFL |

### 설치 (HTML)
```html
<!-- Google Fonts CDN -->
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap" rel="stylesheet">

<!-- 한국: Pretendard -->
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/variable/pretendardvariable.css" rel="stylesheet">

<!-- 가변 폰트 (모든 가중치) -->
<style>
  body { font-family: 'Noto Sans Variable', 'Pretendard Variable', sans-serif; }
</style>
```

### CSS 폴백 체인
```css
/* 좌측부터 우선순위 */
body {
  font-family: 'Pretendard Variable', 'Noto Sans', 'Segoe UI', system-ui, sans-serif;
  /* 한글 → 다국어 → 시스템 */
}

@supports (font-variation-settings: 'wght' 100) {
  body { font-family: 'Noto Sans Variable', 'Pretendard Variable', sans-serif; }
}
```

---

## 7. 자연어 처리 (NLP) — 다국어

### Python NLP 스택

```bash
pip install spacy konlpy mecab transformers polyglot
```

| 라이브러리 | 용도 | 언어 | 모델 |
|---|---|---|---|
| **spaCy** (multilingual) | 토큰화 · NER · 품사 태깅 | 25+ | `xx_sent_ud_sm` |
| **KoNLPy** | 한글 전문 · 형태소 분석 | 한국어 | Okt · Komoran · Janome |
| **MeCab** (일본) | 일본어 형태소 분석 | 일본어 | 사전 기반 |
| **Jieba** (중국) | 중국어 분절 | 중국어 (간체/정체) | 통계 기반 |
| **Transformers (Hugging Face)** | 다국어 모델 · 감정 분석 | 모든 언어 | `xlm-roberta` · `mBERT` |
| **NLTK** | 영어 중심 · 리소스 풍부 | 영어 + 주요 언어 | 다양 |
| **polyglot** | 언어 감지 · 감정 분석 | 130+ | 자동 감지 |

### 한국어 예제
```python
from konlpy.tag import Okt
from transformers import pipeline

# 형태소 분석
okt = Okt()
tokens = okt.morphs('자연어 처리는 재미있습니다')
# ['자연어', '처리', '는', '재미있', '습니다']

# 감정 분석 (다국어 모델)
classifier = pipeline('sentiment-analysis', model='nlptown/bert-base-multilingual-uncased-sentiment')
result = classifier('훌륭한 서비스입니다')
# [{'label': 'positive', 'score': 0.99}]
```

---

## 8. 콘텐츠 관리 (CMS) i18n

| CMS | i18n 기능 | 워크플로우 | 한국어 |
|---|---|---|---|
| **Contentful** | 로케일별 필드 · API 쿼리 | GraphQL / REST |  지원 |
| **Strapi** | 플러그인 기반 i18n · 역할 기반 | UI 직관적 |  지원 |
| **Sanity** | 로케일 필드 · 문서 참조 | Studio 시각적 |  지원 |
| **Directus** | 언어별 행 · 번역 추적 | 데이터베이스 네이티브 |  지원 |
| **Drupal** | 모듈 기반 (언어 · i18n) | 엔터프라이즈급 |  최고 |
| **WordPress** | WPML / Polylang 플러그인 | 플러그인 의존 |  지원 |

### 한국 운영 체크리스트
```yaml
콘텐츠 검수:
  - 한글 맞춤법 (문화체육관광부 표준)
  - 경어 톤 (존댓글 vs 반말)
  - 로컬 관습 (날짜 · 호칭 · 경어 등급)
  - 문화 민감도 (색상 · 상징 · 정치)
```

---

## 9. 품질 보증 (QA) & 검증

### 자동화 도구

```bash
npm install i18n-tasks eslint-plugin-i18n pseudo-localization
pip install i18n-linter
```

| 도구 | 기능 | 언어 | 설치 |
|---|---|---|---|
| **i18n-tasks** | 미사용 키 · 누락 키 · 일관성 | Ruby · JS | `npm install i18n-tasks` |
| **eslint-plugin-i18n** | ESLint 통합 · 누락 감지 | JavaScript | `npm install eslint-plugin-i18n` |
| **pseudo-localization** | 가짜 번역으로 UI 테스트 | 모든 언어 | `npm install pseudo-localization` |
| **zhlint** | 중국어 표준 검증 | 중국어 | `npm install zhlint` |
| **hangul-js** | 한글 초성·중성·종성 분석 | 한국어 | `npm install hangul-js` |

### 가짜 번역 테스트 (Pseudo-localization)
```javascript
// 원본: "Hello World"
// 가짜: "[Ĥéļļő Ŵőŕļď]" (길이 & 특수문자로 레이아웃 테스트)

import { pseudolocalize } from 'pseudo-localization';
const fakeText = pseudolocalize('Hello World');
// UI 레이아웃이 확장된 텍스트에서도 깨지지 않는지 확인
```

### CI/CD 통합
```yaml
# GitHub Actions
name: i18n-validation
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm install i18n-tasks
      - run: npx i18n-tasks check-usage
      - run: npx i18n-tasks check-keys
```

---

## 10. 한국어 특화 도구 & 서비스

### 공식 표준
- **한글맞춤법** (문화체육관광부): https://speller.korean.go.kr/
- **표준국어대사전**: https://stdict.korean.go.kr/
- **한글 자모 분리/결합**: `hangul-js` · `jamo`

### 한국 번역 API
```bash
# Naver Papago (최고 품질)
curl -X POST "https://openapi.naver.com/v1/papago/n2mt" \
  -H "X-Naver-Client-Id: $CLIENT_ID" \
  -H "X-Naver-Client-Secret: $SECRET" \
  -d "source=en&target=ko&text=Hello"

# Kakao i Translator
curl -X POST "https://kapi.kakao.com/v1/translate/translate" \
  -d "query=Hello&src_lang=en&target_lang=ko"
```

### 조사 처리 (한국어 문법)
```python
# "김철수가 왔습니다" vs "김철수를 만났습니다"
from josa import josa

name = "김철수"
print(josa.get_josa(name, "이/가"))  # "김철수가"
print(josa.get_josa(name, "을/를"))  # "김철수를"
```

---

## 11. 마이그레이션 경로

### Google Translate → DeepL
```bash
# 데이터 내보내기
gsutil cp -r gs://your-bucket/translations .

# DeepL API 로 일괄 번역
for file in translations/*.json; do
  curl -X POST https://api-free.deepl.com/v1/document \
    -F "file=@$file" \
    -F "target_lang=KO" \
done
```

### i18next → react-i18next (React 마이그레이션)
```javascript
// Before (standalone i18next)
import i18next from 'i18next';
i18next.t('key');

// After (react-i18next)
import { useTranslation } from 'react-i18next';

function Component() {
  const { t } = useTranslation();
  return <p>{t('key')}</p>;
}
```

---

## 12. 성능 최적화

### 번역 파일 로딩 (Code Splitting)
```javascript
// 동적 로딩: 언어 선택 시에만 로드
const loadLanguage = async (lang) => {
  const messages = await import(`./locales/${lang}.json`);
  i18n.setLocaleMessage(lang, messages.default);
};
```

### 청크 최적화
```json
{
  "locale": "ko",
  "common": { "yes": "네", "no": "아니요" },
  "pages": {
    "home": { "title": "홈" },
    "about": { "title": "소개" }
  }
}
```

---

## 13. 비용 최적화

| 시나리오 | 권장 조합 |
|---|---|
| **스타트업 MVP** | react-i18next + Google Sheets (수동) + Naver Papago (초안) |
| **팀 협업** | Tolgee + Naver Papago (AI 제안) |
| **엔터프라이즈** | Phrase + DeepL API (품질) + 한국어 리뷰어 |
| **오픈소스** | Weblate + Crowdin (커뮤니티 번역자) |
| **한국 중심** | Kakao i Translator (무료 quota) + POEditor (관리) |

---

## 14. 학습 자료

### 공식 문서
- i18next: https://www.i18next.com/
- react-i18next: https://react.i18next.com/
- next-intl: https://next-intl-docs.vercel.app/
- Crowdin: https://crowdin.com/docs
- Naver Papago: https://developers.naver.com/products/papago
- Kakao i: https://developers.kakao.com/docs/latest/ko/translate/dev-guide

### 커뮤니티
- i18next GitHub Discussions: https://github.com/i18next/i18next/discussions
- Stack Overflow: #i18n #localization #translation

---

**최종 업데이트**: 2026-05-20
