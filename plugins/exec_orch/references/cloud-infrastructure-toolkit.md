# Cloud Infrastructure (Advanced) Toolkit Reference

> **목적**: 클라우드 인프라 고급 생태계 종합 맵핑 · IaC, AWS/Azure/GCP, 멀티클라우드, 컨테이너, 서버리스, 비용 최적화
> **범위**: 공통 도구 (도메인 특화 X) · 180+ 도구 · 12 카테고리
> **사용**: 프로젝트별 필요 도구 선택 후 설정 · terraform + Kubernetes + observability 조합 권장

---

## 🌍 카테고리 & 도구 수 (전체 181)

| # | 카테고리 | 도구 수 | 주 목적 |
|---|---|---|---|
| 1 | **IaC (Infrastructure as Code)** | 16 | Terraform, OpenTofu, Pulumi, CDK, CloudFormation, Bicep, Ansible, Chef, Puppet, SaltStack |
| 2 | **AWS 서비스 (Amazon Web Services)** | 24 | EC2, Lambda, ECS/EKS, S3, RDS, DynamoDB, SQS/SNS, CloudFront, Route53, IAM, CloudWatch, Secrets Manager |
| 3 | **Azure 서비스 (Microsoft Azure)** | 16 | App Service, Functions, AKS, Blob Storage, Cosmos DB, Service Bus, Front Door, Key Vault, Bicep |
| 4 | **GCP 서비스 (Google Cloud Platform)** | 14 | Compute, Cloud Run, GKE, Cloud Storage, BigQuery, Pub/Sub, Vertex AI, Secret Manager |
| 5 | **멀티클라우드 (Multi-Cloud)** | 11 | Terraform Cloud, env0, Spacelift, Scalr, Atlantis, CloudBridge, Zappa, Hybridcube |
| 6 | **서버리스 (Serverless)** | 14 | AWS Lambda, Azure Functions, Cloud Functions, Vercel Functions, Netlify Functions, Cloudflare Workers, Deno Deploy |
| 7 | **컨테이너 오케스트레이션 (Kubernetes)** | 18 | Kubernetes, Helm, Kustomize, ArgoCD, Flux, Rancher, K3s, kind, minikube, kubeadm, kubespray |
| 8 | **서비스 메시 (Service Mesh)** | 9 | Istio, Linkerd, Consul Connect, Cilium, Envoy, Open Service Mesh, NGINX Service Mesh |
| 9 | **DNS/도메인/CDN** | 18 | Cloudflare, Route53, Cloud DNS, NS1, DNSimple, Fastly, Akamai, BunnyCDN, KeyCDN, Bunny |
| 10 | **비용 최적화 (Cost Optimization)** | 14 | Infracost, Kubecost, Spot.io, CloudZero, vantage, nuvista, Prosimo, FinOps Foundation |
| 11 | **백업/DR (Backup & Disaster Recovery)** | 13 | Velero, Restic, Longhorn, AWS Backup, Azure Backup, Commvault, Veeam, Bacula |
| 12 | **GitOps/배포 자동화 (GitOps & Deployment)** | 14 | ArgoCD, Flux, Jenkins, GitLab CI, GitHub Actions, CircleCI, Harness, Spinnaker |

**전체 도구**: 181개 | **카테고리**: 12개

---

## 1⃣ IaC (Infrastructure as Code) — 16개

코드로 인프라 정의 · 버전 관리 · 자동 배포 · 멱등성.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 1.1 | **Terraform** | 가장 인기 IaC · 멀티클라우드 · HCL 언어 | `terraform init && terraform plan && terraform apply` / www.terraform.io |
| 1.2 | **OpenTofu** | Terraform 오픈소스 포크 · 완전 호환 | `opentofu init && opentofu apply` / opentofu.org |
| 1.3 | **Pulumi** | 프로그래밍 언어 IaC · Python/Go/TypeScript | `pulumi new aws-python && pulumi up` / pulumi.com |
| 1.4 | **AWS CDK (Cloud Development Kit)** | TypeScript/Python IaC · AWS 최적 | `npm install -g aws-cdk && cdk deploy` / aws.amazon.com/cdk |
| 1.5 | **AWS CloudFormation** | AWS 네이티브 IaC · YAML/JSON | AWS 콘솔 또는 `aws cloudformation create-stack` / aws.amazon.com |
| 1.6 | **Bicep** | Azure ARM 간단 언어 · 더 읽기 쉬움 | `az bicep build --file main.bicep` / microsoft.com/bicep |
| 1.7 | **Azure Resource Manager (ARM)** | Azure IaC · JSON 기반 | Azure 포털 또는 `az deployment group create` / azure.microsoft.com |
| 1.8 | **Google Deployment Manager** | GCP IaC · YAML/Python | `gcloud deployment-manager deployments create` / cloud.google.com |
| 1.9 | **Ansible** | 에이전트리스 자동화 · 순차 실행 · 멱등성 | `ansible-playbook playbook.yml` / ansible.com |
| 1.10 | **Chef** | 구성 관리 · Ruby 기반 | `chef-client` 또는 `chef-zero` / chef.io |
| 1.11 | **Puppet** | 선언형 구성 관리 · 엔터프라이즈 | `puppet agent --test` / puppet.com |
| 1.12 | **SaltStack** | 원격 실행 + 구성 관리 · 확장성 | `salt '*' state.apply` / saltproject.io |
| 1.13 | **Crossplane** | Kubernetes-native IaC · CRD 기반 | `kubectl apply -f crossplane-provider.yaml` / crossplane.io |
| 1.14 | **Terraform Cloud** | Terraform 호스팅 · 상태 관리 · 팀 협업 | `terraform cloud login && terraform apply` / app.terraform.io |
| 1.15 | **CloudFormation Designer** | AWS 비주얼 IaC · 끌어 놓기 | AWS 콘솔 / aws.amazon.com/cloudformation |
| 1.16 | **Customization Engine (Kustomize)** | Kubernetes 템플릿 엔진 · 오버레이 | `kustomize build . \| kubectl apply -f -` / kustomize.io |

