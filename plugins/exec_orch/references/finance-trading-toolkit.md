# Finance & Trading Toolkit Reference

> **목적**: 금융·거래 전체 생태계의 공통 도구 카탈로그 (domain-agnostic)
> **대상**: 모든 금융·거래 플러그인·스킬에서 참고
> **최종 갱신**: 2026-05-20

---

##  카테고리 요약

| # | 카테고리 | 도구 수 | 핵심 용도 |
|----|---------|--------|---------|
| 1 | 📈 주식/시장 데이터 API | 9 | 주가, 시세, 기업 정보, 실시간 데이터 |
| 2 | 🔄 백테스팅 & 시뮬레이션 | 9 | 전략 검증, 리스크 분석, 성과 측정 |
| 3 |  기술 분석 | 8 | 지표 계산, 패턴 인식, 차트 분석 |
| 4 | 🎲 퀀트 & 포트폴리오 | 9 | 최적화, 위험 관리, 성과 분석 |
| 5 | 💰 암호화폐 & 블록체인 | 10 | 거래소 통합, 지갑, 스마트 계약 |
| 6 | 📰 뉴스 & 감성 분석 | 8 | 뉴스 수집, 감정 분석, 여론 추적 |
| 7 |  경제 지표 & 매크로 | 8 | GDP, 금리, 인플레이션, 고용 데이터 |
| 8 | 🇰🇷 한국 금융 특화 | 12 | KRX, 한투, 공공데이터, 국내 거래소 |
| 9 | 📱 대시보드 & UI | 6 | 실시간 모니터링, 리포팅, 시각화 |
| 10 | 💳 결제 & 핀테크 | 10 | 결제 처리, 지갑, 송금, 환전 |
| 11 | 📋 회계 & 재무 | 8 | 자산 관리, 세금 계산, 재무 보고 |
| 12 |  리스크 관리 | 10 | VaR, GARCH, 스트레스 테스트, 헤징 |
| 13 | 🔐 데이터 보안 & 규제 | 8 | 암호화, 감사, 컴플라이언스, 로깅 |
| 14 | 🌍 외환 & 선물 | 8 | FX 거래, 선물 계약, 옵션 가격 |
| 15 | 📡 데이터 저장소 | 6 | 타임시리즈 DB, 캐시, 데이터 웨어하우스 |

**총 도구 수: 129개** (각 카테고리별 최소 6개 이상)

---

## 1⃣ 주식/시장 데이터 API (Market Data)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 1.1 | yfinance | Yahoo Finance 에서 주가, 옵션, 배당금 등 무료 데이터 | `pip install yfinance` |
| 1.2 | Alpha Vantage | 주가, 외환, 암호화폐 기술 지표 API | `pip install alpha-vantage` |
| 1.3 | IEX Cloud | 기업 정보, 뉴스, 실시간 거래, 기본 데이터 | `pip install iexfinance` |
| 1.4 | Polygon.io | 주식, 암호화폐, 외환 실시간 및 히스토리 데이터 | `pip install polygon-api-client` |
| 1.5 | Twelve Data | 글로벌 시장 데이터, 기술 지표, 실시간 스트림 | `pip install twelvedata` |
| 1.6 | Financial Modeling Prep | 기업 재무제표, 현금흐름, 비율 분석 | `pip install financialmodelingprep` |
| 1.7 | Marketstack | 실시간/역사 시장 데이터 (주식, ETF, 지수) | `pip install marketstack` |
| 1.8 | quandl | 대체 데이터, 지표, 경제 데이터 마켓플레이스 | `pip install quandl` |
| 1.9 | pandas-datareader | 다양한 소스(Yahoo, Google, FRED)에서 데이터 읽기 | `pip install pandas-datareader` |

---

## 2⃣ 백테스팅 & 시뮬레이션 (Backtesting)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 2.1 | Backtrader | 실시간/역사 데이터로 전략 백테스팅 및 라이브 거래 | `pip install backtrader` |
| 2.2 | Zipline | 주식 시뮬레이터 (퀀트 자동 거래 프레임워크) | `pip install zipline-reloaded` |
| 2.3 | VectorBT | 벡터화된 고속 백테스팅 및 포트폴리오 최적화 | `pip install vectorbt` |
| 2.4 | Lean (QuantConnect) | 클라우드 백테스팅, 라이브 거래, 데이터 | `pip install lean` |
| 2.5 | PyAlgoTrade | 이벤트 기반 백테스팅 프레임워크 | `pip install pyalgotrade` |
| 2.6 | Fastquant | 간단한 정량 전략 백테스트 | `pip install fastquant` |
| 2.7 | backtesting.py | 경량 백테스팅 라이브러리 (수수료, 슬리피지 포함) | `pip install backtest` |
| 2.8 | bt | 유연한 백테스팅 프레임워크 (Pandas 기반) | `pip install bt` |
| 2.9 | MLflow (모델 배포) | 실험 추적, 모델 버전 관리, 백테스트 결과 기록 | `pip install mlflow` |

