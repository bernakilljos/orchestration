# IoT & Embedded Toolkit

> **목적**: 사물인터넷 · 임베디드 시스템 · 하드웨어 통합 공통 도구 모음 (80+ 도구)
> **적용 범위**: Arduino · Raspberry Pi · ESP32 · IoT 플랫폼 · 센서 · 펌웨어 · 엣지 컴퓨팅
> **카테고리**: 10개 영역 · 하드웨어 · 프로토콜 · 플랫폼 · 펌웨어 · 시각화 · AI · 한국 IoT

---

## 1. 마이크로컨트롤러 & 개발 보드

### 인기 플랫폼 비교

| 보드 | SoC | RAM | 저장소 | 가격 | 용도 | 커뮤니티 |
|---|---|---|---|---|---|---|
| **Arduino Uno** | ATmega328P | 2 KB | 32 KB | $25 | 입문 · 간단 프로젝트 | 매우 큼 |
| **Arduino Nano** | ATmega328P | 2 KB | 32 KB | $10 | 임베디드 · 소형 | 큼 |
| **Raspberry Pi 4** | BCM2711 (ARM Cortex-A72) | 1-8 GB | microSD | $35-75 | 리눅스 기반 · 서버 · 엣지 | 매우 큼 |
| **Raspberry Pi Pico** | RP2040 (Cortex-M0+) | 264 KB | 2 MB | $4 | 초소형 · 실시간 | 증가 중 |
| **ESP8266** | Tensilica L106 | 160 KB | 4 MB | $5-8 | Wi-Fi 프로젝트 · IoT | 큼 |
| **ESP32** | Xtensa Dual-core | 520 KB | 4 MB | $10-15 | Wi-Fi + BLE · IoT 중급 | 매우 큼 |
| **ESP32-S3** | Xtensa Dual-core + AI | 512 KB | 8 MB | $12-18 | 엣지 AI · 카메라 · 음성 | 증가 중 |
| **STM32F4** (Black Pill) | ARM Cortex-M4 | 192 KB | 512 KB | $5-10 | 고성능 · 실시간 제어 | 중간 |
| **Jetson Nano** | NVIDIA Tegra | 4 GB | eMMC 16 GB | $99-149 | AI 추론 · 엣지 GPU | 중간 |
| **Arduino MKR WiFi 1010** | SAMD21 + NINA-W102 | 32 KB | 256 KB | $35 | MQTT · 산업용 | 중간 |

### 선택 가이드

```text
프로젝트 요구사항?
├─ 입문 / LED · 버튼
│  └─ Arduino Uno
├─ Wi-Fi / 클라우드 연결
│  ├─ 저비용 → ESP8266
│  └─ BLE도 필요 → ESP32
├─ 실시간 제어 (모터 · 센서 고정밀)
│  └─ STM32F4 또는 Arduino Due
├─ 리눅스 / 풀 OS (Python · Docker)
│  └─ Raspberry Pi 4
├─ 엣지 AI / 카메라
│  ├─ 경량 → ESP32-S3 + TensorFlow Lite
│  └─ 고성능 → Jetson Nano
└─ 초소형 / 저전력
   └─ Raspberry Pi Pico 또는 Arduino Nano 33 IoT
```

---

## 2. 통신 프로토콜 (Wireless & Wired)

### 무선 프로토콜

| 프로토콜 | 범위 | 전력 | 대역폭 | 용도 | 설정 |
|---|---|---|---|---|---|
| **Wi-Fi (802.11)** | 100m | 중간-높음 | 11-54 Mbps | 인터넷 연결 · 클라우드 | SSID + 비밀번호 |
| **BLE (Bluetooth Low Energy)** | 100m | 매우 낮음 | 1 Mbps | 웨어러블 · 스마트폰 연동 | UUID + 특성 |
| **Zigbee** | 100m (메시 네트워크) | 낮음 | 250 kbps | 스마트홈 · 메시 네트워크 | IEEE 802.15.4 기반 |
| **Z-Wave** | 100m (메시) | 매우 낮음 | 100 kbps | 스마트홈 (유럽) | 소유권 프로토콜 |
| **LoRa** | 15 km (시골) | 매우 낮음 | 50 kbps | 원격 센서 · 광역 IoT | LoRaWAN 표준 |
| **NB-IoT** | 35 km | 낮음 | 250 kbps | 이동통신 기반 IoT | 통신사 망 |
| **5G** | 수 km | 중간 | 10+ Gbps | 초저지연 · 영상 전송 | 통신사 망 |
| **Thread** | 250m (메시) | 낮음 | 250 kbps | IoT · 메시 네트워크 (Apple 지원) | IPv6 기반 |