---

## 2⃣ AWS 서비스 (Amazon Web Services) — 24개

AWS 주요 서비스 · 컴퓨팅 · 데이터베이스 · 네트워킹 · 보안.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 2.1 | **EC2 (Elastic Compute Cloud)** | 가상 머신 · 스케일 유연성 · 기본 컴퓨팅 | AWS 콘솔 또는 `aws ec2 run-instances` / console.aws.amazon.com |
| 2.2 | **Lambda** | 서버리스 함수 · 이벤트 기반 · 자동 스케일 | `aws lambda create-function` / console.aws.amazon.com |
| 2.3 | **ECS (Elastic Container Service)** | 컨테이너 오케스트레이션 · EC2/Fargate | `aws ecs create-service` / console.aws.amazon.com |
| 2.4 | **EKS (Elastic Kubernetes Service)** | 관리형 Kubernetes · AWS 최적화 | `eksctl create cluster` / console.aws.amazon.com |
| 2.5 | **S3 (Simple Storage Service)** | 객체 저장소 · 무제한 확장 · 강력 검색 | `aws s3 cp file.txt s3://bucket/` / console.aws.amazon.com |
| 2.6 | **RDS (Relational Database Service)** | 관리형 SQL DB · MySQL/PostgreSQL/MariaDB/Oracle/MSSQL | `aws rds create-db-instance` / console.aws.amazon.com |
| 2.7 | **DynamoDB** | NoSQL DB · 완전 관리형 · 초저지연 | `aws dynamodb create-table` / console.aws.amazon.com |
| 2.8 | **SQS (Simple Queue Service)** | 메시지 큐 · 비동기 처리 · 장기 보유 | `aws sqs create-queue` / console.aws.amazon.com |
| 2.9 | **SNS (Simple Notification Service)** | 메시지 발행·구독 · 팬아웃 · 다중 채널 | `aws sns create-topic` / console.aws.amazon.com |
| 2.10 | **CloudFront** | 글로벌 CDN · 엣지 캐싱 · DDoS 보호 | `aws cloudfront create-distribution` / console.aws.amazon.com |
| 2.11 | **Route53** | 관리형 DNS · 도메인 등록 · 헬스 체크 | `aws route53 create-hosted-zone` / console.aws.amazon.com |
| 2.12 | **IAM (Identity & Access Management)** | 사용자·역할·권한 · 세분화 제어 | AWS 콘솔 / console.aws.amazon.com |
| 2.13 | **CloudWatch** | 모니터링·로그·메트릭 · 통합 관측 | `aws logs create-log-group` / console.aws.amazon.com |
| 2.14 | **Secrets Manager** | 시크릿 관리 · 자동 로테이션 · 감사 | `aws secretsmanager create-secret` / console.aws.amazon.com |
| 2.15 | **Systems Manager (SSM)** | 파라미터 스토어 · 상태 관리 · 패치 | `aws ssm put-parameter` / console.aws.amazon.com |
| 2.16 | **Step Functions** | 워크플로우 오케스트레이션 · 상태 머신 | AWS 콘솔 / console.aws.amazon.com |
| 2.17 | **Bedrock** | 관리형 생성형 AI · 다중 모델 · API 호출 | `aws bedrock invoke-model` / console.aws.amazon.com |
| 2.18 | **SageMaker** | 머신러닝 플랫폼 · 전체 ML 생명주기 | SageMaker Studio / sagemaker.aws.amazon.com |
| 2.19 | **Kinesis** | 스트리밍 데이터 · 실시간 분석 | `aws kinesis create-stream` / console.aws.amazon.com |
| 2.20 | **ElastiCache** | 인메모리 캐시 · Redis/Memcached | `aws elasticache create-cache-cluster` / console.aws.amazon.com |
| 2.21 | **VPC (Virtual Private Cloud)** | 격리 네트워크 · 서브넷·라우팅 · 보안 | AWS 콘솔 / console.aws.amazon.com |
| 2.22 | **Auto Scaling** | 자동 스케일링 · 부하 기반 · 비용 효율 | `aws autoscaling create-auto-scaling-group` / console.aws.amazon.com |
| 2.23 | **Load Balancer (ALB/NLB)** | 로드 밸런싱 · 고가용성 · 기술별 분산 | `aws elbv2 create-load-balancer` / console.aws.amazon.com |
| 2.24 | **EventBridge** | 이벤트 라우팅 · 워크플로우 자동화 | `aws events put-rule` / console.aws.amazon.com |

