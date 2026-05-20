# 보건의료 & 의료 공통 도구모음 (80+ tools)

> **용도**: 의료 IT·보건 애플리케이션·의료 영상 분석 시 참고
> **범위**: FHIR/HL7 ~ EHR ~ 의료영상 ~ AI 의료 ~ 한국 보건서비스
> **관리**: orchestration_v1 reference (sync 대상 아님)

---

## 1. FHIR & HL7 (의료 데이터 표준)

| 표준 | 용도 | 버전 | 특징 | npm/pip |
|------|------|------|------|---------|
| **FHIR (Fast Healthcare Interoperability Resources)** | RESTful 의료 데이터 | R4, R4B, R5 | 현대 API 기반, JSON 중심 | npm: `fhir` |
| **HL7 v2** | 병원 시스템 간 메시지 | 2.3, 2.4, 2.5, 2.7 | 레거시 (여전히 광범위) | 전용 파서 |
| **HL7 v3** | CDA (Clinical Document Architecture) | 3.0 | XML 기반 임상 문서 | XML 도구 |
| **Smart on FHIR** | 모바일 앱 인증 | 1.0 | OAuth 2.0 + FHIR | npm: `smart-on-fhir` |
| **cimi (Clinical Information Modeling Initiative)** | 임상 데이터 모델링 | 1.0 | FHIR 상위 개념화 | 없음 (스펙) |

### FHIR 서버 (npm)
```bash
npm install hapi-fhir          # 자바 기반 FHIR 서버
npm install fhir               # JS FHIR 클라이언트
npm install fhir.js            # 선언형 FHIR API

# 환자 정보 조회 예
const client = new FHIR.client({
  serverUrl: "https://fhir.example.com",
  clientId: "your_app",
  redirectUri: "https://your_app/callback"
});
client.patient.read().then(pt => console.log(pt));
```

### HL7 FHIR R4 파싱 (Python)
```bash
pip install fhir               # Python FHIR 클라이언트
pip install fhirclient         # 공식 SMART on FHIR SDK

from fhirclient import client
settings = {
  'app_id': 'my_app',
  'app_password': 'secret',
  'api_base': 'https://fhir.epic.com'
}
smart = client.FHIRClient(settings=settings)
patient = smart.patient_id
print(patient)
```

### Smart on FHIR (OAuth)
```bash
npm install smart-on-fhir
# React 앱에서 FHIR 인증
import FHIR from 'fhirclient';
FHIR.oauth2.init({
  clientId: 'MY_CLIENT_ID',
  server: 'https://launch.smarthealthit.org/v/r4/fhir'
}).then(smart => {
  smart.request(`Patient/${smart.patient.id}`).then(pt => {
    console.log(`${pt.name[0].given.join(' ')} ${pt.name[0].family}`);
  });
});
```

---

## 2. EHR/EMR 플랫폼

| 플랫폼 | 형태 | 특징 | FHIR API | 가격 |
|--------|------|------|----------|------|
| **OpenEMR** | 오픈소스 | 미국 FDA 인증, 소규모 의원/診所 | ✅ (R4) | 무료 (서포트 유료) |
| **GNU Health** | 오픈소스 | 전자의료기록 + 병원 관리, 개발도상국 | ⚠️ (HL7 v2) | 무료 |
| **OpenMRS** | 오픈소스 | 발도국 의료 플랫폼 특화 | ✅ (R4) | 무료 |
| **Epic** | 상용 | 북미 점유율 최고 (56% 병원), EHI 강점 | ✅ (R4) | $10k+/월 |
| **Cerner** | 상용 | 미국 병원 2위 (EMR+EHR) | ✅ (R4) | $10k+/월 |
| **Medidata** (Veeva) | 클라우드 | 임상시험 + EHR 통합 | ✅ (R4) | 엔터프라이즈 |
| **NextGen Healthcare** | 클라우드 | 소규모 클리닉 친화 | ✅ (R4) | $500+/월 |

### OpenEMR 설치 (Docker)
```bash
docker run -d \
  --name openemr \
  -e MYSQL_ROOT_PASSWORD=root \
  -e OPENEMR_ADMIN_USER=admin \
  -e OPENEMR_ADMIN_PASS=pass123 \
  -p 80:80 \
  openemr/openemr:latest
```

