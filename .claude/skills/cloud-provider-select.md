---
name: cloud-provider-select
description: VPS 업체 선택 매트릭스 — Oracle Free 1순위, Vultr·AWS Lightsail·Hetzner 폴백. VPS·클라우드·원격 서버 언급 시 활성.
---

## Trigger

사용자가 다음 중 하나를 말하면 활성:
- "VPS 어떤 거 써?"
- "오라클 vs 아마존"
- "무료로 24시간 돌릴 거 없나"
- "원격 서버"
- "/exec_remote-setup" 호출 시 자동 참조

## 결정 매트릭스

| 조건 | 추천 |
|---|---|
| 무료가 절대 우선 | **Oracle Free Tier** |
| 카드 등록 거절 / 가입 실패 | Vultr ($3.50) |
| AWS 자격증/익숙함 | AWS Lightsail ($5) |
| 트래픽 폭주 (수백 GB) | Hetzner CX22 (€4.51, 트래픽 포함 큼) |
| 한국 리전 필수 | Oracle (Seoul/Chuncheon) / AWS (Seoul) |
| 일본 리전 (지연 ↓) | Vultr Tokyo / Linode Tokyo |

## 업체별 상세

### Oracle Free Tier  1순위
- **사양**: 4 OCPU ARM Ampere A1 / 24GB RAM / 200GB / 10TB outbound 무료
- **장점**: 완전 무료, 사양 압도적, Seoul·Chuncheon 리전
- **단점**: 가입 까다로움 (해외카드, 본인인증, capacity 부족 시 발급 지연)
- **함정**: "Always Free" 자원만 사용해야 함 (실수로 paid shape 만들면 과금)
- **시작**: https://signup.cloud.oracle.com

### Vultr (폴백)
- **사양**: 1 vCPU / 1GB / 25GB / 1TB 트래픽 — $3.50/월
- **장점**: 5분이면 발급, 직관적 UI
- **단점**: 사양 약함 (Claude Code 1개 인스턴스만 OK)
- **시작**: https://my.vultr.com

### AWS Lightsail
- **사양**: 1 vCPU / 1GB / 40GB / 2TB — $5/월
- **장점**: AWS 생태계 (S3·Route53 연동 쉬움)
- **단점**: EC2 와 다른 별도 콘솔 (헷갈림)
- **시작**: https://lightsail.aws.amazon.com

### Hetzner Cloud
- **사양**: CX22 — 2 vCPU / 4GB / 40GB / 20TB — €4.51/월
- **장점**: 사양 가성비 최고
- **단점**: EU 리전 (한국에서 ping ~250ms)

###  비추 — AWS EC2
- 학습 곡선 높음, 트래픽 과금 폭탄 위험
- Lightsail 로 시작 권장

## 결제 카드 안내

- Oracle: VISA/Mastercard 모두 OK, 일시 $1 검증 후 환불
- Vultr: 비트코인·Paypal 도 가능
- 카카오뱅크 글로벌 체크카드 / 트래블월렛 등 다 통과

## 응답 패턴

사용자가 막연히 물으면:
> 가입 자신 있으면 **Oracle 무료**, 카드 거절·시간 절약 원하면 **Vultr $3.50**.
> Oracle 발급되면 사양상 압도 (4 OCPU vs 1) — 성공할 때까지 시도 권장.

가입 실패 보고하면:
> Capacity 문제면 다른 시간대(미국 야간 = 한국 점심) 재시도. 카드 거절이면 Vultr 로 갈아타죠.
