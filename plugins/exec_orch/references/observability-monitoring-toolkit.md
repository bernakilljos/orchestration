# Observability & Monitoring Toolkit Reference

> **목적**: 전체 관측(Observability) 및 모니터링 생태계 종합 맵핑
> **범위**: 공통 도구 (도메인 특화 X) · 150+ 도구 · 15 카테고리
> **사용**: 프로젝트별 필요 도구 선택 후 설정

---

##  카테고리 & 도구 수 (전체 131)

| # | 카테고리 | 도구 수 | 주 목적 |
|---|---|---|---|
| 1 | **APM (Application Performance)** | 8 | 애플리케이션 성능·응답시간·트랜잭션 |
| 2 | **메트릭 (Metrics)** | 12 | 시계열 데이터 수집·저장·쿼리 |
| 3 | **로깅 (Logging)** | 14 | 로그 수집·처리·저장·검색 |
| 4 | **분산 추적 (Distributed Tracing)** | 8 | 요청 흐름 추적·지연 원인 분석 |
| 5 | **통합 관측 (Unified Observability)** | 7 | APM+메트릭+로그+추적 통합 |
| 6 | **AI/LLM 관측** | 10 | 생성형 AI·LLM 모니터링 |
| 7 | **인프라 모니터링 (Infrastructure)** | 10 | 서버·OS·네트워크·스토리지 |
| 8 | **클라우드 네이티브** | 9 | AWS·Azure·GCP·Kubernetes |
| 9 | **상태 페이지 (Status Page)** | 6 | 서비스 상태 공시·인시던트 |
| 10 | **경보/알림 (Alerting)** | 8 | 임계값 기반 알림·에스컬레이션 |
| 11 | **비용 모니터링 (Cost Management)** | 8 | 클라우드 비용·리소스 최적화 |
| 12 | **프론트엔드 모니터링** | 10 | 웹 성능·에러·사용자 행동 |
| 13 | **네트워크 (Network)** | 12 | 패킷·네트워크 지연·대역폭 분석 |
| 14 | **합성 모니터링 (Synthetic)** | 9 | 정기 헬스 체크·성능 벤치마크 |
| 15 | **SRE 도구 (Chaos Engineering)** | 8 | 카오스 테스트·복원력 검증 |

**전체 도구**: 131개 | **카테고리**: 15개

---

## 1⃣ APM (Application Performance Monitoring) — 8개

애플리케이션 성능 추적 · 응답시간 · 트랜잭션 · 병목지점 분석.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 1.1 | **Datadog** | 클라우드 APM · 통합 모니터링 · 전사 표준 | `npm i @datadog/browser-rum` / SaaS app.datadoghq.com |
| 1.2 | **New Relic** | Java/Python/Node.js APM · 자동 계측 | `npm i newrelic` / SaaS rpm.newrelic.com |
| 1.3 | **Dynatrace** | AI 기반 APM · 자동 근본원인 분석 | `npm i @dynatrace/browser-agent` / SaaS |
| 1.4 | **Elastic APM** | 오픈소스 기반 APM · ELK 통합 | `npm i elastic-apm-node` / Self-hosted |
| 1.5 | **Instana** | 실시간 APM · 자동 서비스 맵 | Java/Python 에이전트 / SaaS cloud.instana.io |
| 1.6 | **AppDynamics** | 엔터프라이즈 APM · 비즈니스 임팩트 | Java 에이전트 / SaaS |
| 1.7 | **Stackify Retrace** | .NET/Java APM · 프로파일링 | NuGet/Maven / SaaS retrace.stackify.com |
| 1.8 | **OpenTelemetry Instrumentation** | 표준 APM 계측 · 공급자 무관 | `npm i @opentelemetry/auto-instrumentations-node` / 오픈소스 |

---

## 2⃣ 메트릭 (Metrics & Time-Series) — 12개