---

## 3⃣ Azure 서비스 (Microsoft Azure) — 16개

Azure 주요 서비스 · 엔터프라이즈 기능 · Microsoft 통합.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 3.1 | **App Service** | 웹앱 호스팅 · Node.js/Python/.NET 지원 | `az appservice plan create && az webapp create` / portal.azure.com |
| 3.2 | **Azure Functions** | 서버리스 함수 · 다양한 트리거 | `func new && func start` / portal.azure.com |
| 3.3 | **AKS (Azure Kubernetes Service)** | 관리형 Kubernetes · Kubernetes 호환 | `az aks create` / portal.azure.com |
| 3.4 | **Blob Storage** | 객체 저장소 · 대용량 파일 · 계층 | `az storage blob upload` / portal.azure.com |
| 3.5 | **Cosmos DB** | 글로벌 NoSQL · 다중 모델 · SLA 99.99% | `az cosmosdb create` / portal.azure.com |
| 3.6 | **Service Bus** | 메시지 큐·토픽 · 엔터프라이즈 메시징 | `az servicebus queue create` / portal.azure.com |
| 3.7 | **Front Door** | 글로벌 로드 밸런싱 · DDoS 보호 | `az network front-door create` / portal.azure.com |
| 3.8 | **Azure AI Services** | 생성형 AI · Vision · Language · OpenAI | `az cognitiveservices account create` / portal.azure.com |
| 3.9 | **Key Vault** | 시크릿·키·인증서 관리 · 감사 | `az keyvault create` / portal.azure.com |
| 3.10 | **Bicep** | ARM 간단 문법 · 더 읽기 쉬운 IaC | `bicep build main.bicep` / microsoft.com/bicep |
| 3.11 | **Azure SQL Database** | 관리형 SQL · 자동 패치·백업 | `az sql server create` / portal.azure.com |
| 3.12 | **Azure DevOps** | CI/CD · 저장소 · 파이프라인 | `azure-cli 설치 후 로그인` / dev.azure.com |
| 3.13 | **Azure Monitor** | 모니터링·로그·메트릭 · Application Insights | `az monitor metrics list` / portal.azure.com |
| 3.14 | **Azure Virtual Machines** | IaaS 가상 머신 · 유연한 OS 선택 | `az vm create` / portal.azure.com |
| 3.15 | **Azure Container Instances (ACI)** | 컨테이너 호스팅 · 간편 배포 | `az container create` / portal.azure.com |
| 3.16 | **Azure Policy** | 정책 적용 · 규정 준수 · 감사 | `az policy assignment create` / portal.azure.com |

---

## 4⃣ GCP 서비스 (Google Cloud Platform) — 14개

GCP 주요 서비스 · 데이터 분석 · AI 우수.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 4.1 | **Compute Engine** | IaaS 가상 머신 · VM 인스턴스 · 자동 스케일 | `gcloud compute instances create` / cloud.google.com |
| 4.2 | **Cloud Run** | 서버리스 컨테이너 · 도커 실행 · 자동 스케일 | `gcloud run deploy` / cloud.google.com |
| 4.3 | **GKE (Google Kubernetes Engine)** | 관리형 Kubernetes · 자동 업그레이드 | `gcloud container clusters create` / cloud.google.com |
| 4.4 | **Cloud Storage** | 객체 저장소 · 글로벌 배포 · 관리 편의 | `gsutil cp file.txt gs://bucket/` / cloud.google.com |
| 4.5 | **BigQuery** | 데이터 웨어하우스 · 대규모 분석 · SQL | `bq load` / bigquery.cloud.google.com |
| 4.6 | **Pub/Sub** | 메시지 발행·구독 · 실시간 스트리밍 | `gcloud pubsub topics create` / cloud.google.com |
| 4.7 | **Cloud DNS** | 관리형 DNS · 낮은 지연 · 고가용성 | `gcloud dns managed-zones create` / cloud.google.com |
| 4.8 | **Cloud CDN** | 글로벌 CDN · 엣지 캐싱 · DDoS 보호 | GCP 콘솔에서 CDN 활성화 / cloud.google.com |
| 4.9 | **Vertex AI** | 통합 ML 플랫폼 · AutoML · LLM API | `gcloud ai models deploy` / cloud.google.com |
| 4.10 | **Secret Manager** | 시크릿 관리 · 버전 관리 · 감사 | `gcloud secrets create` / cloud.google.com |
| 4.11 | **Cloud SQL** | 관리형 SQL · MySQL/PostgreSQL | `gcloud sql instances create` / cloud.google.com |
| 4.12 | **Firestore** | NoSQL DB · 실시간 동기화 · 모바일 최적 | `gcloud firestore create-database` / cloud.google.com |
| 4.13 | **Cloud Load Balancing** | 글로벌 로드 밸런싱 · 멀티 계층 | GCP 콘솔 / cloud.google.com |
| 4.14 | **Cloud Build** | CI/CD 서비스 · 컨테이너 빌드 · 자동 배포 | `gcloud builds submit` / cloud.google.com |