---

## 3⃣ 기술 분석 (Technical Analysis)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 3.1 | TA-Lib | C 기반 고속 기술 지표 라이브러리 (200+ 지표) | `pip install ta-lib` |
| 3.2 | pandas-ta | pandas 호환 기술 지표 (130+ 지표) | `pip install pandas-ta` |
| 3.3 | finta | 간단한 기술 지표 계산 | `pip install finta` |
| 3.4 | bta-lib | 고급 거래 지표 | `pip install bta-lib` |
| 3.5 | mplfinance | Matplotlib 기반 캔들스틱 차트 | `pip install mplfinance` |
| 3.6 | plotly-candlestick | Plotly 로 인터랙티브 거래 차트 | `pip install plotly` |
| 3.7 | TradingView Pine Script | TradingView 차트 및 전략 스크립트 | 웹 기반 (스크립트 언어) |
| 3.8 | ccxt (차트 기능) | CCXT 내 차트 관련 오버레이 | `pip install ccxt` |

---

## 4⃣ 퀀트 & 포트폴리오 (Quantitative Finance)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 4.1 | QuantLib | 금리, 옵션, 채권 수가격 모델 | `pip install quantlib` |
| 4.2 | Riskfolio | 포트폴리오 최적화 (마코비츠 모델 포함) | `pip install riskfolio-lib` |
| 4.3 | PyPortfolioOpt | 포트폴리오 최적화 및 할당 | `pip install PyPortfolioOpt` |
| 4.4 | empyrical | 포트폴리오 성과 메트릭 계산 | `pip install empyrical` |
| 4.5 | ffn | 금융 함수 라이브러리 (수익률, 비율 분석) | `pip install ffn` |
| 4.6 | pypfopt | 포트폴리오 최적화 (Sharpe, Vol 최소화) | `pip install pypfopt` |
| 4.7 | optapy | 수학적 최적화 문제 풀이 | `pip install optapy` |
| 4.8 | scipy.optimize | 선형, 비선형 최적화 | `pip install scipy` |
| 4.9 | cvxpy | 볼록 최적화 (포트폴리오 최적화) | `pip install cvxpy` |

---

## 5⃣ 암호화폐 & 블록체인 (Cryptocurrency & Blockchain)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 5.1 | ccxt | 100+ 암호 거래소 통합 라이브러리 | `pip install ccxt` |
| 5.2 | python-binance | Binance 거래소 API 클라이언트 | `pip install python-binance` |
| 5.3 | freqtrade | 암호 거래 봇 프레임워크 (자동 거래) | `pip install freqtrade` |
| 5.4 | Hummingbot | 분산화된 거래 봇 및 마켓메이킹 | `pip install hummingbot` |
| 5.5 | Gekko | 암호 거래봇 (Node.js 기반) | `npm install gekko` |
| 5.6 | web3.py | 이더리움 블록체인 상호작용 | `pip install web3` |
| 5.7 | ethers.py | Ethereum 라이브러리 (web3.py 대안) | `pip install ethers` |
| 5.8 | cryptography | 블록체인 암호화 알고리즘 | `pip install cryptography` |
| 5.9 | bitcoin-utils | Bitcoin 트랜잭션 구성 및 서명 | `pip install bitcoinutils` |
| 5.10 | tronpy | TRON 블록체인 상호작용 | `pip install tronpy` |

---

## 6⃣ 뉴스 & 감성 분석 (News & Sentiment Analysis)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 6.1 | finBERT | 금융 도메인 특화 BERT 모델 (감정 분석) | `pip install transformers` |
| 6.2 | VADER Sentiment | 실시간 뉴스 감정 분석 | `pip install vaderSentiment` |
| 6.3 | newspaper3k | 뉴스 기사 수집 및 파싱 | `pip install newspaper3k` |
| 6.4 | newsapi-python | NewsAPI 클라이언트 (1000+ 뉴스 소스) | `pip install newsapi` |
| 6.5 | Tiingo | 뉴스, 기업 공시, 감정 데이터 | `pip install tiingo` |
| 6.6 | tweepy | Twitter API 클라이언트 (여론 추적) | `pip install tweepy` |
| 6.7 | TextBlob | 간단한 자연어 감성 분석 | `pip install textblob` |
| 6.8 | transformers (경량) | Hugging Face 경량 감정 분석 모델 | `pip install transformers` |