### MQTT (메시지 브로커)

```bash
# Broker 설치
docker run -d -p 1883:1883 -p 8883:8883 eclipse-mosquitto

# Python 클라이언트
pip install paho-mqtt

# Node.js 클라이언트
npm install mqtt
```

**예제 (온도 센서)**:
```python
import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect("localhost", 1883)

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    print(f"온도: {data['temp']}°C")

client.on_message = on_message
client.subscribe("home/living_room/temperature")
client.loop_forever()
```

---

## 3. IoT 플랫폼 (클라우드 & 온프레미스)

### AWS IoT Core

```bash
# AWS CLI 설치
pip install boto3

# 인증서 생성 (One-click)
aws iot create-thing --thing-name my-device
aws iot create-thing-type --thing-type-name sensor
```

**예제**:
```python
from awscrt.mqtt import Client as MqttClient
from awscrt.auth import AwsCredentialsProvider

client = MqttClient(...)
client.connect(host_endpoint, port=8883, ...)
client.publish("$aws/things/my-device/shadow/update", ...)
```

### Azure IoT Hub

```bash
# Device Provisioning Service (DPS)
az iot central device create --app-id APP_ID --device-id device_001

pip install azure-iot-device
```

### Google Cloud IoT

```bash
# Cloud IoT Core (Cloud Pub/Sub 통합)
gcloud iot devices create my-device \
  --region=us-central1 \
  --registry=my-registry \
  --public-key path=rsa_cert.pem
```

### 온프레미스 플랫폼

| 플랫폼 | 특징 | 설치 | 한국 |
|---|---|---|---|
| **ThingsBoard** | 오픈소스 · 대시보드 · 규칙 엔진 | Docker / K8s | ✅ 지원 |
| **Home Assistant** | 홈 오토메이션 · 자동화 | Docker / Raspberry Pi | ✅ 최고 |
| **EdgeX Foundry** | 엣지 컴퓨팅 참고 구현 | Docker Compose | ✅ 지원 |
| **Node-RED** | 시각적 프로그래밍 · 플로우 | npm install -g node-red | ✅ 지원 |

---

## 4. 펌웨어 & 개발 환경

### Arduino IDE & 대체재

| 도구 | 언어 | 특징 | 플랫폼 |
|---|---|---|---|
| **Arduino IDE** | C/C++ | 공식 · 초보자 친화 | Windows · macOS · Linux |
| **Arduino IDE 2.0** | C/C++ | 최신 · IntelliSense · 향상된 UI | 동일 |
| **Visual Studio Code + Arduino Extension** | C/C++ | 강력한 편집기 · 확장성 | 동일 |
| **PlatformIO** | C/C++ · Python | 300+ 보드 지원 · 라이브러리 관리 | CLI + VS Code |
| **MicroPython** | Python | 경량 Python · ESP32 · Pi Pico | 해석형 |
| **CircuitPython** | Python | Adafruit 중심 · 교육용 | 해석형 |

### PlatformIO (권장)

```bash
# 설치
pip install platformio

# 새 프로젝트
platformio init -b esp32 --name my_iot_project

# 빌드 & 업로드
pio run -t upload
```

### ESP-IDF (ESP32 공식 SDK)

```bash
# 설치
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf && ./install.sh

# 프로젝트 생성
idf.py create-project-from-template esp-idf-template hello_world
idf.py build && idf.py flash && idf.py monitor
```

### Zephyr RTOS (고급)

```bash
# 설치 (macOS)
brew install cmake ninja gperf python3 ccache dtc libmagic

# 샘플 빌드
west build -b nrf52840dk_nrf52840 zephyr/samples/basic/blink
```

---

## 5. 시각화 & 대시보드

