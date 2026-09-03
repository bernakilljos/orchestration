# Workflow Automation Toolkit — Common Reference

> **목적**: 로우코드부터 고급 워크플로우 엔진까지 150+ 도구 한글 정리
> **범위**: 자동화 전문가가 자주 쓰는 공통 스택
> **업데이트**: 2026-05-20
> **사용**: 다른 도메인의 자동화 구축 시 먼저 참고. 강점·약점·조합 패턴 포함

---

## 1⃣ 로우코드 자동화 플랫폼 (10개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 1 | **n8n** | 자체호스팅 가능한 오픈소스 자동화 플랫폼 (Zapier 대안) | `docker pull n8nio/n8n` · https://n8n.io |
| 2 | **Zapier** | 클라우드 자동화 (6,000+ 앱 연동) | https://zapier.com (가입) |
| 3 | **Make (구 Integromat)** | 고급 필터·매핑·다중 조건 자동화 | https://make.com (가입) |
| 4 | **IFTTT** | 간단한 "If This Then That" 규칙 (IoT·스마트홈) | https://ifttt.com (가입) |
| 5 | **Power Automate** | Microsoft 365 통합 자동화 (클라우드) | https://powerautomate.microsoft.com |
| 6 | **Tray.io** | 엔터프라이즈 자동화 (보안·감시 강화) | https://tray.io (가입) |
| 7 | **Workato** | 엔터프라이즈급 클라우드 통합 | https://workato.com (가입) |
| 8 | **Boomi** | 하이브리드·멀티 클라우드 통합 플랫폼 | https://boomi.com (가입) |
| 9 | **MuleSoft** | 엔터프라이즈 API 관리·통합 | https://www.mulesoft.com (가입) |
| 10 | **Automation.cloud** | 저비용 자동화 (스타트업) | https://automation.cloud (가입) |

---

## 2⃣ 워크플로우 엔진 (12개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 11 | **Temporal** | 마이크로서비스 워크플로우 (내구성 보장) | `npm install @temporalio/client` |
| 12 | **Apache Airflow** | Python 기반 데이터 파이프라인 오케스트레이션 | `pip install apache-airflow` · https://airflow.apache.org |
| 13 | **Prefect** | 현대식 데이터 플로우 (Airflow 대안, 더 간단) | `pip install prefect` · https://prefect.io |
| 14 | **Dagster** | 데이터 오케스트레이션·자산 기반 (타입 안전) | `pip install dagster` · https://dagster.io |
| 15 | **Windmill** | 오픈소스 내부도구 + 워크플로우 (낮은 레이턴시) | `docker pull ghcr.io/windmill-labs/windmill:latest` · https://windmill.dev |
| 16 | **Inngest** | 서버리스 워크플로우 (Temporal 라이트) | `npm install inngest` · https://inngest.com |
| 17 | **Kestra** | 클라우드 네이티브 워크플로우 (Java·Python) | `docker pull kestra/kestra` · https://kestra.io |
| 18 | **Conductor** | 마이크로서비스 오케스트레이션 (Netflix) | `docker pull conductoross/conductor-server` · https://conductor.netflix.com |
| 19 | **Argo Workflows** | Kubernetes 네이티브 워크플로우 | https://argoproj.github.io/argo-workflows |
| 20 | **Tekton** | Kubernetes CI/CD 파이프라인 | https://tekton.dev |
| 21 | **AWS Step Functions** | 클라우드 상태머신 기반 워크플로우 | AWS Console (가입) |
| 22 | **Google Cloud Workflows** | GCP 워크플로우 오케스트레이션 | Google Cloud Console (가입) |

---