### Epic FHIR API (대형 병원)
```bash
# Epic 클라이언트 인증서 필요 (병원 제공)
curl https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize \
  -d "client_id=$CLIENT_ID&response_type=code&scope=patient/*.read"
```

### OpenMRS FHIR 모듈
```bash
# OpenMRS + FHIR 모듈 통합
docker run -d \
  --name openmrs \
  -e DB_DRIVER=mysql \
  -e DB_HOST=mysql \
  openmrs/openmrs-core:latest

# FHIR 모듈 활성화 (관리자 콘솔)
# Modules → Manage Modules → FHIR 2.2.0 활성화
```

---

## 3. 의료 영상 (DICOM & AI 분석)

| 도구 | 특징 | 포맷 | 분석 기능 | 가격 |
|------|-----|------|---------|------|
| **pydicom** | DICOM 파일 읽기/쓰기 (Python) | DICOM | 기본 처리 | 오픈소스 |
| **OHIF Viewer** | 웹 기반 의료 영상 뷰어 | DICOM, 다중 형식 | 기본 주석 | 오픈소스 |
| **3D Slicer** | 3D 의료 영상 분석 | DICOM, NIfTI | 분할, 등록, 모델링 | 오픈소스 |
| **ITK-SNAP** | 영상 분할 소프트웨어 | DICOM, NIfTI | 수동/자동 분할 | 오픈소스 |
| **Cornerstone.js** | 웹 DICOM 뷰어 (JavaScript) | DICOM | 기본 뷰 | 오픈소스 |
| **MONAI (PyTorch 의료)** | 의료 영상 AI 학습 | DICOM, NIfTI | DL 기반 분할, 분류 | 오픈소스 |
| **TorchXRayVision** | 흉부 X선 AI | JPG, DICOM | 위험도 점수, 분류 | 오픈소스 |
| **CheXpert** | 흉부 X선 데이터셋 + 분류 | JPG | 14가지 질병 분류 | 스탠포드 공개 |

### pydicom (DICOM 파일 처리)
```bash
pip install pydicom

from pydicom import dcmread
ds = dcmread("chest_xray.dcm")
print(f"환자명: {ds.PatientName}")
print(f"촬영일: {ds.StudyDate}")

# DICOM → PNG 변환
import matplotlib.pyplot as plt
plt.imshow(ds.pixel_array, cmap='gray')
plt.savefig('xray.png')
```

### OHIF Viewer (웹 호스팅)
```bash
# 클라우드에서 DICOM 뷰어 실행
docker run -d \
  --name ohif-viewer \
  -p 3000:3000 \
  ohif/viewer:latest

# 브라우저: http://localhost:3000/?url=dicomweb:https://your-dicom-server
```

### 3D Slicer (Linux/Mac/Windows)
```bash
# 다운로드: https://download.slicer.org/
# 또는 Docker
docker run -d \
  --name slicer \
  -p 5900:5900 \
  -v /data:/data \
  slicer/slicer:latest

# 원격 데스크톱으로 접속 (VNC)
```

### MONAI (의료 영상 DL)
```bash
pip install monai torch

from monai.networks.nets import UNet
from monai.transforms import Compose, LoadImageD, Resized

# 뇌 종양 분할 모델
model = UNet(
    spatial_dims=3,
    in_channels=1,
    out_channels=2,
    channels=(16, 32, 64),
    strides=(2, 2)
)

# 학습 데이터
transforms = Compose([
    LoadImageD(keys=["image"]),
    Resized(keys=["image"], spatial_size=[128, 128, 128])
])
```

### TorchXRayVision (흉부 X선 분류)
```bash
pip install torchxrayvision
import torchxrayvision as xrv

# 사전학습 모델 로드
model = xrv.models.DenseNet(weights='all')

# X선 이미지 분류
import skimage.io as io
img = io.imread('chest.jpg')
outputs = model(torch.tensor(img).unsqueeze(0))
# 폐렴, 폐결핵, 기흉 등 14가지 검출
```

### CheXpert (흉부 X선 데이터셋)
```bash
# 스탠포드 공개 데이터셋
wget https://stanfordmlgroup.github.io/competitions/chexpert/download_data.py
python download_data.py

# 학습 예
from torchvision import models
model = models.resnet18(pretrained=True)
# CheXpert 라벨로 미세조정
```