---

## 7⃣ 경제 지표 & 매크로 (Macroeconomic Indicators)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 7.1 | pandas-datareader (FRED) | FRED API 를 통한 경제 지표 | `pip install pandas-datareader` |
| 7.2 | FRED API (fredapi) | 미국 연방 경제 데이터 직접 접근 | `pip install fredapi` |
| 7.3 | World Bank API | 세계은행 경제 통계 | `pip install wbdata` |
| 7.4 | OECD API | 경제협력개발기구 데이터 | `pip install pandas-datareader` |
| 7.5 | Trading Economics API | 금리, 인플레이션, GDP, 실업률 | `pip install tradingeconomics` |
| 7.6 | IMF API | 국제통화기금 경제 데이터 | `pip install requests` |
| 7.7 | ECB API | 유럽중앙은행 환율, 금리 | `pip install requests` |
| 7.8 | CEIC Data API | 중앙은행 및 정부 경제 통계 | API 기반 (requests 사용) |

---

## 8⃣ 한국 금융 특화 (Korean Finance)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 8.1 | pykrx | KRX (한국거래소) 주가, 선물, 옵션 데이터 | `pip install pykrx` |
| 8.2 | FinanceDataReader | 국내 주식, ETF, 환율, 암호화폐 데이터 | `pip install finance-datareader` |
| 8.3 | mojito | 한투 (미래에셋대우) API 클라이언트 | `pip install mojito` |
| 8.4 | ebest API (eBEST) | 대신증권 API (한투 연동) | API 문서 참고 |
| 8.5 | 공공데이터 DART | 상장회사 공시 데이터 (한국거래소) | `pip install dart-fss` |
| 8.6 | Ko3K (한투) | 한투 주식 거래 API | 직접 설치 필요 |
| 8.7 | Naver Finance 스크래핑 | Naver 금융 페이지 파싱 (BeautifulSoup) | `pip install beautifulsoup4 requests` |
| 8.8 | 금감원 공시 시스템 | 금융감시원 공시 정보 | API 문서 참고 |
| 8.9 | 한은 금리/환율 조회 | 한국은행 기준금리, 기준환율 | `pip install requests` |
| 8.10 | 국세청 세목별 통계 | 국내 세금, 투자 통계 | 공개 데이터 포털 |
| 8.11 | 통계청 경제활동인구 | 고용률, 산업 지표 | `pip install requests` |
| 8.12 | 한국투자 API | 한국투자증권 실시간 거래 API | API 문서 참고 |

---

## 9⃣ 대시보드 & UI (Dashboard & Visualization)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 9.1 | Streamlit | 빠른 금융 대시보드 구축 (Python) | `pip install streamlit` |
| 9.2 | Dash (Plotly) | 엔터프라이즈급 거래 대시보드 | `pip install dash` |
| 9.3 | Panel | Jupyter 및 웹 기반 실시간 모니터링 | `pip install panel` |
| 9.4 | Grafana | 실시간 메트릭 시각화 대시보드 | `npm install -g grafana-cli` |
| 9.5 | Bokeh | 대용량 시장 데이터 인터랙티브 차트 | `pip install bokeh` |
| 9.6 | Flask + plotly | 맞춤형 거래 웹 애플리케이션 | `pip install flask plotly` |

---

## 🔟 결제 & 핀테크 (Payment & Fintech)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 10.1 | Stripe | 신용카드 결제 및 가입 결제 | `pip install stripe` |
| 10.2 | PayPal SDK | PayPal 결제 통합 | `pip install paypalrestsdk` |
| 10.3 | Toss Payments (토스페이먼츠) | 한국 결제 게이트웨이 | `pip install requests` (API 기반) |
| 10.4 | PortOne (구 아임포트) | 한국 결제 통합 플랫폼 | `pip install requests` (API 기반) |
| 10.5 | Square | POS 및 온라인 결제 | `pip install squareup` |
| 10.6 | Braintree | PayPal 자회사 결제 게이트웨이 | `pip install braintree` |
| 10.7 | Wise (TransferWise) | 국제 송금 및 환전 | `pip install wise-api` |
| 10.8 | Circle API | 암호 결제 및 지갑 | `pip install requests` (API 기반) |
| 10.9 | Revolut API | FinTech 뱅킹 및 결제 | `pip install requests` (API 기반) |
| 10.10 | Plaid | 은행 계좌 연결 및 거래 데이터 | `pip install plaid-python` |