---

## 5⃣ 멀티클라우드 (Multi-Cloud Orchestration) — 11개

여러 클라우드 관리 · 일관된 배포 · 벤더 락인 회피.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 5.1 | **Terraform Cloud** | Terraform 호스팅 · 멀티클라우드 관리 · 상태 동기화 | `terraform login && terraform apply` / app.terraform.io |
| 5.2 | **env0** | Terraform/Pulumi 플랫폼 · 비용 관리 · RBAC | UI 로그인 후 환경 생성 / env0.com |
| 5.3 | **Spacelift** | Terraform 거버넌스 · 정책 적용 · 감시 | UI 로그인 후 스택 생성 / spacelift.io |
| 5.4 | **Scalr** | Terraform 엔터프라이즈 · 규정 준수 · 보안 | UI 로그인 후 환경 생성 / scalr.com |
| 5.5 | **Atlantis** | Terraform CI/CD · GitHub/GitLab 통합 · Pull Request | `atlantis server --gh-user --gh-token` / runatlantis.com |
| 5.6 | **CloudBridge** | 멀티클라우드 네트워킹 · 일관된 보안 | CloudBridge 콘솔 / cloudbridges.com |
| 5.7 | **Zappa** | Python 서버리스 배포 · AWS Lambda 자동화 | `pip install zappa && zappa deploy production` / zappa.readthedocs.io |
| 5.8 | **Hybridcube** | 멀티클라우드 관리 · 단일 제어 패널 | Hybridcube 콘솔 / hybridcube.io |
| 5.9 | **HashiCorp Consul** | 서비스 메시 · 서비스 디스커버리 · 멀티클라우드 | `consul agent -server -ui` / consul.io |
| 5.10 | **Bedrock Multi-Model** | 다중 클라우드 LLM API · 일관된 인터페이스 | AWS 콘솔 / bedrock.aws.amazon.com |
| 5.11 | **Karpenter** | Kubernetes 자동 스케일링 · 클라우드 최적화 | `helm install karpenter` / karpenter.sh |

---

## 6⃣ 서버리스 (Serverless Computing) — 14개

코드 실행 · 인프라 관리 없음 · 자동 스케일 · 사용량 기반 요금.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 6.1 | **AWS Lambda** | 이벤트 기반 함수 · 다양한 트리거 · 자동 스케일 | `aws lambda create-function` / console.aws.amazon.com |
| 6.2 | **Azure Functions** | C#/Python/JavaScript 함수 · HTTP/Timer 트리거 | `func new && func start` / portal.azure.com |
| 6.3 | **Google Cloud Functions** | Python/Node.js 함수 · Pub/Sub 트리거 | `gcloud functions deploy` / cloud.google.com |
| 6.4 | **Vercel Functions** | Edge Functions · Next.js 통합 · 글로벌 배포 | Vercel 콘솔에서 함수 생성 / vercel.com |
| 6.5 | **Netlify Functions** | JavaScript 함수 · AWS Lambda 백엔드 · 간편 배포 | Netlify 콘솔 또는 `netlify functions:list` / netlify.com |
| 6.6 | **Cloudflare Workers** | Edge 함수 · Wasm 지원 · 글로벌 실행 | `wrangler publish` / workers.cloudflare.com |
| 6.7 | **Deno Deploy** | TypeScript/JavaScript Edge 함수 · 글로벌 CDN | Deno 콘솔 또는 Git 연결 / deno.com/deploy |
| 6.8 | **IBM Cloud Functions** | OpenWhisk 기반 · Python/JavaScript/Go | `ibmcloud fn action create` / cloud.ibm.com |
| 6.9 | **OpenFaas** | 오픈소스 함수 플랫폼 · Kubernetes 위 | `faas-cli new && faas-cli up` / openfaas.com |
| 6.10 | **Knative** | Kubernetes 서버리스 · 자동 스케일 | `kubectl apply -f knative-service.yaml` / knative.dev |
| 6.11 | **AWS SAM (Serverless Application Model)** | Lambda 템플릿 · 로컬 테스트 | `sam build && sam deploy` / aws.amazon.com/serverless/sam |
| 6.12 | **Serverless Framework** | 멀티클라우드 배포 · 플러그인 지원 | `npm install -g serverless && serverless deploy` / serverless.com |
| 6.13 | **Fission** | Kubernetes 기반 함수 플랫폼 · 빠른 시작 | `fission env create && fission function create` / fission.io |
| 6.14 | **Supabase Edge Functions** | PostgreSQL + Edge 함수 · Deno 런타임 | Supabase 콘솔 / supabase.com |