---

## 4. 건강 데이터 & 피트니스 API

| API | 플랫폼 | 데이터 | 인증 | 가격 |
|-----|--------|--------|------|------|
| **Apple HealthKit** | iOS/watchOS | 걸음, 심박, 혈당, 체중 등 | OAuth 2.0 | 무료 (앱) |
| **Google Fit API** | Android/웹 | 활동, 스트레스, 수면 | OAuth 2.0 | 무료 |
| **Fitbit API** | Fitbit 밴드 | 심박, 활동, 수면, 영양 | OAuth 2.0 | 무료 개발자 |
| **Withings API** | Withings 기기 | 체중, BP, 산소포화도 | OAuth 2.0 | 무료 개발자 |
| **Oura Ring** | Oura 반지 | 수면, HRV, 활동, 회복 | OAuth 2.0 | 프리미엄 구독 |
| **Garmin** | Garmin 기기 | 활동, 수면, HR 변동성 | OAuth 2.0 | 무료 개발자 |

### Apple HealthKit (Swift)
```swift
import HealthKit

let healthStore = HKHealthStore()
let readTypes: Set = [HKObjectType.quantityType(forIdentifier: .stepCount)!]

healthStore.requestAuthorization(toShare: nil, read: readTypes) { (success, error) in
    if success {
        let now = Date()
        let startOfDay = Calendar.current.startOfDay(for: now)
        let predicate = HKQuery.predicateForSamples(withStart: startOfDay, end: now)
        let query = HKSampleQuery(sampleType: readTypes.first!, predicate: predicate, limit: 1) { (query, results, error) in
            if let stepCount = results?.first as? HKQuantitySample {
                print("오늘 걸음: \(stepCount.quantity.doubleValue(for: HKUnit.count()))")
            }
        }
        healthStore.execute(query)
    }
}
```

### Google Fit API (Python)
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

from googleapiclient.discovery import build
from google.oauth2 import service_account

# OAuth 2.0 인증
service = build('fitness', 'v1', credentials=credentials)

# 7일 활동 데이터 조회
body = {
    "aggregateBy": [{
        "dataTypeName": "com.google.step_count.delta"
    }],
    "bucketByTime": { "durationMillis": 86400000 },  # 1일
    "startTimeMillis": int((now - timedelta(days=7)).timestamp() * 1000),
    "endTimeMillis": int(now.timestamp() * 1000)
}
dataset = service.users().dataset().aggregate(userId='me', body=body).execute()
```

### Fitbit API (Python)
```bash
pip install fitbit

import fitbit
client = fitbit.Fitbit(client_id='$CLIENT_ID',
                        client_secret='$CLIENT_SECRET',
                        access_token='ACCESS_TOKEN',
                        refresh_token='REFRESH_TOKEN')

# 오늘 심박 데이터
hr_data = client.intraday_time_series('activities/heart', date='today', detail_level='15min')
print(hr_data['activities-heart-intraday']['dataset'])
```

---

## 5. 약물 데이터 & 의약품 정보

| 데이터베이스 | 범위 | 특징 | API | 언어 |
|--------|------|------|-----|------|
| **OpenFDA** | 미국 의약품, 의료기기 | FDA 공식 DB, 부작용 데이터 | REST API | 영어 |
| **RxNorm** | 미국 약품 명명 표준 | NLM 표준, EHR 필수 | REST API | 영어 |
| **DrugBank** | 약물 특성, 상호작용 | 5000+ 약물, 작용 메커니즘 | REST API | 영어 |
| **PubChem** | 화학 물질 | NIH 공개, 구조식 검색 | REST API | 영어 |
| **건강보험심사평가원** | 한국 의약품, 급여기준 | 건강보험 인정 약물 | REST API | 한국어 |
| **의약품안전나라** | 한국 의약품 안전정보 | 식약청 공식, 부작용, 리콜 | REST API | 한국어 |
| **공공데이터포털** (의약품) | 한국 제약사, 임상시험 | 식약청 등록 약물 | REST API | 한국어 |

### OpenFDA API
```bash
# 의약품 검색
curl "https://api.fda.gov/drug/label.json?search=aspirin&limit=5"

