# 🎯 PRISM WebSocket 구조 - 빠른 시작 가이드

## 📦 설치 완료!

모든 패키지가 설치되었습니다:

- ✅ FastAPI & Uvicorn (웹 서버)
- ✅ WebSocket 지원
- ✅ Express (Node.js 백엔드)
- ✅ 모든 Python 패키지

---

## 🚀 3단계로 시작하기

### 1️⃣ FastAPI 서버 실행

```bash
cd "/Users/ipang/Desktop/대학교/활동/대외 활동/엣지 AI기반 헬스케어 서비스개발자과정/PRISM"
python server/api_server.py
```

서버 실행 후:

- 📡 HTTP API: http://localhost:8000
- 🔌 WebSocket: ws://localhost:8000/ws
- 📚 API 문서: http://localhost:8000/docs

---

### 2️⃣ 테스트 데이터 전송

**새 터미널**을 열고:

```bash
python scripts/test_sender.py
```

이 스크립트는 3개의 가상 디바이스(rpi-01, opi-01, test-device)에서  
5초마다 자동으로 더미 데이터를 전송합니다.

---

### 3️⃣ 웹 페이지에서 실시간 확인

브라우저에서 다음 파일을 엽니다:

```
public/websocket_test.html
```

또는 다음 주소로 접속:

```
http://localhost:8000
```

---

## 🎬 실제 라즈베리 파이에서 실행

라즈베리 파이 또는 오렌지 파이에서:

```bash
# 서버 주소 설정 (Mac의 IP 주소로 변경)
export API_SERVER="http://192.168.1.XXX:8000"
export DEVICE_ID="rpi-01"

# 센서 스크립트 실행
python iot_devices/raspberry_pi_sensor.py
```

**Mac의 IP 주소 확인:**

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

---

## 📊 데이터 흐름

```
[라즈베리파이] → HTTP POST /ingest → [FastAPI] → WebSocket → [브라우저]
    센서 데이터          JSON 전송        실시간 처리     실시간 표시
```

---

## 🧪 테스트 명령어

### 서버 상태 확인

```bash
curl http://localhost:8000/health
```

### 수동으로 데이터 전송

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test-01",
    "data": {"temp": 25.5, "hum": 60},
    "ts": 1730000000.0
  }'
```

### 최신 데이터 조회

```bash
curl http://localhost:8000/latest
```

---

## 📁 주요 파일

| 파일                         | 설명                                  |
| ---------------------------- | ------------------------------------- |
| `api_server.py`              | FastAPI 서버 (WebSocket 포함)         |
| `raspberry_pi_sensor.py`     | 라즈베리파이/오렌지파이 센서 스크립트 |
| `test_sender.py`             | 테스트용 더미 데이터 전송             |
| `public/websocket_test.html` | 실시간 대시보드 웹 페이지             |
| `WEBSOCKET_GUIDE.md`         | 상세 가이드 문서                      |

---

## ⚙️ 환경 설정

### 라즈베리 파이

```bash
export API_SERVER="http://192.168.1.10:8000"  # FastAPI 서버 IP
export DEVICE_ID="rpi-01"                      # 디바이스 ID
```

### 오렌지 파이

```bash
export API_SERVER="http://192.168.1.10:8000"
export DEVICE_ID="opi-01"
```

---

## 🎉 다음 단계

1. **실제 센서 연결**: `raspberry_pi_sensor.py`의 센서 읽기 함수 수정
2. **웹 대시보드 커스터마이징**: `websocket_test.html` 수정
3. **데이터베이스 연동**: PostgreSQL, MongoDB 등
4. **알림 기능 추가**: 임계값 초과 시 알림
5. **배포**: Vercel, Heroku, AWS 등

---

## 🆘 문제 해결

### "연결할 수 없습니다"

→ FastAPI 서버가 실행 중인지 확인: `python server/api_server.py`

### WebSocket 연결 실패

→ 방화벽 설정 확인, 8000번 포트 열기

### 데이터가 표시되지 않음

→ `/latest` 엔드포인트로 데이터 확인: `curl http://localhost:8000/latest`

---

## 📞 추가 정보

자세한 내용은 `WEBSOCKET_GUIDE.md` 파일을 참고하세요!

**API 문서**: http://localhost:8000/docs