시계열 데이터 저장 · 메트릭 수집 · 다차원 쿼리 · 시각화.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 2.1 | **Prometheus** | 오픈소스 메트릭 수집 · Pull 기반 | `docker run prom/prometheus` / Self-hosted |
| 2.2 | **Grafana** | 메트릭 시각화 · 대시보드 · 기본 도구 | `docker run grafana/grafana` / Self-hosted + SaaS |
| 2.3 | **InfluxDB** | 시계열 DB · 고속 쓰기 · 강력 쿼리 | `docker run influxdb` / Self-hosted + SaaS |
| 2.4 | **Thanos** | Prometheus 장기 저장 · 클러스터 | `go get github.com/thanos-io/thanos` / Self-hosted |
| 2.5 | **Cortex** | 다중 테넌트 메트릭 서비스 · 확장성 | `docker-compose` / Self-hosted |
| 2.6 | **VictoriaMetrics** | 고속 메트릭 DB · Prometheus 호환 | `docker run victoriametrics/victoria-metrics` / Self-hosted |
| 2.7 | **Mimir** | Grafana 메트릭 서비스 · 클라우드 네이티브 | `helm install mimir` / Self-hosted + SaaS |
| 2.8 | **OpenTSDB** | 분산 메트릭 DB · HBase 기반 | `docker run petergrace/opentsdb` / Self-hosted |
| 2.9 | **Kairos** | 시계열 DB · 빠른 쿼리 · 메타데이터 | `docker run kairosdb/kairosdb` / Self-hosted |
| 2.10 | **TimescaleDB** | PostgreSQL 시계열 확장 · SQL 기반 | `docker run timescale/timescaledb` / Self-hosted |
| 2.11 | **QuestDB** | 초고속 시계열 DB · 금융 거래 | `docker run questdb/questdb` / Self-hosted |
| 2.12 | **Graphite** | 메트릭 저장소 · 레거시 표준 | `pip install graphite-web` / Self-hosted |

---

## 3⃣ 로깅 (Logging & Log Management) — 14개

로그 수집 · 처리 · 저장 · 검색 · 분석.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 3.1 | **Elasticsearch** | 분산 검색·분석 엔진 · ELK 기초 | `docker run docker.elastic.co/elasticsearch/elasticsearch` / Self-hosted + SaaS |
| 3.2 | **Kibana** | ELK 시각화 · 로그 브라우징 | `docker run docker.elastic.co/kibana/kibana` / Self-hosted + SaaS |
| 3.3 | **Logstash** | 로그 파이프라인 · 필터·변환 | `docker run docker.elastic.co/logstash/logstash` / Self-hosted |
| 3.4 | **Loki** | 가벼운 로그 시스템 · Prometheus 스타일 | `docker run grafana/loki` / Self-hosted |
| 3.5 | **Fluentd** | 로그 통합 · 다중 출력 | `td-agent` 패키지 설치 / Self-hosted |
| 3.6 | **Fluent Bit** | 경량 로그 수집 · C 기반 | `docker run fluent/fluent-bit` / Self-hosted |
| 3.7 | **Graylog** | 중앙화 로그 관리 · 강력 검색 | `docker run graylog/graylog` / Self-hosted + SaaS |
| 3.8 | **Vector** | 로그 라우팅 · 통합 에이전트 | `curl --proto '=https' --tlsv1.2 -sSfL https://sh.vector.dev | sh` / Self-hosted |
| 3.9 | **Splunk** | 엔터프라이즈 로그 분석 · 보안 | SaaS / Self-hosted |
| 3.10 | **Sumologic** | 클라우드 로그 · 실시간 분석 | SaaS app.sumologic.com |
| 3.11 | **Papertrail** | 클라우드 로그 호스팅 · 간편 | SaaS logs.papertrailapp.com |
| 3.12 | **Sumo Logic** | 통합 로그 분석 · SIEM 기능 | SaaS |
| 3.13 | **AWS CloudWatch Logs** | AWS 로그 서비스 · 기본 제공 | AWS 콘솔 / `aws logs` CLI |
| 3.14 | **Azure Monitor Logs** | Azure 로그 · KQL 쿼리 | Azure 포털 / `az monitor` CLI |

---

## 4⃣ 분산 추적 (Distributed Tracing) — 8개

요청 흐름 추적 · 마이크로서비스 지연 분석 · 의존성 매핑.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 4.1 | **Jaeger** | 오픈소스 분산 추적 · CNCF 표준 | `docker run jaegertracing/all-in-one` / Self-hosted |
| 4.2 | **Zipkin** | 분산 추적 · 시각화 · 레거시 표준 | `docker run openzipkin/zipkin` / Self-hosted |
| 4.3 | **Tempo** | Grafana 분산 추적 · 높은 처리량 | `docker run grafana/tempo` / Self-hosted |
| 4.4 | **Lightstep** | 클라우드 분산 추적 · AI 분석 | SaaS app.lightstep.com |
| 4.5 | **AWS X-Ray** | AWS 분산 추적 · 서비스 맵 | AWS 콘솔 / SDK |
| 4.6 | **OpenTelemetry Tracing** | 표준 추적 규격 · OTLP 프로토콜 | `npm i @opentelemetry/api` / 오픈소스 |
| 4.7 | **Signoz** | 오픈소스 APM · 추적·메트릭·로그 통합 | `docker-compose` / Self-hosted |
| 4.8 | **DataDog APM Tracing** | Datadog 추적 · 자동 계측 | Datadog 에이전트 / SaaS |