---

## 1⃣1⃣ 회계 & 재무 (Accounting & Finance)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 11.1 | xlwings | Excel 자동화 및 VBA 대체 | `pip install xlwings` |
| 11.2 | openpyxl | Excel 읽기/쓰기 (XLSX) | `pip install openpyxl` |
| 11.3 | pandas (Excel 연동) | pandas 로 Excel 데이터 처리 | `pip install pandas openpyxl` |
| 11.4 | num2words | 숫자를 한글/영문 단어로 변환 | `pip install num2words` |
| 11.5 | forex-python | 환율 계산 및 환전 | `pip install forex-python` |
| 11.6 | Money (python-money) | 화폐 단위 처리 및 계산 | `pip install py-money` |
| 11.7 | Babel (금융 포맷) | 통화 형식화 및 국제화 | `pip install babel` |
| 11.8 | reportlab | PDF 재무 보고서 생성 | `pip install reportlab` |

---

## 1⃣2⃣ 리스크 관리 (Risk Management)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 12.1 | scipy.stats | 통계 분포 및 VaR 계산 | `pip install scipy` |
| 12.2 | arch (GARCH) | GARCH 모델로 변동성 예측 | `pip install arch` |
| 12.3 | statsmodels | 시계열 분석 및 회귀 모델 | `pip install statsmodels` |
| 12.4 | numpy (선형대수) | 포트폴리오 공분산 행렬, 위험 계산 | `pip install numpy` |
| 12.5 | pandas-rolling-stats | 이동평균 변동성, Sharpe 비율 | `pip install pandas` |
| 12.6 | scikit-learn (VaR) | 머신러닝 기반 리스크 모델 | `pip install scikit-learn` |
| 12.7 | copulas (의존성) | Copula 모델로 자산 상관관계 분석 | `pip install copulas` |
| 12.8 | getdist | 위험 분포 시각화 | `pip install getdist` |
| 12.9 | riskmetrics | RiskMetrics 방법론 구현 | `pip install requests` (API 기반) |
| 12.10 | CVaR (조건부 VaR) | 극단적 손실 측정 | scipy 기반 커스텀 구현 |

---

## 1⃣3⃣ 데이터 보안 & 규제 (Security & Compliance)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 13.1 | cryptography | 데이터 암호화 및 서명 | `pip install cryptography` |
| 13.2 | PyCryptodome | 암호화 알고리즘 (AES, RSA) | `pip install pycryptodome` |
| 13.3 | python-jose | JWT 토큰 처리 (OAuth) | `pip install python-jose` |
| 13.4 | sqlalchemy | 데이터베이스 감시 및 로깅 | `pip install sqlalchemy` |
| 13.5 | python-dateutil | 규정 준수 시간대 및 감사 로그 | `pip install python-dateutil` |
| 13.6 | logging (표준) | 거래 감시 및 감사 추적 | 내장 모듈 |
| 13.7 | elasticsearch-py | 감사 로그 중앙화 및 검색 | `pip install elasticsearch` |
| 13.8 | jaeger-client | 분산 추적 및 성능 모니터링 | `pip install jaeger-client` |

---

## 1⃣4⃣ 외환 & 선물 (Forex & Derivatives)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 14.1 | QuantLib (FX옵션) | 외환 옵션 가격 모델 | `pip install quantlib` |
| 14.2 | mibian | 블랙-숄즈 옵션 가격 | `pip install mibian` |
| 14.3 | py_vollib | 내재 변동성 계산 | `pip install py_vollib` |
| 14.4 | QuantLib (선물) | 선물 계약 가격 및 헤징 | `pip install quantlib` |
| 14.5 | pandas-datareader (FOREX) | 역사적 환율 데이터 | `pip install pandas-datareader` |
| 14.6 | oandapyV20 | OANDA 외환 거래 API | `pip install oandapyv20` |
| 14.7 | ta-lib (선물 지표) | 선물 기술 분석 지표 | `pip install ta-lib` |
| 14.8 | ib_insync | Interactive Brokers 선물 거래 API | `pip install ib_insync` |

---

