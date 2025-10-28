# PRISM 센서 통합 업데이트 (2025-10-28)

## 🎯 개선 사항 요약

라즈베리 파이의 실제 센서 데이터 구조를 반영하여 PRISM 대시보드를 전면 개선했습니다.

## 📊 센서 데이터 구조

### 라즈베리 파이 센서 (라즈베리 파이에서 직접 실행)

```json
{
  "device_id": "rpi-01",
  "data": {
    "flame": false, // 불꽃 감지 (boolean)
    "gas": 126, // 가스 농도 원시값 (0~1023)
    "gas_voltage": 0.406, // 가스 센서 전압 (V)
    "temperature": 23.56, // 온도 (°C)
    "pm1": 4, // 미세먼지 PM1.0 (μg/m³)
    "pm25": 1, // 미세먼지 PM2.5 (μg/m³)
    "pm10": 4, // 미세먼지 PM10 (μg/m³)
    "gas_delta": 22 // 가스 변화량 (baseline 대비)
  }
}
```

**참고**: 라즈베리 파이의 센서 코드는 라즈베리 파이에서 직접 실행되며, API 서버는 HTTP POST로 전송된 데이터를 받아서 처리합니다.

## 🚨 위험 단계 임계값

### 1. 불꽃 감지 (flame)

- **위험**: 불꽃 감지 시 즉시 알람

### 2. 온도 (temperature)

- **위험 (danger)**: > 35°C
- **경고 (warning)**: > 30°C
- **주의 (caution)**: > 25°C

### 3. 가스 농도 (gas)

- **위험**: > 200 (원시값)
- **경고**: > 150
- **주의**: > 100

### 4. 가스 급증 (gas_delta)

- **위험**: > 50 (급격한 증가)
- **경고**: > 30

### 5. 미세먼지 PM1.0 (pm1)

- **위험**: > 50 μg/m³

### 6. 미세먼지 PM2.5 (pm25)

- **위험**: > 35 μg/m³
- **경고**: > 25 μg/m³
- **주의**: > 15 μg/m³

### 7. 미세먼지 PM10 (pm10)

- **위험**: > 100 μg/m³
- **경고**: > 75 μg/m³
- **주의**: > 50 μg/m³

## 🔧 주요 변경 사항

### 1. API 서버 개선

- **파일**: `server/api_server.py`
- **추가 기능**:
  - `check_thresholds()` 함수: 실시간 임계값 체크
  - 위험 수준 판단 (danger/warning/caution/normal)
  - WebSocket으로 알람 브로드캐스트
  - 알람 이유 (reasons) 전송

### 2. 대시보드 UI 업데이트

- **파일**: `public/index.html`
- **센서 표시**:
  - 온도 (temperature)
  - 가스 농도 (gas)
  - 미세먼지 (PM1, PM2.5, PM10을 종합하여 계산)
  - 불꽃 감지 (flame)
  - 가스 변화량 (gas_delta)

**미세먼지 계산 로직**:

- PM2.5 값을 우선 사용
- PM2.5가 없으면 PM1과 PM10의 평균으로 추정
- 단일 값으로 표시하여 직관적인 모니터링 제공

### 3. JavaScript 로직 개선

- **파일**: `public/js/dashboard.js`
- **추가 기능**:
  - WebSocket 실시간 연결
  - 자동 재연결 (5초 간격)
  - 위험 알람 표시 (`showDangerAlert()`)
  - 브라우저 알림 (Notification API)
  - 임계값 체크 로직 동기화
  - 미세먼지 종합 계산 (PM1, PM2.5, PM10)

### 4. CSS 스타일 개선

- **파일**: `public/css/dashboard.css`
- **추가 스타일**:
  - 센서 그리드 자동 조정 (auto-fit)
  - 위험 알람 애니메이션 (pulse-danger, pulse-warning)
  - 호버 효과 개선
  - 알람 텍스트 펄스 애니메이션

## 🌐 시스템 아키텍처