---

## 5⃣ 통합 관측 (Unified Observability Stack) — 7개

APM + 메트릭 + 로그 + 추적 + 대시보드 통합 플랫폼.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 5.1 | **Grafana Stack** | Prometheus + Loki + Tempo + Mimir 통합 | `docker-compose` / Grafana Cloud |
| 5.2 | **OpenTelemetry Full Stack** | OTEL SDK + Collector + Jaeger/Tempo + Prometheus 통합 | `npm i @opentelemetry/*` / 오픈소스 |
| 5.3 | **Elastic Stack (ELK)** | Elasticsearch + Kibana + Beats + APM 통합 | `docker-compose` / Self-hosted + SaaS |
| 5.4 | **SigNoz** | 오픈소스 관측 플랫폼 · 추적·메트릭·로그 | `docker-compose` / Self-hosted |
| 5.5 | **Uptrace** | OpenTelemetry 기반 관측 | SaaS uptrace.dev |
| 5.6 | **Datadog** | 전사 관측 플랫폼 · 통합 | SaaS app.datadoghq.com |
| 5.7 | **New Relic One** | 통합 관측 플랫폼 · AI 분석 | SaaS one.newrelic.com |

---

## 6⃣ AI/LLM 관측 (AI & LLM Monitoring) — 10개

생성형 AI · LLM 토큰 · 비용 · 정확도 · 지연시간 모니터링.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 6.1 | **Langfuse** | LLM 애플리케이션 관측 · 평가 · 비용 | SaaS langfuse.com / Self-hosted |
| 6.2 | **LangSmith** | LangChain 기본 관측 · 디버깅 | SaaS smith.langchain.com |
| 6.3 | **Phoenix (Arize)** | LLM 애플리케이션 성능 · 모니터링 | SaaS / Self-hosted |
| 6.4 | **Helicone** | LLM API 모니터링 · 비용 최적화 | SaaS helicone.ai |
| 6.5 | **Lunary** | LLM 앱 성능 · A/B 테스트 | SaaS lunary.ai |
| 6.6 | **Portkey** | LLM 프로덕션 관측 · 폴오버 | SaaS portkey.ai |
| 6.7 | **Galileo** | LLM 평가 · 품질 모니터링 | SaaS rungalileo.io |
| 6.8 | **Weights & Biases** | ML 실험·평가·모니터링 | SaaS wandb.ai |
| 6.9 | **Fiddler** | ML 모델 모니터링 · 설명가능성 | SaaS fiddler.ai |
| 6.10 | **Deepchecks** | ML 데이터·모델 검증 | `pip install deepchecks` / SaaS |

---

## 7⃣ 인프라 모니터링 (Infrastructure Monitoring) — 10개

서버 · OS · 네트워크 · 스토리지 · 리소스 모니터링.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 7.1 | **Zabbix** | 오픈소스 인프라 모니터링 · 강력 | `docker run zabbix/zabbix-server-mysql` / Self-hosted |
| 7.2 | **Nagios** | 클래식 인프라 모니터링 · NRPE | `yum install nagios` / Self-hosted |
| 7.3 | **Netdata** | 실시간 모니터링 · 경량 에이전트 | `bash <(curl -Ss https://get.netdata.cloud/kickstart.sh)` / Self-hosted |
| 7.4 | **Check_MK (Checkmk)** | 엔터프라이즈 모니터링 · 자동 discovery | `docker run checkmk/check-mk-raw` / Self-hosted |
| 7.5 | **PRTG Network Monitor** | 상용 네트워크 모니터링 · 30 센서 무료 | SaaS / Self-hosted |
| 7.6 | **LibreNMS** | 오픈소스 네트워크 모니터링 · SNMP | `docker run librenms/librenms` / Self-hosted |
| 7.7 | **Prometheus Node Exporter** | 리눅스 시스템 메트릭 · Prometheus 연동 | `docker run prom/node-exporter` / Self-hosted |
| 7.8 | **collectd** | 시스템 통계 수집 · 경량 | `apt install collectd` / Self-hosted |
| 7.9 | **Telegraf** | 메트릭 수집 에이전트 · InfluxDB 연동 | `apt install telegraf` / Self-hosted |
| 7.10 | **Munin** | 리소스 추적 · 그래프 자동 생성 | `apt install munin` / Self-hosted |