---

## 7⃣ 컨테이너 오케스트레이션 (Kubernetes) — 18개

컨테이너 자동 배포 · 스케일링 · 자동 복구 · 롤링 업데이트.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 7.1 | **Kubernetes (k8s)** | 컨테이너 오케스트레이션 표준 · CNCF · 복잡성 높음 | `kubectl apply -f deployment.yaml` / kubernetes.io |
| 7.2 | **Helm** | Kubernetes 패키지 관리자 · 차트 · 템플릿 | `helm install release chart/name` / helm.sh |
| 7.3 | **Kustomize** | Kubernetes 템플릿 엔진 · 오버레이 · 중복 제거 | `kustomize build . \| kubectl apply -f -` / kustomize.io |
| 7.4 | **ArgoCD** | GitOps CD · Git 소스 진실 · 자동 동기화 | `kubectl apply -n argocd -f argocd-app.yaml` / argocd.io |
| 7.5 | **Flux** | GitOps 도구 · 선언형 업데이트 · Helm 통합 | `flux install && flux create source git` / fluxcd.io |
| 7.6 | **Rancher** | Kubernetes 관리 플랫폼 · 멀티 클러스터 · UI | Rancher UI 또는 `helm install rancher` / rancher.com |
| 7.7 | **K3s** | 경량 Kubernetes · IoT/엣지 최적 · <100MB | `curl -sfL https://get.k3s.io \| sh` / k3s.io |
| 7.8 | **kind** | Kubernetes in Docker · 로컬 테스트 | `kind create cluster && kubectl apply -f app.yaml` / kind.sigs.k8s.io |
| 7.9 | **minikube** | 단일 노드 Kubernetes · 로컬 개발 · VM/Docker | `minikube start && kubectl apply -f app.yaml` / minikube.sigs.k8s.io |
| 7.10 | **kubeadm** | Kubernetes 클러스터 초기화 · 수동 관리 | `kubeadm init && kubeadm join` / kubernetes.io/docs/reference/setup-tools/kubeadm |
| 7.11 | **kubespray** | Kubernetes 자동 배포 · Ansible 기반 | `ansible-playbook -i inventory.ini cluster.yml` / kubespray.io |
| 7.12 | **Docker Swarm** | 경량 오케스트레이션 · Kubernetes 대안 · 단순 | `docker swarm init && docker service create` / docs.docker.com/engine/swarm |
| 7.13 | **OpenShift** | Kubernetes 배포판 · Red Hat · 엔터프라이즈 | OpenShift 콘솔 / redhat.com/openshift |
| 7.14 | **Nomad** | 멀티 워크로드 오케스트레이션 · HashiCorp · 유연 | `nomad job run app.hcl` / nomadproject.io |
| 7.15 | **ECS (AWS Elastic Container Service)** | AWS 컨테이너 · Kubernetes 대안 · 간편 | `aws ecs create-service` / aws.amazon.com/ecs |
| 7.16 | **Kubernetes Operator** | 커스텀 Kubernetes 리소스 · CRD · 자동화 | `kubectl apply -f operator.yaml` / kubernetes.io/docs/concepts/extend-kubernetes/operator |
| 7.17 | **Kubelet** | Kubernetes 노드 에이전트 · Pod 실행 | Kubernetes 설치 시 자동 포함 / kubernetes.io |
| 7.18 | **Kubectl** | Kubernetes CLI · 가장 중요한 도구 | `kubectl version --client` / kubernetes.io/docs/reference/kubectl |

---

## 8⃣ 서비스 메시 (Service Mesh) — 9개