## 3⃣ 이벤트 기반 자동화 (11개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 23 | **AWS EventBridge** | 이벤트 버스 (수백 AWS 서비스 연동) | AWS Console |
| 24 | **AWS Lambda** | 서버리스 함수 (이벤트 트리거) | AWS Console |
| 25 | **Google Cloud Functions** | GCP 서버리스 함수 | Google Cloud Console |
| 26 | **Azure Functions** | Microsoft 함수형 컴퓨팅 | Azure Portal |
| 27 | **Trigger.dev** | TypeScript 기반 클라우드 워크플로우 | `npm install @trigger.dev/sdk` · https://trigger.dev |
| 28 | **Encore** | Go·TypeScript 이벤트 기반 API | https://encore.dev |
| 29 | **Pub/Sub (GCP)** | 메시지 큐 + 구독 아키텍처 | Google Cloud Console |
| 30 | **SNS (AWS)** | Simple Notification Service | AWS Console |
| 31 | **RabbitMQ** | 메시지 브로커 (AMQP, 자체호스팅) | `docker run -d rabbitmq` · https://www.rabbitmq.com |
| 32 | **Apache Kafka** | 분산 이벤트 스트리밍 플랫폼 | https://kafka.apache.org |
| 33 | **Redpanda** | Kafka 호환 (더 빠름) | `docker run -it redpandadata/redpanda` |

---

## 4⃣ 폼·설문·수집 (10개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 34 | **Typeform** | 아름다운 폼 + 자동화 (조건부 로직) | https://typeform.com (가입) |
| 35 | **Google Forms** | 무료 폼 (Google Sheet 자동 저장) | https://forms.google.com (Google 계정) |
| 36 | **Tally** | 프라이빗하고 빠른 폼 (Typeform 대안) | https://tally.so (가입) |
| 37 | **Fillout** | API 기반 폼 (개발자 친화) | https://fillout.com · `npm install @fillout/react` |
| 38 | **Formbricks** | 오픈소스 설문 플랫폼 (자체호스팅) | `docker pull formbricks/formbricks` · https://formbricks.com |
| 39 | **SurveyJS** | JavaScript 오픈소스 설문 엔진 | `npm install survey-core` · https://surveyjs.io |
| 40 | **Jotform** | 광범위 폼 빌더 (150+ 템플릿) | https://jotform.com (가입) |
| 41 | **Formstack** | 엔터프라이즈 폼·서명 | https://www.formstack.com (가입) |
| 42 | **Qualtrics** | 고급 설문·피드백 (분석 강화) | https://www.qualtrics.com (가입) |
| 43 | **SurveySparrow** | 멀티채널 설문 (SMS·앱·웹) | https://www.surveysparrow.com (가입) |

---

## 5⃣ 문서 자동화·전자서명 (10개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 44 | **DocuSign** | 전자서명 표준 (법적 효력) | https://www.docusign.com (가입) |
| 45 | **PandaDoc** | 문서 자동화 + 서명 + eSign | https://www.pandadoc.com (가입) |
| 46 | **DocuSeal** | 오픈소스 전자서명 (자체호스팅) | `docker pull docusealco/docuseal` · https://docuseal.co |
| 47 | **Jotform Sign** | Jotform 내 eSign (저비용) | https://www.jotform.com/products/sign |
| 48 | **HelloSign (Dropbox Sign)** | Dropbox 소유, 간단한 서명 | https://www.hellosign.com (가입) |
| 49 | **Adobe Sign** | Adobe 통합 전자서명 | https://www.adobe.com/sign (가입) |
| 50 | **SignatureFlow** | 한국 국내 전자서명 | https://www.signatureflow.com (가입) |
| 51 | **Document Automation (Microsoft)** | Word+Power Apps 문서 생성 | Microsoft 365 구독 |
| 52 | **Vanta** | 준수 자동화 + 문서 추적 | https://www.vanta.com (가입) |
| 53 | **Contract.ai** | AI 계약 분석·자동화 | https://contract.ai (가입) |

---