---

## 8⃣ 클라우드 네이티브 (Cloud Native & Kubernetes) — 9개

AWS · Azure · GCP · Kubernetes · 컨테이너 모니터링.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 8.1 | **AWS CloudWatch** | AWS 통합 모니터링 · 메트릭·로그·알람 | AWS 콘솔 / CLI |
| 8.2 | **Azure Monitor** | Azure 통합 모니터링 · Application Insights | Azure 포털 / CLI |
| 8.3 | **Google Cloud Monitoring** | GCP 통합 모니터링 · Cloud Trace | GCP 콘솔 / CLI |
| 8.4 | **Kubernetes Dashboard** | K8s 기본 대시보드 · Pod·Node 상태 | `kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/...` |
| 8.5 | **Prometheus Operator** | K8s Prometheus 자동화 · ServiceMonitor | `helm install prometheus-community/kube-prometheus-stack` |
| 8.6 | **kube-state-metrics** | K8s 오브젝트 메트릭 · Prometheus 연동 | `helm install kube-state-metrics` |
| 8.7 | **Kubecost** | K8s 비용 모니터링 · 리소스 최적화 | `helm install kubecost/cost-analyzer` / SaaS |
| 8.8 | **Prometheus kube-apiserver** | K8s API 서버 메트릭 · 기본 제공 | Prometheus scrape config |
| 8.9 | **Container Insights (AWS)** | ECS·EKS 컨테이너 모니터링 | AWS CloudWatch / CloudFormation |

---

## 9⃣ 상태 페이지 (Status Page & Incident Management) — 6개

서비스 상태 공시 · 인시던트 추적 · 사용자 소통.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 9.1 | **Statuspage.io** | 상태 페이지 호스팅 · 사용자 친화적 | SaaS statuspage.io |
| 9.2 | **Cachet** | 오픈소스 상태 페이지 · 자체 호스팅 | `docker run cachethq/cachet` / Self-hosted |
| 9.3 | **Upptime** | GitHub 기반 상태 페이지 · 무료 | GitHub Action / Self-hosted |
| 9.4 | **Gatus** | 가벼운 상태 페이지 · 헬스 체크 | `docker run twinproduction/gatus` / Self-hosted |
| 9.5 | **Vigil** | 모니터링 + 상태 페이지 · 러스트 기반 | Self-hosted |
| 9.6 | **OneUptime** | 통합 인시던트 관리 · 상태 페이지 | SaaS / Self-hosted |

---

## 🔟 경보/알림 (Alerting & Incident Response) — 8개

임계값 기반 알림 · 에스컬레이션 · 온콜 관리 · 통합 알림.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 10.1 | **PagerDuty** | 표준 온콜 플랫폼 · 에스컬레이션 | SaaS pagerduty.com |
| 10.2 | **OpsGenie (Atlassian)** | 알림 관리 · 우선순위 | SaaS opsgenie.atlassian.net |
| 10.3 | **Alertmanager** | Prometheus 알림 관리 · 라우팅 | `docker run prom/alertmanager` / Self-hosted |
| 10.4 | **Rootly** | 인시던트 대응 자동화 · Slack 통합 | SaaS rootly.io |
| 10.5 | **incident.io** | 인시던트 추적 · 포스트모템 | SaaS incident.io |
| 10.6 | **Opsgenie**  | Atlassian 알림 · 팀 협업 | SaaS |
| 10.7 | **Victorops** | 온콜 일정 · 에스컬레이션 | SaaS victorops.com |
| 10.8 | **OnePager** | 인시던트 커뮤니케이션 · 템플릿 | SaaS onepagerapp.com |

---

## 1⃣1⃣ 비용 모니터링 (Cost Management & Optimization) — 8개