### Web 기반 대시보드

```bash
npm install grafana influxdb-client plotly.js
pip install grafana-api influxdb-client
```

| 도구 | 기능 | 호스팅 | 가격 |
|---|---|---|---|
| **Grafana** | 메트릭 시각화 · 경보 · 플러그인 | 셀프호스트 · Cloud | 무료 + Pro |
| **Blynk** | 모바일 앱 · 간단한 IoT | Blynk Cloud | 무료 + 유료 |
| **ThingsBoard** | Dashboard · 규칙 엔진 · REST API | 셀프호스트 | 오픈소스 무료 |
| **Node-RED** | 시각적 플로우 · 대시보드 | 셀프호스트 · Node-RED Cloud | 무료 |
| **Home Assistant** | 홈 오토메이션 · 자동화 · 모바일 | 셀프호스트 + Cloud | 무료 |
| **InfluxDB + Grafana** | 시계열 DB + 시각화 | 셀프호스트 · Cloud | 무료 + Pro |

### Grafana 설정 예제

```bash
# Docker 실행
docker run -d -p 3000:3000 grafana/grafana

# 데이터소스 추가 (InfluxDB)
curl -X POST http://localhost:3000/api/datasources \
  -d '{"name":"InfluxDB","type":"influxdb","url":"http://influxdb:8086"}'
```

---

## 6. 엣지 AI & 머신러닝

### TensorFlow Lite (경량 모델)

```bash
# 설치
pip install tensorflow tensorflow-lite

# 모델 변환 (TensorFlow → TFLite)
converter = tf.lite.TFLiteConverter.from_saved_model("my_model")
tflite_model = converter.convert()

with open("model.tflite", "wb") as f:
    f.write(tflite_model)
```

### Arduino/ESP32에 배포

```cpp
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "model.tflite"

// 모델 로드
const unsigned char* model_tflite = model_data;
tflite::Model* model = tflite::GetModel(model_tflite);

// 추론
interpreter->Invoke();
TfLiteTensor* output = interpreter->output(0);
```

### ONNX Runtime (다중 프레임워크)

```bash
pip install onnxruntime onnx

# 모델 로드 및 추론
import onnxruntime
sess = onnxruntime.InferenceSession("model.onnx")
output = sess.run(None, {"input": input_data})
```

### 대체 엣지 AI

| 프레임워크 | 모델 크기 | 지연 | 정확도 |
|---|---|---|---|
| **TensorFlow Lite** | 작음 | 매우 낮음 | 높음 |
| **ONNX Runtime** | 작음 | 낮음 | 높음 |
| **OpenVINO** (Intel) | 작음 | 낮음 | 높음 (Intel HW 최적) |
| **Core ML** (Apple) | 작음 | 낮음 | 높음 (Apple HW 최적) |
| **PyTorch Mobile** | 중간 | 중간 | 높음 |
| **MediaPipe** | 매우 작음 | 매우 낮음 | 우수 (특정 작업) |

### Edge Impulse (시각 & 음성)

```bash
# CLI 설치
npm install -g edge-impulse-cli

# 프로젝트 초기화
edge-impulse-cli login
edge-impulse-cli project create --name my_ml_project
```

---

## 7. 시뮬레이션 & 프로토타이핑

### Wokwi (온라인 시뮬레이터)

```markdown
- 웹 기반 · 회원가입 무료
- Arduino · ESP32 · Raspberry Pi Pico 지원
- 시뮬레이션 실시간 · 파형 표시
- 코드 편집 + 실행 한 번에
```

**URL**: https://wokwi.com/

### TinkerCAD Circuits

```markdown
- Autodesk 제공 · 무료 (계정 필요)
- 회로도 + 시뮬레이션 + 코드 에디터 통합
- 초보자 친화
```

**URL**: https://www.tinkercad.com/circuits

### QEMU (Raspberry Pi 시뮬레이션)

```bash
# QEMU 설치
brew install qemu  # macOS
apt install qemu   # Linux

# Raspberry Pi OS 시뮬레이션
qemu-system-arm -M raspi3b -kernel kernel8.img -drive file=sdcard.img
```

### Proteus (전문 회로 시뮬레이터)

