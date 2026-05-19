# Public API Toolkit — 무료/공개 API 서비스 카탈로그

> **목적**: 개발 시 바로 사용 가능한 무료 공개 API 총정리
> **참고**: github.com/public-apis/public-apis (300k+ stars)

---

## 1. 영화 / TV / 엔터테인먼트

| API | 설명 | 인증 | 무료 |
|-----|------|------|------|
| **TMDB** | 영화·TV 정보 (포스터, 평점, 배우) | API 키 | ✅ |
| **OMDb** | 영화 검색 (IMDb 데이터) | API 키 | ✅ (1000/일) |
| **TVmaze** | TV 프로그램 정보 | 없음 | ✅ |
| **Jikan** | 애니메이션 (MyAnimeList) | 없음 | ✅ |
| **Spotify** | 음악 검색·재생 | OAuth | ✅ |
| **iTunes Search** | Apple 음악·앱·팟캐스트 | 없음 | ✅ |
| **YouTube Data** | 영상 검색·채널·댓글 | API 키 | ✅ (10000 쿼터/일) |

```python
# TMDB 영화 검색
import requests
r = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={KEY}&query=inception")
movies = r.json()["results"]
```

---

## 2. 요리 / 레시피

| API | 설명 | 무료 |
|-----|------|------|
| **TheMealDB** | 레시피 검색 (카테고리, 재료) | ✅ |
| **Spoonacular** | 레시피 + 영양 정보 + 식단 | ✅ (150 req/일) |
| **Edamam** | 레시피 + 영양소 분석 | ✅ (제한적) |
| **CocktailDB** | 칵테일 레시피 | ✅ |

```python
# TheMealDB
r = requests.get("https://www.themealdb.com/api/json/v1/1/search.php?s=chicken")
```

---

## 3. URL / 링크

| API | 설명 | 무료 |
|-----|------|------|
| **TinyURL** | URL 단축 | ✅ |
| **Bitly** | URL 단축 + 분석 | ✅ (1000/월) |
| **Rebrandly** | 브랜드 링크 | ✅ (500/월) |
| **Short.io** | URL 단축 + 커스텀 도메인 | ✅ (1000/월) |

---

## 4. IP / 위치 / 지도

| API | 설명 | 무료 |
|-----|------|------|
| **ipapi.co** | IP → 위치 (국가, 도시, ISP) | ✅ (30k/월) |
| **ip-api.com** | IP 위치 조회 | ✅ (45/분) |
| **ipinfo.io** | IP 정보 (ASN, 회사) | ✅ (50k/월) |
| **ipgeolocation.io** | IP 지오로케이션 | ✅ (30k/월) |
| **OpenStreetMap Nominatim** | 주소 ↔ 좌표 (지오코딩) | ✅ |
| **Google Maps** | 지도, 경로, 장소 | ✅ ($200 크레딧/월) |
| **Mapbox** | 지도 + 내비게이션 | ✅ (50k 로드/월) |
| **Kakao Map** | 한국 지도 API | ✅ (300k/일) |
| **Naver Map** | 한국 지도 API | ✅ |

```python
# IP 위치 조회
r = requests.get("http://ip-api.com/json/")
print(r.json())  # {"country": "South Korea", "city": "Seoul", ...}
```

---

## 5. 명언 / 랜덤 텍스트

| API | 설명 | 무료 |
|-----|------|------|
| **Quotable** | 랜덤 명언 | ✅ |
| **ZenQuotes** | 영감 명언 | ✅ |
| **API Ninjas Quotes** | 카테고리별 명언 | ✅ |
| **Lorem Ipsum** | 더미 텍스트 | ✅ |
| **Bacon Ipsum** | 음식 더미 텍스트 | ✅ |
| **JSONPlaceholder** | 가짜 REST API (개발용) | ✅ |
| **DummyJSON** | 가짜 데이터 (유저, 상품, 댓글) | ✅ |

```python
# 랜덤 명언
r = requests.get("https://api.quotable.io/random")
print(r.json()["content"])
```

---

## 6. 환율 / 금융