## 6⃣ 일정·스케줄링 (10개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 54 | **cal.com** | 오픈소스 캘린더 (Calendly 대안) | `docker pull calcom/cal.com` · https://cal.com |
| 55 | **Calendly** | 인기 있는 스케줄링 (Google Calendar 연동) | https://calendly.com (가입) |
| 56 | **SavvyCal** | 팀 스케줄링 (시간대 자동 최적화) | https://savvycal.com (가입) |
| 57 | **TidyCal** | 저렴한 Calendly 대안 | https://www.tidycal.com (가입) |
| 58 | **Acuity Scheduling** | 서비스 예약 (결제 통합) | https://acuityscheduling.com (가입) |
| 59 | **Setmore** | 프리 스케줄링 + SMS 알림 | https://www.setmore.com (가입) |
| 60 | **YouCanBookMe** | 개인 일정 공유 (커스텀 필드) | https://youcanbook.me (가입) |
| 61 | **SimplyBook.me** | 비즈니스 예약 (다중 직원) | https://simplybook.me (가입) |
| 62 | **Appointy** | 멀티 서비스 예약 앱 | https://www.appointy.com (가입) |
| 63 | **BookingBug (Insider)** | 클래스·서비스 예약 | https://www.insider.com/bookingbug (가입) |

---

## 7⃣ 프로젝트 관리·추적 (12개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 64 | **Linear** | 현대식 이슈 추적 (개발팀 우선) | https://linear.app (가입) |
| 65 | **Jira** | 전통 이슈·스프린트 관리 (Atlassian) | https://www.atlassian.com/software/jira (가입) |
| 66 | **Asana** | 시각적 작업 관리 (캔반·타임라인) | https://asana.com (가입) |
| 67 | **Monday.com** | 워크OS (유연한 뷰) | https://monday.com (가입) |
| 68 | **ClickUp** | 올인원 작업 (100+ 기능) | https://clickup.com (가입) |
| 69 | **Notion Projects** | Notion 내 프로젝트 보드 | https://notion.so (가입) |
| 70 | **Plane** | 오픈소스 프로젝트 (자체호스팅) | `docker run -d -p 3000:3000 planepowers/plane:latest` |
| 71 | **OpenProject** | 오픈소스 프로젝트·간트 | https://www.openproject.org |
| 72 | **Taiga** | 애자일 관리 (오픈소스) | `docker pull taigaio/taiga-back` · https://taiga.io |
| 73 | **Trello** | 간단한 캔반 (가벼움) | https://trello.com (가입) |
| 74 | **GitHub Projects** | GitHub 내 프로젝트 관리 | GitHub 계정 |
| 75 | **GitLab** | DevOps 플랫폼 (프로젝트 포함) | https://gitlab.com (가입) |

---

## 8⃣ 노코드 앱 빌더 (10개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 76 | **Retool** | 내부도구 빌더 (DB·API 연결) | `docker run retool/backend` · https://retool.com |
| 77 | **Appsmith** | 오픈소스 내부도구 (자체호스팅) | `docker run appsmith/appsmith` · https://appsmith.com |
| 78 | **Budibase** | 오픈소스 로우코드 (자동화 강화) | `docker run -p 10000:10000 budibase/budibase` |
| 79 | **ToolJet** | 오픈소스 내부도구 (한글 커뮤니티) | `docker run tooljet/tooljet:latest` |
| 80 | **Directus** | 오픈소스 헤드리스 CMS (API 우선) | `npm install -g @directus/cli` · https://directus.io |
| 81 | **NocoDB** | 오픈소스 스마트 스프레드시트 (DB 조작) | `docker run nocodb/nocodb:latest` |
| 82 | **Airtable** | 클라우드 스프레드시트 + 자동화 | https://airtable.com (가입) |
| 83 | **FlutterFlow** | 비주얼 모바일 앱 빌더 | https://flutterflow.io (가입) |
| 84 | **WeWeb** | 프론트엔드 빌더 (백엔드 API 연동) | https://www.weweb.io (가입) |
| 85 | **Bildr** | 풀 스택 앱 빌더 (드래그앤드롭) | https://www.bildr.com (가입) |

---

