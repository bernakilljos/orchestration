# Business Logic Templates — 서비스 비즈니스 로직 패턴 모음

> **목적**: Airbnb·Twitter 비교에서 "해당 없음"이던 비즈니스 로직을 템플릿으로 제공
> **용도**: 새 프로젝트에서 빠르게 비즈니스 로직 구현 시작

---

## 1. 인증 / 사용자 관리 (Auth)

### FastAPI + JWT
```python
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] python-multipart
```

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"
pwd_context = CryptContext(schemes=["bcrypt"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_token(data: dict, expires_delta: timedelta = timedelta(hours=24)):
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + expires_delta
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

app = FastAPI()

@app.post("/token")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    # DB에서 사용자 확인 + 비밀번호 검증
    if not pwd_context.verify(form.password, hashed_password):
        raise HTTPException(400, "Incorrect password")
    return {"access_token": create_token({"sub": form.username})}

@app.get("/me")
async def me(user = Depends(verify_token)):
    return user
```

### OAuth2 소셜 로그인
```python
pip install authlib httpx
# Google, GitHub, Kakao, Naver 소셜 로그인
```

---

## 2. 결제 (Payment)

### Stripe
```python
pip install stripe
```

```python
import stripe
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

# 결제 의도 생성
intent = stripe.PaymentIntent.create(
    amount=10000,  # 100원 (센트 단위)
    currency="krw",
    payment_method_types=["card"],
)

# 구독 생성
subscription = stripe.Subscription.create(
    customer="cus_xxx",
    items=[{"price": "price_xxx"}],
)
```

### 토스페이먼츠 (한국)
```python
pip install requests
# POST https://api.tosspayments.com/v1/payments/confirm
headers = {"Authorization": f"Basic {base64(secret_key + ':')}"}
data = {"paymentKey": key, "orderId": order_id, "amount": amount}
```

### 결제 상태 머신
```text
PENDING → CONFIRMED → PAID → (REFUNDED)
    ↓                    ↓
  CANCELLED           PARTIALLY_REFUNDED
```

---

## 3. 예약 / 스케줄링 (Booking)

### 가용성 체크 패턴
```python
def check_availability(listing_id, start_date, end_date):
    conflicts = db.query(Booking).filter(
        Booking.listing_id == listing_id,
        Booking.status != 'cancelled',
        Booking.start_date < end_date,
        Booking.end_date > start_date,
    ).count()
    return conflicts == 0
```

### 예약 생성 (동시성 제어)
```python
from sqlalchemy import select, func

async def create_booking(listing_id, user_id, start, end):
    async with db.begin():
        # SELECT FOR UPDATE — 동시 예약 방지
        listing = await db.execute(
            select(Listing).where(Listing.id == listing_id).with_for_update()
        )
        if not check_availability(listing_id, start, end):
            raise HTTPException(409, "Already booked")
        booking = Booking(listing_id=listing_id, user_id=user_id, start_date=start, end_date=end)
        db.add(booking)
    return booking
```

---

## 4. 알림 (Notification)

### 멀티 채널 알림
```python
pip install apprise  # 70+ 서비스 통합

import apprise
apobj = apprise.Apprise()
apobj.add('slack://token_a/token_b/token_c')
apobj.add('tgram://bot_token/chat_id')
apobj.add('mailto://user:pass@gmail.com')
apobj.notify(body="새 예약이 들어왔습니다!", title="알림")
```

### 이벤트 기반 알림
```python
# 이벤트 → 알림 매핑
NOTIFICATION_MAP = {
    "booking.created": {"channels": ["email", "push"], "template": "booking_confirmed"},
    "booking.cancelled": {"channels": ["email", "sms"], "template": "booking_cancelled"},
    "review.posted": {"channels": ["push"], "template": "new_review"},
    "payment.failed": {"channels": ["email", "sms", "push"], "template": "payment_failed"},
}
```

---

## 5. 피드 / 타임라인 (Feed)

### Fan-out on Write (Twitter 방식)
```python
# 글 작성 시 팔로워 전원의 타임라인 캐시에 push
async def publish_post(author_id, content):
    post = await create_post(author_id, content)
    followers = await get_followers(author_id)
    for follower_id in followers:
        await redis.lpush(f"timeline:{follower_id}", post.id)
        await redis.ltrim(f"timeline:{follower_id}", 0, 999)  # 최근 1000개만
```

### Fan-out on Read (간단 버전)
```python
# 타임라인 요청 시 팔로잉 목록의 최근 글 조합
async def get_timeline(user_id, limit=50):
    following = await get_following(user_id)
    posts = await db.query(Post).filter(
        Post.author_id.in_(following)
    ).order_by(Post.created_at.desc()).limit(limit).all()
    return posts
```

---

## 6. 검색 (Search)

### Meilisearch (간단 + 강력)
```python
pip install meilisearch

import meilisearch
client = meilisearch.Client('http://localhost:7700')
client.index('listings').add_documents([
    {"id": 1, "title": "서울 강남 원룸", "price": 50000, "city": "서울"},
    {"id": 2, "title": "부산 해운대 오션뷰", "price": 80000, "city": "부산"},
])

# 검색 (오타 허용, 필터, 정렬)
results = client.index('listings').search('강남 원룸', {
    'filter': 'price < 100000',
    'sort': ['price:asc'],
})
```

---

## 7. 파일 업로드 / 스토리지

### S3 호환 (AWS S3 / MinIO / Cloudflare R2)
```python
pip install boto3

import boto3
s3 = boto3.client('s3',
    endpoint_url='https://xxx.r2.cloudflarestorage.com',  # R2
    aws_access_key_id='KEY',
    aws_secret_access_key='SECRET',
)

# 업로드
s3.upload_file('photo.jpg', 'my-bucket', 'uploads/photo.jpg')

# 서명된 URL (임시 공개)
url = s3.generate_presigned_url('get_object',
    Params={'Bucket': 'my-bucket', 'Key': 'uploads/photo.jpg'},
    ExpiresIn=3600,
)
```

### 무료 스토리지
| 서비스 | 무료 | 특장 |
|--------|------|------|
| **Cloudflare R2** | 10GB + 1M req/월 | S3 호환, 이그레스 무료 |
| **Supabase Storage** | 1GB | PostgreSQL 연동 |
| **Firebase Storage** | 5GB | 모바일 연동 |
| **Backblaze B2** | 10GB | S3 호환, 저렴 |

---

## 8. 리뷰 / 평점

```python
class Review(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    listing_id: int = Field(foreign_key="listing.id")
    user_id: int = Field(foreign_key="user.id")
    rating: float = Field(ge=1, le=5)
    comment: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# 평균 평점 (캐시 + 실시간 업데이트)
async def update_avg_rating(listing_id):
    avg = await db.execute(
        select(func.avg(Review.rating)).where(Review.listing_id == listing_id)
    )
    await redis.set(f"rating:{listing_id}", avg.scalar())
```

---

## 9. 추천 엔진 (Recommendation)

### 콘텐츠 기반 (Content-Based)
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 아이템 유사도 계산
tfidf = TfidfVectorizer()
matrix = tfidf.fit_transform([item.description for item in items])
similarity = cosine_similarity(matrix)

def recommend(item_id, top_n=10):
    idx = item_id_to_idx[item_id]
    scores = list(enumerate(similarity[idx]))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [items[i] for i, _ in scores[1:top_n+1]]
```

### 협업 필터링 (Collaborative Filtering)
```python
pip install implicit  # ALS 협업 필터링

from implicit.als import AlternatingLeastSquares
model = AlternatingLeastSquares(factors=64)
model.fit(user_item_matrix)
recommendations = model.recommend(user_id, user_item_matrix[user_id])
```

---

## 10. 이메일 (Transactional Email)

```python
pip install resend  # 모던 이메일 API

import resend
resend.api_key = os.environ["RESEND_API_KEY"]

resend.Emails.send({
    "from": "noreply@example.com",
    "to": "user@example.com",
    "subject": "예약이 확정되었습니다",
    "html": "<h1>예약 확인</h1><p>서울 강남 원룸 - 5월 20일~22일</p>",
})
```

| 서비스 | 무료 | 특장 |
|--------|------|------|
| **Resend** | 100통/일 | 모던 API, 리액트 이메일 |
| **SendGrid** | 100통/일 | 가장 널리 쓰임 |
| **Mailgun** | 5000통/월 (3개월) | API 강력 |
| **AWS SES** | 62000통/월 (EC2 내) | 가장 저렴 |