## 1⃣5⃣ 데이터 저장소 (Data Storage & Infrastructure)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 15.1 | InfluxDB | 시계열 데이터베이스 (실시간 가격) | `pip install influxdb` |
| 15.2 | Redis | 캐시 및 고속 데이터 저장 | `pip install redis` |
| 15.3 | MongoDB | 문서형 데이터베이스 (비구조화 데이터) | `pip install pymongo` |
| 15.4 | PostgreSQL | 관계형 DB (거래 기록) | `pip install psycopg2` |
| 15.5 | SQLite | 경량 로컬 DB (테스트용) | `pip install sqlite3` |
| 15.6 | HDF5 (PyTables) | 대용량 수치 데이터 압축 저장 | `pip install pytables` |

---

## 추가 유틸리티 & 헬퍼

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| A.1 | requests | HTTP 요청 (API 호출) | `pip install requests` |
| A.2 | aiohttp | 비동기 HTTP 클라이언트 | `pip install aiohttp` |
| A.3 | websocket-client | WebSocket 실시간 데이터 스트리밍 | `pip install websocket-client` |
| A.4 | python-dateutil | 날짜/시간 처리 | `pip install python-dateutil` |
| A.5 | pytz | 시간대 관리 | `pip install pytz` |
| A.6 | joblib | 병렬 처리 (멀티프로세싱) | `pip install joblib` |
| A.7 | tqdm | 진행 표시줄 | `pip install tqdm` |
| A.8 | loguru | 고급 로깅 | `pip install loguru` |
| A.9 | pydantic | 데이터 검증 및 설정 | `pip install pydantic` |
| A.10 | click | CLI 응용프로그램 프레임워크 | `pip install click` |

---

##  사용 예시

### 예 1: 주가 데이터 → 기술 분석 → 백테스팅 → 대시보드

```python
import yfinance as yf
import pandas_ta as ta
import backtrader as bt
import streamlit as st

# 1. 데이터 수집
data = yf.download('AAPL', start='2023-01-01', end='2024-01-01')

# 2. 기술 지표 추가
data.ta.add_all_indicators()

# 3. 백테스팅
# backtrader 전략 구성...

# 4. 결과 시각화
st.line_chart(data[['Close']])
```

### 예 2: 포트폴리오 최적화

```python
import pandas as pd
from riskfolio import Portfolio
import yfinance as yf

# 자산 수익률 계산
assets = ['AAPL', 'GOOGL', 'MSFT']
data = yf.download(assets, start='2023-01-01')['Adj Close']
returns = data.pct_change().dropna()

# 포트폴리오 최적화
port = Portfolio(returns=returns)
weights = port.optimization(...)
```

### 예 3: 암호 거래봇

```python
import ccxt
import backtrader as bt

# Binance 연결
exchange = ccxt.binance()

# 전략 백테스트
# freqtrade 또는 Hummingbot 프레임워크...
```

---

## 📌 주요 선택 기준

### 초보자
- **데이터**: yfinance → Alpha Vantage
- **분석**: pandas + pandas-ta
- **백테스팅**: backtesting.py
- **대시보드**: Streamlit

### 중급자
- **데이터**: Polygon.io, Twelve Data
- **백테스팅**: Backtrader, Zipline
- **포트폴리오**: Riskfolio, PyPortfolioOpt
- **대시보드**: Dash, Panel

### 고급자 (엔터프라이즈)
- **데이터**: 직접 API 통합 (IEX, Polygon, Twelve Data)
- **백테스팅**: QuantConnect (Lean)
- **퀀트**: QuantLib, scipy, statsmodels
- **대시보드**: Grafana, 커스텀 Flask/FastAPI
- **데이터 저장**: PostgreSQL, InfluxDB, Redis

---

##  참고 자료

- TA-Lib 지표: https://mrjbq7.github.io/ta-lib/
- QuantLib 문서: https://www.quantlib.org/
- CCXT 교환 목록: https://github.com/ccxt/ccxt/wiki/Exchanges
- Backtrader 튜토리얼: https://www.backtrader.com/
- Streamlit 문서: https://docs.streamlit.io/

---

## 🔄 버전 관리

| 버전 | 변경사항 | 날짜 |
|------|--------|------|
| 1.0 | 초기 작성 (129개 도구) | 2026-05-20 |

---

**마지막 업데이트**: 2026-05-20 (Claude Opus)

이 문서는 **공통 도구 카탈로그**입니다. 특정 도메인·산업별 추가 도구는 해당 플러그인의 `references/` 디렉토리에 작성하세요.
