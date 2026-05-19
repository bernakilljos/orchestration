# Monetization Toolkit — 수익화·SaaS·API·광고·구독·마켓플레이스

> **목적**: 만든 것으로 돈 버는 패턴 총정리

---

## 1. SaaS 수익 모델

### 구독 (Subscription)
```python
# Stripe 구독
pip install stripe

import stripe
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

# 가격 플랜 생성
price = stripe.Price.create(
    unit_amount=9900,  # ₩9,900
    currency="krw",
    recurring={"interval": "month"},
    product_data={"name": "Pro Plan"},
)

# 결제 링크 생성 (노코드)
link = stripe.PaymentLink.create(line_items=[{"price": price.id, "quantity": 1}])
print(link.url)  # 이 URL 공유하면 끝
```

### 프리미엄 (Freemium)
| 기능 | Free | Pro ($9.9/월) | Enterprise ($99/월) |
|------|------|---------------|---------------------|
| API 호출 | 100/일 | 10,000/일 | 무제한 |
| 모델 | 기본 | GPT-4 | Claude Opus |
| 스토리지 | 100MB | 10GB | 100GB |
| 지원 | 커뮤니티 | 이메일 | 전담 |

### 사용량 과금 (Usage-Based)
```python
# Stripe Metered Billing
meter = stripe.billing.Meter.create(
    display_name="API Calls",
    event_name="api_call",
)

# 사용량 기록
stripe.billing.MeterEvent.create(
    event_name="api_call",
    payload={"stripe_customer_id": "cus_xxx", "value": "1"},
)
```

---

## 2. API 수익화

### API 게이트웨이 + 과금
| 서비스 | 특장 | 비용 |
|--------|------|------|
| **RapidAPI** | API 마켓플레이스 (판매) | 수수료 20% |
| **Stripe Billing** | 사용량 과금 | 수수료 2.9% |
| **AWS API Gateway** | 관리형 게이트웨이 | 종량제 |
| **Kong** | 오픈소스 API 게이트웨이 | 무료/유료 |

### 내 API 판매 패턴
```python
# FastAPI + API 키 + 사용량 제한
from fastapi import FastAPI, Header, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

API_KEYS = {
    "free_xxx": {"tier": "free", "limit": 100},
    "pro_xxx": {"tier": "pro", "limit": 10000},
}

@app.get("/api/v1/analyze")
@limiter.limit("100/day")  # 기본 제한
async def analyze(text: str, x_api_key: str = Header()):
    if x_api_key not in API_KEYS:
        raise HTTPException(401, "Invalid API key")
    # 비즈니스 로직
    return {"result": "..."}
```

### API 수익 사례
| API | 수익 모델 | 예상 수익 |
|-----|----------|----------|
| **이미지 복원 API** | $0.01/장 | 1만장/일 = $100/일 |
| **영상 업스케일 API** | $0.1/분 | 1000분/일 = $100/일 |
| **AI 번역 API** | $0.005/1000자 | 대량 → $50+/일 |
| **OCR API** | $0.01/페이지 | 문서 처리 |
| **음성 TTS API** | $0.01/1000자 | 오디오북·교육 |

---

## 3. 디지털 상품 판매

### 판매 플랫폼
| 플랫폼 | 수수료 | 적합 |
|--------|--------|------|
| **Gumroad** | 10% | 디지털 상품 (템플릿, 에셋, 강의) |
| **Lemon Squeezy** | 5%+$0.50 | SaaS + 디지털 상품 |
| **Paddle** | 5%+$0.50 | SaaS (세금 자동 처리) |
| **itch.io** | 0~30% (선택) | 게임, 에셋 |
| **Creative Market** | 40% | 디자인 에셋 |
| **Envato** | 37.5~87.5% | 테마, 플러그인 |
| **Udemy** | 37% (자체 마케팅) | 강의 |

### 팔 수 있는 것
| 상품 | 가격대 | 플랫폼 |
|------|--------|--------|
| **Claude Code 플러그인** | $5~50 | Gumroad |
| **PPT 템플릿** | $5~30 | Gumroad, Creative Market |
| **AI 프롬프트 팩** | $5~20 | Gumroad, PromptBase |
| **게임 에셋** | $5~50 | itch.io |
| **Notion 템플릿** | $5~30 | Gumroad, Notion Market |
| **코드 보일러플레이트** | $20~200 | Gumroad |
| **온라인 강의** | $10~200 | Udemy, 인프런 |
| **E-book** | $5~50 | Gumroad, Amazon KDP |
| **폰트** | $10~100 | Creative Market |
| **아이콘 팩** | $10~50 | Gumroad, Iconfinder |

---

## 4. 광고 수익

### 웹사이트 광고
| 서비스 | 조건 | RPM |
|--------|------|-----|
| **Google AdSense** | 누구나 | $1~5 |
| **Mediavine** | 50K 세션/월 | $10~30 |
| **AdThrive** | 100K PV/월 | $15~40 |
| **Carbon Ads** | 개발자 타겟 | $2~5 |
| **EthicalAds** | 오픈소스/개발자 | $2~4 |

