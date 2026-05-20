# Social Platform API COMMON Toolkit

> **Scope**: Social/YouTube plugin (`mcp_social`, `cost_youtube`) 공통 도구 카탈로그  
> **용도**: YouTube, Instagram, TikTok, Twitter/X, 네이버, 분석 도구 일괄 참조  
> **업데이트**: 2026-05-20  
> **관리**: plugins/exec_orch/references/ (동기화 불필요, 참조 전용)

---

## 1. YouTube API & 도구

| 도구/라이브러리 | 설명 | 설치/API |
|---|---|---|
| **YouTube Data API v3** | 공식 API (채널, 영상, 댓글, 분석) | [developers.google.com/youtube](https://developers.google.com/youtube) |
| **youtube-dl** | 영상 다운로드 (레거시, 유지보수 중단) | `pip install youtube-dl` |
| **yt-dlp** | youtube-dl 포크 (활발 유지보수) | `pip install yt-dlp` 또는 `apt install yt-dlp` |
| **pytube** | 간단한 YouTube 다운로더 (Python) | `pip install pytube` |
| **pafy** | 메타데이터 + 스트림 URL 추출 | `pip install pafy` |
| **youtube-transcript-api** | YouTube 자막 추출 | `pip install youtube-transcript-api` |
| **YouTube Analytics API** | 채널 분석 (조회수, 시청시간 등) | [developers.google.com/youtube/analytics](https://developers.google.com/youtube/analytics) |
| **vidIQ** | YouTube SEO 최적화 도구 | [vidiq.com](https://www.vidiq.com) (Free/$10~$200/month) |
| **TubeBuddy** | YouTube 채널 관리, 키워드 연구 | [tubebuddy.com](https://www.tubebuddy.com) (Free/$9.99~$39.99/month) |
| **Social Blade** | YouTube 채널 통계 및 순위 | [socialblade.com](https://www.socialblade.com) (Free/$25+/year) |
| **Descript** | 영상 자막 자동 생성, 편집 | [descript.com](https://www.descript.com) ($24/month) |
| **Opus Clip** | 긴 영상 → 쇼츠 자동 생성 | [opusclip.com](https://www.opusclip.com) (Free/$10~$100/month) |
| **Pictory** | 텍스트/블로그 → 영상 자동 생성 | [pictory.ai](https://pictory.ai) ($25~$300/month) |
| **Synthesia** | AI 아바타 영상 생성 | [synthesia.io](https://www.synthesia.io) ($30~$840/month) |
| **Google Sheets + YT API** | Google Sheets로 유튜브 통계 관리 | gspread 라이브러리 |

---

## 2. Instagram API & 도구

| 도구/라이브러리 | 설명 | 설치/가격 |
|---|---|---|
| **Instagram Graph API** | 공식 API (Meta 제공, 비즈니스 계정 필요) | [developers.facebook.com/docs/instagram-api](https://developers.facebook.com/docs/instagram-api) |
| **instagrapi** | 비공식 Instagram API (Python) | `pip install instagrapi` |
| **InstaPy** | Instagram 자동화 봇 (레거시, 유지보수 중단) | `pip install instapy` |
| **Instaloader** | 사진, 비디오, 스토리 다운로드 | `pip install instaloader` |
| **instagram-api-py** | Instagram API 래퍼 | `pip install instagram-api-py` |
| **Hootsuite** | Instagram 관리 + 스케줄링 | [hootsuite.com](https://hootsuite.com) ($49~/month) |
| **Later** | Instagram 스케줄링 + 분석 | [later.com](https://www.later.com) ($15~/month) |
| **Buffer** | 멀티플랫폼 스케줄링 | [buffer.com](https://buffer.com) ($5~$100/month) |
| **Metricool** | 멀티플랫폼 분석 | [metricool.com](https://metricool.com) (Free/$19~/month) |
| **JPER** | Instagram 분석 대시보드 | [jper.io](https://jper.io) |
| **Sprout Social** | 엔터프라이즈 소셜 관리 | [sproutsocial.com](https://www.sproutsocial.com) ($89~/month) |
| **Brandwatch** | 소셜 리스닝 + 분석 | [brandwatch.com](https://www.brandwatch.com) |
| **Upfluence** | 인플루언서 마케팅 | [upfluence.com](https://www.upfluence.com) |

---

## 3. TikTok API & 도구

| 도구/라이브러리 | 설명 | 설치/API |
|---|---|---|
| **TikTok for Developers** | 공식 API (개발자 신청 필수) | [developers.tiktok.com](https://developers.tiktok.com) |
| **TikAPI** | TikTok 비공식 API (Python) | `pip install TikTok` |
| **tiktokapipy** | TikTok 데이터 스크래핑 | `pip install tiktokapipy` |
| **TikTok Creator Marketplace** | 공식 광고/협력 플랫폼 | [tiktok.com/creator](https://www.tiktok.com/creator) |
| **CapCut** | TikTok 공식 영상 편집 앱 | [capcut.com](https://www.capcut.com) (Free) |
| **CapCut API** | CapCut 영상 생성 API | [capcut.com/api](https://www.capcut.com/api) (제한 공개) |
| **TikTok Creative Center** | 공식 영감 + 트렌드 | [tiktok.com/creative-center](https://www.tiktok.com/creative-center) |
| **Opus Clip** | TikTok Shorts 자동 생성 | [opusclip.com](https://www.opusclip.com) |
| **Later** | TikTok 스케줄링 + 분석 | [later.com](https://www.later.com) |
| **Hootsuite** | TikTok 관리 + 분석 | [hootsuite.com](https://hootsuite.com) |
| **Social Blade** | TikTok 크리에이터 순위 | [socialblade.com](https://www.socialblade.com) |

---

## 4. X (Twitter) API & 도구

| 도구/라이브러리 | 설명 | 설치 |
|---|---|---|
| **X API v2** | 공식 API (트윗, DM, 검색) | [developer.twitter.com/docs/twitter-api](https://developer.twitter.com/docs/twitter-api) |
| **tweepy** | X API Python 라이브러리 | `pip install tweepy` |
| **snscrape** | X/Twitter 스크래핑 (비공식) | `pip install snscrape` |
| **Tweetdeck** | X 공식 관리 도구 (웹) | [tweetdeck.twitter.com](https://tweetdeck.twitter.com) (Free) |
| **Hootsuite** | X 스케줄링 + 분석 | [hootsuite.com](https://hootsuite.com) |
| **Buffer** | X 스케줄링 + 분석 | [buffer.com](https://buffer.com) |
| **Sprout Social** | 엔터프라이즈 X 관리 | [sproutsocial.com](https://www.sproutsocial.com) |
| **Mention** | 브랜드 모니터링 | [mention.com](https://mention.com) |
| **Talkwalker** | 소셜 리스닝 | [talkwalker.com](https://www.talkwalker.com) |
| **Brandwatch** | 경쟁사 모니터링 | [brandwatch.com](https://www.brandwatch.com) |

---

## 5. 네이버 플랫폼 & API

| 도구/서비스 | 설명 | 링크 |
|---|---|---|
| **Naver Blog API** | 블로그 글쓰기, 통계 | [developers.naver.com/docs/blog](https://developers.naver.com/docs/blog) |
| **SearchAdvisor** | SEO 키워드 관리 | [searchadvisor.naver.com](https://searchadvisor.naver.com) |
| **Naver Analytics** | 블로그/카페 통계 | Naver 관리자 센터 |
| **Naver DataLab** | 검색 트렌드 분석 | [datalab.naver.com](https://datalab.naver.com) |
| **Naver SmartStore API** | 스마트스토어 관리 | [developers.naver.com](https://developers.naver.com) |
| **Papago API** | 자동 번역 (네이버) | [developers.naver.com/docs/papago](https://developers.naver.com/docs/papago) |
| **Clova API** | AI 음성/이미지 인식 (네이버) | [developers.naver.com/docs/clova](https://developers.naver.com/docs/clova) |
| **Naver Video** | 동영상 업로드 + 수익화 | [video.naver.com](https://video.naver.com) |
| **Naver Band** | 커뮤니티 관리 | [band.us](https://band.us) |
| **카페** | 네이버 카페 관리 | [cafe.naver.com](https://cafe.naver.com) |

---

## 6. Tistory & 개인 블로그 플랫폼

| 도구/API | 설명 | 링크 |
|---|---|---|
| **Tistory Open API** | Tistory 블로그 관리 API | [tistory.com/open/api](https://www.tistory.com/open/api) |
| **Tistory 플러그인** | 커스텀 플러그인 개발 | [tistory.com/guide](https://www.tistory.com/guide) |
| **RSS 피드** | Tistory RSS 피드 자동화 | `https://example.tistory.com/rss` |
| **WordPress.com API** | 워드프레스 블로그 API | [developer.wordpress.com](https://developer.wordpress.com) |
| **Medium API** | Medium 글쓰기 + 통계 | [medium.com/developers](https://medium.com/developers) |
| **Hashnode API** | 개발자 블로그 API | [hashnode.com/api](https://hashnode.com/api) |
| **Dev.to API** | Dev.to 개발 커뮤니티 API | [dev.to/api](https://dev.to/api) |

---

## 7. 소셜 관리 플랫폼 (멀티플랫폼)

| 도구 | 지원 플랫폼 | 가격 |
|---|---|---|
| **Buffer** | Facebook, Instagram, LinkedIn, Twitter, TikTok, YouTube | $5~$100/month |
| **Hootsuite** | 모든 주요 플랫폼 | $49~$739/month |
| **Later** | Instagram, Pinterest, TikTok, LinkedIn | $15~$50/month |
| **Sprout Social** | 모든 플랫폼 (엔터프라이즈) | $89~$249/month |
| **Metricool** | Instagram, Facebook, LinkedIn, Pinterest, TikTok, YouTube | Free/$19~$99/month |
| **Agorapulse** | 모든 주요 플랫폼 | $49~$299/month |
| **Sendible** | 모든 플랫폼 (SMB/엔터프라이즈) | $25~$199/month |
| **MeetEdgar** | 모든 플랫폼 + 콘텐츠 라이브러리 | $49~$199/month |
| **HubSpot Social** | 소셜 + CRM 통합 | Free/$50+/month |
| **Zapier** | 소셜 연동 자동화 | Free/$25+/month |
| **IFTTT** | 소셜 트리거 자동화 | Free/$9.99/month |
| **Make** (구 Integromat) | 소셜 워크플로우 | Free/$9.99~$299/month |

---

## 8. 분석 & 모니터링

| 도구 | 설명 | 가격 |
|---|---|---|
| **Social Blade** | YouTube, Instagram, TikTok, Twitch 통계 | Free / $25+/year |
| **Brandwatch** | 브랜드 모니터링 + 경쟁사 분석 | Enterprise 가격 |
| **Mention** | 브랜드 + 키워드 모니터링 | $20~/month |
| **Talkwalker** | 소셜 리스닝 + 경쟁 분석 | Enterprise 가격 |
| **Sentoo** | 감정 분석 (한글 지원) | Free/Pro |
| **Brandseye** | 브랜드 리스닝 | Enterprise 가격 |
| **HubSpot Analytics** | 소셜 + 웹 분석 | Free/$50+/month |
| **Google Analytics 4** | 소셜 트래픽 추적 | Free |
| **Mixpanel** | 이벤트 기반 분석 | Free/$999+/month |
| **Amplitude** | 사용자 행동 분석 | Free/$995+/month |
| **Segment** | 데이터 통합 플랫폼 | Free/$120+/month |

---

## 9. 콘텐츠 제작 도구

| 도구 | 설명 | 가격 |
|---|---|---|
| **Canva** | 그래픽 + 영상 디자인 | Free/$120~$180/year |
| **CapCut** | 영상 편집 (TikTok 공식) | Free |
| **Opus Clip** | 긴 영상 → 쇼츠 자동 생성 | Free/$10~$100/month |
| **InShot** | 모바일 영상 편집 | Free/$99.99/year |
| **Descript** | 자동 자막 + 음성 편집 | Free/$24/month |
| **Synthesia** | AI 아바타 영상 생성 | $25~$840/month |
| **Pictory** | 텍스트 → 영상 자동 생성 | $25~$300/month |
| **Adobe Premiere Rush** | 프로 영상 편집 | $9.99/month |
| **Adobe Express** | 빠른 그래픽 생성 | Free/Premium |
| **Figma** | 디자인 콜라보 | Free/$12+/month |
| **Adobe Firefly** | AI 생성형 이미지 | 포함 (Creative Cloud) |
| **Midjourney** | AI 아트 생성 | $10~$120/month |
| **DALL-E** | OpenAI 이미지 생성 | 종량제 |
| **Runway ML** | AI 영상 효과 | Free/$12~$76/month |

---

## 10. 인플루언서 & 협력 플랫폼

| 도구 | 설명 | 가격 |
|---|---|---|
| **Upfluence** | 인플루언서 마케팅 | 구독형 |
| **HypeAuditor** | 인플루언서 데이터베이스 | Free/$99+/month |
| **Modash** | 인플루언서 발견 + 캠페인 | Free/$99+/month |
| **AspireIQ** | 인플루언서 매칭 | Enterprise 가격 |
| **Creator.co** | 인플루언서 협력 플랫폼 | Free |
| **GRIN** | 소셜 네트워킹 | Enterprise 가격 |
| **Famebit** (Google) | 크리에이터 협력 마켓 | [famebit.com](https://www.famebit.com) |
| **Barter** | 상품 협찬 거래소 | [barter.com](https://barter.com) |
| **Fohr** | 인플루언서 + 브랜드 네트워크 | Enterprise 가격 |

---

## 11. 라이브 스트리밍 도구

| 도구 | 플랫폼 | 설명 |
|---|---|---|
| **OBS Studio** | 모든 플랫폼 | 무료 라이브 스트리밍 소프트웨어 |
| **Streamlabs OBS** | YouTube, Twitch, Facebook | OBS 기반 + 모네타이제이션 |
| **XSplit** | YouTube, Twitch, Facebook | 프로 레벨 스트리밍 |
| **YouTube Live** | YouTube | 공식 라이브 스트리밍 |
| **Facebook Live** | Facebook | 공식 라이브 기능 |
| **Instagram Live** | Instagram | 공식 라이브 기능 |
| **TikTok Live** | TikTok | 공식 라이브 + 선물 수익 |
| **Twitch** | 게임 스트리밍 | [twitch.tv](https://www.twitch.tv) |
| **Restream** | 멀티플랫폼 동시 라이브 | Free/$15~$60/month |

---

## 12. 댓글 & 커뮤니티 관리

| 도구 | 설명 | 가격 |
|---|---|---|
| **Comment Analyzer** | YouTube 댓글 분석 | Free |
| **Moderation API** | 자동 스팸/악플 탐지 | API 종량제 |
| **ModerationGuard** | AI 악플 자동 삭제 | Free/$9.99+/month |
| **Community Pulse** | 커뮤니티 톤 분석 | Enterprise 가격 |
| **Zendesk** | 고객 커뮤니티 관리 | $69~/month |
| **Mighty Networks** | 브랜드 커뮤니티 앱 | Free/$68/month |
| **Circle** | 온라인 커뮤니티 | $29~/month |
| **Slack** | 팀 커뮤니케이션 | Free/$7.25+/month |
| **Discord** | 크리에이터 커뮤니티 | Free/Premium |

---

## 13. 한글 소셜 도구 (K-콘텐츠)

| 도구 | 플랫폼 | 설명 |
|---|---|---|
| **Naver Analytics** | 블로그/카페 | 한국 SEO 통계 |
| **KOMCA** | 음악 저작권 | 한국 음악 저작권 관리 |
| **Podbbang** | 팟캐스트 | 한국 팟캐스트 호스팅 |
| **수요미식회** 등 조회 | YouTube | 한국 인기 쇼 + 콘텐츠 |
| **네이버 트렌드** | 네이버 | 한국 검색 트렌드 |
| **GS 홈쇼핑 등** | 라이브커머스 | 한국 라이브쇼핑 |
| **당근마켓** | 로컬 커뮤니티 | 지역 콘텐츠 |
| **번개장터** | 중고 거래 | 한국 거래 커뮤니티 |

---

## 14. 링크 단축 & URL 트래킹

| 도구 | 설명 | 가격 |
|---|---|---|
| **Bitly** | URL 단축 + 분석 | Free/$35~$500/month |
| **TinyURL** | 간단한 URL 단축 | Free |
| **Rebrandly** | 커스텀 도메인 단축 | Free/$30+/month |
| **ClickMeter** | 클릭 추적 + 분석 | $20~/month |
| **Trackly** | 소셜 링크 추적 | Free/$99+/month |
| **Branch** | 모바일 디ープ링크 | Free/Enterprise |

---

## 15. 콘텐츠 캘린더 & 기획

| 도구 | 설명 | 가격 |
|---|---|---|
| **Asana** | 팀 프로젝트 + 소셜 캘린더 | Free/$10.99~/month |
| **Monday.com** | 워크플로우 관리 | $9~/month |
| **Notion** | 협업 노트 + 캘린더 | Free/$10/month |
| **Coda** | 문서 + 프로젝트 | Free/$10~/month |
| **Trello** | 칸반 보드 | Free/$5~/month |
| **Google Calendar** | 일정 관리 | Free (Google 계정) |
| **Excel/Sheets 템플릿** | 자체 캘린더 | Free |
| **Loom** | 영상 리뷰 + 협업 | Free/$10~/month |

---

## 16. AI & 자동화

| 도구 | 설명 | 가격 |
|---|---|---|
| **ChatGPT** | 텍스트 생성 (캡션, 스크립트) | Free/$20/month |
| **Claude** | 고급 텍스트 생성 | Free/$20/month |
| **Jasper** | 마케팅 카피 생성 | $39~/month |
| **Copy.ai** | 마케팅 텍스트 AI | Free/$49+/month |
| **Midjourney** | AI 아트 생성 | $10~$120/month |
| **DALL-E 3** | OpenAI 이미지 생성 | 종량제 |
| **Zapier** | 소셜 워크플로우 자동화 | Free/$25+/month |
| **Make** | 복잡한 자동화 | Free/$9.99~$299/month |
| **IFTTT** | 간단한 트리거 자동화 | Free/$9.99/month |
| **Eleven Labs** | AI 음성 생성 | Free/$11+/month |

---

## 17. 라이브러리 & Python SDK

| 라이브러리 | 설명 | 설치 |
|---|---|---|
| **tweepy** | X API Python 클라이언트 | `pip install tweepy` |
| **instagrapi** | Instagram 자동화 | `pip install instagrapi` |
| **facebook-sdk** | Facebook API | `pip install facebook-sdk` |
| **python-telegram-bot** | Telegram 봇 | `pip install python-telegram-bot` |
| **tweepy-async** | 비동기 X API | `pip install tweepy-async` |
| **google-api-client** | Google API 클라이언트 | `pip install google-auth google-api-python-client` |
| **requests** | HTTP 요청 (모든 API) | `pip install requests` |
| **aiohttp** | 비동기 HTTP | `pip install aiohttp` |
| **schedule** | 작업 스케줄 | `pip install schedule` |
| **pandas** | 데이터 분석 + API 결과 | `pip install pandas` |

---

## 참조

- **YouTube 최적화 가이드**: [YouTube SEO 완벽 가이드](docs/2026-05-20/youtube-seo-guide.md)
- **Instagram 알고리즘**: [Instagram Algorithm 2026](docs/2026-05-20/instagram-algorithm.md)
- **TikTok 바이럴 전략**: [TikTok Viral Strategy](docs/2026-05-20/tiktok-viral.md)
- **소셜 스케줄링 비교**: [Buffer vs Hootsuite vs Later](docs/2026-05-20/scheduling-comparison.md)
- **API 통합 튜토리얼**: [YouTube API 시작하기](docs/2026-05-20/youtube-api-tutorial.md)
- **한국 소셜 마케팅**: [네이버·카카오 전략](docs/2026-05-20/korean-social-strategy.md)

---

**최종 업데이트**: 2026-05-20  
**총 도구 개수**: 180+  
**플랫폼**: YouTube, Instagram, TikTok, Twitter/X, 네이버, Tistory + 멀티플랫폼  
**카테고리**: 17개 (API, 도구, 분석, 관리, 창작, 커뮤니티)  
**유지보수**: 월별 신규 도구 추가
