# Cybersecurity & DevSecOps Toolkit — 완벽 카탈로그

> **목적**: SAST·DAST·SCA·시크릿 탐지·컨테이너·K8s·IAM·네트워크·침투테스트·WAF·인증서·취약점 관리·SBOM·자동화·클라우드·규정 준수·안전 코딩 도구 모음
> **용도**: CI/CD 보안 자동화, 취약점 스캔, 정책 준수, 침투 테스트, 인증/인가 구축, 위협 탐지
> **총 도구 수**: 165개 (17개 카테고리)

---

## 1. SAST (정적 분석 보안 테스트) — 23개

### 다목적 SAST

```bash
npm install -g semgrep          # Semgrep — 규칙 기반 정적 분석 (25+ 언어, OWASP/CWE 매핑)
npm install -g sonarqube        # SonarQube — 엔터프라이즈 SAST (코드 품질+보안, 중앙화)
pip install bandit              # Bandit — Python SAST (보안 이슈, CWE 자동 매핑)
npm install -g snyk-code        # Snyk Code — AI 기반 SAST (취약점, 라이선스, 의존성)
npm install -g eslint-plugin-security  # ESLint Security — JavaScript/TypeScript 보안 규칙
npm install -g tslint-eslint-rules  # TSLint 규칙 — TypeScript 보안 검사
pip install pylint              # Pylint — Python 정적 분석 (보안·품질)
pip install flake8              # Flake8 — Python 스타일·에러 (보안 플러그인 추가)
pip install prospector          # Prospector — Python 다중 분석기 통합 (pylint, pep8, dodgy)
```

### 언어별 SAST

```bash
pip install pylint              # Python — 일반 정적 분석
npm install -g eslint           # JavaScript/TypeScript — 스타일·보안
go install honnef.co/go/tools/cmd/staticcheck@latest  # Go — 정적 분석 (버그·효율성·보안)
cargo install clippy --locked   # Rust — 린터·성능·보안 제안
php -S localhost:8000           # PHP 내장 서버 + php -l 문법 검사 (별도 보안 도구 필요)
ruby -w -c                      # Ruby 문법 검사 (brakeman 추천)
gem install brakeman            # Brakeman — Rails SAST (SQL Injection, XSS, CSRF)
pip install pylint-flask        # Flask-Pylint — Flask 앱 SAST
go install golang.org/x/tools/cmd/vet@latest  # Go Vet — 기본 정적 분석
npm install -g codeql           # CodeQL — 의미 기반 정적 분석 (GitHub 무료)
```

### 특화 SAST

```bash
npm install -g checkmarx        # Checkmarx SAST — 엔터프라이즈급 정적 분석
pip install pyt                 # Python Taint — 데이터 흐름 추적 (보안)
npm install -g insecure-npm     # npm audit — npm 패키지 보안 감시 (내장)
pip install astroid             # Astroid — Python AST 기반 분석
npm install -g retire           # Retire.js — JavaScript 라이브러리 취약점
go install github.com/presidentbeef/brakeman@latest  # Brakeman — Ruby on Rails SAST
pip install semgrep             # Semgrep Python CLI — Python/다언어
cargo install cargo-audit       # Cargo Audit — Rust 의존성 취약점
npm install -g npm-audit        # npm audit (내장) — npm 패키지 감시
```

---

## 2. DAST (동적 분석 보안 테스트) — 18개

### 웹 애플리케이션 DAST

```bash
docker run -t owasp/zap:latest  # OWASP ZAP — 웹 보안 스캔 (활성·수동, 자동화)
apt-get install burpsuite       # Burp Suite Community — 웹 프록시·스캐너 (수동 테스트)
pip install nuclei              # Nuclei — YAML 기반 웹 스캔 (1000+ 템플릿, 빠름)
pip install sqlmap              # SQLmap — SQL Injection 자동 테스트 (99% DBMS 지원)
apt-get install nikto           # Nikto — CGI 스캐너 (웹서버, 취약점 데이터베이스)
pip install arachni-cli         # Arachni — 웹 애플리케이션 스캔 (JavaScript 렌더링)
pip install w3af                # W3AF — 웹 취약점 스캔 (공격 시뮬레이션)
pip install skipfish            # Skipfish — 웹 재귀 크롤러 (Google)
npm install -g wpscan           # WPScan — WordPress DAST (플러그인·테마·코어 취약점)
pip install joomla-scanner      # Joomla 스캐너 — Joomla 취약점 탐지
```

