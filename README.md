# PRISM

공장 내 위험 요소를 실시간으로 감지하고 모니터링하는 산업 안전 관제 시스템입니다. 오렌지파이의 온디바이스 AI와 라즈베리파이 센서를 통해 온도, 가스, 미세먼지, 불꽃을 감지하며, 웹 대시보드를 통해 실시간 데이터를 시각화하여 조기 예방을 진행합니다.

## 배포된 서비스

- **웹 대시보드**: https://prism-ejmi593l2-pangs-projects-6d3df8bf.vercel.app
- **API 서버 (FastAPI)**: https://prism-api.onrender.com
- **API 문서**: https://prism-api.onrender.com/docs

> 참고: FastAPI 서버는 Render.com의 무료 플랜으로 배포되어 있어, 15분 미사용 시 슬립 모드로 전환됩니다. 첫 요청 시 약간의 지연이 발생할 수 있습니다.

## 주요 기능

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

## 프로젝트 구조

```
PRISM/
├── public/
│   ├── index.html          # 메인 대시보드 HTML
│   ├── css/
│   │   ├── main.css        # 기본 스타일
│   │   └── dashboard.css   # 대시보드 스타일
│   ├── js/
│   │   └── dashboard.js    # 대시보드 로직
│   └── image/              # 이미지 리소스
├── api_server.py           # FastAPI 서버
├── app.js                  # Node.js Express 서버 (프록시)
├── raspberry_pi_sensor.py  # 라즈베리파이 센서 데이터 수집/전송
├── package.json            # Node.js 의존성
├── requirements.txt        # Python 의존성
├── vercel.json             # Vercel 배포 설정
├── render.yaml             # Render 배포 설정
├── .env.example            # 환경 변수 예제
├── .gitignore              # Git 제외 파일
├── create_package.ps1      # 배포 패키지 생성 스크립트
├── README.md               # 프로젝트 문서
├── INSTALLATION_GUIDE.md   # 설치 가이드
└── DEPLOYMENT.md           # 배포 가이드
```

## 설치 및 실행

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
npm start
# 또는 개발 모드
npm run dev
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

**로컬 개발 환경:**
```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:3000',  // Express 서버 주소 (FastAPI로 프록시)
    UPDATE_INTERVAL: 5000,                  // 데이터 업데이트 주기 (5초)
    CHART_UPDATE_INTERVAL: 30000,           // 차트 업데이트 주기 (30초)
};
```

**프로덕션 환경:**
```javascript
const CONFIG = {
    API_BASE_URL: 'https://prism-ejmi593l2-pangs-projects-6d3df8bf.vercel.app',
    UPDATE_INTERVAL: 5000,
    CHART_UPDATE_INTERVAL: 30000,
};
```

### Python (raspberry_pi_sensor.py)

**로컬 개발 환경:**
```python
API_SERVER = "http://localhost:8000"  # FastAPI 서버 주소
ZONE_ID = "testbox"                   # 구역 ID
SEND_INTERVAL = 5                     # 전송 주기 (초)
```

**프로덕션 환경 (FastAPI 배포 후):**
```python
API_SERVER = "https://prism-api.onrender.com"  # 배포된 FastAPI 서버 주소
ZONE_ID = "testbox"
SEND_INTERVAL = 5
```

## 설정

### JavaScript (dashboard.js)


## API 엔드포인트

### 1. 센서 데이터 전송 (라즈베리파이 → FastAPI 서버)
```http
POST /api/sensors/{zone}
Content-Type: application/json
```

**요청 파라미터:**
- `zone` (string, path): 구역 ID (예: "testbox", "warehouse", "storage", "office")

**요청 본문 (JSON):**
```json
{
  "zone": "testbox",           // 구역 ID (필수)
  "temperature": 25.5,         // 온도 (°C, 필수, float)
  "gas": 30.2,                 // 가스 농도 (ppm, 필수, float)
  "dust": 12.5,                // 미세먼지 (μg/m³, 필수, float)
  "flame": false,              // 불꽃 감지 (필수, boolean)
  "timestamp": "2025-11-04T15:30:00"  // 타임스탬프 (선택, 없으면 서버 시간 사용)
}
```

**응답:**
```json
{
  "status": "success",
  "zone": "testbox",
  "message": "Sensor data updated"
}
```

---

### 2. 센서 데이터 조회 (대시보드 → Express → FastAPI)
```http
GET /api/sensors/{zone}
```

**요청 파라미터:**
- `zone` (string, path): 구역 ID

**응답 (JSON):**
```json
{
  "zone": "testbox",
  "temperature": 25.5,         // 현재 온도 (°C)
  "gas": 30.2,                 // 현재 가스 농도 (ppm)
  "dust": 12.5,                // 현재 미세먼지 (μg/m³)
  "flame": false,              // 불꽃 감지 여부
  "timestamp": "2025-11-04T15:30:00"  // 마지막 업데이트 시간
}
```