## 9⃣ 데이터 통합·ETL (12개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 86 | **Airbyte** | 오픈소스 데이터 통합 (ELT) | `docker run airbyte/server:latest` · https://airbyte.com |
| 87 | **Fivetran** | 클라우드 데이터 통합 (빠른 설정) | https://fivetran.com (가입) |
| 88 | **Stitch** | Talend 소유, 간단 ELT | https://www.stitchdata.com (가입) |
| 89 | **dlt (Data Load Tool)** | Python 기반 오픈소스 ELT | `pip install dlt[redshift]` · https://dlthub.com |
| 90 | **Singer** | 오픈소스 데이터 표준 (탭·타겟) | https://www.singer.io · `pip install pipelinewise` |
| 91 | **Meltano** | 오픈소스 ELT 플랫폼 (Singer 기반) | `pip install meltano` · https://meltano.com |
| 92 | **Talend** | 엔터프라이즈 데이터 통합 | https://www.talend.com (가입) |
| 93 | **Informatica** | 엔터프라이즈 데이터 품질·통합 | https://www.informatica.com (가입) |
| 94 | **DBT (Data Build Tool)** | 데이터 변환 (SQL·Python) | `pip install dbt-core` · https://www.getdbt.com |
| 95 | **Pentaho** | BI·ETL 통합 (오픈소스·상용) | https://www.pentaho.com |
| 96 | **Apache NiFi** | 데이터 흐름 자동화 (자체호스팅) | https://nifi.apache.org |
| 97 | **Keboola** | 클라우드 데이터 스택 | https://keboola.com (가입) |

---