### 다목적 동적 스캔

```bash
pip install openvas             # OpenVAS — 원격 취약점 스캔 (CVSS 점수)
docker pull greenbone/openvas   # OpenVAS Docker — 컨테이너 기반 배포
apt-get install nmap            # Nmap — 포트 스캔·서비스 열거 (OS 감지)
apt-get install masscan         # Masscan — 초고속 포트 스캔 (병렬 처리)
docker run aquasec/trivy         # Trivy DAST — 컨테이너 이미지 스캔
npm install -g retire           # Retire.js — 클라이언트 JS 취약점
pip install commix              # Commix — OS Command Injection 테스트
apt-get install hydra           # Hydra — 온라인 패스워드 크래킹 (22/23/25/110 등)
```

---

## 3. SCA (소프트웨어 구성 분석) — 16개

### 일반 SCA 도구

```bash
npm install -g snyk             # Snyk — 의존성 취약점 (npm, pip, maven, yarn)
npm install -g npm-audit        # npm audit — npm 내장 감시
pip install safety              # Safety — Python 의존성 취약점 (pyup.io DB)
pip install pip-audit           # pip-audit — Python 패키지 감시 (PyPA)
npm install -g dependabot       # Dependabot — GitHub 자동 PR (내장)
npm install -g renovate         # Renovate — 다중 플랫폼 PR 자동화 (npm, pip, golang 등)
docker run aquasec/trivy        # Trivy SCA — 이미지·저장소 스캔
pip install grype               # Grype — SBOM 기반 SCA (Syft 통합)
```

### 언어별 SCA

```bash
npm install -g npm              # npm audit (내장) — JavaScript/Node.js
pip install poetry              # Poetry — Python 의존성 관리 + 보안
pip install pipenv              # Pipenv — Python 가상환경 + 의존성
cargo audit                      # Cargo Audit (내장) — Rust 의존성
go list -json ./... | nancy     # Nancy — Go 의존성 취약점 (Sonatype OSS Index)
bundler audit                    # Bundler Audit — Ruby Gem 취약점 (RailsBlog DB)
mvn dependency-check:check      # OWASP Dependency-Check (Maven) — Java 의존성
gradle dependencyCheckAnalyze    # Gradle Dependency-Check — Gradle 프로젝트
```

### 고급 SCA

```bash
pip install cyclonedx-bom        # CycloneDX Generator — SBOM 생성 (SPDX 호환)
npm install -g cyclonedx-npm     # CycloneDX npm — npm SBOM 생성
pip install syft                 # Syft — SBOM 생성 (이미지, 디렉토리, git)
docker run aquasec/trivy        # Trivy SBOM — Software Bill of Materials
pip install tern                 # Tern — 컨테이너 이미지 분석 (의존성·라이선스·취약점)
apt-get install composer        # Composer (PHP) — 의존성 관리 + security check
```

---

## 4. 시크릿 탐지 — 14개

### Git 기반 시크릿 탐지

```bash
pip install gitleaks            # Gitleaks — Git 리포지토리 시크릿 탐지 (API 키, 토큰)
pip install truffleHog          # TruffleHog — 엔트로피 기반 시크릿 찾기 (Git 히스토리)
pip install detect-secrets      # detect-secrets — Yelp 시크릿 탐지 (동적, 파이썬 통합)
pip install git-secrets         # git-secrets — AWS Labs 시크릿 방지 (pre-commit hook)
npm install -g gitguardian      # GitGuardian CLI — 깃허브 공개 리포 시크릿 스캔
pip install detect_secrets_cli  # detect-secrets CLI — 저장소 전체 스캔
```

### YARA/Regex 기반 탐지

```bash
pip install pymongo             # PyMongo (통합 스캔용) — MongoDB 보안 스캔
apt-get install yara            # YARA — 악성코드 탐지 (규칙 기반, 시크릿도 가능)
apt-get install chkrootkit      # chkrootkit — rootkit 탐지 (시크릿 흔적)
pip install pycryptodome         # PyCryptodome — 암호화 라이브러리 (시크릿 암호화)
npm install -g snyk             # Snyk — 시크릿 노출 탐지 (npm)
```

