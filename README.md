# PRISM

라즈베리파이/오렌지파이 센서 데이터를 **WebSocket으로 실시간 수집**하고 웹 대시보드에 즉시 표시하는 공장 혼합 구역 실시간 관제 시스템입니다.

## 🚀 새로운 WebSocket 구조 (v3.0.0)

```
┌─────────────────┐      ┌─────────────────┐
│  라즈베리 파이     │       │    오렌지 파이    │
│   (센서 데이터)    │      │   (센서 데이터)    │
└────────┬────────┘      └────────┬────────┘
         │                        │
         │   HTTP POST /ingest    │
         │      (JSON 데이터)       │
         └──────────┬─────────────┘
                    ▼
         ┌─────────────────────┐
         │     FastAPI 서버     │
         │     (데이터 허브)      │
         │    - 데이터 수집       │
         │    - WebSocket 서버  │
         └─────────┬───────────┘
                   │
                   │ WebSocket 실시간 스트리밍
                   ▼
         ┌─────────────────────┐
         │      웹 브라우저       │
         │    (실시간 대시보드)    │
         └─────────────────────┘
```

## 🎯 주요 기능

### 🔥 WebSocket 실시간 스트리밍 (NEW!)

- **즉각적인 데이터 전달**: 센서 데이터가 수집되는 즉시 모든 연결된 브라우저에 전송
- **자동 재연결**: 연결이 끊어지면 자동으로 재연결 시도
- **다중 디바이스 지원**: 여러 라즈베리파이/오렌지파이 동시 관리
- **연결 상태 모니터링**: 실시간 연결 상태 표시

### 웹 대시보드

- **실시간 모니터링**: 온도, 가스, 미세먼지, 불꽃 감지 센서 데이터 실시간 표시
- **구역 관리**: 여러 구역(TEST BOX, 원자재 창고, 제품 검사실, 기계/전기실)을 선택하여 모니터링
- **상태 표시**: 위험, 경고, 주의, 정상 4단계 상태 색상 구분
- **CCTV 모니터링**: 각 구역의 CCTV 실시간 스트리밍
- **과거 데이터**: 일간 평균 상태 그래프 및 최근 이벤트 로그
- **WebSocket 테스트 페이지**: 실시간 데이터 스트림 확인용 페이지

### FastAPI 서버 (v3.0.0)

- **WebSocket 지원**: 실시간 양방향 통신
- **데이터 수집**: `/ingest` 엔드포인트로 센서 데이터 수신
- **실시간 브로드캐스트**: 새 데이터를 모든 연결된 클라이언트에게 즉시 전송
- **히스토리 관리**: 최근 1000개 데이터 포인트 저장
- **다중 디바이스**: device_id로 여러 디바이스 구분 관리
- **자동 문서화**: FastAPI의 자동 API 문서 제공 (/docs)

### 라즈베리파이/오렌지파이 센서 시스템

- **다중 센서 지원**: 온도, 가스, 미세먼지, 불꽃 감지 센서
- **자동 전송**: 5초마다 센서 데이터를 FastAPI 서버로 자동 전송
- **유연한 데이터 구조**: JSON 형식으로 자유로운 센서 데이터 전송
- **임계값 알림**: 위험 수준 감지시 콘솔 알림
- **연결 상태 확인**: 서버 헬스 체크 및 재연결 로직

## 📁 프로젝트 구조

> 📖 상세한 구조 설명은 **[STRUCTURE.md](STRUCTURE.md)** 파일을 참고하세요!

```
PRISM/
├── 📁 server/              # 서버 관련 파일
│   ├── api_server.py       # FastAPI 서버 (WebSocket 지원)
│   └── app.js              # Express 서버 (선택)
│
├── 📁 iot_devices/         # IoT 디바이스 스크립트
│   └── raspberry_pi_sensor.py  # 라즈베리파이/오렌지파이
│
├── 📁 public/              # 웹 프론트엔드
│   ├── index.html          # 메인 대시보드
│   ├── websocket_test.html # WebSocket 테스트 페이지
│   ├── css/                # 스타일시트
│   ├── js/                 # JavaScript
│   └── image/              # 이미지 리소스
│
├── 📁 scripts/             # 유틸리티 스크립트
│   └── test_sender.py      # 테스트 데이터 전송
│
├── 📁 tests/               # 테스트 파일
│
├── 📁 docs/                # 문서
│   ├── QUICKSTART.md       # 빠른 시작 가이드
│   ├── WEBSOCKET_GUIDE.md  # WebSocket 상세 가이드
│   ├── INSTALLATION_GUIDE.md  # 설치 가이드
│   └── DEPLOYMENT.md       # 배포 가이드
│
├── 📄 README.md            # 이 파일
├── 📄 STRUCTURE.md         # 프로젝트 구조 상세 설명
├── 📄 requirements.txt     # Python 패키지
├── 📄 package.json         # Node.js 패키지
└── 📄 .env.example         # 환경 변수 예제
```

## 🚀 빠른 시작 (3단계)

> 📖 자세한 내용은 **[docs/QUICKSTART.md](docs/QUICKSTART.md)** 파일을 참고하세요!

### 1️⃣ FastAPI 서버 실행

```bash
# Python 패키지 설치
pip install -r requirements.txt

# FastAPI 서버 실행
python server/api_server.py
```

서버 실행 후:

- 📡 HTTP API: http://localhost:8000
- 🔌 WebSocket: ws://localhost:8000/ws
- 📚 API 문서: http://localhost:8000/docs

### 2️⃣ 테스트 데이터 전송 (새 터미널)

```bash
# 테스트용 더미 데이터 자동 전송
python scripts/test_sender.py
```

3개의 가상 디바이스(rpi-01, opi-01, test-device)에서 5초마다 데이터 전송