| API | 설명 | 무료 |
|-----|------|------|
| **ExchangeRate-API** | 환율 변환 | ✅ (1500/월) |
| **Open Exchange Rates** | 170+ 통화 환율 | ✅ (1000/월) |
| **Frankfurter** | ECB 환율 (오픈소스) | ✅ |
| **CoinGecko** | 암호화폐 가격 | ✅ |
| **CoinMarketCap** | 암호화폐 시세 | ✅ (제한적) |
| **Alpha Vantage** | 주식 시세 + 기술 지표 | ✅ (25/일) |
| **Yahoo Finance (yfinance)** | 주식·ETF | ✅ |
| **한국은행 경제통계** | 한국 경제 데이터 | ✅ |

```python
# 환율
r = requests.get("https://api.frankfurter.app/latest?from=USD&to=KRW")
print(r.json()["rates"]["KRW"])

# 주식 (yfinance)
pip install yfinance
import yfinance as yf
msft = yf.Ticker("MSFT")
print(msft.info["currentPrice"])
```

---

## 7. 뉴스

| API | 설명 | 무료 |
|-----|------|------|
| **NewsAPI** | 전세계 뉴스 검색 | ✅ (100/일, 개발용) |
| **GNews** | Google 뉴스 API | ✅ (100/일) |
| **MediaStack** | 뉴스 피드 | ✅ (500/월) |
| **The Guardian** | 가디언 기사 | ✅ |
| **New York Times** | NYT 기사 검색 | ✅ |
| **Naver 뉴스 검색** | 한국 뉴스 | ✅ (25000/일) |

---

## 8. 날씨

| API | 설명 | 무료 |
|-----|------|------|
| **OpenWeatherMap** | 날씨 + 예보 | ✅ (60/분) |
| **WeatherAPI** | 날씨 + 천문 | ✅ (1M/월) |
| **Open-Meteo** | 날씨 예보 (오픈소스) | ✅ (무제한) |
| **기상청 API** | 한국 날씨 | ✅ |
| **Visual Crossing** | 과거+현재+예보 | ✅ (1000/일) |

```python
# Open-Meteo (키 불필요!)
r = requests.get("https://api.open-meteo.com/v1/forecast?latitude=37.56&longitude=126.97&current_weather=true")
print(r.json()["current_weather"])
```

---

## 9. AI / ML API

| API | 설명 | 무료 |
|-----|------|------|
| **Anthropic Claude** | LLM API | 유료 ($3/1M 입력) |
| **OpenAI** | GPT-4, DALL-E, Whisper | 유료 |
| **Google Gemini** | Gemini Pro/Flash | ✅ (무료 티어) |
| **Groq** | 초고속 LLM 추론 | ✅ (무료 티어) |
| **Together AI** | 오픈소스 모델 호스팅 | ✅ ($5 크레딧) |
| **Replicate** | AI 모델 실행 | ✅ (무료 크레딧) |
| **Hugging Face Inference** | 50만+ 모델 | ✅ (제한적) |
| **Pollinations** | 이미지 생성 (무료) | ✅ |
| **Stability AI** | Stable Diffusion API | ✅ (25 크레딧) |

---

## 10. 이미지 / 미디어

| API | 설명 | 무료 |
|-----|------|------|
| **Unsplash** | 고품질 사진 | ✅ (50/시간) |
| **Pexels** | 사진 + 비디오 | ✅ (200/시간) |
| **Pixabay** | 사진·일러스트·벡터 | ✅ |
| **Lorem Picsum** | 랜덤 placeholder 이미지 | ✅ |
| **PlaceKitten** | 고양이 placeholder | ✅ |
| **remove.bg** | 배경 제거 | ✅ (50/월) |
| **TinifyPNG** | 이미지 압축 | ✅ (500/월) |
| **Cloudinary** | 이미지 변환 CDN | ✅ (25 크레딧/월) |
| **imgix** | 이미지 최적화 CDN | ✅ (1000/월) |

---

## 11. 번역 / 언어

| API | 설명 | 무료 |
|-----|------|------|
| **DeepL** | 최고 품질 번역 | ✅ (500k 문자/월) |
| **Google Translate** | 100+ 언어 번역 | ✅ ($10 크레딧) |
| **Papago** | 한국어 번역 최강 (Naver) | ✅ (10000/일) |
| **LibreTranslate** | 오픈소스 번역 | ✅ |
| **MyMemory** | 번역 메모리 | ✅ |
| **Dictionary API** | 영영 사전 | ✅ |
| **국립국어원 사전** | 한국어 사전 | ✅ |

---

## 12. 소셜 / 커뮤니케이션