### 클라우드 시크릿 탐지

```bash
pip install checkov             # Checkov — IaC 시크릿 탐지 (Terraform, CloudFormation, K8s)
apt-get install vault           # Vault — HashiCorp 시크릿 관리 (탐지 X, 저장용)
pip install pulumi-policy-as-code  # Pulumi — IaC 정책 (시크릿 검증)
pip install detect_secrets_baseline  # detect-secrets 베이스라인 — 증분 감시
npm install -g snyk-code        # Snyk Code — 시크릿 + 코드 취약점
```

---

## 5. 컨테이너 보안 — 17개

### 이미지 스캔·강화

```bash
docker pull aquasec/trivy        # Trivy — 컨테이너 이미지 취약점 스캔 (가장 빠름)
docker pull anchore/anchore-engine  # Anchore Engine — 심층 이미지 분석 (정책)
docker pull quay.io/clair        # Clair — 컨테이너 취약점 스캔 (CoreOS)
docker pull aquasec/microscanner # Microscanner — 경량 스캔 (build 단계)
docker run aquasec/trivy image debian:latest  # Trivy — Debian 기본 이미지 스캔
docker run aquasec/trivy image alpine:latest  # Trivy — Alpine 스캔 (최소화)
docker pull sysdig/sysdig-inspector  # Sysdig Inspector — 런타임 동작 분석
docker pull aquasec/grype        # Grype — SBOM 기반 스캔 (Syft 통합)
```

### 런타임 보안·감시

```bash
docker pull falcosecurity/falco  # Falco — 컨테이너 런타임 위협 탐지 (시스콜 분석)
docker pull sysdig/sysdig        # Sysdig — 컨테이너 추적·감시 (프로세스, 네트워크)
docker pull aquasec/container-security  # Aqua CSP — 정책 기반 컨테이너 보안
docker run docker:latest scout cves image  # Docker Scout — Docker 기본 취약점 분석
docker pull falcosecurity/falco  # Falco Rules — 공개 규칙 라이브러리 (보안)
```

### 이미지 강화·모니터링

```bash
docker run debian:latest apt-get install -y distroless  # Distroless — 최소 기본 이미지
docker pull gcr.io/distroless/base  # Distroless 컨테이너 — 공격 표면 최소화
docker pull quay.io/in-toto/in-toto  # In-Toto — 공급망 보안 (빌드 메타데이터)
docker run aquasec/trivy config .  # Trivy Config — Dockerfile 정책 검사
pip install kubescape           # Kubescape 이미지 스캔 — K8s-specific 검사
```

---

## 6. Kubernetes 보안 — 15개

### K8s 정책·정적 분석

```bash
npm install -g kubescape         # Kubescape — K8s 자동 보안 평가 (NSA 가이드 준수)
apt-get install kube-bench       # kube-bench — CIS Kubernetes 벤치마크 점검
apt-get install popeye           # Popeye — K8s 클러스터 검사 (설정, 리소스, 보안)
pip install polaris              # Polaris — K8s 정책 감시 (Pod Security Policies)
docker run openpolicyagent/opa   # OPA/Gatekeeper — K8s 정책 엔진 (동적 정책)
docker pull nirmata/kyverno      # Kyverno — K8s-native 정책 (YAML 기반)
docker pull aquasec/starboard    # Starboard — K8s 보안 스캔 (CVE, RBAC, PSP)
```

### K8s 런타임 보안

```bash
docker run falcosecurity/falco   # Falco K8s — 런타임 위협 탐지 (syscall)
docker pull aquasec/kube-mgmt    # Kube-mgmt — K8s 정책 자동 배포
docker pull kubewarden/policy-server  # Kubewarden — WebAssembly 정책 엔진
docker pull cloud.weave.works/scope  # Weave Scope — K8s 시각화·모니터링
docker pull datadog/agent        # Datadog Agent K8s — 모니터링 + 위협 탐지
```

### K8s RBAC·접근 제어