```markdown
- 유료 ($400+)
- 전자 회로 시뮬레이션 전문
- PSpice 통합 · 측정 도구
```

---

## 8. 데이터 저장 & 시계열 DB

### 시계열 데이터베이스

| DB | 특징 | 설치 | 한국 |
|---|---|---|---|
| **InfluxDB** | IoT 최적화 · 고속 쓰기 · 쿼리 언어 Flux | `docker run -d -p 8086:8086 influxdb` | ✅ 지원 |
| **TimescaleDB** | PostgreSQL 확장 · SQL · 빠른 압축 | `CREATE EXTENSION timescaledb` | ✅ 지원 |
| **QuestDB** | 초고속 · SIMD · 진정한 OLAP | `docker run -d -p 9000:9000 questdb/questdb` | ✅ 지원 |
| **Prometheus** | 메트릭 중심 · Pull 모델 · 경보 | `docker run -d -p 9090:9090 prom/prometheus` | ✅ 지원 |
| **Apache Kafka** | 스트리밍 · 고처리량 · 메시지 브로커 | `docker run -d confluentinc/cp-kafka` | ✅ 지원 |
| **MongoDB** (시계열) | NoSQL · 유연함 · 수평 확장 | `docker run -d -p 27017:27017 mongo` | ✅ 지원 |
| **SQLite** (엣지) | 경량 · 파일 기반 · 무제한 무료 | 내장 (Python · Node.js 등) | ✅ 최고 |

### InfluxDB 예제

```python
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

client = InfluxDBClient(url="http://localhost:8086", token="$TOKEN", org="my-org")
write_api = client.write_api(write_type=SYNCHRONOUS)

# 센서 데이터 저장
point = Point("temperature").tag("location", "living_room").field("value", 22.5)
write_api.write(bucket="my-bucket", record=point)

# 조회
query_api = client.query_api()
tables = query_api.query('from(bucket:"my-bucket") |> range(start:-1h)')
```

---

## 9. 스마트홈 & 자동화

### Home Assistant

```bash
# 설치 (Docker)
docker run -d --name homeassistant -p 8123:8123 homeassistant/home-assistant:latest

# configuration.yaml
automation:
  - alias: "온도 알림"
    trigger:
      platform: numeric_state
      entity_id: sensor.living_room_temperature
      above: 28
    action:
      service: notify.telegram
      data:
        message: "온도가 높습니다!"
```

### 한국 스마트홈 통합

```yaml
# SmartThings (Samsung)
integration:
  - type: smartthings
    token: $TOKEN

# Naver SmartHome API
homeassistant:
  # IFTTT로 연동
  - platform: ifttt
    key: $IFTTT_KEY
```

### Node-RED (시각적 자동화)

```markdown
1. Node-RED 실행: `npm install -g node-red && node-red`
2. http://localhost:1880 접속
3. 노드 연결:
   - [Inject] → [Function] → [MQTT out]
   - 시각적으로 플로우 구성
4. Deploy
```

---

## 10. 한국 IoT 생태계

### 통신사 IoT 플랫폼

| 사업자 | 기술 | 특징 | 가격 |
|---|---|---|---|
| **SKT (T-IoT)** | Cat.M1 · LoRa | 포괄적 · 엔터프라이즈 | 월 정액제 |
| **KT (GiGA IoT)** | NB-IoT · LoRa | 5G 통합 · 데이터센터 | 월 정액제 |
| **LG U+** | NB-IoT | 스마트홈 중심 | 월 정액제 |
| **ETRI** (한국전자통신연구원) | 표준 제시 · IoT 플랫폼 | 연구 · 개발자 지원 | 공개 |

### 공공 데이터 & API

| 자원 | 데이터 | API | 가격 |
|---|---|---|---|
| **공공데이터포털** | 환경 · 교통 · 기상 · 실시간 버스 | REST · XML | 무료 |
| **기상청 API** | 날씨 · 예보 · 초단시간 | REST | 무료 (API Key) |
| **한국도로공사 API** | 교통 정보 · 휴게소 · CCTV | REST | 무료 |
| **서울시 열린데이터광장** | 도시 데이터 · 센서 | REST · GeoJSON | 무료 |
| **SKT IoT 플랫폼** | 온디바이스 애널리틱스 · 디바이스 관리 | REST | 가입 필수 |