# 부작용 데이터
curl "https://api.fda.gov/drug/event.json?search=patient.reaction.reactionmeddrapt:fever&count=reactionmeddrapt"

# Python
import requests
response = requests.get(
  "https://api.fda.gov/drug/label.json",
  params={"search": "aspirin", "limit": 1}
)
drug = response.json()['results'][0]
print(drug['indications_and_usage'])
```

### RxNorm API
```bash
# 약품명 검색
curl "https://rxnav.nlm.nih.gov/REST/rxcui.json?name=Tylenol"

# 상호작용 검사
curl "https://rxnav.nlm.nih.gov/REST/interaction/interaction.json?rxcuis=5489-5521"

# Python
import requests
resp = requests.get("https://rxnav.nlm.nih.gov/REST/rxcui.json", 
  params={"name": "Aspirin"})
rxcui = resp.json()['idGroup']['rxList'][0]['rxcui']
```

### 건강보험심사평가원 API (한국)
```bash
# 공공데이터포털에서 키 신청 필수
curl "https://www.data.go.kr/api/15042959/execute-layer" \
  -d '{
    "query": "아스피린",
    "type": "의약품",
    "page": 1
  }'
```

### 의약품안전나라 (식약청 API)
```bash
# 공공데이터포털
curl "https://www.data.go.kr/api/..." \
  # -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "query": "약품명",
    "searchType": "약품명",
    "numOfRows": 10
  }'
```

---

## 6. AI 의료 & 머신러닝

| 도구 | 특화 | 기술 | 정확도 | 규제 |
|------|-----|------|--------|------|
| **MONAI** | 의료 영상 DL | PyTorch, 분할·분류 | 90%+ (특정 태스크) | FDA 510(k) 경로 |
| **TorchXRayVision** | 흉부 X선 분류 | ResNet, 이미 지도학습 | 85-95% | 임상용 X |
| **CheXpert** | 흉부 X선 모델 | CNN 앙상블 | 94% (폐렴) | 임상용 X (연구) |
| **Med-PaLM** | 의료 언어 AI | Google LLM 의료 특화 | 95% 의료 시험 | 규제 검토 중 |
| **BioBERT** | 생의학 자연어 | BERT 의료 특화 | 90%+ (관계추출) | 비임상용 |
| **DeepChem** | 신약개발 AI | GNN, LSTM 분자 특성 | 데이터 의존 | 연구 단계 |
| **AlphaFold** | 단백질 구조 예측 | Attention 메커니즘 | 99% (구조 유사도) | 무료 API |
| **Tempus AI** | 암 정밀의학 | 종양 유전체 AI | 90%+ 생존 예측 | FDA 승인 경로 |

### MONAI로 뇌 종양 분할
```bash
pip install monai torch pytorch-lightning

from monai.apps import download_and_extract
from monai.transforms import (Compose, LoadImageD, Resized, NormalizeIntensityd)

# 데이터 다운로드
download_and_extract("https://www.med.upenn.edu/cbica/brats2021.html")

# 전처리
transforms = Compose([
    LoadImageD(keys=["image", "label"]),
    Resized(keys=["image", "label"], spatial_size=[240, 240, 155]),
    NormalizeIntensityd(keys=["image"])
])

# 모델 학습
from monai.networks.nets import UNet
model = UNet(
    spatial_dims=3,
    in_channels=4,  # BRATS 4가지 모드
    out_channels=4,  # 4가지 종양 클래스
    channels=(32, 64, 128),
    strides=(2, 2)
)
```

### Med-PaLM (의료 LLM)
```bash
pip install google-generativeai

import google.generativeai as genai
genai.configure(api_key="$API_KEY")

# 의료 진단 지원
model = genai.GenerativeModel("gemini-pro")
response = model.generate_content(
    """다음 증상을 가진 45세 남성:
    - 가슴 통증 (3일)
    - 호흡곤란
    - 메스꺼움
    가능한 진단은?"""
)
print(response.text)
```

### AlphaFold (단백질 구조)
```bash
pip install alphafold
pip install biopython