```bash
kubectl auth can-i --as=user@example.com list pods  # kubectl auth — RBAC 검증
docker pull aquasec/rbac-police  # RBAC Police — K8s 역할 권한 감시
docker pull redhat/certification  # RedHat Certification — K8s 호환성
docker run aquasec/kubectl-who-can  # Kubectl Who Can — RBAC 권한 추적
apt-get install kubelet          # Kubelet — K8s 보안 설정 (--protect-kernel-defaults)
```

---

## 7. IAM / 인증 & 인가 — 17개

### 오픈 소스 IAM

```bash
docker pull keycloak/keycloak    # Keycloak — 오픈 IAM (OAuth2, SAML, OIDC)
docker pull authentik/server      # Authentik — 현대형 IAM (SSO, MFA, 정책)
docker pull authelia/authelia    # Authelia — 경량 IAM (Traefik, 2FA)
docker pull supertokens/supertokens  # SuperTokens — 오픈 인증 (로그인, 세션)
docker pull zitadel/zitadel      # ZITADEL — 엔터프라이즈 IAM (OIDC, SAML)
docker pull 42crunch/api-firewall  # API 방화벽 — API 게이트웨이 보안
npm install -g passport          # Passport.js — Node.js 인증 미들웨어
```

### 클라우드 호스팅 IAM

```bash
npm install -g auth0-cli         # Auth0 CLI — Auth0 관리
pip install aws-cli              # AWS CLI — AWS IAM 관리 (policies, roles)
gcloud auth configure-docker      # Google Cloud IAM — GCP 인증
az login                          # Azure CLI — Azure 역할 기반 접근 (RBAC)
```

### MFA·토큰·인증 강화

```bash
docker pull duo/duo_client       # Duo Security — MFA (2FA, TOTP, Push)
pip install pyotp                # pyOTP — TOTP/HOTP 생성 (MFA 토큰)
npm install -g speakeasy         # Speakeasy — 2FA/MFA 라이브러리 (Node.js)
apt-get install haproxy          # HAProxy — 리버스 프록시 (인증 강화)
docker pull nginx                # Nginx + oauth2-proxy — OAuth2 프록시 (게이트웨이 인증)
docker pull bitnamiwp/nginx      # Nginx + ModSecurity — WAF + 인증
npm install -g ldap3             # LDAP 클라이언트 — 디렉토리 서비스 인증
```

---

## 8. 네트워크 보안 — 19개

### 네트워크 모니터링·분석

```bash
apt-get install wireshark        # Wireshark — 패킷 분석 (GUI, 프로토콜 디코딩)
apt-get install tshark           # TShark — Wireshark CLI 버전
apt-get install tcpdump          # tcpdump — 패킷 캡처 (PCAP)
pip install scapy                # Scapy — 패킷 조작 (Python)
apt-get install zeek             # Zeek (구 Bro) — 네트워크 IDS (로그, JSON)
pip install suricata             # Suricata — 네트워크 IDS/IPS (멀티스레드)
docker pull osquery/osquery       # osquery — 호스트 모니터링 (SQL 인터페이스)
```

### 포트·서비스 스캔

```bash
apt-get install nmap             # Nmap — 포트 스캔 (버전 감지, 스크립트)
apt-get install masscan          # Masscan — 초고속 스캔 (병렬, 1000s pps)
apt-get install zmap             # ZMap — 인터넷 전역 포트 스캔 (연구용)
apt-get install shodan-cli        # Shodan CLI — 인터넷 기기 검색 (API)
curl -s https://www.censys.io    # Censys API — 인터넷 자산 검색
npm install -g snyk              # Snyk — 네트워크 취약점 (API)
```

### 고급 네트워크 보안

```bash
pip install paramiko             # Paramiko — SSH 클라이언트 (자동화)
pip install netmiko              # Netmiko — SSH 네트워크 장비 자동화
apt-get install wireguard        # WireGuard — VPN (경량, 고속)
apt-get install openssl          # OpenSSL — SSL/TLS 분석·생성
docker pull mitmproxy/mitmproxy  # mitmproxy — HTTPS 인터셉트 (테스트, 모니터링)
pip install dnspython            # dnspython — DNS 조회·조작
```

---

## 9. 침투 테스트 & 익스플로잇 — 18개

### 메타스플로잇 생태계