**에러 응답 (센서 미연결 시):**
```json
{
  "detail": "No sensor data available for zone: testbox"
}
```
HTTP 상태 코드: 404

---

### 3. 과거 데이터 조회
```http
GET /api/history/{zone}?hours={hours}
```

**요청 파라미터:**
- `zone` (string, path): 구역 ID
- `hours` (integer, query): 조회 시간 범위 (기본값: 24시간)

**응답 (JSON 배열):**
```json
[
  {
    "timestamp": "2025-11-04T14:00:00",
    "temperature": 24.5,       // 온도 (°C)
    "gas": 28.0,               // 가스 농도 (ppm)
    "dust": 10.2               // 미세먼지 (μg/m³)
  },
  {
    "timestamp": "2025-11-04T13:00:00",
    "temperature": 24.8,
    "gas": 29.5,
    "dust": 11.0
  }
]
```

---

### 4. 구역 목록 조회
```http
GET /api/zones
```

**응답 (JSON 배열):**
```json
[
  {
    "id": "testbox",          // 구역 ID
    "name": "TEST BOX",       // 구역 이름
    "active": true,           // 활성 상태
    "status": "normal"        // 상태 (normal/caution/warning/danger)
  },
  {
    "id": "warehouse",
    "name": "WARE HOUSE",
    "active": false,
    "status": "inactive"
  }
]
```

---

### 5. 장치 목록 조회
```http
GET /api/devices
```

**응답 (JSON 배열):**
```json
[
  {
    "device_id": "raspberry_pi_01",
    "device_type": "raspberry_pi",
    "ip_address": "192.168.1.100",
    "status": "online",
    "last_seen": "2025-11-04T15:30:00",
    "zone": "testbox"
  }
]
```

---

### 6. CCTV 스트림 (영상)
```http
GET /api/cctv/{zone}/stream
```

**요청 파라미터:**
- `zone` (string, path): 구역 ID

**응답:**
- 실시간 비디오 스트림 (MJPEG/WebRTC)
- IP 카메라 또는 라즈베리파이 카메라 모듈 연동

**에러 응답 (카메라 미연결 시):**
```json
{
  "detail": "CCTV 스트림이 연결되지 않았습니다"
}
```
HTTP 상태 코드: 503

## 상태 색상 기준

| 상태 | 온도 | 가스 (ppm) | 미세먼지 (g/m³) | 불꽃 | 색상 | AI |
|------|------|------------|-----------------|------|------|----|
| 위험 | > 50°C | > 100 | > 50 | 감지 | 빨강 | 화재, 연기 감지|
| 경고 | > 40°C | > 70 | > 30 | - | 주황 | - |
| 주의 | > 30°C | > 50 | > 20 | - | 파랑 | - |
| 정상 | ≤ 30°C | ≤ 50 | ≤ 20 | - | 초록 | - |

## 라즈베리파이 센서 연결

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

## 개발 환경

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python 3.8+, FastAPI, Uvicorn
- **Charts**: Chart.js
- **Icons**: Font Awesome 6
- **Hardware**: Raspberry Pi (3/4), 각종 센서, Orange Pi(YOLOv5)

## 테스트 모드

FastAPI 서버와 라즈베리파이 센서 프로그램은 더미 데이터를 생성하여 실제 센서 없이도 테스트할 수 있습니다.

1. FastAPI 서버 실행
2. 웹 브라우저에서 대시보드 열기
3. 자동으로 더미 데이터가 표시됨

## 문제 해결

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

## 배포 가이드

### Vercel (프론트엔드)
프론트엔드는 이미 Vercel에 배포되어 있습니다.
- URL: https://prism-ejmi593l2-pangs-projects-6d3df8bf.vercel.app

업데이트 방법:
```bash
vercel --prod
```

### Render.com (FastAPI 백엔드)
FastAPI 서버가 이미 Render.com에 배포되어 있습니다.
- URL: https://prism-api.onrender.com
- API 문서: https://prism-api.onrender.com/docs

업데이트 방법:
1. GitHub에 코드 푸시
```bash
git add .
git commit -m "Update message"
git push origin main
```
2. Render.com에서 자동으로 재배포됨

### 환경 변수 설정
배포 후 Vercel 환경 변수에 FastAPI URL 설정:
```
FASTAPI_URL=https://prism-api.onrender.com
```

자세한 내용은 `DEPLOYMENT.md` 참고

## 라이선스

이 프로젝트는 교육 및 개발 목적으로 제작되었습니다.

## 개발팀

미야호팀 - PRISM 프로젝트