마이크로서비스 통신 · 트래픽 관리 · 보안 · 관찰성.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 8.1 | **Istio** | 인기 서비스 메시 · 트래픽 관리 · 보안 정책 | `istioctl install --set profile=demo` / istio.io |
| 8.2 | **Linkerd** | 경량 서비스 메시 · Go 기반 · 빠른 성능 | `linkerd install \| kubectl apply -f -` / linkerd.io |
| 8.3 | **Consul Connect** | HashiCorp Consul · 서비스 메시 기능 · 멀티클라우드 | `consul agent -server -ui` / consul.io |
| 8.4 | **Cilium** | eBPF 기반 네트워킹 · 성능 우수 · 관찰성 | `helm install cilium cilium/cilium` / cilium.io |
| 8.5 | **Envoy** | 프록시 · 데이터 플레인 · L7 라우팅 | `envoy -c config.yaml` / envoyproxy.io |
| 8.6 | **Open Service Mesh (OSM)** | CNCF 서비스 메시 · 간단한 설정 · SMI 표준 | `osm install` / openservicemesh.io |
| 8.7 | **NGINX Service Mesh** | NGINX 기반 메시 · 성능 우수 | NGINX 콘솔 또는 Helm / nginx.com |
| 8.8 | **AWS App Mesh** | AWS 관리형 서비스 메시 · Envoy 기반 | AWS 콘솔 / aws.amazon.com/app-mesh |
| 8.9 | **Azure Service Fabric** | 마이크로서비스 플랫폼 · 신뢰성 · Windows 지원 | Azure 포털 / azure.microsoft.com/services/service-fabric |

---

## 9⃣ DNS / 도메인 / CDN — 18개

도메인 관리 · DNS 라우팅 · 엣지 캐싱 · DDoS 보호.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 9.1 | **Cloudflare** | DNS + CDN + 보안 · 무료 플랜 · 강력한 DDoS | cloudflare.com 콘솔 / Nameserver 변경 |
| 9.2 | **AWS Route53** | AWS DNS · 도메인 등록 · 헬스 체크 | `aws route53 create-hosted-zone` / console.aws.amazon.com |
| 9.3 | **Google Cloud DNS** | GCP DNS · 낮은 지연 · 관리 편의 | `gcloud dns managed-zones create` / cloud.google.com |
| 9.4 | **NS1** | 인텔리전트 DNS · 지역 기반 라우팅 · 분석 | NS1 콘솔 / ns1.com |
| 9.5 | **DNSimple** | 도메인 등록 + DNS · 간단한 UI · API | DNSimple 콘솔 / dnsimple.com |
| 9.6 | **Fastly** | CDN + 엣지 컴퓨팅 · 성능 우수 · Varnish | Fastly 콘솔 / fastly.com |
| 9.7 | **Akamai** | 엔터프라이즈 CDN · 보안 · 방대한 네트워크 | Akamai 콘솔 / akamai.com |
| 9.8 | **BunnyCDN** | 저비용 CDN · 높은 성능 · 단순 설정 | BunnyCDN 콘솔 / bunnycdn.com |
| 9.9 | **KeyCDN** | CDN · 원본 풀 · 헬스 체크 | KeyCDN 콘솔 / keycdn.com |
| 9.10 | **Azure CDN** | Azure 통합 CDN · Akamai/Verizon/Microsoft | Azure 포털 / portal.azure.com |
| 9.11 | **Bunny** | CDN 번들 · 저비용 · 스트리밍 최적 | Bunny 콘솔 / bunny.com |
| 9.12 | **CacheFly** | CDN · 비디오 최적화 · 안정성 | CacheFly 콘솔 / cachefly.com |
| 9.13 | **Netlify DNS** | Netlify 통합 DNS · 간편 설정 | Netlify 콘솔 / netlify.com |
| 9.14 | **Vercel DNS** | Vercel 통합 DNS · 자동 설정 | Vercel 콘솔 / vercel.com |
| 9.15 | **GoDaddy DNS** | 도메인 등록사 DNS · 기본 제공 | GoDaddy 콘솔 / godaddy.com |
| 9.16 | **Name.com** | 도메인 등록 + DNS · 가성비 · 개인 DNS | Name.com 콘솔 / name.com |
| 9.17 | **DynDNS** | 동적 DNS · IP 변경 자동 반영 | DynDNS 콘솔 / dyn.com |
| 9.18 | **CoreDNS** | Kubernetes DNS · 플러그인 기반 · 커스터마이징 | `kubectl apply -f coredns.yaml` / coredns.io |

---

## 🔟 비용 최적화 (Cost Optimization) — 14개