### 유튜브 수익
```text
- 구독자 1,000명 + 시청시간 4,000시간 → 파트너 프로그램
- RPM: $2~10 (한국), $5~30 (미국)
- 슈퍼챗, 멤버십, 머천다이즈 추가 수익
```

### 앱 광고
| SDK | 특장 |
|-----|------|
| **Google AdMob** | 모바일 앱 광고 |
| **Unity Ads** | 게임 광고 |
| **AppLovin** | 모바일 광고 네트워크 |

---

## 5. 마켓플레이스

### 마켓플레이스 구축
```python
# 양면 마켓 (판매자-구매자)
pip install stripe-connect     # Stripe Connect (양면 결제)

# 플랫폼 수수료 패턴
payment = stripe.PaymentIntent.create(
    amount=10000,
    currency="krw",
    application_fee_amount=1500,  # 15% 수수료
    transfer_data={"destination": "acct_seller_xxx"},
)
```

### 마켓플레이스 SaaS 도구
| 도구 | 특장 |
|------|------|
| **Sharetribe** | 마켓플레이스 노코드 |
| **Medusa** | 오픈소스 커머스 (headless) |
| **Saleor** | GraphQL 커머스 |
| **WooCommerce** | WordPress 커머스 |

---

## 6. 어필리에이트 / 제휴

### AI 도구 어필리에이트
| 프로그램 | 수수료 | 쿠키 |
|---------|--------|------|
| **Anthropic API** | 크레딧 공유 | — |
| **OpenAI API** | 크레딧 공유 | — |
| **Notion** | 50% (첫해) | 90일 |
| **Vercel** | 25% (반복) | 90일 |
| **DigitalOcean** | $200/가입 | 30일 |
| **Cloudflare** | 25% (반복) | 60일 |
| **Hostinger** | 60% | 30일 |
| **NordVPN** | 40~100% | 30일 |

### 구현
```python
# 어필리에이트 링크 트래킹
@app.get("/go/{partner}")
async def affiliate_redirect(partner: str, ref: str = None):
    # 클릭 기록
    await db.execute(insert(Click).values(partner=partner, ref=ref))
    # 리다이렉트
    return RedirectResponse(AFFILIATE_URLS[partner])
```

---

## 7. 프리랜서 / 컨설팅

### AI 컨설팅 서비스
| 서비스 | 가격대 |
|--------|--------|
| Claude Code 셋업 | $500~2000 |
| AI 워크플로우 자동화 | $1000~5000 |
| RAG 파이프라인 구축 | $2000~10000 |
| AI 교육/워크샵 (기업) | $1000~5000/일 |
| 영상 복원 서비스 | $50~500/편 |

### 플랫폼
| 플랫폼 | 타겟 | 수수료 |
|--------|------|--------|
| **크몽** | 한국 (범용) | 20% |
| **숨고** | 한국 (서비스) | 건별 |
| **Upwork** | 글로벌 | 10~20% |
| **Fiverr** | 글로벌 (단가↓) | 20% |
| **Toptal** | 고급 프리랜서 | 심사제 |

---

## 8. 오픈소스 수익화

| 모델 | 예시 |
|------|------|
| **Open Core** | 기본 무료 + 엔터프라이즈 유료 (GitLab, Supabase) |
| **Hosting** | 셀프호스팅 무료 + 관리형 유료 (Plausible, n8n) |
| **Sponsorship** | GitHub Sponsors, Open Collective |
| **Dual License** | AGPL + 상용 라이선스 (MongoDB) |
| **Support** | 코드 무료 + 지원 유료 (Red Hat) |

### GitHub Sponsors 설정
```markdown
# .github/FUNDING.yml
github: [your-username]
ko_fi: your-username
buy_me_a_coffee: your-username
custom: ["https://your-site.com/sponsor"]
```

---

## 9. 우리 킷으로 바로 돈 되는 것

| 항목 | 수익 모델 | 필요 도구 (이미 있음) |
|------|----------|---------------------|
| **영상 복원 서비스** | 건당 $50~500 | /video-restore + Real-ESRGAN |
| **PPT 자동 제작** | 건당 $20~100 | /design_ppt + Playwright |
| **AI 교육 콘텐츠** | 강의 $10~200 | teaching-doc + Word/PDF |
| **게임 에셋 판매** | 팩 $5~50 | game-asset-toolkit + SD |
| **API 서비스** | 사용량 과금 | FastAPI + Stripe |
| **Claude 플러그인 판매** | 건당 $5~50 | plugin 구조 이미 있음 |
| **음악/효과음 판매** | 팩 $5~30 | MusicGen + Demucs |
| **번역 서비스** | 건당 $0.01/자 | Whisper + Claude |
| **정보보호공시 SaaS** | 월 $500~2000 | ISDS PPT 이미 제작 |