### 3️⃣ 웹 페이지에서 실시간 확인

브라우저에서 열기:

```bash
open public/websocket_test.html
```

또는 브라우저에서 http://localhost:8000 접속

---

## 🔧 실제 라즈베리 파이/오렌지 파이 연결

### 라즈베리 파이 설정

```bash
# 서버 주소 설정 (Mac/PC의 IP 주소로 변경)
export API_SERVER="http://192.168.1.XXX:8000"
export DEVICE_ID="rpi-01"

# 센서 스크립트 실행
python iot_devices/raspberry_pi_sensor.py
```

### 오렌지 파이 설정

```bash
export API_SERVER="http://192.168.1.XXX:8000"
export DEVICE_ID="opi-01"

python iot_devices/raspberry_pi_sensor.py
```

**Mac/PC의 IP 주소 확인:**

```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig
```

---

## 📊 API 엔드포인트

### 🔥 WebSocket & 새로운 데이터 수집 API

| 엔드포인트             | 메서드    | 설명                      |
| ---------------------- | --------- | ------------------------- |
| `/ws`                  | WebSocket | 실시간 데이터 스트림      |
| `/ingest`              | POST      | 센서 데이터 수집          |
| `/latest`              | GET       | 모든 디바이스 최신 데이터 |
| `/latest/{device_id}`  | GET       | 특정 디바이스 최신 데이터 |
| `/history/{device_id}` | GET       | 특정 디바이스 히스토리    |
| `/devices`             | GET       | 연결된 디바이스 목록      |
| `/health`              | GET       | 서버 상태 확인            |
| `/docs`                | GET       | API 문서 (Swagger)        |

### WebSocket 연결 예시

```javascript
const ws = new WebSocket("ws://localhost:8000/ws");

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === "update") {
    console.log("새 데이터:", message.device_id, message.data);
  }
};
```

### 데이터 전송 예시 (라즈베리파이)

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "rpi-01",
    "data": {"temp": 25.5, "hum": 60, "gas": 12.3},
    "ts": 1730000000.0
  }'
```

---

## 🎨 상태 색상 기준

| 상태 | 온도   | 가스 (ppm) | 미세먼지 (μg/m³) | 불꽃 | 색상 |
| ---- | ------ | ---------- | ---------------- | ---- | ---- |
| 위험 | > 50°C | > 100      | > 50             | 감지 | 빨강 |
| 경고 | > 40°C | > 70       | > 30             | -    | 주황 |
| 주의 | > 30°C | > 50       | > 20             | -    | 파랑 |
| 정상 | ≤ 30°C | ≤ 50       | ≤ 20             | -    | 초록 |

---

## 🔌 라즈베리파이 센서 연결

### 권장 센서

1. **온도 센서**: DHT22 (온도/습도)
2. **가스 센서**: MQ-2, MQ-135 (ADC 필요: ADS1115)
3. **미세먼지 센서**: PMS5003, GP2Y1010AU0F
4. **불꽃 감지 센서**: KY-026 Flame Sensor

### GPIO 핀 연결 예제

```
DHT22      → GPIO 4
MQ-2       → ADS1115 (I2C: SDA, SCL)
PMS5003    → UART (TX, RX)
KY-026     → GPIO 17
```

---

## 🧪 테스트

### 1. 서버 헬스 체크

```bash
curl http://localhost:8000/health
```

### 2. 최신 데이터 조회

```bash
curl http://localhost:8000/latest
```

### 3. 수동 데이터 전송

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test","data":{"temp":25},"ts":1730000000}'
```

---

## 🛠 개발 환경

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python 3.8+, FastAPI, Uvicorn, WebSockets
- **Charts**: Chart.js
- **Icons**: Font Awesome 6
- **Hardware**: Raspberry Pi, Orange Pi, 각종 센서

---

## 🚨 문제 해결

### WebSocket 연결 실패

- FastAPI 서버가 실행 중인지 확인
- 방화벽에서 8000번 포트 허용
- 브라우저 콘솔에서 에러 메시지 확인

### 데이터가 표시되지 않음

- 라즈베리 파이에서 데이터 전송 확인
- `/latest` 엔드포인트로 데이터 확인: `curl http://localhost:8000/latest`
- 서버 로그 확인

### 네트워크 문제

- 같은 네트워크에 연결되어 있는지 확인
- IP 주소가 올바른지 확인
- ping으로 연결 테스트: `ping 192.168.1.XXX`

---

## 📚 추가 문서

- **[QUICKSTART.md](QUICKSTART.md)** - 빠른 시작 가이드
- **[WEBSOCKET_GUIDE.md](WEBSOCKET_GUIDE.md)** - WebSocket 상세 가이드
- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - 설치 가이드
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - 배포 가이드

---

## 🎓 주요 변경사항 (v3.0.0)

✨ **새로운 기능**

- WebSocket 실시간 스트리밍 추가
- `/ingest` 엔드포인트로 간소화된 데이터 수집
- 다중 디바이스 지원 (device_id 기반)
- 자동 재연결 기능
- 히스토리 데이터 관리 (최근 1000개)
- WebSocket 테스트 페이지 추가

🔄 **호환성**

- 기존 API 엔드포인트 유지 (`/api/sensors/{zone}`)
- 점진적 마이그레이션 지원

---

## 📄 라이선스

이 프로젝트는 교육 및 개발 목적으로 제작되었습니다.

## 👥 개발팀

미야호팀 - PRISM 프로젝트

---

**🚀 지금 바로 시작하세요!**

```bash
python server/api_server.py     # 1. 서버 실행
python scripts/test_sender.py    # 2. 테스트 데이터 전송
open public/websocket_test.html  # 3. 웹 페이지 확인
```