# AlphaFold API 사용 (ESMfold 대체)
from esmfold import esmfold
sequence = "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWERVMGDGERQFSTLKSTVEAIWAGIKATEAAVSEEFGLAPFLPDQIHFVHSQELLSRYPDLDAKGRERAIAKDLGAVFLVGIGGKLSDGHRHDVRAPDYDDWSTPSELGHAGLNGDILVWNPVLEDAFELSSMGIRVDADTLKHQLALTGDEDRLELEWHQALLRGEMPQTIGGGIGQSRLTMLLLQLPHIGQVQAGVWPAAVRESVPSLL"

structure = esmfold(sequence)
structure.save("protein.pdb")
```

---

## 7. 원격진료 & 텔레헬스

| 플랫폼 | 특징 | 보안 | 가격 | HIPAA |
|--------|------|------|------|--------|
| **Twilio Video (HIPAA)** | 실시간 화상진료 | TLS 1.2, 암호화 | $0.04-0/분 | ✅ 준수 |
| **Doxy.me** | 통합 비디오 + 대기실 | HIPAA 준수 | $20+/월 | ✅ 준수 |
| **Zoom for Healthcare** | 화상회의 HIPAA 버전 | 종단 암호화 | $150+/월 | ✅ 준수 |
| **Teladoc** | 원격진료 플랫폼 (B2B) | 군데이터 센터 | 요청 시 | ✅ 준수 |
| **MDLive** | 전문의 매칭 플랫폼 | HIPAA 준수 | $0-500/상담 | ✅ 준수 |
| **Amwell** | 원격진료 + 의료기관 통합 | EHR 연계 | 요청 시 | ✅ 준수 |

### Twilio Video HIPAA API (Node.js)
```bash
npm install twilio

const twilio = require("twilio");

// 액세스 토큰 생성 (의료용 HIPAA)
const AccessToken = twilio.jwt.AccessToken;
const VideoGrant = AccessToken.VideoGrant;

const token = new AccessToken(
  process.env.TWILIO_ACCOUNT_SID,
  process.env.TWILIO_API_KEY,
  process.env.TWILIO_API_SECRET
);

token.addGrant(new VideoGrant({ room: "medical-consultation-123" }));
console.log(token.toJwt());

// 클라이언트: Video.connect(token, options)
```

### Doxy.me 통합
```bash
curl https://api.doxy.me/api/patient/intake \
  # -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "patient_name": "John Doe",
    "visit_reason": "Follow-up",
    "scheduled_time": "2024-05-20T14:00:00Z"
  }'
```

---

## 8. 한국 보건의료 API & 서비스

| 서비스 | 주요 데이터 | API | 출처 |
|--------|-----------|-----|------|
| **건강보험공단** | 진료 청구, 약제 이용, 입원 | REST API | 공공데이터포털 |
| **심평원 (건강보험심사평가원)** | 약제 급여기준, 진료 기준 | REST API | 공공데이터포털 |
| **의약품안전나라 (MFDS)** | 식약청 허가약, 부작용 | REST API | 공공데이터포털 |
| **질병관리청** | 감염병 통계, 예방접종 정보 | REST API | 공공데이터포털 |
| **국립암센터** | 암 통계, 치료 가이드라인 | 웹 포털 | https://www.ncc.re.kr |
| **건강검진 통합 정보** | 국가건강검진 결과, 질병 예측 | REST API | 공공데이터포털 |
| **의료기관 정보** | 병원, 의원, 약국 위치 | 공공API | 공공데이터포털 + 건보공단 |
| **임상시험 정보** | CRIS (임상시험 정보 검색) | 웹 검색 | https://cris.nih.go.kr |

### 건강보험공단 API (공공데이터포털)
```bash
# 진료 청구 데이터 (개별 가입자 요청)
curl "https://www.data.go.kr/api/15058087/execute-layer" \
  # -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "member_id": "XXXXXXXXXXXXX",
    "year_month": "202405"
  }'
```

### 심평원 약제 급여기준
```bash
# 공공데이터포털 API
curl "https://www.data.go.kr/api/15044572/execute-layer" \
  -d '{
    "drug_name": "아스피린",
    "search_type": "상품명"
  }'
```

### 의약품안전나라 (부작용 정보)
```bash
curl "https://www.data.go.kr/api/..." \
  -d '{
    "drug_name": "약품명",
    "report_type": "부작용"
  }' \
  | jq '.adverse_events[] | {date, symptom, severity}'