클라우드 비용 분석 · 리소스 최적화 · 예산 관리 · RI/Savings Plans.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 11.1 | **Infracost** | 테라폼 비용 분석 · CI/CD 통합 | `brew install infracost` / Self-hosted |
| 11.2 | **Kubecost** | Kubernetes 비용 분석 · Pod 단위 | `helm install kubecost/cost-analyzer` / SaaS |
| 11.3 | **CloudHealth (Broadcom)** | 멀티클라우드 비용 · RI 최적화 | SaaS / Self-hosted |
| 11.4 | **Spot.io (NetApp)** | Spot 인스턴스 활용 · 70% 절감 | SaaS spot.io |
| 11.5 | **Flexera One** | 멀티클라우드 비용·거버넌스 | SaaS |
| 11.6 | **Densify** | 클라우드 리소스 우화 · 비용 | SaaS densify.com |
| 11.7 | **CloudForecast** | 클라우드 비용 예측 · 예산 관리 | SaaS |
| 11.8 | **Vantage** | AWS·Azure·GCP 비용 비교 · 추천 | SaaS vantage.sh |

---

## 1⃣2⃣ 프론트엔드 모니터링 (Frontend & Web Performance) — 10개

웹 성능 · JavaScript 에러 · 사용자 행동 · RUM (Real User Monitoring).

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 12.1 | **Sentry** | 에러 추적·성능 모니터링 · JavaScript 필수 | `npm i @sentry/react` / SaaS + Self-hosted |
| 12.2 | **LogRocket** | 세션 리플레이 · RUM · 이슈 재현 | `npm i logrocket` / SaaS logrocket.com |
| 12.3 | **FullStory** | 디지털 경험 분석 · 세션 재생 | SaaS fullstory.com |
| 12.4 | **Hotjar** | 사용자 행동 · 히트맵 · 설문 | SaaS hotjar.com |
| 12.5 | **PostHog** | 오픈소스 분석·세션 재생 · A/B 테스트 | `npm i posthog-js` / Self-hosted + SaaS |
| 12.6 | **Highlight.io** | 오픈소스 세션 재생·에러 추적 | `npm i highlight.run` / Self-hosted + SaaS |
| 12.7 | **Datadog RUM** | Datadog 웹 성능 · 통합 | `npm i @datadog/browser-rum` |
| 12.8 | **Speedcurve** | 웹 성능 모니터링 · 시각 회귀 | SaaS speedcurve.com |
| 12.9 | **WebPageTest** | 웹 성능 분석 · 무료 오픈소스 | SaaS webpagetest.org / Self-hosted |
| 12.10 | **Grafana Faro** | 오픈소스 프론트엔드 모니터링 | `npm i @grafana/faro-web-sdk` / Self-hosted |

---

## 1⃣3⃣ 네트워크 (Network Monitoring & Analysis) — 12개

패킷 분석 · 네트워크 지연 · 대역폭 · 트래픽 분석 · DNS.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 13.1 | **Wireshark** | 패킷 분석 · 네트워크 프로토콜 디버깅 | `brew install wireshark` / Self-hosted |
| 13.2 | **tcpdump** | 패킷 캡처 · 명령줄 · 경량 | `apt install tcpdump` (기본 내장) |
| 13.3 | **mtr** | 경로 추적 · traceroute + ping 통합 | `apt install mtr` / Self-hosted |
| 13.4 | **nmap** | 네트워크 스캔 · 포트 매핑 · 보안 | `apt install nmap` / Self-hosted |
| 13.5 | **iperf3** | 네트워크 성능 · 대역폭 측정 | `apt install iperf3` / Self-hosted |
| 13.6 | **Netperf** | 네트워크 성능 · 처리량·지연 | `apt install netperf` / Self-hosted |
| 13.7 | **Grafana Loki + promtail** | 로그 기반 네트워크 분석 | `docker run grafana/loki` + Promtail |
| 13.8 | **PRTG Network Monitor** | 트래픽 모니터링 · SNMP | Self-hosted + SaaS |
| 13.9 | **Nagios** | 네트워크 인프라 모니터링 | Self-hosted |
| 13.10 | **Ping-T** | ICMP 핑 모니터링 · 가용성 | Self-hosted |
| 13.11 | **DNS 분석 도구들** | DNS 쿼리·응답·속도 분석 | `dig` / `nslookup` / `dnstop` |
| 13.12 | **Speedtest** | 인터넷 속도 측정 · 대역폭 | SaaS speedtest.net |

