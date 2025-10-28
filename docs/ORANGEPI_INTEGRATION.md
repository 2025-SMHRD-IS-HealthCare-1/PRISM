# 🔥 오렌지파이 화재 감지 시스템 통합 가이드

## 📋 개요

오렌지파이의 화재/연기 감지 AI 모델을 PRISM 대시보드에 통합하여 실시간 화재 감지 및 경보 시스템을 구현했습니다.

---

## 🎯 주요 기능

### 1. 화재/연기 감지 자동 알림
- 오렌지파이가 화재 또는 연기 감지
- **무조건 위험 상태로 전환**
- TEST BOX 구역이 빨간색으로 표시
- 최상단 고정 이벤트 추가

### 2. CCTV 실시간 스트림
- 오렌지파이의 카메라 영상을 Base64로 실시간 전송
- 대시보드에서 CCTV 버튼 클릭 시 실시간 영상 표시
- 화재 감지 시 해당 프레임도 함께 표시

### 3. 라즈베리파이 부저 자동 울림
- 화재 감지 시 WebSocket으로 명령 전달
- 라즈베리파이가 부저를 자동으로 울림
- 5초간 경보음 발생

### 4. 브라우저 알림
- 화재 감지 시 즉시 브라우저 알림
- 신뢰도(confidence) 정보 포함
- 알림 클릭 시 대시보드로 이동

---

## 🔄 시스템 아키텍처

```
┌─────────────────────┐
│   오렌지파이          │
│   (화재 감지 AI)      │
│                      │
│  - YOLOv5 모델       │
│  - USB 카메라        │
│  - Fire/Smoke 감지   │
└──────────┬───────────┘
           │ WebSocket (fire_detection, video_stream)
           ▼
┌─────────────────────┐
│   FastAPI 서버       │
│   (중앙 허브)        │
│                      │
│  - WebSocket 브로드  │
│  - 부저 트리거 API   │
└──────────┬───────────┘
           │ 
           ├───────────────────────┐
           │                       │
           ▼                       ▼
┌─────────────────────┐   ┌─────────────────────┐
│   웹 대시보드        │   │   라즈베리파이       │
│   (프론트엔드)       │   │   (센서 + 부저)      │
│                      │   │                      │
│  - 화재 알림 표시    │   │  - 센서 데이터 전송  │
│  - CCTV 스트림       │   │  - 부저 울림         │
│  - 위험 상태 전환    │   │  - WebSocket 수신    │
└─────────────────────┘   └─────────────────────┘
```

---

## 📡 데이터 형식

### 1. 화재/연기 감지 메시지

```json
{
  "ts": "2025-10-28T12:34:56.789Z",
  "source": "orangepi_fire_detector_01",
  "type": "fire_detection",
  "label": "Fire",  // 또는 "Smoke"
  "score": 0.89,
  "bbox": [120, 45, 320, 280],
  "frame_size": [640, 480]
}
```

### 2. 비디오 스트림 메시지

```json
{
  "ts": "2025-10-28T12:34:56.789Z",
  "source": "orangepi_fire_detector_01",
  "type": "video_stream",
  "frame": "base64_encoded_image_data...",
  "width": 640,
  "height": 480
}
```

### 3. 부저 트리거 명령 (서버 → 라즈베리파이)

```json
{
  "type": "buzzer_trigger",
  "zone": "testbox",
  "reason": "fire_detected",
  "duration": 5000,
  "timestamp": "2025-10-28T12:34:56.789Z"
}
```

---

## 🚀 실행 방법

### 1️⃣ FastAPI 서버 실행

```bash
cd server
python3 api_server.py

# 또는 Render에 배포된 서버 사용
# https://prism-api-ay8q.onrender.com
```

### 2️⃣ 라즈베리파이 센서 실행

```bash
# websocket-client 설치 (부저 기능 활성화)
pip install websocket-client

# 센서 프로그램 실행
cd iot_devices
python3 raspberry_pi_sensor.py
```

실행 시 출력:
```
✅ WebSocket 연결 성공 (부저 리스너 활성화)
📊 데이터 수집 시작...
```

### 3️⃣ 오렌지파이 화재 감지 실행

```bash
# 오렌지파이에서 화재 감지 프로그램 실행
python3 fire_gui1.py
```

프로그램이 자동으로:
- API 서버에 연결
- 화재/연기 감지 시 WebSocket으로 메시지 전송
- 비디오 스트림 실시간 전송

### 4️⃣ 웹 대시보드 접속

```
https://prism-jnhr0jkrd-pangs-projects-6d3df8bf.vercel.app
```

---

## ✅ 동작 확인 체크리스트

### 화재 감지 테스트

- [ ] 오렌지파이 프로그램 실행
- [ ] 화재/연기 이미지를 카메라에 보여줌
- [ ] 대시보드에서 TEST BOX가 빨간색(위험)으로 변경되는지 확인
- [ ] 이벤트 목록 최상단에 "🔥 Fire 감지!" 표시되는지 확인
- [ ] 브라우저 알림이 뜨는지 확인
- [ ] 라즈베리파이 부저가 울리는지 확인 (5초)

### CCTV 스트림 테스트

- [ ] 대시보드에서 TEST BOX의 CCTV 버튼 클릭
- [ ] 오렌지파이 카메라 영상이 실시간으로 표시되는지 확인
- [ ] 화재 감지 시 해당 프레임이 표시되는지 확인

