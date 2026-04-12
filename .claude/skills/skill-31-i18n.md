# Skill 31: i18n (다국어)

## 목적
프로젝트의 UI 텍스트를 다국어로 자동 번역/관리한다.
한국어 → 영어/일본어/중국어 동시 지원.

## 트리거
- "다국어", "i18n", "번역", "localization"
- 새 페이지 추가 시 자동 제안

## 실행 흐름

### 1. 텍스트 추출
```
Vue:  {{ $t('key') }} / v-text / placeholder
React: t('key') / <Trans>
HTML:  data-i18n="key"
Python: _('text') / gettext('text')
```

### 2. 번역 파일 구조
```
locales/
  ko.json    {"login.title": "로그인", "login.button": "확인"}
  en.json    {"login.title": "Login", "login.button": "Confirm"}
  ja.json    {"login.title": "ログイン", "login.button": "確認"}
  zh.json    {"login.title": "登录", "login.button": "确认"}
```

### 3. 자동 번역
```
1. 소스 코드에서 한국어 텍스트 추출
2. 키 이름 자동 생성 (페이지.컴포넌트.용도)
3. WebSearch 또는 AI로 번역
4. 코드에서 하드코딩 텍스트 → $t('key') 치환
5. 누락 키 감지 + 리포트
```

### 4. 누락 감지
```
[WARN] 번역 누락:
  ko.json: 45 keys
  en.json: 42 keys (3 missing: login.error, signup.terms, nav.settings)
  ja.json: 40 keys (5 missing)
```

## 출력
- `locales/*.json` — 번역 파일
- `docs/YYYY-MM-DD/i18n-report.md` — 누락/변경 리포트