## 🔟 RPA (로봇 프로세스 자동화, 8개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 98 | **UiPath** | 엔터프라이즈 RPA (가장 인기) | https://www.uipath.com (가입) |
| 99 | **Automation Anywhere** | 엔터프라이즈 RPA (AI 강화) | https://www.automationanywhere.com (가입) |
| 100 | **Power Automate Desktop** | Microsoft RPA (Desktop + Cloud) | Windows 또는 Microsoft 365 |
| 101 | **Robocorp** | 오픈소스 RPA (Python·Robot Framework) | `pip install robocorp` · https://robocorp.com |
| 102 | **TagUI** | 오픈소스 웹 자동화 | `npm install -g tagui` · https://tagui.readthedocs.io |
| 103 | **PyAutoGUI** | Python 화면·마우스 자동화 | `pip install pyautogui` |
| 104 | **Selenium** | 웹 브라우저 자동화 (테스트 외) | `pip install selenium` · https://www.selenium.dev |
| 105 | **OpenRPA** | 오픈소스 RPA (C#·Python) | https://github.com/open-rpa/openrpa |

---

## 1⃣1⃣ API 관리·개발 (10개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 106 | **Postman** | API 테스트·문서·자동화 | https://www.postman.com (가입) |
| 107 | **Hoppscotch** | 오픈소스 API 클라이언트 (자체호스팅) | `docker run hoppscotch/hoppscotch-ce:latest` |
| 108 | **Insomnia** | 경량 REST 클라이언트 | https://insomnia.rest (다운로드) |
| 109 | **REST Client (VS Code)** | VS Code 확장 (곧바로 API 테스트) | `code --install-extension humao.rest-client` |
| 110 | **Swagger/OpenAPI** | API 사양 표준 | https://swagger.io · `npm install -g @openapitools/openapi-generator-cli` |
| 111 | **Stoplight** | API 설계·문서화·테스트 | https://stoplight.io (가입) |
| 112 | **Kong** | 오픈소스 API 게이트웨이 | `docker run kong:latest` · https://konghq.com |
| 113 | **Apigee (Google)** | 엔터프라이즈 API 관리 | https://cloud.google.com/apigee (가입) |
| 114 | **AWS API Gateway** | AWS API 호스팅·관리 | AWS Console |
| 115 | **CloudFlare** | CDN·API 보안 | https://www.cloudflare.com (가입) |

---

## 1⃣2⃣ 웹훅·이벤트 배송 (8개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 116 | **Svix** | 웹훅 인프라 (신뢰성·재시도) | `npm install svix` · https://www.svix.com (가입) |
| 117 | **Hookdeck** | 웹훅 모니터링·재시도 | https://hookdeck.com (가입) |
| 118 | **ngrok** | 로컬 서버 터널 (개발 웹훅 테스트) | `brew install ngrok` · https://ngrok.com |
| 119 | **localtunnel** | 오픈소스 로컬 터널 | `npm install -g localtunnel` |
| 120 | **Smee.io** | 무료 웹훅 프록시 | https://smee.io (가입 불필요) |
| 121 | **RequestBin** | 웹훅 디버깅 (요청 검사) | https://requestbin.com |
| 122 | **Webhook.cool** | 임시 웹훅 엔드포인트 | https://webhook.cool |
| 123 | **Webhookit** | 웹훅 관리·로깅 | https://webhookit.com (가입) |

---

## 1⃣3⃣ 작업 큐·비동기 처리 (10개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 124 | **Celery** | Python 분산 작업 큐 | `pip install celery` · https://docs.celeryproject.io |
| 125 | **Bull (Node)** | Redis 기반 Job 큐 (Node.js) | `npm install bull` · https://github.com/OptimalBits/bull |
| 126 | **BullMQ** | Bull 최신 버전 (TypeScript) | `npm install bullmq` · https://docs.bullmq.io |
| 127 | **Sidekiq** | Ruby 작업 큐 | `gem install sidekiq` · https://sidekiq.org |
| 128 | **Faktory** | 언어 중립 작업 서버 | https://contribsys.com/faktory · `docker pull contribsys/faktory:latest` |
| 129 | **TaskTiger** | Redis 기반 작업 큐 (Python) | `pip install tasktiger` |
| 130 | **Resque** | Ruby/Redis 작업 큐 | `gem install resque` |
| 131 | **ActiveJob (Rails)** | Rails 내장 작업 큐 | Rails 기본 포함 |
| 132 | **APScheduler** | Python 스케줄러 (대체 cron) | `pip install apscheduler` · https://apscheduler.readthedocs.io |
| 133 | **Huey** | Python 마이크로 작업 큐 | `pip install huey` |

---

## 1⃣4⃣ 크론·스케줄링 (10개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 134 | **crontab** | Unix 표준 스케줄러 (이미 설치) | `crontab -e` (Linux/Mac) |
| 135 | **Cron (Windows Task Scheduler)** | Windows 예약 작업 | 제어판 또는 `schtasks` |
| 136 | **node-cron** | Node.js 크론 표현식 | `npm install node-cron` · https://github.com/node-cron/node-cron |
| 137 | **cron (Python)** | Python 크론 라이브러리 | `pip install python-cron` |
| 138 | **schedule (Python)** | Python 간단 스케줄러 | `pip install schedule` · https://schedule.readthedocs.io |
| 139 | **Ofelia** | Docker 컨테이너 크론 (자동화) | `docker run -d -v /var/run/docker.sock:/var/run/docker.sock mcuadros/ofelia daemon --docker` |
| 140 | **Supercronic** | crontab 호환 크론 (컨테이너) | `docker run -d mcuadros/supercronic` |
| 141 | **Chronos** | 분산 스케줄러 (Mesos 기반) | https://mesos.apache.org/documentation/latest/chronos |
| 142 | **Quartz** | Java 엔터프라이즈 스케줄러 | https://www.quartz-scheduler.org |
| 143 | **Joblib** | Python 병렬 작업·캐싱 | `pip install joblib` · https://joblib.readthedocs.io |

---

## 1⃣5⃣ 알림·노티피케이션 (12개)

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 144 | **ntfy** | 오픈소스 푸시 알림 (자체호스팅) | `docker run -d -p 80:80 binwiederhier/ntfy` |
| 145 | **Gotify** | 오픈소스 메시지 서버 (자체호스팅) | `docker pull gotify/server:latest` |
| 146 | **Pushover** | 푸시 알림 (iOS·Android·데스크톱) | https://pushover.net (가입) |
| 147 | **Apprise** | 멀티채널 알림 (60+ 서비스) | `pip install apprise` · https://github.com/caronc/apprise |
| 148 | **Shoutrrr** | 알림 라우터 (20+ 서비스) | `docker pull shoutrrr/shoutrrr` · https://containrrr.dev/shoutrrr |
| 149 | **Twilio** | SMS·음성 알림 (글로벌) | https://www.twilio.com (가입) |
| 150 | **SendGrid** | 이메일 API | https://sendgrid.com (가입) |
| 151 | **Amazon SNS** | AWS 메시지 배송 | AWS Console |
| 152 | **Google Cloud Pub/Sub** | GCP 메시지 큐 | Google Cloud Console |
| 153 | **Slack API** | Slack 메시지·봇 | https://api.slack.com (가입) |
| 154 | **Discord Webhooks** | Discord 메시지 자동화 | https://discord.com (가입) |
| 155 | **Microsoft Teams Webhooks** | Teams 메시지·알림 | Microsoft 365 (가입) |

---

## 추가 도구 (심화) — 8개

| # | 이름 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 156 | **Zapier + Webhooks** | 웹훅으로 Zapier 밖 커스텀 연동 | Zapier Platform (가입) |
| 157 | **OpenFaaS** | 오픈소스 서버리스 플랫폼 | `kubectl apply -f https://openfaas.github.io/...` |
| 158 | **Knative** | Kubernetes 서버리스 (Google 지원) | https://knative.dev |
| 159 | **Dapr** | 마이크로서비스 상태·이벤트 (Microsoft) | https://dapr.io |
| 160 | **MinIO** | S3 호환 오브젝트 스토리지 (자동화 데이터) | `docker run minio/minio server /data` |
| 161 | **OpenStack** | 오픈소스 클라우드 (자동화 인프라) | https://www.openstack.org |
| 162 | **Docker Compose** | 멀티 컨테이너 오케스트레이션 | `docker-compose up` (Docker 설치 필요) |
| 163 | **Kubernetes (K8s)** | 컨테이너 오케스트레이션 (대규모) | https://kubernetes.io |

---

## 📋 빠른 선택 가이드

### 상황별 추천 조합

| 상황 | 추천 스택 |
|---|---|
| **완전 초보자** | Zapier 또는 n8n + Google Forms + Airtable |
| **스타트업** | n8n + Plane + cal.com + Retool |
| **데이터 중심** | Airflow + dbt + Airbyte + Dagster |
| **Slack 기반 자동화** | n8n + Slack API + Apprise |
| **엔터프라이즈** | Temporal + Airflow + Kafka + UiPath |
| **마이크로서비스** | Temporal + Dapr + OpenFaaS + Kafka |
| **내부도구** | Retool + Linear + Notion Projects |
| **문서 생성** | PandaDoc + Zapier + Directus |
| **실시간 이벤트** | Kafka + EventBridge + Trigger.dev |
| **RPA (UI 자동화)** | Robocorp + TagUI 또는 Power Automate Desktop |

---

## 🔗 강점·약점 비교 (핵심 3개)

### n8n vs Zapier vs Make

| 항목 | n8n | Zapier | Make |
|---|---|---|---|
| 호스팅 |  자체호스팅 | ☁ 클라우드만 | ☁ 클라우드만 |
| 앱 수 | 350+ | 6000+ | 3000+ |
| 조건부 로직 |  강화 |  기본 |  강화 |
| 비용 | $ 저렴 (자체호스팅) | $$ 중상 | $ 저렴 |
| 학습곡선 | 중상 | 낮음 | 낮음 |

### Airflow vs Prefect vs Dagster

| 항목 | Airflow | Prefect | Dagster |
|---|---|---|---|
| 학습곡선 | 높음 (DAG 문법) | 낮음 (Python) | 중상 (자산) |
| 데이터 관측 |  기본 |  우수 |  우수 |
| 타입 안전 |  없음 |  부분 |  강화 |
| 커뮤니티 | 매우 큼 (Apache) | 성장 | 성장 |
| 엔터프라이즈 |  확립 | 진행 중 | 진행 중 |

---

##  참고 문서

- n8n Docs: https://docs.n8n.io
- Airflow 튜토리얼: https://airflow.apache.org/docs/apache-airflow/stable/tutorial.html
- Temporal 개념: https://temporal.io/learn
- 자동화 패턴: `docs/automation-checklist.md`

---

**마지막 업데이트**: 2026-05-20 | **도구 수**: 163개