---

## 1⃣4⃣ 합성 모니터링 (Synthetic Monitoring) — 9개

정기적 헬스 체크 · 성능 벤치마크 · 가용성 확인 · 엣지 로케이션.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 14.1 | **Checkly** | API·웹사이트 모니터링 · Playwright 기반 | SaaS checkly.com |
| 14.2 | **Playwright Test Mode** | 합성 테스트 · 브라우저 자동화 | `npm i @playwright/test` / Self-hosted |
| 14.3 | **k6 Browser** | 성능 테스트 · JavaScript 스크립트 | `npm i k6` / Self-hosted + Cloud |
| 14.4 | **Datadog Synthetics** | Datadog 합성 모니터링 · 브라우저 테스트 | Datadog 콘솔 |
| 14.5 | **AWS CloudWatch Synthetics** | AWS 합성 모니터링 · Lambda 기반 | AWS 콘솔 |
| 14.6 | **Selenium Grid** | 브라우저 자동화 · 분산 테스트 | `docker run selenium/standalone-chrome` |
| 14.7 | **Cypress** | E2E 테스트 · 합성 시뮬레이션 | `npm i cypress` / Self-hosted |
| 14.8 | **Nightwatch** | 웹 테스트 · 자동화 | `npm i nightwatch` / Self-hosted |
| 14.9 | **Uptime Robot** | 간단한 가용성 모니터링 · 무료 | SaaS uptimerobot.com |

---

## 1⃣5⃣ SRE & Chaos Engineering (카오스 엔지니어링) — 8개

복원력 검증 · 장애 주입 · 장애 시뮬레이션 · 테스트.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 15.1 | **Chaos Monkey** | Netflix 카오스 엔지니어링 · 랜덤 인스턴스 종료 | `docker run netflixoss/chaosmonkey` / Self-hosted |
| 15.2 | **LitmusChaos** | Kubernetes 카오스 테스트 · CNCF | `helm repo add litmuschaos https://...` / Self-hosted |
| 15.3 | **Gremlin** | 클라우드 카오스 플랫폼 · 상용 | SaaS gremlin.com |
| 15.4 | **Steadybit** | 엔터프라이즈 카오스 플랫폼 | SaaS steadybit.com |
| 15.5 | **AWS Fault Injection Simulator** | AWS 인프라 장애 주입 | AWS 콘솔 |
| 15.6 | **GameDays** | 재난 훈련 · 인시던트 시뮬레이션 | Self-hosted 워크숍 |
| 15.7 | **Pumba** | Docker 컨테이너 카오스 테스트 | `docker run gaiaadm/pumba` / Self-hosted |
| 15.8 | **Chaos Toolkit** | 오픈소스 카오스 엔지니어링 | `pip install chaostoolkit` / Self-hosted |

---

## 📋 빠른 선택 가이드

### 스타트업 (비용 우선)
- 로깅: **Loki** + **Grafana**
- 메트릭: **Prometheus** + **Grafana**
- 추적: **Jaeger** / **Tempo**
- 에러: **Sentry** (무료 Tier)
- 웹: **PostHog** / **Highlight.io**

### 스케일업 (균형)
- APM: **Datadog** / **New Relic**
- 통합: **Grafana Stack** (Prometheus + Loki + Tempo)
- 인프라: **Prometheus Node Exporter** + **Grafana**
- 알림: **Alertmanager** + **PagerDuty**
- 비용: **Infracost** / **Kubecost**

### 엔터프라이즈 (기능·보안)
- APM: **Dynatrace** / **AppDynamics**
- 통합: **Elastic Stack** / **Datadog**
- 인프라: **Zabbix** / **Nagios**
- 알림: **PagerDuty** + **Rootly**
- 카오스: **Gremlin** / **Steadybit**

### AI/LLM 중심
- 추적: **Langfuse** / **LangSmith**
- 평가: **Arize Phoenix** / **Galileo**
- 비용: **Helicone**
- 통합: **OpenTelemetry** + **LLM 관측 SDK**

### Kubernetes 중심
- 기본: **Prometheus** + **Grafana** + **Kubernetes Dashboard**
- 비용: **Kubecost**
- 추적: **Jaeger** / **Tempo**
- 카오스: **LitmusChaos**

---

##  설치 패턴

