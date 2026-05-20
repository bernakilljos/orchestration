# E-commerce Toolkit — 100+ 공통 도구

> **범위**: 결제·배송·재고·구독·마켓플레이스·검색·분석 등 전자상거래 필수 인프라  
> **성격**: 도메인 독립 (Shopify/WooCommerce/커스텀 모두 적용 가능)  
> **최근 업데이트**: 2026-05-20

---

## 1. 결제 (Payment Processing)

결제 게이트웨이 및 카드 처리 서비스.

| 도구 | 주요 기능 | 지역 | npm / 설치 |
|------|---------|------|-----------|
| **Stripe** | 카드/계좌이체 | 글로벌 | `npm install stripe` |
| **PayPal** | 카드/PayPal | 글로벌 | `npm install @paypal/checkout-server-sdk` |
| **Toss Payments** | 카드/계좌이체 | 한국 | `npm install tosimpayments` (비공식) |
| **PortOne (구 아임포트)** | 다중 PG 통합 | 한국 | `npm install iamport-rest-client` |
| **Square** | 카드/모바일 | 글로벌 | `npm install square` |
| **Adyen** | 다중 결제수단 | 글로벌 | `npm install @adyen/api-library` |
| **Braintree** | 카드/PayPal | 글로벌 | `npm install braintree` |
| **Razorpay** | 인도/동남아 | 인도 | `npm install razorpay` |

### 강점
- 다중 결제수단 통합 (카드·계좌·월렛)
- PCI 준수 및 보안 자격
- Webhook 기반 실시간 동기

### 약점
- 설정 복잡 (merchant account 필수)
- 서로 다른 API 스펙 (통합 어려움)

### 강추
- **스타트업**: PortOne (한국) + Stripe (글로벌) 조합
- **대규모**: Adyen (다중 지역) 또는 Razorpay (인도/동남아)

---

## 2. 장바구니 & 쇼핑몰 플랫폼

완전한 e-commerce 플랫폼 또는 API.

| 도구 | 타입 | 기능 | npm 설치 |
|------|------|------|---------|
| **Shopify** | SaaS | 완전한 쇼핑몰 | `npm install @shopify/shopify-api` |
| **WooCommerce** | 플러그인 | WordPress 기반 | REST API (HTTP) |
| **Medusa.js** | Headless | Node.js 오픈소스 | `npm install @medusajs/medusa` |
| **Saleor** | Headless | GraphQL API | `npm install graphql-request` (클라) |
| **Vendure** | Headless | Node.js GraphQL | `npm install @vendure/core` |
| **Bagisto** | PHP | Laravel 기반 | REST API (PHP) |
| **BigCommerce** | SaaS | API 우선 | REST/GraphQL API |

### 강점
- 기본 CRUD 자동 제공
- 주문·상품·고객 관리 통합
- Webhook 지원

### 약점
- 호스팅 비용 (SaaS)
- 확장성 제한 (플러그인 의존)

### 강추
- **빠른 시작**: Shopify
- **제어권**: Medusa.js / Vendure (Headless)
- **WordPress 연계**: WooCommerce

---

## 3. 재고관리 (Inventory Management)

실시간 재고 추적 및 동기.

| 도구 | 기능 | 통합 | API |
|------|------|------|-----|
| **TradeGecko** | 다채널 재고 | Shopify/Amazon | REST |
| **Cin7** | 창고 관리 | 다중 채널 | REST |
| **Zoho Inventory** | 완전한 ERP 라이트 | Shopify/eBay | REST |
| **inFlow** | 로컬 재고 추적 | Windows/Mac | SDK |

### 강점
- 실시간 동기 (Webhook)
- 다중 채널 통합
- 분석 대시보드

### 강추
- **e-commerce 네이티브**: TradeGecko / Zoho Inventory

---

## 4. 배송 (Shipping & Logistics)

배송사 연동 및 추적.

| 도구 | 주요 배송사 | 지역 | npm 설치 |
|------|-----------|------|---------|
| **ShipStation** | 다중 배송사 | 글로벌 | REST API |
| **Shippo** | UPS/FedEx/DHL | 글로벌 | `npm install shippo` |
| **EasyPost** | 다중 통합 | 글로벌 | `npm install @easypost/api` |
| **CJ 대한통운** | CJ 한정 | 한국 | REST (자체 API) |
| **롯데택배** | 롯데 한정 | 한국 | 자체 SDK |
| **우체국** | 우편 | 한국 | REST |

### 강점
- 실시간 배송 요금 계산
- 픽업 라벨 자동 생성
- 추적 통합

### 약점
- 배송사별 다른 API
- 한국 통합 복잡

### 강추
- **글로벌**: EasyPost / Shippo
- **한국**: ShipStation + 로컬 통합 + CJ/롯데 다이렉트

---

## 5. 구독 & 멤버십 (Subscription Management)

반복 결제 및 구독 관리.

| 도구 | 기능 | 특징 | npm 설치 |
|------|------|------|---------|
| **Stripe Subscriptions** | 반복 결제 | Stripe 네이티브 | Stripe SDK 사용 |
| **Chargebee** | 구독 전용 | 분석 강력 | REST API |
| **Recurly** | 구독 전용 | 컴플라이언스 | `npm install recurly` |
| **Paddle** | 결제+구독 | 디지털 상품 | REST API |

### 강점
- 자동 청구 및 갱신
- 구독자 분석
- Dunning (미수금 재청구)

### 강추
- **Stripe 사용 중**: Stripe Subscriptions
- **분석 필요**: Chargebee

