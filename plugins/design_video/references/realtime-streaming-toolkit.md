# Realtime Streaming Toolkit — 실시간·라이브·인터랙티브

> **Phase 4**: 텍스트→디자인→미디어 이후 = **실시간**

---

## 1. WebSocket (양방향 실시간 통신)

### Python
```bash
pip install websockets         # 표준 WebSocket (async)
pip install python-socketio    # Socket.IO (폴링 폴백 포함)
pip install fastapi[all]       # FastAPI WebSocket 내장
pip install channels           # Django WebSocket (ASGI)
```

### JavaScript/Node
```html
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
```
```bash
npm install ws                 # Node.js WebSocket
npm install socket.io          # Socket.IO 서버
npm install @fastify/websocket # Fastify WebSocket
```

### 패턴: FastAPI WebSocket
```python
from fastapi import FastAPI, WebSocket
app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

---

## 2. SSE (Server-Sent Events — 단방향 스트리밍)

### Python
```python
# FastAPI SSE
from fastapi.responses import StreamingResponse
import asyncio

async def event_generator():
    while True:
        yield f"data: {json.dumps({'time': str(datetime.now())})}\n\n"
        await asyncio.sleep(1)

@app.get("/stream")
async def stream():
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### JavaScript (클라이언트)
```javascript
const source = new EventSource('/stream');
source.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

## 3. WebRTC (P2P 영상·음성 스트리밍)

### Python
```bash
pip install aiortc            # Python WebRTC
pip install aiohttp           # 시그널링 서버
```

### JavaScript
```html
<script src="https://cdn.jsdelivr.net/npm/peerjs@1.5.4/dist/peerjs.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/simple-peer@9.11.1/simplepeer.min.js"></script>
```
```bash
npm install mediasoup          # SFU 서버 (대규모)
npm install livekit-client     # LiveKit (오픈소스 Zoom 대안)
npm install @daily-co/daily-js # Daily.co (영상회의 API)
```

### 패턴: PeerJS (1:1 화상통화)
```javascript
const peer = new Peer();
peer.on('open', id => console.log('My ID:', id));

// 전화 걸기
navigator.mediaDevices.getUserMedia({video: true, audio: true})
  .then(stream => {
    const call = peer.call('remote-peer-id', stream);
    call.on('stream', remoteStream => {
      document.getElementById('remote-video').srcObject = remoteStream;
    });
  });
```

---

## 4. Live Dashboard (실시간 대시보드)

### Python
```bash
pip install streamlit          # 데이터 앱 (자동 리로드)
pip install gradio             # AI 데모 UI
pip install panel              # HoloViz 대시보드
pip install dash               # Plotly 대시보드
pip install nicegui            # Python-only 웹 UI
```

### JavaScript
```html
<!-- Chart.js 실시간 업데이트 -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>

<!-- Grafana Embed -->
<iframe src="http://grafana:3000/d/dashboard?refresh=5s" />

<!-- Apache ECharts 실시간 -->
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
```

### 패턴: Streamlit 실시간 메트릭
```python
import streamlit as st
import time

placeholder = st.empty()
while True:
    with placeholder.container():
        col1, col2, col3 = st.columns(3)
        col1.metric("CPU", f"{get_cpu()}%", "+2%")
        col2.metric("메모리", f"{get_mem()}GB")
        col3.metric("요청/초", f"{get_rps()}")
    time.sleep(1)
```

---

## 5. Message Queue (비동기 메시징)

### Python
```bash
pip install celery             # 분산 태스크 큐
pip install redis              # Redis (브로커 + 캐시)
pip install aio-pika           # RabbitMQ async
pip install kafka-python       # Apache Kafka
pip install nats-py            # NATS (경량 메시징)
```

### 패턴: Celery + Redis
```python
from celery import Celery
app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def restore_video(path):
    # 영상 복원 작업 (백그라운드)
    return upscale(path)

# 호출
restore_video.delay('/path/to/old_video.mp4')
```

---

## 6. Push Notification (푸시 알림)

### 웹 푸시
```bash
pip install pywebpush          # Web Push API
npm install web-push           # Node.js Web Push
```

### 모바일 푸시
```bash
pip install firebase-admin     # FCM (Android + iOS)
pip install apns2              # APNs (iOS 직접)
```

### 데스크톱 알림
```bash
pip install plyer              # 크로스플랫폼 알림 (Windows/Mac/Linux)
pip install win10toast-click   # Windows 10/11 토스트
```

---

## 7. Live Coding / Collaboration

### 실시간 협업 에디터
```bash
npm install yjs                # CRDT 실시간 동기화
npm install @hocuspocus/server # Yjs WebSocket 서버
npm install automerge          # CRDT (Ink & Switch)
```
```html
<script src="https://cdn.jsdelivr.net/npm/yjs@13.6.15/dist/yjs.min.js"></script>
```

### 터미널 공유
```bash
pip install ttyd               # 웹 터미널 (브라우저로 터미널 공유)
npm install xterm              # 웹 터미널 프론트엔드
```

---

## 8. IoT / Edge (사물인터넷)

```bash
pip install paho-mqtt          # MQTT 클라이언트 (IoT 표준)
pip install bleak              # Bluetooth LE
pip install pyserial           # 시리얼 통신 (Arduino 등)
npm install mqtt               # MQTT.js (브라우저 + Node)
```

---

## 9. Game / Interactive

### 게임 엔진 (웹)
```html
<script src="https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/kaboom@3000.1.17/dist/kaboom.js"></script>
<script src="https://cdn.jsdelivr.net/npm/excalibur@0.29.3/build/dist/excalibur.min.js"></script>
```

### Python 게임
```bash
pip install pygame             # 2D 게임
pip install arcade             # 모던 2D 게임 (교육용)
pip install pyglet             # OpenGL 게임
pip install ursina             # 3D 게임 (초간단)
```

---

## 10. Screen / Desktop Automation

```bash
pip install pyautogui          # 마우스·키보드 자동화
pip install pynput             # 입력 감지·제어
pip install mss                # 초고속 스크린샷 (멀티모니터)
pip install pygetwindow        # 윈도우 제어
pip install ahk                # AutoHotkey Python 바인딩
```

---

## 카테고리별 추천 조합

### 실시간 AI 대시보드
```text
FastAPI + WebSocket + Chart.js + Streamlit
```

### 영상 스트리밍 서비스
```text
WebRTC + mediasoup + FFmpeg + HLS.js
```

### 협업 에디터
```text
Yjs + WebSocket + Monaco Editor + Socket.IO
```

### IoT 모니터링
```text
MQTT + InfluxDB + Grafana + Celery
```

### 실시간 미디어 처리
```text
FFmpeg + Redis + Celery + WebSocket (진행률 알림)
```