클라우드 비용 분석 · 예측 · 최적화 · FinOps.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 10.1 | **Infracost** | Terraform 비용 추정 · PR 댓글 · CLI | `brew install infracost && infracost breakdown -p .` / infracost.io |
| 10.2 | **Kubecost** | Kubernetes 비용 분석 · 파드별 할당 · FinOps | `helm install kubecost kubecost/cost-analyzer` / kubecost.com |
| 10.3 | **Spot.io** | 클라우드 최적화 · 인스턴스 추천 · 예약 구매 | Spot 콘솔 / spot.io |
| 10.4 | **CloudZero** | 클라우드 비용 관찰 · 컨텍스트 기반 · 할당 | CloudZero 콘솔 / cloudzero.com |
| 10.5 | **vantage** | 비용 관리 · 여러 클라우드 · 예산 추적 | vantage 콘솔 / vantage.sh |
| 10.6 | **nuvista** | 비용 최적화 · 예약 구매 · 스팟 인스턴스 | nuvista 콘솔 / nuvista.io |
| 10.7 | **Prosimo** | 멀티클라우드 비용 · 네트워크 최적화 | Prosimo 콘솔 / prosimo.io |
| 10.8 | **FinOps Foundation** | FinOps 표준·규칙·커뮤니티 | finops.org |
| 10.9 | **AWS Cost Explorer** | AWS 비용 분석 · 추천 · 예산 | AWS 콘솔 / console.aws.amazon.com |
| 10.10 | **Azure Cost Management** | Azure 비용 분석 · 예산·경고 | Azure 포털 / portal.azure.com |
| 10.11 | **GCP Cost Management** | GCP 비용 분석 · 예산·권장사항 | GCP 콘솔 / cloud.google.com |
| 10.12 | **ComputeOptimizer** | AWS 리소스 추천 · 규모 조정 | AWS 콘솔 / console.aws.amazon.com |
| 10.13 | **Rightsize** | 인스턴스 규모 추천 · 자동화 | Rightsize 콘솔 / rightsize.io |
| 10.14 | **Densify** | 멀티클라우드 최적화 · AI 기반 · 자동 규모 조정 | Densify 콘솔 / densify.com |

---

## 1⃣1⃣ 백업 / DR (Backup & Disaster Recovery) — 13개

데이터 보호 · 복원 · 재해 복구 · RTO/RPO.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 11.1 | **Velero** | Kubernetes 백업·복구 · 클라우드 스토리지 | `velero install` / velero.io |
| 11.2 | **Restic** | 파일 백업 · 암호화 · 증분 | `restic backup /path` / restic.net |
| 11.3 | **Longhorn** | Kubernetes 분산 스토리지 · 자동 백업 · 복제 | `helm install longhorn` / longhorn.io |
| 11.4 | **AWS Backup** | 중앙화 백업 · 크로스 리전 · 정책 기반 | `aws backup create-backup-vault` / aws.amazon.com/backup |
| 11.5 | **Azure Backup** | Azure 백업 · 온프레미스 지원 · 장기 보관 | Azure 포털 / azure.microsoft.com/services/backup |
| 11.6 | **Commvault** | 엔터프라이즈 백업 · 멀티 환경 · 관리 중앙화 | Commvault 콘솔 / commvault.com |
| 11.7 | **Veeam** | 백업·복제·복구 · 엔터프라이즈 · Windows 최적 | Veeam 콘솔 / veeam.com |
| 11.8 | **Bacula** | 오픈소스 백업 · 스케일러블 · 엔터프라이즈 | `bacula-fd` 에이전트 설치 / bacula.us |
| 11.9 | **Duplicati** | 오픈소스 백업 · 암호화 · 클라우드 저장 | `duplicati-server` 실행 / duplicati.com |
| 11.10 | **BorgBackup** | 중복 제거 백업 · 암호화 · 효율 | `borg init /backup` / borgbackup.readthedocs.io |
| 11.11 | **AWS Disaster Recovery** | AWS 재해 복구 · 크로스 리전 · 자동 페일오버 | AWS 콘솔 / aws.amazon.com/disaster-recovery |
| 11.12 | **Azure Site Recovery** | Azure 재해 복구 · 온프레미스 지원 | Azure 포털 / azure.microsoft.com/services/site-recovery |
| 11.13 | **GCP Backup & DR** | GCP 백업 · 재해 복구 · 일관성 | GCP 콘솔 / cloud.google.com |

---

## 1⃣2⃣ GitOps / 배포 자동화 (GitOps & Deployment) — 14개

코드 기반 배포 · CI/CD · 자동 실행 · 감사 추적.

| # | 도구 | 한글 설명 | 설치/접근 |
|---|---|---|---|
| 12.1 | **ArgoCD** | Kubernetes GitOps · Git 진실 · 자동 동기화 | `kubectl apply -n argocd -f argocd-server.yaml` / argocd.io |
| 12.2 | **Flux** | GitOps 도구 · 선언형 · Helm 통합 | `flux bootstrap github` / fluxcd.io |
| 12.3 | **Jenkins** | 자동화 서버 · CI/CD · 플러그인 풍부 | `docker run jenkins/jenkins` / jenkins.io |
| 12.4 | **GitLab CI/CD** | GitLab 통합 · 러너 기반 · 파이프라인 | `.gitlab-ci.yml` 파일 생성 / gitlab.com |
| 12.5 | **GitHub Actions** | GitHub 통합 · 워크플로우 · 마켓플레이스 | `.github/workflows/` 폴더에 YAML 파일 / github.com/actions |
| 12.6 | **CircleCI** | SaaS CI/CD · 빠른 빌드 · 오브 지원 | CircleCI 콘솔 또는 `.circleci/config.yml` / circleci.com |
| 12.7 | **Harness** | 배포 자동화 · CD · 무중단 배포 | Harness 콘솔 / harness.io |
| 12.8 | **Spinnaker** | 배포 자동화 · 다중 클라우드 · 전략 엔진 | `docker run spinnaker/deck` / spinnaker.io |
| 12.9 | **Tekton** | Kubernetes CI/CD · 클라우드 네이티브 · CRD 기반 | `kubectl apply -f tekton-pipeline.yaml` / tekton.dev |
| 12.10 | **Deployment Manager** | GCP IaC · 배포 자동화 | `gcloud deployment-manager deployments create` / cloud.google.com |
| 12.11 | **Azure DevOps Pipelines** | Azure 통합 CI/CD · 멀티 에이전트 | Azure DevOps 포털 / dev.azure.com |
| 12.12 | **Travis CI** | SaaS CI/CD · GitHub 통합 · 간편 설정 | `.travis.yml` 파일 생성 / travis-ci.com |
| 12.13 | **Drone** | 오픈소스 CI/CD · Docker 기반 · 간단 | `docker run drone/drone` / drone.io |
| 12.14 | **Argo Workflows** | Kubernetes 워크플로우 · 복잡한 DAG · 병렬 | `kubectl apply -f argo-workflow.yaml` / argoproj.github.io |

