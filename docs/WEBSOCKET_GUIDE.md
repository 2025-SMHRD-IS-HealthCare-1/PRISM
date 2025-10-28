# 🚀 PRISM WebSocket 구조 - 사용 가이드

## 📊 시스템 구조

```
┌─────────────────┐      ┌─────────────────┐
│   라즈베리 파이    │      │    오렌지 파이     │
│   (센서 데이터)    │      │   (센서 데이터)    │
└────────┬────────┘      └────────┬────────┘
         │                        │
         │   HTTP POST /ingest    │
         │     (JSON 데이터)        │
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

## 🔧 설치 및 실행

### 1️⃣ FastAPI 서버 실행

```bash
# Python 패키지 설치 (이미 완료)
# pip install -r requirements.txt

# FastAPI 서버 실행
python server/api_server.py
```

서버가 실행되면:

- HTTP 서버: `http://localhost:8000`
- WebSocket: `ws://localhost:8000/ws`
- API 문서: `http://localhost:8000/docs`

### 2️⃣ 라즈베리 파이/오렌지 파이 설정

각 파이에서 `raspberry_pi_sensor.py`를 실행:

```bash
# 환경 변수 설정 (선택)
export API_SERVER="http://192.168.1.10:8000"  # FastAPI 서버 IP
export DEVICE_ID="rpi-01"  # 또는 "opi-01"

# 센서 스크립트 실행
python iot_devices/raspberry_pi_sensor.py
```

**여러 디바이스 실행 예시:**

라즈베리 파이:

```bash
DEVICE_ID="rpi-01" python iot_devices/raspberry_pi_sensor.py
```

오렌지 파이:

```bash
DEVICE_ID="opi-01" python iot_devices/raspberry_pi_sensor.py
```

### 3️⃣ 웹 페이지에서 확인

브라우저에서 다음 주소로 접속:

```
http://localhost:8000/static/websocket_test.html
```

또는 직접 `public/websocket_test.html` 파일을 열어도 됩니다.

## 📡 데이터 전송 형식

### 라즈베리 파이 → FastAPI

**엔드포인트:** `POST /ingest`

**요청 형식:**

```json
{
  "device_id": "rpi-01",
  "data": {
    "temperature": 24.8,
    "gas": 15.2,
    "dust": 8.5,
    "flame": false,
    "humidity": 55.0
  },
  "ts": 1730000000.0
}
```

**cURL 예시:**

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "rpi-01",
    "data": {"temp": 25.5, "hum": 60, "gas": 12.3},
    "ts": 1730000000.0
  }'
```

### FastAPI → 웹 브라우저 (WebSocket)

**연결:** `ws://localhost:8000/ws`

**메시지 형식:**

초기 연결 시:

```json
{
  "type": "init",
  "data": {
    "rpi-01": {
      "device_id": "rpi-01",
      "data": { "temperature": 24.8, "gas": 15.2 },
      "timestamp": 1730000000.0,
      "datetime": "2024-10-27T10:30:00"
    }
  },
  "timestamp": "2024-10-27T10:30:00"
}
```

데이터 업데이트 시:

```json
{
  "type": "update",
  "device_id": "rpi-01",
  "data": { "temperature": 25.1, "gas": 16.0 },
  "timestamp": "2024-10-27T10:30:05"
}
```

## 🧪 테스트

### 1. 서버 헬스 체크

```bash
curl http://localhost:8000/health
```

### 2. 최신 데이터 조회

```bash
# 모든 디바이스
curl http://localhost:8000/latest

# 특정 디바이스
curl http://localhost:8000/latest/rpi-01
```

### 3. 히스토리 데이터 조회

```bash
curl http://localhost:8000/history/rpi-01?limit=50
```

### 4. 연결된 디바이스 목록

```bash
curl http://localhost:8000/devices
```

## 🎯 실제 센서 연결

`raspberry_pi_sensor.py`의 센서 읽기 함수를 실제 센서 코드로 교체:

```python
def read_temperature_sensor():
    # 예: DHT22 센서
    import Adafruit_DHT
    sensor = Adafruit_DHT.DHT22
    pin = 4
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    return temperature if temperature is not None else 0
```

## 📋 주요 엔드포인트

| 엔드포인트             | 메서드    | 설명                      |
| ---------------------- | --------- | ------------------------- |
| `/ingest`              | POST      | 센서 데이터 수집          |
| `/ws`                  | WebSocket | 실시간 데이터 스트림      |
| `/latest`              | GET       | 모든 디바이스 최신 데이터 |
| `/latest/{device_id}`  | GET       | 특정 디바이스 최신 데이터 |
| `/history/{device_id}` | GET       | 특정 디바이스 히스토리    |
| `/devices`             | GET       | 연결된 디바이스 목록      |
| `/health`              | GET       | 서버 상태 확인            |
| `/docs`                | GET       | API 문서 (Swagger)        |

## 🔥 특징

✅ **실시간 스트리밍**: WebSocket으로 즉시 데이터 전달  
✅ **다중 디바이스 지원**: 여러 라즈베리파이/오렌지파이 동시 관리  
✅ **유연한 데이터 구조**: JSON 형식으로 자유로운 센서 데이터  
✅ **자동 재연결**: 연결 끊김 시 자동 재연결  
✅ **히스토리 저장**: 최근 1000개 데이터 포인트 저장

## 🛠️ 트러블슈팅

### WebSocket 연결 실패

- FastAPI 서버가 실행 중인지 확인
- 방화벽에서 8000번 포트 허용
- CORS 설정 확인

### 데이터가 표시되지 않음

- 라즈베리 파이에서 데이터 전송 확인
- `/latest` 엔드포인트로 데이터 확인
- 브라우저 콘솔에서 에러 메시지 확인

### 네트워크 문제

- 같은 네트워크에 연결되어 있는지 확인
- IP 주소가 올바른지 확인
- ping으로 연결 테스트

## 📝 환경 변수

라즈베리 파이:

- `API_SERVER`: FastAPI 서버 주소 (기본: http://localhost:8000)
- `DEVICE_ID`: 장치 ID (기본: rpi-01)

FastAPI 서버:

- `PORT`: 서버 포트 (기본: 8000)

## 🎓 추가 개선 사항

- [ ] 데이터베이스 연동 (MySQL)
- [ ] 사용자 인증 (JWT)
- [ ] HTTPS 지원
- [ ] Docker 컨테이너화

## 📞 문의

문제가 발생하면 GitHub Issues에 남겨주세요!
