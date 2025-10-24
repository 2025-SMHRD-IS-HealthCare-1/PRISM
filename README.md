# PRISM

라즈베리파이 센서 데이터를 실시간으로 수집하고 웹 대시보드에 표시하는 공장 혼합 구역 실시간 관제 시스템입니다.

## 🎯 주요 기능

### 웹 대시보드
- **실시간 모니터링**: 온도, 가스, 미세먼지, 불꽃 감지 센서 데이터 실시간 표시
- **구역 관리**: 여러 구역(TEST BOX, 원자재 창고, 제품 검사실, 기계/전기실)을 선택하여 모니터링
- **상태 표시**: 위험, 경고, 주의, 정상 4단계 상태 색상 구분
- **CCTV 모니터링**: 각 구역의 CCTV 실시간 스트리밍 (팝업)
- **상세 정보**: 구역별 상세 정보 및 과거 데이터 그래프
- **과거 데이터**: 일간 평균 상태 그래프 및 최근 이벤트 로그
- **통계 정보**: 일일 이벤트 발생 건수, 활성 센서/카메라 수, 시스템 가동 상태

### FastAPI 서버
- **센서 데이터 수신**: 라즈베리파이에서 POST 요청으로 센서 데이터 수신
- **데이터 제공**: 웹 대시보드에 GET 요청으로 실시간/과거 데이터 제공
- **CORS 지원**: 웹 브라우저에서 API 호출 가능
- **자동 문서화**: FastAPI의 자동 API 문서 제공 (/docs)

### 라즈베리파이 센서 시스템
- **다중 센서 지원**: 온도, 가스, 미세먼지, 불꽃 감지 센서
- **자동 전송**: 5초마다 센서 데이터를 FastAPI 서버로 자동 전송
- **임계값 알림**: 위험 수준 감지시 콘솔 알림

## 📁 프로젝트 구조

```
PRISM/
├── public/
│   ├── index.html          # 메인 대시보드 HTML
│   ├── Example.html        # 참고용 예제 (주석)
│   ├── css/
│   │   ├── main.css        # 기본 스타일
│   │   └── dashboard.css   # 대시보드 스타일
│   └── js/
│       └── dashboard.js    # 대시보드 로직 (FastAPI 연동)
├── api_server.py           # FastAPI 서버
├── raspberry_pi_sensor.py  # 라즈베리파이 센서 데이터 수집/전송
├── app.js                  # Node.js Express 서버 (선택)
├── package.json
└── README.md               # 이 파일
```

## 🚀 설치 및 실행

### 1. 웹 서버 실행 (정적 파일)

#### 방법 1: Python HTTP 서버 (간단)
```bash
cd PRISM/public
python -m http.server 3000
```

#### 방법 2: Node.js Express 서버
```bash
cd PRISM
npm install
node app.js
```

웹 브라우저에서 접속: http://localhost:3000

### 2. FastAPI 서버 실행

#### 설치
```bash
pip install fastapi uvicorn requests
```

#### 실행
```bash
cd PRISM
python api_server.py
```

FastAPI 서버가 http://localhost:8000 에서 실행됩니다.
API 문서: http://localhost:8000/docs

### 3. 라즈베리파이 센서 시스템 실행

#### 설치 (라즈베리파이)
```bash
pip install requests

# 실제 센서 사용시 추가 라이브러리
# pip install RPi.GPIO Adafruit_DHT adafruit-circuitpython-ads1x15
```

#### 실행
```bash
cd PRISM
python raspberry_pi_sensor.py
```

**주의**: `raspberry_pi_sensor.py` 파일에서 API_SERVER 주소를 FastAPI 서버의 실제 주소로 변경하세요.

```python
API_SERVER = "http://192.168.1.100:8000"  # FastAPI 서버 IP 주소
```

## 🔧 설정

### JavaScript (dashboard.js)
```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',  // FastAPI 서버 주소
    UPDATE_INTERVAL: 5000,                  // 데이터 업데이트 주기 (5초)
    CHART_UPDATE_INTERVAL: 30000,           // 차트 업데이트 주기 (30초)
};
```

### Python (raspberry_pi_sensor.py)
```python
API_SERVER = "http://localhost:8000"  # FastAPI 서버 주소
ZONE_ID = "testbox"                   # 구역 ID
SEND_INTERVAL = 5                     # 전송 주기 (초)
```

## 📊 API 엔드포인트

### 센서 데이터 전송 (라즈베리파이 → 서버)
```http
POST /api/sensors/{zone}
Content-Type: application/json

{
  "zone": "testbox",
  "temperature": 25.5,
  "gas": 30.2,
  "dust": 12.5,
  "flame": false,
  "timestamp": "2024-10-23T15:30:00"
}
```

### 센서 데이터 가져오기 (서버 → 대시보드)
```http
GET /api/sensors/{zone}

Response:
{
  "zone": "testbox",
  "temperature": 25.5,
  "gas": 30.2,
  "dust": 12.5,
  "flame": false,
  "timestamp": "2024-10-23T15:30:00"
}
```

### 과거 데이터 가져오기
```http
GET /api/history/{zone}?hours=24

Response: [
  {
    "timestamp": "2024-10-23T14:00:00",
    "temperature": 24.5,
    "gas": 28.0,
    "dust": 10.2
  },
  ...
]
```

### 구역 목록
```http
GET /api/zones

Response: [
  {
    "id": "testbox",
    "name": "TEST BOX",
    "active": true,
    "status": "normal"
  },
  ...
]
```

## 🎨 상태 색상 기준

| 상태 | 온도 | 가스 (ppm) | 미세먼지 (g/m³) | 불꽃 | 색상 |
|------|------|------------|-----------------|------|------|
| 위험 | > 50°C | > 100 | > 50 | 감지 | 빨강 |
| 경고 | > 40°C | > 70 | > 30 | - | 주황 |
| 주의 | > 30°C | > 50 | > 20 | - | 파랑 |
| 정상 | ≤ 30°C | ≤ 50 | ≤ 20 | - | 초록 |

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

## 🛠 개발 환경

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python 3.8+, FastAPI, Uvicorn
- **Charts**: Chart.js
- **Icons**: Font Awesome 6
- **Hardware**: Raspberry Pi (3/4), 각종 센서

## 📝 테스트 모드

FastAPI 서버와 라즈베리파이 센서 프로그램은 더미 데이터를 생성하여 실제 센서 없이도 테스트할 수 있습니다.

1. FastAPI 서버 실행
2. 웹 브라우저에서 대시보드 열기
3. 자동으로 더미 데이터가 표시됨

## 🚨 문제 해결

### CORS 오류
- FastAPI 서버의 CORS 설정 확인
- 브라우저 개발자 도구에서 네트워크 탭 확인

### 센서 데이터가 표시되지 않음
- FastAPI 서버가 실행 중인지 확인
- `dashboard.js`의 `API_BASE_URL` 확인
- 브라우저 콘솔에서 오류 메시지 확인

### 라즈베리파이 연결 오류
- FastAPI 서버 주소가 올바른지 확인
- 방화벽 설정 확인
- 네트워크 연결 확인

## 📄 라이선스

이 프로젝트는 교육 및 개발 목적으로 제작되었습니다.

## 👥 개발팀

미야호팀 - PRISM 프로젝트

---

**참고**: `Example.html`에는 프로젝트 요구사항이 주석으로 정리되어 있습니다.