```bash
apt-get install metasploit-framework  # Metasploit — 침투 테스트 플랫폼 (수천 익스플로잇)
docker pull metasploitframework/metasploit  # Metasploit Docker
docker pull offensive-security/metasploit  # Rapid7 공식 Metasploit
msfconsole                       # Metasploit Console — 대화형 명령어
msfvenom                         # MSFVenom — 페이로드 생성 (Windows, Linux, Web)
```

### 익스플로잇·취약점 도구

```bash
pip install sqlmap              # SQLmap — SQL Injection 자동화
pip install commix              # Commix — OS Command Injection
pip install xsstrike            # XSStrike — XSS 탐지·이용 (WAF bypass)
apt-get install weevely          # Weevely — PHP 웹셸 + 리버스 쉘
apt-get install cewl             # CeWL — 웹사이트 크롤러 (패스워드 사전 생성)
pip install exploit-db           # Exploit-DB — 알려진 익스플로잇 데이터베이스
```

### 패스워드·해시 크래킹

```bash
apt-get install hashcat          # Hashcat — GPU 해시 크래킹 (13B+ 해시 지원)
apt-get install john             # John the Ripper — 암호 크래킹 (CPU)
apt-get install hydra            # Hydra — 온라인 패스워드 공격 (SSH, FTP, HTTP)
apt-get install medusa           # Medusa — 병렬 패스워드 공격
apt-get install aircrack-ng      # Aircrack-ng — WiFi WPA/WPA2 크래킹
```

### 정찰·열거

```bash
apt-get install curl             # curl — URL 시뮬레이션 (헤더, 리다이렉트 분석)
pip install requests             # requests — HTTP 라이브러리 (자동화)
pip install autopsy              # Autopsy — 포렌식 분석 (파일 복구)
apt-get install lynis            # Lynis — 보안 감사 도구 (설정, 패치)
```

---

## 10. WAF (Web Application Firewall) & 방어 — 13개

### 오픈 소스 WAF

```bash
docker pull owasp/modsecurity    # ModSecurity — 오픈 WAF (Nginx, Apache, IIS)
docker pull curiouscode/modsecurity_crs  # ModSecurity CRS — OWASP Core Rule Set
docker pull modsecurity/modsecurity  # ModSecurity Docker
apt-get install fail2ban         # Fail2ban — IP 차단 (보안 로그 기반)
docker pull crowdsec/crowdsec    # CrowdSec — 협력형 WAF (IP 차단 공유)
```

### 클라우드 WAF

```bash
aws wafv2 create-web-acl        # AWS WAF — AWS 매니지드 WAF
gcloud compute security-policies create  # Google Cloud Armor — GCP WAF
az network waf-policy create     # Azure WAF — Azure 규칙
npm install -g cloudflare-cli    # Cloudflare CLI — Cloudflare WAF 관리
```

### WAF 규칙·정책

```bash
docker pull modsecurity/modsecurity_crs  # OWASP ModSecurity CRS
docker pull coreruleset/coreruleset  # OWASP CRS (공식 이미지)
git clone https://github.com/SpiderLabs/owasp-modsecurity-crs  # CRS 규칙 저장소
docker pull airlock/waf          # Airlock WAF — 엔터프라이즈 WAF
docker pull imperva/incapsula    # Imperva Incapsula (클라우드 WAF)
apt-get install nginx            # Nginx + ModSecurity — Web 서버 + WAF
docker pull traefik/traefik      # Traefik — 리버스 프록시 + WAF 지원
```

---

## 11. 인증서 & TLS 관리 — 12개

### 무료·자동 인증서

```bash
apt-get install certbot          # Certbot (Let's Encrypt 클라이언트) — 자동 갱신
docker pull certbot/certbot      # Certbot Docker
pip install pyopenssl            # PyOpenSSL — Python SSL/TLS 라이브러리
npm install -g letsencrypt       # Let's Encrypt 통합 (Node.js)
apt-get install acme.sh          # acme.sh — ACME 클라이언트 (bash)
```

### 로컬 CA·개발 인증서

```bash
apt-get install mkcert           # mkcert — 로컬 CA (개발용 신뢰 인증서)
docker pull smallstep/step-ca    # Step CA — 프라이빗 CA (자동화)
apt-get install cfssl            # CFSSL (CloudFlare) — CA 도구 (JSON 기반)
pip install cryptography         # cryptography — 인증서 조작 (Python)
```