### Docker Compose 스택 (로컬)
```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
  loki:
    image: grafana/loki
    ports:
      - "3100:3100"
  tempo:
    image: grafana/tempo
    ports:
      - "3200:3200"
```

### Kubernetes Helm
```bash
# Prometheus + Grafana + Loki + Tempo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack
helm install loki grafana/loki-stack
helm install tempo grafana/tempo
```

### NPM 클라이언트 (Frontend)
```bash
npm i @opentelemetry/api @opentelemetry/sdk-web @opentelemetry/auto-instrumentations-web
npm i @sentry/react
npm i @datadog/browser-rum
npm i logrocket
npm i posthog-js
```

---

## 🔗 통합 맵

```text
┌─────────────────────────────────────────────────────────────────┐
│                    관측 통합 플랫폼 (5)                           │
│    (Grafana Stack, ELK, Datadog, SigNoz, OpenTelemetry)       │
└───────────┬─────────────────────┬──────────────┬────────────────┘
            │                     │              │
      ┌─────┴─────┐         ┌─────┴──────┐    ┌─┴─────────────┐
      │            │         │            │    │               │
   메트릭(2)    로깅(3)   추적(4)      APM(1)   AI/LLM(6)
   Prometheus  Loki      Jaeger       Datadog   Langfuse
   Grafana    Logstash   Zipkin       New Relic LangSmith
   InfluxDB   Fluentd    Tempo        Dynatrace Phoenix
   │            │         │            │        │
   └─────────────┼─────────┼────────────┼────────┘
                 │         │            │
            ┌────┴─────────┴────────────┴──────────┐
            │                                       │
        인프라(7)                        경보(10)/비용(11)
        Zabbix                         PagerDuty
        Prometheus                     OpsGenie
        Netdata                        Alertmanager
            │                               │
            └───────────┬───────────────────┘
                        │
                    ┌───┴───────────────────┐
                    │                       │
                프론트엔드(12)         합성 모니터링(14)
                Sentry                  Checkly
                LogRocket               k6
                FullStory               Playwright
```

---

##  도구별 주요 특징 비교

### 메트릭 저장소
| 도구 | 처리량 | 장기저장 | 비용 | 학습곡선 |
|---|---|---|---|---|
| Prometheus | 중 | 약 | 무료 | 낮음 |
| InfluxDB | 매우 높음 | 강 | 중간 | 중간 |
| VictoriaMetrics | 매우 높음 | 강 | 낮음 | 중간 |
| Mimir | 매우 높음 | 강 | 중간 | 높음 |

### 로그 시스템
| 도구 | 속도 | 확장성 | 비용 | 검색능력 |
|---|---|---|---|---|
| Elasticsearch | 중 | 높음 | 높음 | 매우 강 |
| Loki | 높음 | 중 | 낮음 | 중간 |
| Splunk | 매우 높음 | 매우 높음 | 매우 높음 | 매우 강 |

### 분산 추적
| 도구 | 처리량 | UI | 저장소 | 비용 |
|---|---|---|---|---|
| Jaeger | 높음 | 훌륭 | 유연 | 무료 |
| Tempo | 매우 높음 | 중간 | Loki만 | 낮음 |
| Lightstep | 매우 높음 | 매우 좋음 | 클라우드 | 높음 |

---

## ⚡ 성능 기준

### 처리량 (초당 이벤트)
- **초고속** (>1M/sec): VictoriaMetrics, Mimir, Tempo, Splunk
- **고속** (100K-1M): Prometheus, InfluxDB, Elasticsearch
- **중간** (10K-100K): Loki, Grafana, New Relic

### 저장소 용량 (월)
- **매우 큼** (>100GB): Elasticsearch, Splunk, InfluxDB
- **중간** (10-100GB): Prometheus, Loki, Tempo
- **작음** (<10GB): Graphite, OpenTSDB

---

## 🔐 보안 고려사항

- **데이터 암호화**: TLS (전송), AES-256 (저장소)
- **접근제어**: RBAC (Role-Based Access Control)
- **감사 추적**: 모든 쓰기 작업 기록
- **규정 준수**: GDPR, HIPAA, SOC 2

---

## 참고

- 도구 활성 개발 여부: 주간 커밋 확인 (GitHub)
- 커뮤니티 규모: GitHub Star · StackOverflow 질문
- 상용 지원: 엔터프라이즈 구독 가능 여부
- 통합성: OpenTelemetry, Prometheus, Docker, Kubernetes 지원