### 한국 센서 제조사

```bash
# 인기 센서 (온오프라인 쇼핑)
- DHT22 (온습도): 알리익스프레스 · 쿠팡
- MQ-135 (공기질): 한국전자
- HC-SR04 (초음파 거리): 로보틱스 가게
- GY-521 (가속도 + 자이로): 일반 전자부품점
- VEML7700 (조도): 고급 센서 전문점
```

---

## 11. 보안 (IoT Security)

### 펌웨어 서명 (OTA 업데이트)

```cpp
// ESP32 OTA 업데이트 (HTTPS)
#include "esp_ota_ops.h"
#include "esp_https_ota.h"

esp_https_ota_config_t ota_config = {
    .http_config = &http_config,
    .cert_pem = (char *)server_cert_pem_start,
};
esp_https_ota(&ota_config);
```

### 암호화 & 인증

```python
# MQTT over TLS
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.tls_set(
    ca_certs="ca.crt",
    certfile="client.crt",
    keyfile="client.key",
    tls_version=mqtt.ssl.PROTOCOL_TLSv1_2
)
client.connect("iot.example.com", 8883)
```

### 펌웨어 보안 점검

```bash
# Bandit (Python 보안 검사)
bandit -r .

# Cppcheck (C/C++ 정적 분석)
cppcheck --enable=all src/

# OWASP Dependency Check
dependency-check --project "My IoT" --scan ./libraries
```

---

## 12. 학습 리소스

### 튜토리얼 & 커뮤니티
- **Arduino Official**: https://www.arduino.cc/
- **Adafruit Learning System**: https://learn.adafruit.com/
- **Raspberry Pi Official**: https://www.raspberrypi.com/
- **ESP32 Documentation**: https://docs.espressif.com/
- **Home Assistant Community**: https://community.home-assistant.io/

### 온라인 강좌
- **Coursera**: IoT System Architecture & Design
- **edX**: Embedded Systems by UT Austin
- **YouTube**: GreatScott! · Andreas Spiess (IoT 튜토리얼)

---

## 13. 의사결정 매트릭스

```bash
프로젝트 복잡도?
├─ 단순 (LED · 버튼)
│  ├─ 보드: Arduino Uno
│  ├─ IDE: Arduino IDE
│  └─ 통신: Serial
├─ 중급 (Wi-Fi · 센서 · 클라우드)
│  ├─ 보드: ESP32
│  ├─ IDE: PlatformIO
│  ├─ 펌웨어: Arduino Core for ESP32
│  ├─ 통신: MQTT + Wi-Fi
│  └─ 클라우드: AWS IoT Core 또는 ThingsBoard
├─ 고급 (AI · 엣지 처리 · 고성능)
│  ├─ 보드: Jetson Nano 또는 Raspberry Pi 4
│  ├─ OS: Ubuntu / Raspbian
│  ├─ 프레임워크: TensorFlow Lite · PyTorch Mobile
│  ├─ 데이터: InfluxDB + Grafana
│  └─ 자동화: Home Assistant 또는 Node-RED
└─ 생산 배포
   ├─ 펌웨어: ESP-IDF (ESP32) 또는 Zephyr RTOS
   ├─ 보안: OTA 업데이트 · TLS · 펌웨어 서명
   └─ 모니터링: Prometheus + Grafana
```

---

## 14. 비용 최적화

| 시나리오 | 권장 조합 | 예상 비용 |
|---|---|---|
| **DIY 스마트홈** | Raspberry Pi 4 + Home Assistant + MQTT | $100-200 |
| **스타트업 IoT** | ESP32 × 100 + AWS IoT Core (프리 티어) | $500-1,000 |
| **엔터프라이즈** | Jetson Nano × 50 + InfluxDB 엔터프라이즈 + Grafana Cloud | $5,000+ |
| **한국 LTE IoT** | SKT T-IoT 기기 + 월정액 (단말 무료) | 월 3,000원+ |
| **오픈소스** | Raspberry Pi Pico × 50 + Home Assistant (자체호스트) | $300-500 |

---

**최종 업데이트**: 2026-05-20