### TLS·인증서 분석

```bash
apt-get install openssl          # OpenSSL — SSL/TLS 분석 (cert 검증)
npm install -g ssl-checker       # SSL Checker — 인증서 만료 모니터링
docker pull owasp/https-shield   # HTTPS Shield — 인증서 감시
docker run ssllabs/testssl       # SSL Labs 로컬 스캔
```

---

## 12. 취약점 관리 & 스캐닝 — 14개

### 엔터프라이즈 취약점 관리

```bash
docker pull tenable/nessus       # Nessus — 상용 취약점 스캔 (전 업계 표준)
docker pull greenbone/openvas    # OpenVAS — 오픈 취약점 매니저
docker pull qualys/qualys-agent  # Qualys VMDR — 클라우드 취약점 스캔
docker pull rapid7/insightvm     # Rapid7 InsightVM — 위험도 기반 우선순위
```

### 경량·특화 취약점 도구

```bash
docker pull aquasec/trivy         # Trivy — 이미지·저장소·파일 취약점
pip install grype                # Grype — SBOM 기반 취약점
docker pull aquasec/clair        # Clair — 컨테이너 취약점 분석
pip install safety               # Safety — Python 의존성 취약점
npm install -g npm-audit         # npm audit — npm 패키지 취약점
```

### CVSS·CVE 데이터베이스

```bash
curl -s https://nvd.nist.gov/api  # NVD API — 국가 취약점 데이터베이스
docker pull nvd-cli              # NVD CLI 래퍼
pip install python-nvd           # Python NVD 라이브러리
docker pull exploitdb            # Exploit-DB — 공개 익스플로잇
```

---

## 13. SBOM (Software Bill of Materials) — 11개

### SBOM 생성

```bash
pip install syft                 # Syft — 이미지·디렉토리 SBOM 생성 (CycloneDX, SPDX)
npm install -g cyclonedx-npm     # CycloneDX npm — npm SBOM
pip install cyclonedx-bom        # CycloneDX Generator — Python SBOM
docker run aquasec/trivy sbom image  # Trivy SBOM 생성
pip install tern                 # Tern — 컨테이너 이미지 SBOM (라이선스 포함)
```

### SBOM 분석·검증

```bash
pip install grype                # Grype — SBOM 기반 취약점 분석
docker run anchore/grype sbom  # Grype SBOM 스캔
pip install spdx-tools           # SPDX Tools — SBOM 검증
npm install -g cyclonedx-bom-viewer  # SBOM 뷰어 (웹)
docker pull spdx/spdx-build      # SPDX 빌더 도구
```

### SBOM 관리·추적

```bash
docker pull in-toto/in-toto      # In-Toto — 공급망 보안 메타데이터 (SBOM 추적)
```

---

## 14. 보안 자동화 & SOAR — 13개

### SOAR (Security Orchestration, Automation, Response)

```bash
docker pull shuffleriot/shuffle  # Shuffle — 오픈 SOAR (워크플로우 자동화)
docker pull thehive/thehive      # TheHive — 사건 대응 플랫폼 (SOAR)
docker pull cortexproject/cortex  # Cortex — TheHive 분석 엔진
docker pull securityonion/securityonion  # Security Onion — IDS + SOAR
docker pull wazuh/wazuh          # Wazuh — 위협 탐지 + 대응 자동화
```

### 규칙 기반 탐지

```bash
apt-get install yara             # YARA — 악성코드·시크릿 탐지 규칙
pip install yara-python          # YARA Python 바인딩
docker pull sigma                # Sigma — SIEM 규칙 포맷 (표준화)
docker run sigma-rule-tool       # Sigma 규칙 컴파일러 (SIEM용)
```

### 위협 인텔리전스·자동화

```bash
docker pull misp/misp            # MISP — 위협 정보 공유 플랫폼
docker pull abuse-ch/urlhaus      # URLhaus — 악성 URL 데이터베이스
docker pull otx-rest-api         # AlienVault OTX API — 위협 정보 피드
pip install tox                  # tox — 자동화 테스트 (CI/CD 보안)
```

---

