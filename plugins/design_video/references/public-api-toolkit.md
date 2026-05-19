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

## 19. 스포츠 / 피트니스

| API | 설명 | 무료 |
|-----|------|------|
| **Strava** | 러닝·자전거 데이터 | ✅ |
| **Fitbit Web API** | 활동·수면·심박 | ✅ |
| **Wger** | 운동 DB (헬스·요가) | ✅ (오픈소스) |
| **API-Football** | 축구 경기·통계 | ✅ (100/일) |
| **NBA API** | 농구 통계 | ✅ |
| **ESPN** | 스포츠 뉴스·스코어 | ✅ |
| **TheSportsDB** | 스포츠 팀·경기 | ✅ |
| **Nutritionix** | 영양정보·칼로리 | ✅ (제한) |
| **Open Food Facts** | 식품 성분 DB (오픈소스) | ✅ |
| **USDA FoodData** | 미국 식품 영양 DB | ✅ |

---

## 20. 여행 / 숙박

| API | 설명 | 무료 |
|-----|------|------|
| **Amadeus** | 항공권·호텔 검색 | ✅ (테스트) |
| **Skyscanner** | 항공권 비교 | ✅ (파트너) |
| **Booking.com** | 호텔 검색 | ✅ (파트너) |
| **Google Places** | 장소·리뷰 | ✅ ($200/월) |
| **Foursquare** | 장소 데이터 | ✅ |
| **RestCountries** | 국가 정보 | ✅ |
| **한국관광공사 API** | 관광지·축제·숙박 | ✅ |
| **기상청 API** | 날씨 (여행 계획) | ✅ |
| **Open Cage** | 지오코딩 (무료) | ✅ (2500/일) |

---

## 21. 부동산 / 경매

| API | 설명 | 무료 |
|-----|------|------|
| **국토부 실거래가 API** | 아파트·오피스텔 실거래 | ✅ (공공데이터) |
| **네이버 부동산** | 매물·시세 | 크롤링 |
| **카카오 지도** | 부동산 위치 | ✅ |
| **법원경매 API** | 경매 물건 조회 | ✅ (공공데이터) |
| **건축물대장 API** | 건물 정보 | ✅ (공공데이터) |
| **Zillow** | 미국 부동산 (Zestimate) | ✅ |

---

## 22. 자동차 / 모빌리티

| API | 설명 | 무료 |
|-----|------|------|
| **NHTSA** | 차량 안전·리콜 (미국) | ✅ |
| **CarMD** | 차량 진단 데이터 | ✅ (제한) |
| **한국교통안전공단** | 자동차 검사·이력 | ✅ (공공데이터) |
| **충전소 API** | 전기차 충전소 위치 | ✅ (한국환경공단) |
| **Open Charge Map** | 전세계 EV 충전소 | ✅ |
| **카카오 내비** | 경로·교통 | ✅ |

---

## 23. 반려동물

| API | 설명 | 무료 |
|-----|------|------|
| **Dog CEO** | 랜덤 강아지 사진 | ✅ |
| **TheDogAPI** | 견종 정보 + 사진 | ✅ |
| **TheCatAPI** | 묘종 정보 + 사진 | ✅ |
| **동물보호관리시스템** | 유기동물 조회 (한국) | ✅ (공공데이터) |
| **PetFinder** | 입양 동물 검색 (미국) | ✅ |

---

## 24. 패션 / 뷰티

| API | 설명 | 무료 |
|-----|------|------|
| **Unsplash** | 패션 사진 | ✅ |
| **Google Vision** | 이미지 분류·라벨링 (패션 분석) | ✅ ($10 크레딧) |
| **Sephora** | 뷰티 제품 (크롤링) | 크롤링 |
| **Makeup API** | 화장품 DB | ✅ |
| **Color API** | 컬러 팔레트 생성 | ✅ |

---

## 25. 교육 / 시험

| API | 설명 | 무료 |
|-----|------|------|
| **Open Trivia DB** | 퀴즈 문제 생성 | ✅ |
| **Dictionary API** | 영어 사전 | ✅ |
| **국립국어원 사전** | 한국어 사전 | ✅ |
| **Oxford Dictionaries** | 영어 사전 (고급) | ✅ (제한) |
| **Math.js** | 수학 계산 API | ✅ |
| **Wolfram Alpha** | 수학·과학 계산 | ✅ (2000/월) |
| **Khan Academy** | 교육 콘텐츠 | 크롤링 |

---

## 26. 법률 / 행정 / 정부

| API | 설명 | 무료 |
|-----|------|------|
| **국가법령정보센터** | 법령·판례 검색 | ✅ |
| **대법원 판례** | 판례 조회 | ✅ (공공데이터) |
| **정부24 API** | 공공서비스 | ✅ |
| **공공데이터포털** | 5만+ API | ✅ |
| **국세청 홈택스** | 세금 관련 | ✅ (공공데이터) |
| **고용노동부** | 취업·노무 | ✅ (공공데이터) |
| **특허청 KIPRIS** | 특허·상표 검색 | ✅ |