---

## 📋 도구별 조합 (권장 스택)

### 🔧 기본 스택 (Startup / 소규모팀)
- **IaC**: Terraform / Pulumi
- **컴퓨팅**: AWS Lambda or Google Cloud Run (서버리스)
- **데이터**: S3 / Cloud Storage / DynamoDB
- **CI/CD**: GitHub Actions / CircleCI
- **모니터링**: CloudWatch / Prometheus + Grafana

### 🏢 엔터프라이즈 스택 (규모 있는 팀)
- **IaC**: Terraform + Terraform Cloud + Ansible
- **컨테이너**: Kubernetes (EKS/AKS/GKE) + Helm + ArgoCD
- **컴퓨팅**: EC2 / App Service / Compute Engine
- **데이터**: RDS / Cosmos DB / BigQuery
- **서비스 메시**: Istio / Linkerd
- **모니터링**: Datadog / New Relic / Elastic Stack
- **비용**: Infracost + Kubecost + FinOps
- **백업**: Velero + AWS Backup

### ☁ 멀티클라우드 스택 (AWS + Azure + GCP)
- **IaC**: Terraform Cloud + env0 / Spacelift
- **멀티클라우드**: HashiCorp Consul + Karpenter
- **컨테이너**: Kubernetes 표준
- **DNS/CDN**: Route53 + Cloudflare (멀티 레이어)
- **비용**: CloudZero / Spot.io (통합 분석)

###  FinOps 스택 (비용 최적화)
- **측정**: Infracost + Kubecost + CloudZero
- **최적화**: Spot.io + ComputeOptimizer
- **자동화**: Terraform 비용 정책 + Lambda
- **추적**: FinOps Foundation 기준 준수

---

## 🔗 관계도 (카테고리 연결)

```text
IaC (Terraform)
  ├── AWS / Azure / GCP (프로비저닝)
  ├── Kubernetes (컨테이너 오케스트)
  │   ├── Helm (패키지 관리)
  │   ├── ArgoCD (GitOps)
  │   └── Linkerd (서비스 메시)
  │
  ├── DNS/CDN (Cloudflare, Route53)
  └── 모니터링 (Prometheus, Datadog)

서버리스 (Lambda)
  ├── 비용 최적화 (Infracost)
  └── CI/CD (GitHub Actions)

멀티클라우드 (Terraform Cloud)
  ├── 비용 통합 (CloudZero)
  ├── 보안 (Secrets Manager)
  └── 백업 (Velero, AWS Backup)
```

---

##  사용 팁

1. **시작**: Terraform + AWS/Azure/GCP 로컬 리소스 프로비저닝
2. **확장**: Kubernetes + Helm + ArgoCD 로 멀티 환경 관리
3. **관찰성**: Prometheus + Grafana + Elasticsearch 기본 3종 세트
4. **비용 제어**: Infracost + Kubecost + FinOps 정책 의무
5. **보안**: Secrets Manager + RBAC (IAM) + 감시 (CloudWatch)
6. **재해 복구**: Velero (K8s) + AWS Backup (클라우드)
7. **배포**: ArgoCD (GitOps) + GitHub Actions (CI)

---

## 📖 참조

- **공식 문서**: terraform.io, kubernetes.io, aws.amazon.com, azure.microsoft.com, cloud.google.com
- **커뮤니티**: CNCF (kubernetes.io), Terraform Registry (registry.terraform.io), Helm Hub (artifacthub.io)
- **FinOps**: finops.org (표준, 규칙, 커뮤니티)
- **로드맵**: 새 도구 추가 시 이 목록 갱신 (월 1회 권장)

---

**마지막 업데이트**: 2026-05-20
**도구 수**: 181개 · **카테고리**: 12개
**상태**: 공통 도구 (도메인 특화 X) · 모든 프로젝트에서 조합 사용 가능