```

### 질병관리청 감염병 현황
```bash
# 실시간 코로나, 독감 등 현황
curl "https://www.data.go.kr/api/..." \
  -d '{
    "disease": "코로나19",
    "date": "20240520"
  }'
```

---

## 9. 생명과학 & 바이오인포매틱스

| 도구 | 특화 | 기능 | 언어 | 용도 |
|------|------|------|------|------|
| **BioPython** | 서열 분석 | DNA/단백질 파싱, BLAST | Python | 생물정보 분석 |
| **RDKit** | 화학 구조 | 분자 구조 매칭, 성질 예측 | Python | 신약개발 |
| **DeepChem** | 분자 학습 | 약물 상호작용, 독성 예측 | Python | AI 신약 |
| **AlphaFold** | 단백질 구조 | 3D 구조 예측 | Python | 단백질 이해 |
| **EMBOSS** | 서열 도구 | 서열 검색, 정렬, 분석 | CLI | 고전 생물정보 |

### BioPython (DNA 서열 분석)
```bash
pip install biopython

from Bio import SeqIO, NCBI
from Bio.SeqUtils import molecular_weight

# FASTA 파일 읽기
for record in SeqIO.parse("sequence.fasta", "fasta"):
    print(f"ID: {record.id}")
    print(f"길이: {len(record.seq)}")
    print(f"분자량: {molecular_weight(record.seq)}")
    
# BLAST 검색
from Bio.Blast import NCBIWWW
result = NCBIWWW.qblast("blastn", "nr", "ATCGATCGATCG")
```

### RDKit (화학 구조)
```bash
pip install rdkit

from rdkit import Chem
from rdkit.Chem import Draw, Descriptors

# 분자 생성
mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")  # 아스피린
print(f"분자량: {Descriptors.MolWt(mol):.2f}")
print(f"로그P: {Descriptors.MolLogP(mol):.2f}")

# 분자 그리기
img = Draw.MolToImage(mol)
img.save("aspirin.png")
```

### DeepChem (신약 예측)
```bash
pip install deepchem

from deepchem.models import GraphConvModel
from deepchem.feat import ConvMolFeaturizer

# 약물 독성 예측 모델
featurizer = ConvMolFeaturizer()
X = featurizer.featurize(["CC(=O)O", "CCCC"])  # SMILES
model = GraphConvModel(n_tasks=1)
model.fit(X, y)  # y = 독성 라벨
predictions = model.predict(X)
```

---

## 10. 의료 규정 & 규제 준수

| 규제 | 관할 | 국가 | 특징 | 준수 방법 |
|------|------|------|------|----------|
| **HIPAA** | HHS (보건부) | 미국 | 환자정보 보호, 감사 필수 | 암호화, 로그 기록 |
| **GDPR** | EU | 유럽 | 개인정보 권리, 동의 필수 | 개인정보 삭제권, DPA |
| **PIPA (개인정보보호법)** | 개인정보보호위원회 | 한국 | 정보주체 권리, 안전조치 의무 | 암호화, 악성코드 백신 |
| **의료법** | 보건복지부 | 한국 | 의료기관 허가, 원격진료 규정 | 의료인 확인, 기록 보관 |
| **의료기기법** | 식약청 | 한국 | 의료기기 허가, 품질관리 | 인증, 시판 후 조사 |
| **임상시험법** | 식약청 | 한국 | 신약 임상시험 | IRB 승인, 동의서 |
| **FDA 510(k)** | FDA | 미국 | 의료기기 승인 | 근거 제출, 검사 |
| **CE 마킹** | NANDO | EU | 의료기기 적합성 | 기술문서, 제3자 인증 |

### HIPAA 준수 체크리스트
```markdown
## HIPAA 기술적 보호장치
- [ ] 데이터 암호화 (전송 + 저장): TLS 1.2, AES-256
- [ ] 접근제어: MFA, 최소권한 원칙
- [ ] 감사 로그: 모든 PHI (Protected Health Information) 접근 기록
- [ ] 백업·복구: 정기 백업, 재해복구 계획
- [ ] 로그인 관리: 타임아웃, 비밀번호 정책