---

## 27. 사주 / 운세 / 점술

| API | 설명 | 무료 |
|-----|------|------|
| **Aztro** | 별자리 운세 | ✅ |
| **Horoscope API** | 일간·주간 운세 | ✅ |
| **Tarot API** | 타로 카드 | ✅ |
| **만세력 계산** | Python 라이브러리 | `pip install lunardate sxtwl` |
| **음양력 변환** | 한국천문연구원 | ✅ (공공데이터) |

---

## 28. 커뮤니티 / 소셜

| API | 설명 | 무료 |
|-----|------|------|
| **Reddit** | 게시글·댓글 | ✅ |
| **Discord** | 봇·채널 | ✅ |
| **Mastodon** | 분산 소셜 | ✅ |
| **Matrix/Element** | 분산 메시징 | ✅ |
| **카카오톡** | 메시지·로그인 | ✅ |
| **네이버 카페/블로그** | 검색·게시 | ✅ |

---

## 29. 농업 / 스마트팜 / 식품

| API | 설명 | 무료 |
|-----|------|------|
| **농사로 API** | 작물·병해충·농업기술 (농촌진흥청) | ✅ |
| **농산물유통정보** | 도매·소매 시세 (KAMIS) | ✅ |
| **스마트팜코리아** | IoT 센서 데이터 | ✅ (공공) |
| **기상청 농업날씨** | 농업 특화 기상 | ✅ |
| **식품안전나라** | 식품 성분·영양·인허가 | ✅ |
| **HACCP 인증** | 식품 안전 인증 조회 | ✅ |
| **Open Food Facts** | 식품 성분 DB (글로벌) | ✅ |

---

## 30. 제조 / 산업 / 에너지

| API | 설명 | 무료 |
|-----|------|------|
| **한국전력 전력데이터** | 전력 사용량·요금 | ✅ (공공) |
| **에너지공단 API** | 에너지 효율·보급 | ✅ |
| **탄소배출권 거래소** | 배출권 시세 | ✅ |
| **산업안전보건공단** | 산업재해 통계·MSDS | ✅ |
| **한국표준협회** | KS 표준·인증 | ✅ |
| **기상청 미세먼지** | 대기질 데이터 | ✅ |
| **환경부 수질정보** | 수질 측정 데이터 | ✅ |

---

## 31. 물류 / 무역 / 통관

| API | 설명 | 무료 |
|-----|------|------|
| **관세청 통관 API** | 수출입·통관·HS코드 | ✅ |
| **해운항만물류정보** | 선박·항만·컨테이너 | ✅ |
| **우체국 배송조회** | 택배 추적 | ✅ |
| **CJ대한통운** | 택배 추적 | API |
| **Shippo** | 배송 라벨·추적 (글로벌) | ✅ (무료 티어) |
| **EasyPost** | 배송 API (글로벌) | ✅ (무료 티어) |

---

## 32. 건설 / 시설 / 안전

| API | 설명 | 무료 |
|-----|------|------|
| **건축물대장 API** | 건물 정보·용도 | ✅ (공공) |
| **국토부 토지정보** | 토지이용·지목·공시지가 | ✅ |
| **소방청 API** | 소방시설·안전점검 | ✅ |
| **CCTV 관제 API** | 도로·교통 CCTV | ✅ (공공) |
| **도로교통공단** | 교통사고·신호·주차 | ✅ |
| **대중교통 API** | 버스·지하철 실시간 | ✅ (TAGO) |

---

## 33. HR / 기업관리

| API | 설명 | 무료 |
|-----|------|------|
| **4대보험 API** | 건강·국민·고용·산재 | ✅ (공공) |
| **국세청 사업자확인** | 사업자등록 상태 조회 | ✅ |
| **고용노동부 채용** | 구인구직 | ✅ (워크넷) |
| **고용24** | 고용 지원금·정책 | ✅ |
| **중소벤처기업부** | 중소기업 지원사업 | ✅ |
| **정부지원금 API** | 보조금24 | ✅ |
| **전자계약 API** | 모두싸인·도큐사인 연동 | 유료 |

---

## 34. 금융 / 핀테크

| API | 설명 | 무료 |
|-----|------|------|
| **금융결제원 오픈뱅킹** | 계좌 조회·이체 | 인증 필요 |
| **금융감독원** | 금융상품·공시·통계 | ✅ |
| **보험개발원** | 보험 상품·요율 | ✅ |
| **한국신용정보원** | 신용정보 | 인증 |
| **마이데이터 API** | 개인 금융 데이터 통합 | 인증 |
| **토스페이먼츠** | 결제 (한국) | 수수료만 |
| **아임포트(포트원)** | 결제 통합 (한국) | 수수료만 |
| **로또 API** | 당첨번호 조회 | ✅ (동행복권) |

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