| API | 설명 | 무료 |
|-----|------|------|
| **Slack** | 메시징 | ✅ |
| **Discord** | 봇 / 메시징 | ✅ |
| **Telegram Bot** | 봇 API | ✅ |
| **Twitter/X** | 트윗 검색·게시 | ✅ (제한적) |
| **Reddit** | 게시글·댓글 | ✅ |
| **GitHub** | 리포·이슈·PR | ✅ (5000/시간) |
| **카카오** | 메시지·지도·검색 | ✅ |
| **네이버** | 검색·블로그·쇼핑 | ✅ |

---

## 13. 이메일 / SMS

| API | 설명 | 무료 |
|-----|------|------|
| **Resend** | 이메일 전송 | ✅ (100/일) |
| **SendGrid** | 이메일 전송 | ✅ (100/일) |
| **Mailgun** | 이메일 API | ✅ (5000/월) |
| **Twilio** | SMS + 전화 | ✅ (트라이얼) |
| **AWS SES** | 이메일 (저렴) | ✅ (62000/월, EC2) |

---

## 14. 인증 / OAuth

| 서비스 | 설명 | 무료 |
|--------|------|------|
| **Auth0** | 인증 서비스 | ✅ (25000 MAU) |
| **Clerk** | 인증 + 사용자 관리 | ✅ (10000 MAU) |
| **Supabase Auth** | 인증 (PostgreSQL 내장) | ✅ |
| **Firebase Auth** | Google 인증 | ✅ |
| **Keycloak** | 셀프호스팅 인증 | ✅ (오픈소스) |

---

## 15. Rate Limiting / 보안

| API/도구 | 설명 | 설치 |
|---------|------|------|
| **Upstash Redis** | 서버리스 Redis (rate limit) | ✅ (10k cmd/일) |
| **Cloudflare** | DDoS 방어 + WAF | ✅ |
| **hCaptcha** | CAPTCHA (reCAPTCHA 대안) | ✅ |
| **Turnstile** | Cloudflare CAPTCHA (사용자 친화) | ✅ |

```python
# FastAPI Rate Limiting
pip install slowapi
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.get("/api/search")
@limiter.limit("10/minute")
async def search(q: str):
    return {"results": [...]}
```

---

## 16. 검색

| API | 설명 | 무료 |
|-----|------|------|
| **Google Custom Search** | 웹 검색 | ✅ (100/일) |
| **Bing Search** | 웹 검색 | ✅ (1000/월) |
| **SerpAPI** | SERP 스크래핑 | ✅ (100/월) |
| **Brave Search** | 프라이버시 검색 | ✅ (2000/월) |
| **Naver 검색** | 한국 웹/뉴스/블로그 | ✅ (25000/일) |
| **Algolia** | 실시간 검색 | ✅ (10k 레코드) |

---

## 17. QR / 바코드

| API | 설명 | 무료 |
|-----|------|------|
| **QR Server** | QR 코드 생성 | ✅ |
| **GoQR.me** | QR 코드 생성 | ✅ |

```python
# QR 코드 생성 (URL)
qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded_url}"
```

---

## 18. 기타 재미있는 API

| API | 설명 | 무료 |
|-----|------|------|
| **PokeAPI** | 포켓몬 데이터 | ✅ |
| **SWAPI** | 스타워즈 데이터 | ✅ |
| **Dog CEO** | 랜덤 강아지 사진 | ✅ |
| **Cat Facts** | 고양이 사실 | ✅ |
| **Bored API** | 할 일 추천 | ✅ |
| **Advice Slip** | 랜덤 조언 | ✅ |
| **Chuck Norris** | 척 노리스 농담 | ✅ |
| **Trivia API** | 퀴즈 문제 | ✅ |
| **NASA** | 우주 사진·소행성·화성 | ✅ |
| **SpaceX** | SpaceX 발사 데이터 | ✅ |
| **공공데이터포털** | 한국 공공 API 5만+ | ✅ |

---

## 추천 조합

### 뉴스 앱
```text
NewsAPI + DeepL 번역 + Unsplash 이미지 + Firebase Auth
```

### 영화 검색 앱
```text
TMDB + YouTube Data (예고편) + Unsplash + Algolia
```

### 금융 대시보드
```text
Alpha Vantage + ExchangeRate-API + CoinGecko + Chart.js
```

### AI 채팅봇
```text
Claude API + Brave Search + Open-Meteo + Papago
```

### 한국 서비스
```text
카카오 API + 네이버 API + 공공데이터포털 + 기상청 + 한국은행
```