## 15. 클라우드 보안 — 16개

### AWS 보안 스캔

```bash
pip install prowler              # Prowler — AWS 보안 프레임워크 (240+ 체크)
pip install cloudmapper          # CloudMapper — AWS 네트워크 시각화
pip install scoutsuite           # ScoutSuite — AWS 보안 감시
pip install cloudtracker         # CloudTracker — CloudTrail 분석
```

### GCP 보안 스캔

```bash
gcloud scc list-findings         # Cloud Security Command Center — GCP 보안 중앙화
gcloud compute security-policies  # Google Cloud Armor — GCP 정책
pip install forseti-security     # Forseti — GCP 자동 감시 (deprecated, Prowler 사용)
```

### Azure 보안 스캔

```bash
az security assessment create     # Azure Security Center — 평가
az keyvault secret list          # Azure Key Vault — 시크릿 관리
pip install azure-cli            # Azure CLI — 보안 정책
```

### 멀티 클라우드·IaC 보안

```bash
pip install checkov              # Checkov — IaC 정책 (Terraform, CloudFormation)
pip install cloudtruth           # CloudTruth — IaC 환경변수 관리
docker pull tfsec                # tfsec — Terraform 보안 스캔
docker pull bridgecrewio/checkov # Checkov — Docker 버전
pip install stackstorm           # StackStorm — 자동화 플랫폼
docker pull twistlock/prisma     # Prisma Cloud (Palo Alto) — 클라우드 CWPP
```

---

## 16. 규정 준수 & 정책 — 15개

### 규정 준수 프레임워크

```bash
docker pull inspec               # InSpec — 규정 준수 코드 (NIST, CIS, HIPAA)
docker pull openscap             # OpenSCAP — SCAP 스캐너 (NIST, PCI-DSS)
docker pull vuls/vuls            # Vuls — 취약점 + 규정 준수
pip install compliance-checker    # Compliance Checker — 다중 기준
docker pull security-compliance-center  # Compliance Center (엔터프라이즈)
```

### NIST CSF·CIS 벤치마크

```bash
docker pull cis-benchmark        # CIS Benchmark — 운영체제·서비스 기준
docker pull nist-csf             # NIST Cybersecurity Framework
docker pull pci-dss-checklist    # PCI-DSS 체크리스트 자동화
docker run kube-bench            # kube-bench — CIS K8s 벤치마크
```

### 데이터 보호·GDPR·개인정보

```bash
pip install privacyraven         # PrivacyRaven — 개인정보 탐지
pip install anonymizer           # Anonymizer — 데이터 익명화
docker pull securegov/compliance  # Compliance Dashboard
pip install guardrails           # Guardrails — AI 안전성 감시
docker pull collibra/govrance    # Collibra 규정 준수
```

### 감사·로깅

```bash
docker pull elastic/elasticsearch  # Elasticsearch — 로그 수집
docker pull kibana/kibana        # Kibana — 로그 시각화
docker pull graylog/graylog      # Graylog — 중앙화 로깅
docker pull splunk/splunk        # Splunk — 보안 정보 및 이벤트 관리 (SIEM)
```

---

## 17. 안전한 코딩 & 보안 가이드 — 15개

### OWASP Top 10·CWE 참조

```bash
docker pull owasp/owasp-top-10   # OWASP Top 10 가이드
docker pull cwe/cwe-checker      # CWE Top 25 검사기
docker pull sans/sans-top-25     # SANS Top 25 가이드
docker pull cisa/known-exploited-vulnerabilities  # CISA KEV 카탈로그
```

### 안전한 코딩 도구

```bash
pip install bandit               # Bandit — Python 보안 문제
npm install -g eslint-plugin-security  # ESLint Security — JavaScript
cargo clippy --all-targets       # Clippy — Rust 린터 (보안)
python -m py_compile --version   # Python 컴파일 체크
pip install pylint               # Pylint — Python 품질+보안
```

### 암호화·해싱

```bash
pip install cryptography         # cryptography — 암호화 라이브러리
pip install pycryptodome         # PyCryptodome — 암호 알고리즘
npm install bcryptjs             # bcryptjs — 패스워드 해싱
npm install jsonwebtoken         # JWT — 토큰 서명
python -c "import hashlib"       # hashlib — 내장 해싱
```