---

## 6. 마켓플레이스 (Marketplace Platforms)

다중 셀러 마켓플레이스 운영.

| 도구 | 타입 | 수수료 | API |
|------|------|--------|-----|
| **Sharetribe** | SaaS 마켓플레이스 | 2-8% | REST/GraphQL |
| **Arcadier** | SaaS 마켓플레이스 | 5-10% | REST |
| **쿠팡 Open API** | 한국 마켓 | 정산형 | REST |
| **네이버 스마트스토어** | 한국 마켓 | 정산형 | REST |

### 강점
- 셀러 관리 자동화
- 수수료 정산 자동 계산
- 정산 리포팅

### 약점
- 호스팅 비용
- 커스터마이징 제한

### 강추
- **자체 운영**: Sharetribe / Arcadier
- **한국 진출**: 쿠팡 + 네이버

---

## 7. 세금 & 인보이스 (Tax & Invoicing)

자동 세금 계산 및 인보이스.

| 도구 | 기능 | 지역 | npm 설치 |
|------|------|------|---------|
| **TaxJar** | 판매세 자동 | 미국 | `npm install taxjar` |
| **Avalara** | 복잡한 세금 | 글로벌 | REST API |
| **Invoice Ninja** | 인보이스 생성 | 글로벌 | 자체 호스팅 |
| **Zoho Invoice** | SaaS 인보이싱 | 글로벌 | REST API |

### 강점
- 자동 세금 계산
- 인보이스 템플릿
- 회계 시스템 연동

### 약점
- 지역별 컴플라이언스 차이
- 비용 누적

### 강추
- **미국/글로벌**: TaxJar / Avalara
- **한국**: 외부 회계시스템 + 수동 통합

---

## 8. 리뷰 & 평점 (Reviews & Ratings)

고객 리뷰 수집 및 관리.

| 도구 | 기능 | 특징 | npm |
|------|------|------|-----|
| **Judge.me** | Shopify 리뷰 | Shopify 네이티브 | App 형태 |
| **Yotpo** | 다중 채널 리뷰 | 사진 UGC | REST API |
| **Stamped.io** | Shopify/WooCommerce | 설문 통합 | App 형태 |
| **Trustpilot** | B2B 리뷰 | 신뢰도 높음 | REST API |

### 강점
- 자동 리뷰 요청 이메일
- SEO 스키마 생성
- 피드백 수집

### 약점
- SaaS 비용
- 네이티브 통합 의존

### 강추
- **Shopify**: Judge.me / Stamped.io
- **글로벌**: Yotpo

---

## 9. 검색 & 추천 (Search & Discovery)

상품 검색 및 개인화 추천.

| 도구 | 기능 | 특징 | npm 설치 |
|------|------|------|---------|
| **Algolia** | 고속 검색 | 실시간 인덱싱 | `npm install algoliasearch` |
| **Typesense** | 오픈소스 검색 | 자체 호스팅 | `npm install typesense` |
| **MeiliSearch** | 가볍고 빠름 | 러스트 기반 | REST API |
| **Recombee** | 개인화 추천 | 머신러닝 | REST API |
| **Amazon Personalize** | AWS 추천 | 확장성 | AWS SDK |

### 강점
- 밀리초 응답시간
- 자동 완성 (autocomplete)
- 필터링 및 패싯

### 약점
- 별도 인덱싱 비용
- 동기 지연 (실시간 X)

### 강추
- **SaaS**: Algolia
- **자체 호스팅**: Typesense / MeiliSearch
- **ML 추천**: Recombee / Amazon Personalize

---

## 10. 분석 (Analytics & Insights)

전자상거래 성과 분석.

| 도구 | 기능 | 특징 | npm 설치 |
|------|------|------|---------|
| **Google Analytics (GA4)** | 웹 분석 | Ecommerce 플러그인 | `npm install @react/ga4` |
| **Mixpanel** | 이벤트 분석 | 사용자 행동 추적 | `npm install mixpanel-browser` |
| **PostHog** | 오픈소스 분석 | 자체 호스팅 | `npm install posthog-js` |
| **Segment** | 데이터 라우팅 | 다중 도구 통합 | `npm install @segment/analytics-next` |

### 강점
- 전환 추적
- 사용자 세분화
- 코호트 분석

### 약점
- 학습곡선
- 복잡한 설정

### 강추
- **시작**: Google Analytics
- **심화**: Mixpanel / PostHog
- **통합**: Segment (다중 도구)

---

## 예제: 통합 플로우

```bash
# Stripe + Medusa.js + Algolia + PostHog

npm install stripe @medusajs/medusa algoliasearch posthog-js

# Stripe 계산 (Node.js)
const stripe = require('stripe')('sk_test_...');
const payment = await stripe.paymentIntents.create({
  amount: 10000,
  currency: 'usd',
  payment_method: 'pm_1234',
  confirm: true,
});

# Algolia 검색
const client = algoliasearch('APP_ID', 'SEARCH_KEY');
const index = client.initIndex('products');
const results = await index.search('laptop', {
  filters: 'price <= 1000'
});

# PostHog 분석
posthog.capture('product_viewed', {
  productId: '123',
  price: 999,
});
```

---

## 참조

- **Stripe 공식**: https://stripe.com/docs
- **Medusa.js**: https://medusajs.com
- **Algolia 검색**: https://www.algolia.com
- **한국 결제**: https://portone.io
- **마켓플레이스**: https://sharetribe.com