## 행정적 보호장치
- [ ] 개인정보보호 정책 문서화
- [ ] 직원 훈련 (매년)
- [ ] 벤더 계약: BAA (Business Associate Agreement)
- [ ] 사고 대응 계획
- [ ] 정기 위험 평가
```

### PIPA (한국) 준수
```markdown
## PIPA 기술적 보호
- [ ] 개인정보 암호화 (저장): AES-128 이상
- [ ] 악성코드 백신 설치
- [ ] 접근제어: 시스템 관리자만
- [ ] 로그 관리: 최소 1년 보관
- [ ] 정기 보안진단 (연 1회+)

## 행정적 절차
- [ ] 개인정보보호 담당자 지정
- [ ] 정보주체 동의서 수집 (사전)
- [ ] 개인정보 삭제 요청 시 30일 내 완료
- [ ] 개인정보 유출 시 대상자에게 72시간 내 통지
```

---

## 11. 종합 비교 표

| 기준 | FHIR 추천 | EHR 추천 | AI 의료 추천 | 한국 의료 | 원격진료 추천 |
|------|----------|---------|------------|---------|------------|
| **무료/오픈소스** | FHIR JS, HAPI | OpenEMR, GNU Health | MONAI, AlphaFold | KIPRIS, 질병청 | Twilio 스타트업 |
| **엔터프라이즈** | Epic, Cerner FHIR | Epic, Cerner EMR | Tempus, IBM Watson | 병원EHR 자체 개발 | Zoom, Amwell |
| **한국 친화** | 없음 (번역 필요) | 없음 (해외 제품) | 없음 (한국어 미지원) | ✅ 건보공단, 심평원 | Doxy.me, 국내 업체 |
| **AI 강점** | 데이터 교환 표준 | 데이터 저장 표준 | ✅ MONAI, AlphaFold | 없음 (AI 미흡) | AI 진단 보조 미약 |
| **규제 명확** | ✅ FHIR 표준화 | ❌ EHR 경쟁 | ⚠️ FDA 승인 경로 | ✅ 의료법, 의료기기법 | ✅ HIPAA, PIPA |

---

## 12. 설치 & 통합 예

### OpenEMR + FHIR + 한국 건보 데이터 통합
```bash
# OpenEMR + FHIR 모듈
docker run -d --name emr openemr/openemr:latest
# FHIR 활성화: /openemr/interface/modules/

# 건보 데이터 가져오기
curl "https://www.data.go.kr/api/..." \
  -d '{"patient_id": "..."}' | \
  # FHIR 형식 변환 (Python 스크립트)
  python convert_to_fhir.py | \
  # OpenEMR에 로드
  curl https://localhost:8300/fhir/Patient \
    -X POST \
    -H "Content-Type: application/fhir+json"
```

### MONAI + DICOM 자동 분석
```bash
# 병원 DICOM 서버 → MONAI 분할 → 리포트 생성
python train_monai_model.py --data dicom_server
# 새 환자 CT 스캔 → 자동 분할 → PDF 리포트
python infer_and_report.py --input patient_ct.dcm --output report.pdf
```

### Twilio + Doxy.me 원격진료
```javascript
// 의료기관 웹사이트
const token = await fetch("/api/twilio-token", {
  method: "POST",
  body: JSON.stringify({ patientId: "123" })
}).then(r => r.json());

Twilio.Video.connect(token, {
  name: "medical-consultation",
  audio: true,
  video: { width: 640 },
  networkQuality: { local: 3, remote: 3 }
}).then(room => {
  // 진료 비디오 세션
  console.log("진료 시작");
  room.participants.forEach(attachParticipant);
  room.on("participantConnected", attachParticipant);
});
```

---

## 참조

- **FHIR**: https://www.hl7.org/fhir/
- **OpenEMR**: https://www.open-emr.org/
- **MONAI**: https://monai.io/
- **pydicom**: https://github.com/pydicom/pydicom
- **AlphaFold**: https://alphafold.ebi.ac.uk/
- **건강보험공단 API**: https://www.data.go.kr/
- **의약품안전나라**: https://ezdrug.mfds.go.kr/
- **HIPAA 가이드**: https://www.hhs.gov/hipaa/
- **PIPA (PIPC)**: https://www.pipc.go.kr/
- **BioPython**: https://biopython.org/