### 부저 트리거 테스트

- [ ] 라즈베리파이에서 `python3 raspberry_pi_sensor.py` 실행
- [ ] "WebSocket 리스너 시작 중..." 메시지 확인
- [ ] "✅ WebSocket 연결 성공 (부저 리스너 활성화)" 확인
- [ ] 화재 감지 시 "🔔 부저 트리거 명령 수신" 메시지 확인
- [ ] 부저가 울리는지 확인 (실제 GPIO 연결 필요)

---

## 🔧 설정 방법

### 오렌지파이 설정

`fire_gui1.py` 파일에서 API 서버 주소 확인:

```python
API_SERVER = "https://prism-api-ay8q.onrender.com"
```

### 라즈베리파이 설정

`raspberry_pi_sensor.py` 파일에서 API 서버 주소 확인:

```python
API_SERVER = os.getenv("API_SERVER", "http://localhost:8000")
```

환경 변수로 설정:
```bash
export API_SERVER=https://prism-api-ay8q.onrender.com
export DEVICE_ID=rpi-01
```

### 프론트엔드 설정

`public/js/dashboard.js` 파일에서 자동으로 설정됨:

```javascript
const CONFIG = {
  API_BASE_URL: window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "https://prism-api-ay8q.onrender.com",
  WS_BASE_URL: window.location.hostname === "localhost"
    ? "ws://localhost:8000"
    : "wss://prism-api-ay8q.onrender.com",
};
```

---

## 🐛 문제 해결

### 화재 감지가 안 될 때

1. **오렌지파이 프로그램이 실행 중인지 확인**
   ```bash
   ps aux | grep fire_gui1.py
   ```

2. **API 서버 연결 확인**
   ```bash
   curl https://prism-api-ay8q.onrender.com/health
   ```

3. **WebSocket 연결 확인**
   - 브라우저 개발자 도구 → Console
   - "✅ WebSocket 연결 성공" 메시지 확인

### CCTV 스트림이 안 나올 때

1. **오렌지파이가 video_stream 메시지를 전송하는지 확인**
   ```bash
   # API 서버 로그 확인
   journalctl -u prism-api -f
   ```

2. **브라우저 콘솔에서 확인**
   ```javascript
   // 개발자 도구 → Console
   console.log(cctvStreamFrame);  // Base64 데이터 확인
   ```

### 부저가 안 울릴 때

1. **websocket-client 설치 확인**
   ```bash
   pip list | grep websocket
   ```

2. **WebSocket 리스너 활성화 확인**
   ```bash
   # raspberry_pi_sensor.py 실행 시 출력 확인
   ✅ WebSocket 연결 성공 (부저 리스너 활성화)
   ```

3. **GPIO 핀 연결 확인**
   ```python
   # raspberry_pi_sensor.py에서 GPIO 설정 주석 해제
   import RPi.GPIO as GPIO
   GPIO.setmode(GPIO.BCM)
   GPIO.setup(BUZZER_PIN, GPIO.OUT)
   ```

4. **수동으로 부저 테스트**
   ```python
   import RPi.GPIO as GPIO
   GPIO.setmode(GPIO.BCM)
   GPIO.setup(18, GPIO.OUT)
   GPIO.output(18, GPIO.HIGH)
   import time
   time.sleep(3)
   GPIO.output(18, GPIO.LOW)
   GPIO.cleanup()
   ```

---

## 📊 API 엔드포인트

### POST /api/buzzer/trigger

부저를 울리는 명령을 WebSocket으로 전달합니다.

**요청 본문:**
```json
{
  "zone": "testbox",
  "reason": "fire_detected",
  "duration": 5000
}
```

**응답:**
```json
{
  "status": "success",
  "message": "부저 트리거 명령 전송 완료 (testbox)",
  "data": {
    "type": "buzzer_trigger",
    "zone": "testbox",
    "reason": "fire_detected",
    "duration": 5000,
    "timestamp": "2025-10-28T12:34:56.789Z"
  }
}
```

**cURL 예제:**
```bash
curl -X POST https://prism-api-ay8q.onrender.com/api/buzzer/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "zone": "testbox",
    "reason": "fire_detected",
    "duration": 5000
  }'
```

---

## 🔐 보안 고려사항

1. **API Key 추가** (권장)
   - 현재는 API Key 없이 동작
   - 프로덕션 환경에서는 `X-Api-Key` 헤더 추가 권장

2. **HTTPS/WSS 사용**
   - Vercel: 자동으로 HTTPS
   - Render: 자동으로 HTTPS + WSS

3. **CORS 설정**
   - 현재는 모든 도메인 허용 (`allow_origins=["*"]`)
   - 프로덕션에서는 특정 도메인만 허용 권장

---

## 📚 추가 참고 문서

- [OPI_API_guide.md](./OPI_API_guide.md) - 오렌지파이 API 상세 가이드
- [WEBSOCKET_GUIDE.md](./WEBSOCKET_GUIDE.md) - WebSocket 사용 가이드
- [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md) - 설치 가이드

---

## 🎉 완료!

이제 오렌지파이의 화재 감지 결과가 실시간으로 대시보드에 반영되고, 라즈베리파이 부저가 자동으로 울립니다! 🔥🚨