### 보안 HTTP·API

```bash
pip install requests             # requests + urllib3 — HTTPS 자동화
npm install helmet               # Helmet.js — Express.js 보안 헤더
pip install django-cors-headers  # Django CORS — 교차 출처 보안
npm install @hapi/joi            # Joi — 입력 검증 (스키마)
docker pull nginx:latest         # Nginx — 보안 헤더 설정
```

### 테스트·검증

```bash
pip install pytest-cov           # pytest-cov — 테스트 커버리지 (보안 테스트)
npm install -g jest              # Jest — JavaScript 단위 테스트 (보안)
docker pull sonarqube/sonarqube  # SonarQube — 코드 품질 + 보안
pip install hypothesis           # Hypothesis — 속성 기반 테스트
npm install -g npm-audit         # npm audit — 의존성 보안
```

---

## 전체 요약

| 카테고리 | 도구 수 |
|---------|--------|
| 1. SAST | 23개 |
| 2. DAST | 18개 |
| 3. SCA | 16개 |
| 4. 시크릿 탐지 | 14개 |
| 5. 컨테이너 보안 | 17개 |
| 6. K8s 보안 | 15개 |
| 7. IAM/인증 | 17개 |
| 8. 네트워크 보안 | 19개 |
| 9. 침투 테스트 | 18개 |
| 10. WAF | 13개 |
| 11. 인증서/TLS | 12개 |
| 12. 취약점 관리 | 14개 |
| 13. SBOM | 11개 |
| 14. 보안 자동화 | 13개 |
| 15. 클라우드 보안 | 16개 |
| 16. 규정 준수 | 15개 |
| 17. 안전한 코딩 | 15개 |
| **총합** | **235개** |

---

## 빠른 시작 (검사 목적별)

###  긴급 — 한 시간 안에
```bash
# Step 1: Git 시크릿 탐지
pip install gitleaks
gitleaks detect --source . -v

# Step 2: 의존성 취약점
npm audit fix --force
pip install safety && safety check

# Step 3: 기본 SAST
pip install bandit
bandit -r . -f json -o scan.json

# Step 4: 컨테이너 이미지
docker pull aquasec/trivy
trivy image myapp:latest
```

###  표준 — 반일 범위
```bash
# 위 4단계 + 다음:
# Step 5: 정적 분석
npm install -g semgrep
semgrep --config=p/owasp-top-ten .

# Step 6: DAST
docker run -t owasp/zap:latest -t https://app.example.com

# Step 7: K8s (있으면)
apt-get install kubescape
kubescape scan

# Step 8: 클라우드 (AWS/GCP)
pip install prowler
prowler -g aws_audit
```

###  전수 — 전체 감시 (지속)
```bash
# 위 8단계 + 다음:
# Step 9: WAF + 정책
docker pull owasp/modsecurity

# Step 10: 침투 테스트 (정기)
msfconsole -x "db_import nessus_report.nessus"

# Step 11: SBOM + SCA 자동화 (CI/CD)
syft . -o spdx > sbom.spdx.json
grype sbom.spdx.json

# Step 12: 자동화 (SOAR)
docker pull shuffleriot/shuffle
```

---

## 참고·학습

- **OWASP 공식**: https://owasp.org/www-project-top-ten/
- **CWE Top 25**: https://cwe.mitre.org/top25/
- **NIST CSF**: https://www.nist.gov/cyberframework
- **CIS Benchmarks**: https://www.cisecurity.org/cis-benchmarks/
- **SANS Top 25**: https://www.sans.org/top25-software-errors/
- **Shodan**: https://www.shodan.io/
- **Censys**: https://censys.io/
- **GitHub Security Lab**: https://securitylab.github.com/
- **Exploit-DB**: https://www.exploit-db.com/
- **NVD (National Vulnerability Database)**: https://nvd.nist.gov/

---

**마지막 업데이트**: 2026-05-20  
**카테고리 구조**: 17개 (SAST, DAST, SCA, 시크릿, 컨테이너, K8s, IAM, 네트워크, 침투, WAF, 인증서, 취약점, SBOM, 자동화, 클라우드, 규정, 안전)  
**총 도구**: 235개 (설치 명령어 포함)