```
┌─────────────────────┐
│  라즈베리 파이       │
│  (all_sensors_      │
│   integrated.py)    │
│  - Flame Sensor     │
│  - MQ-2 (Gas)       │
│  - DS18B20 (Temp)   │
│  - PMS7003M (PM)    │
│  - Buzzer Alarm     │
└──────────┬──────────┘
           │ HTTP POST
           │ /ingest
           ▼
┌─────────────────────┐
│   FastAPI 서버       │
│   (api_server.py)   │
│  - 임계값 체크       │
│  - 데이터 저장       │
│  - WebSocket 전송    │
└──────────┬──────────┘
           │ WebSocket
           │ /ws
           ▼
┌─────────────────────┐
│   웹 브라우저        │
│   (dashboard.js)    │
│  - 실시간 모니터링   │
│  - 알람 표시         │
│  - 차트 업데이트     │
└─────────────────────┘
```

## 🚀 실행 방법

### 1. 라즈베리 파이에서 센서 실행

```bash
# 환경변수 설정 (선택)
export API_SERVER="https://prism-api-ay8q.onrender.com"
export DEVICE_ID="rpi-01"

# 센서 프로그램 실행
python3 iot_devices/all_sensors_integrated.py
```

### 2. API 서버 실행 (Render에 이미 배포됨)

```bash
# 로컬 테스트
cd server
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000
```

### 3. 대시보드 접속

- **로컬**: http://localhost:8000 (API 서버에서 정적 파일 제공)
- **배포**: https://prism-dashboard.vercel.app

## 📱 브라우저 알림 설정

대시보드에서 위험 알람 발생 시 브라우저 알림을 받으려면:

```javascript
// 개발자 도구 콘솔에서 실행
Notification.requestPermission();
```

## 🔍 테스트 방법

### 1. 센서 데이터 전송 테스트

```bash
curl -X POST https://prism-api-ay8q.onrender.com/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "rpi-01",
    "data": {
      "flame": true,
      "gas": 250,
      "temperature": 40,
      "pm1": 60,
      "pm25": 45,
      "pm10": 120,
      "gas_delta": 80
    }
  }'
```

### 2. WebSocket 연결 테스트

```javascript
// 브라우저 개발자 도구에서 실행
const ws = new WebSocket("wss://prism-api-ay8q.onrender.com/ws");
ws.onmessage = (e) => console.log("수신:", JSON.parse(e.data));
ws.onopen = () => console.log("✅ 연결됨");
```

## 📝 주요 파일 목록

```
PRISM/
├── server/
│   └── api_server.py                 # ✏️ 수정: 임계값 체크 추가
├── public/
│   ├── index.html                    # ✏️ 수정: 센서 표시 간소화
│   ├── css/
│   │   └── dashboard.css             # ✏️ 수정: 알람 스타일 추가
│   └── js/
│       └── dashboard.js              # ✏️ 수정: WebSocket, 미세먼지 계산
└── SENSOR_INTEGRATION_UPDATE.md      # 🆕 이 문서
```

## 🎨 UI/UX 개선 사항

1. **센서 카드 자동 배치**: 추가 센서에 맞춰 그리드 자동 조정
2. **위험 알람 애니메이션**: 펄스 효과로 시각적 경고
3. **실시간 상태 업데이트**: WebSocket으로 지연 없는 모니터링
4. **브라우저 알림**: 위험 감지 시 즉시 알림
5. **자동 재연결**: 네트워크 단절 시 자동 복구

## 🔐 보안 및 성능

- **HTTPS/WSS**: 보안 통신 (Render 배포)
- **메모리 관리**: 최근 1000개 데이터만 유지
- **센서 보정**: MQ-2 가스 센서 EMA 평활화
- **알람 래칭**: 3초 최소 지속으로 오작동 방지

## 📚 참고 자료

- [FastAPI WebSocket 문서](https://fastapi.tiangolo.com/advanced/websockets/)
- [Raspberry Pi GPIO 문서](https://www.raspberrypi.com/documentation/computers/os.html#gpio-and-the-40-pin-header)
- [PMS7003M 데이터시트](http://www.plantower.com/en/content/?110.html)

---

**작성일**: 2025-10-28  
**버전**: 3.0.0  
**작성자**: PRISM Team
