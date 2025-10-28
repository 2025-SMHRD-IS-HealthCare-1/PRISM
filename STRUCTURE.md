# 📂 PRISM 프로젝트 구조

## 📋 목차

- [전체 구조 개요](#전체-구조-개요)
- [폴더별 설명](#폴더별-설명)
- [주요 파일 설명](#주요-파일-설명)
- [데이터 흐름](#데이터-흐름)

---

## 🗂️ 전체 구조 개요

```
PRISM/
├── 📁 server/              # 서버 관련 파일
│   ├── api_server.py       # FastAPI 서버 (WebSocket 지원)
│   └── app.js              # Express 서버 (선택사항)
│
├── 📁 iot_devices/         # IoT 디바이스 관련 스크립트
│   └── raspberry_pi_sensor.py  # 라즈베리파이/오렌지파이 센서 스크립트
│
├── 📁 public/              # 웹 프론트엔드 (정적 파일)
│   ├── index.html          # 메인 대시보드
│   ├── websocket_test.html # WebSocket 테스트 페이지
│   ├── Example.html        # 참고용 예제
│   ├── css/               # 스타일시트
│   │   ├── main.css
│   │   └── dashboard.css
│   ├── js/                # JavaScript
│   │   └── dashboard.js
│   └── image/             # 이미지 리소스
│       ├── prism_logo.png
│       ├── logo_white.png
│       └── logo_gray.png
│
├── 📁 scripts/             # 유틸리티 스크립트
│   └── test_sender.py      # 테스트 데이터 전송 스크립트
│
├── 📁 tests/               # 테스트 파일 (향후 추가 예정)
│
├── 📁 docs/                # 문서
│   ├── INSTALLATION_GUIDE.md  # 설치 가이드
│   ├── DEPLOYMENT.md          # 배포 가이드
│   ├── QUICKSTART.md          # 빠른 시작 가이드
│   └── WEBSOCKET_GUIDE.md     # WebSocket 상세 가이드
│
├── 📄 README.md            # 프로젝트 메인 문서
├── 📄 STRUCTURE.md         # 이 파일 (프로젝트 구조 설명)
├── 📄 requirements.txt     # Python 패키지 의존성
├── 📄 package.json         # Node.js 패키지 의존성
├── 📄 .env.example         # 환경 변수 예제
├── 📄 .gitignore           # Git 제외 파일
├── 📄 vercel.json          # Vercel 배포 설정
└── 📄 render.yaml          # Render 배포 설정
```

---

## 📁 폴더별 설명

### 1. `server/` - 서버 파일

백엔드 서버 관련 파일들이 위치합니다.

| 파일            | 설명                                         | 기술 스택                   |
| --------------- | -------------------------------------------- | --------------------------- |
| `api_server.py` | **메인 서버** - FastAPI 기반, WebSocket 지원 | Python, FastAPI, WebSockets |
| `app.js`        | Express 서버 (선택사항, API 프록시)          | Node.js, Express            |

**주요 기능:**

- 센서 데이터 수집 (`/ingest` 엔드포인트)
- WebSocket 실시간 스트리밍
- REST API 제공
- CORS 처리

### 2. `iot_devices/` - IoT 디바이스 스크립트

라즈베리파이, 오렌지파이 등 IoT 디바이스에서 실행되는 스크립트들입니다.

| 파일                     | 설명                          | 대상 디바이스           |
| ------------------------ | ----------------------------- | ----------------------- |
| `raspberry_pi_sensor.py` | 센서 데이터 수집 및 서버 전송 | Raspberry Pi, Orange Pi |

**주요 기능:**

- 다중 센서 데이터 읽기 (온도, 가스, 미세먼지, 불꽃)
- FastAPI 서버로 HTTP POST 전송
- 주기적 데이터 전송 (기본 5초)
- 연결 상태 확인 및 재연결

### 3. `public/` - 웹 프론트엔드

사용자가 브라우저에서 보는 웹 페이지와 관련 리소스들입니다.

#### HTML 파일

| 파일                  | 설명                                        |
| --------------------- | ------------------------------------------- |
| `index.html`          | 메인 대시보드 - 구역별 센서 모니터링        |
| `websocket_test.html` | WebSocket 연결 테스트 및 실시간 데이터 확인 |
| `Example.html`        | 프로젝트 요구사항 및 참고 예제              |

#### CSS 파일

| 파일            | 설명                                       |
| --------------- | ------------------------------------------ |
| `main.css`      | 기본 스타일 (색상, 타이포그래피, 레이아웃) |
| `dashboard.css` | 대시보드 전용 스타일                       |

#### JavaScript 파일

| 파일           | 설명                                        |
| -------------- | ------------------------------------------- |
| `dashboard.js` | 대시보드 로직 (API 호출, 차트, 이벤트 처리) |

### 4. `scripts/` - 유틸리티 스크립트

개발 및 테스트에 사용되는 스크립트들입니다.

| 파일             | 설명             | 용도         |
| ---------------- | ---------------- | ------------ |
| `test_sender.py` | 더미 데이터 전송 | 테스트, 개발 |

**사용 예:**

```bash
python scripts/test_sender.py  # 3개 가상 디바이스 데이터 전송
```

### 5. `tests/` - 테스트 파일

단위 테스트 및 통합 테스트 파일들이 위치합니다. (향후 추가 예정)

**예정된 테스트:**

- API 엔드포인트 테스트
- WebSocket 연결 테스트
- 센서 데이터 검증 테스트

### 6. `docs/` - 문서

프로젝트 관련 문서들입니다.

| 파일                    | 설명                         |
| ----------------------- | ---------------------------- |
| `INSTALLATION_GUIDE.md` | 설치 가이드                  |
| `DEPLOYMENT.md`         | 배포 가이드 (Vercel, Render) |
| `QUICKSTART.md`         | 3단계 빠른 시작              |
| `WEBSOCKET_GUIDE.md`    | WebSocket 상세 사용법        |

---

## 📄 주요 파일 설명

### 설정 파일

#### `requirements.txt` - Python 패키지

```txt
fastapi==0.104.1          # 웹 프레임워크
uvicorn[standard]==0.24.0 # ASGI 서버
pydantic==2.5.0           # 데이터 검증
python-multipart==0.0.6   # 파일 업로드
python-dotenv==1.0.0      # 환경 변수
websockets==12.0          # WebSocket 지원
requests==2.31.0          # HTTP 클라이언트
```

#### `package.json` - Node.js 패키지

```json
{
  "dependencies": {
    "express": "^4.21.2", // 웹 서버
    "cors": "^2.8.5", // CORS 처리
    "axios": "^1.6.2", // HTTP 클라이언트
    "dotenv": "^16.3.1" // 환경 변수
  },
  "devDependencies": {
    "nodemon": "^3.0.2" // 자동 재시작
  }
}
```

#### `.env.example` - 환경 변수 템플릿

```bash
# FastAPI 서버 설정
PORT=8000
FASTAPI_URL=http://localhost:8000

# 디바이스 설정
API_SERVER=http://localhost:8000
DEVICE_ID=rpi-01
```

### 배포 설정 파일

#### `vercel.json` - Vercel 배포

프론트엔드 정적 파일을 Vercel에 배포하기 위한 설정

#### `render.yaml` - Render 배포

FastAPI 서버를 Render에 배포하기 위한 설정

---

## 🔄 데이터 흐름

### 1. 센서 → 서버 (데이터 수집)

```
[라즈베리파이/오렌지파이]
        │
        │ 센서 데이터 읽기
        │ (온도, 가스, 미세먼지, 불꽃)
        │
        ▼
[iot_devices/raspberry_pi_sensor.py]
        │
        │ HTTP POST /ingest
        │ JSON: {device_id, data, ts}
        │
        ▼
[server/api_server.py]
        │
        ├─ 데이터 저장 (LATEST, HISTORY)
        └─ WebSocket 브로드캐스트
```

### 2. 서버 → 브라우저 (실시간 표시)

```
[server/api_server.py]
        │
        │ WebSocket /ws
        │
        ▼
[public/websocket_test.html]
[public/index.html]
        │
        │ 데이터 수신 및 표시
        │
        ▼
사용자 브라우저에 실시간 표시
```

### 3. API 호출 흐름

```
브라우저
    │
    │ HTTP GET
    │
    ▼
API 엔드포인트
    │
    ├─ GET /latest          → 최신 데이터
    ├─ GET /latest/{id}     → 특정 디바이스
    ├─ GET /history/{id}    → 히스토리
    ├─ GET /devices         → 디바이스 목록
    └─ GET /health          → 서버 상태
```

---

## 🚀 실행 순서

### 개발 환경

1. **서버 실행**

   ```bash
   python server/api_server.py
   ```

2. **테스트 데이터 전송** (선택)

   ```bash
   python scripts/test_sender.py
   ```

3. **웹 브라우저 접속**
   ```
   http://localhost:8000
   또는
   open public/websocket_test.html
   ```

### 실제 IoT 환경

1. **서버 실행** (PC/Mac)

   ```bash
   python server/api_server.py
   ```

2. **IoT 디바이스 설정** (라즈베리파이)

   ```bash
   export API_SERVER="http://192.168.1.XXX:8000"
   export DEVICE_ID="rpi-01"
   python iot_devices/raspberry_pi_sensor.py
   ```

3. **웹 대시보드 접속**
   ```
   http://192.168.1.XXX:8000
   ```

---

## 📦 의존성 관리

### Python 패키지 설치

```bash
pip install -r requirements.txt
```

### Node.js 패키지 설치

```bash
npm install
```

---

## 🔧 개발 가이드

### 새로운 센서 추가

1. `iot_devices/raspberry_pi_sensor.py`에 센서 읽기 함수 추가
2. `collect_sensor_data()` 함수에서 새 센서 데이터 포함
3. 웹 대시보드에서 표시 로직 추가

### 새로운 API 엔드포인트 추가

1. `server/api_server.py`에 엔드포인트 함수 작성
2. `@app.get()` 또는 `@app.post()` 데코레이터 사용
3. API 문서 자동 업데이트됨 (`/docs`)

### 프론트엔드 수정

1. `public/index.html` - HTML 구조 수정
2. `public/css/dashboard.css` - 스타일 수정
3. `public/js/dashboard.js` - 로직 수정

---

## 📚 추가 정보

자세한 내용은 다음 문서를 참고하세요:

- **[README.md](../README.md)** - 프로젝트 개요
- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - 빠른 시작
- **[docs/WEBSOCKET_GUIDE.md](docs/WEBSOCKET_GUIDE.md)** - WebSocket 가이드
- **[docs/INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md)** - 설치 가이드
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - 배포 가이드

---

## 🤝 기여 방법

1. 새 기능 추가 시 해당 폴더에 파일 생성
2. 테스트 코드는 `tests/` 폴더에 작성
3. 문서는 `docs/` 폴더에 추가
4. `.gitignore` 확인하여 불필요한 파일 제외

---

**최종 업데이트:** 2025년 10월 27일  
**버전:** 3.0.0 (WebSocket 지원)
