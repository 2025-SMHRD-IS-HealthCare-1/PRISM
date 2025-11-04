# PRISM 설치 및 실행 가이드

## 📦 프로젝트 전달 방법

### 방법 1: ZIP 파일로 전달 (권장)
```bash
# 필요한 파일만 포함하여 압축
# node_modules, .git 등 제외
```

**포함해야 할 파일/폴더:**
- ✅ `public/` (전체)
- ✅ `config/` (전체)
- ✅ `routes/` (전체)
- ✅ `api_server.py`
- ✅ `app.js`
- ✅ `raspberry_pi_sensor.py`
- ✅ `package.json`
- ✅ `requirements.txt`
- ✅ `README.md`
- ✅ `INSTALLATION_GUIDE.md` (이 파일)
- ✅ `vercel.json`
- ✅ `.env.example` (환경 변수 예제)

**제외해야 할 파일/폴더:**
- ❌ `node_modules/` (용량 큼 - 설치 필요)
- ❌ `__pycache__/` (Python 캐시)
- ❌ `.git/` (Git 저장소)
- ❌ `data/` (로그 파일 등)

### 방법 2: GitHub 저장소 (협업에 최적)
```bash
# GitHub에 업로드 후 공유
git init
git add .
git commit -m "Initial commit"
git remote add origin [GitHub 저장소 URL]
git push -u origin main
```

### 방법 3: Google Drive / Dropbox
- ZIP 파일 업로드 후 공유 링크 전달

---

## 🚀 빠른 시작 가이드

### 1단계: 프로젝트 다운로드
```bash
# ZIP 파일 압축 해제
unzip PRISM.zip
cd PRISM
```

### 2단계: 환경 설정 파일 생성
```bash
# .env 파일 생성 (Windows PowerShell)
Copy-Item .env.example .env

# 또는 수동으로 생성
# .env 파일 내용:
PORT=3000
FASTAPI_URL=http://localhost:8000
```

### 3단계: Node.js 패키지 설치
```bash
npm install
```

**설치되는 패키지:**
- express ^4.18.2
- cors ^2.8.5
- axios ^1.6.2
- dotenv ^16.3.1
- nodemon ^3.0.2 (개발용)

### 4단계: Python 패키지 설치
```bash
pip install -r requirements.txt
```

**설치되는 패키지:**
- fastapi==0.120.0
- uvicorn[standard]==0.38.0
- pydantic==2.12.3
- python-multipart==0.0.20
- python-dotenv==1.2.1

### 5단계: 서버 실행

#### Terminal 1: FastAPI 서버
```bash
python api_server.py
```
✅ 실행 확인: http://localhost:8000/docs

#### Terminal 2: Express 서버
```bash
node app.js
# 또는 개발 모드 (자동 재시작)
npm run dev
```
✅ 실행 확인: http://localhost:3000

### 6단계: 웹 브라우저 접속
```
http://localhost:3000
```

---

## 🔧 상세 설정

### API 엔드포인트 변경
**파일: `public/js/dashboard.js`**
```javascript
const CONFIG = {
    // 로컬 개발
    API_BASE_URL: 'http://localhost:3000',
    
    // 실제 서버 (예시)
    // API_BASE_URL: 'http://192.168.1.100:3000',
    
    UPDATE_INTERVAL: 5000,        // 5초마다 데이터 갱신
    CHART_UPDATE_INTERVAL: 30000  // 30초마다 차트 갱신
};
```

### 라즈베리파이 설정
**파일: `raspberry_pi_sensor.py`**
```python
# FastAPI 서버 주소 (실제 IP로 변경)
API_SERVER = "http://192.168.1.100:8000"  # Windows PC의 IP

# 구역 ID
ZONE_ID = "testbox"  # testbox, warehouse, inspection, machine

# 장치 ID
DEVICE_ID = "raspberry_pi_01"

# 전송 주기 (초)
SEND_INTERVAL = 5
```

---

## 🌐 운영 환경 배포

### Vercel 배포 (프론트엔드)
```bash
# Vercel CLI 설치
npm install -g vercel

# 배포
vercel
```

**설정 (`vercel.json`):**
- Express 서버가 Vercel Serverless Function으로 실행됨
- 환경 변수 설정 필요: `FASTAPI_URL`

### Render 배포 (백엔드)
1. Render 계정 생성: https://render.com
2. New Web Service 생성
3. GitHub 저장소 연결
4. 설정:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python api_server.py`
   - **Port**: 8000

---

## 🔍 문제 해결

### 1. 포트 충돌 오류
```bash
# Windows에서 포트 사용 중인 프로세스 확인
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# 프로세스 종료
taskkill /PID [PID번호] /F
```

### 2. CORS 오류
- `api_server.py`의 CORS 설정 확인
- `allow_origins=["*"]` → 모든 도메인 허용 (개발용)
- 운영 환경에서는 특정 도메인만 허용 권장

### 3. 센서 데이터가 표시되지 않음
**체크리스트:**
- [ ] FastAPI 서버가 실행 중인가? (http://localhost:8000/docs 접속 확인)
- [ ] Express 서버가 실행 중인가? (http://localhost:3000 접속 확인)
- [ ] 브라우저 콘솔에 에러가 있는가? (F12 개발자 도구 확인)
- [ ] `dashboard.js`의 `API_BASE_URL`이 올바른가?

### 4. 센서 미연결 상태로 표시됨
- **현재 날짜를 제외한 과거 데이터**: 고정된 가짜 데이터 표시 (정상)
- **현재 센서 값**: "센서 미연결 상태.." 표시 (정상)
- **실제 센서 연결**: `raspberry_pi_sensor.py` 실행 필요

---

## 📊 데이터 흐름

```
┌─────────────────┐
│ Raspberry Pi    │
│ (센서 데이터)    │
└────────┬────────┘
         │ POST /api/sensors/{zone}
         ↓
┌─────────────────┐
│ FastAPI Server  │
│ (Port 8000)     │
│ - 데이터 저장    │
│ - 과거 데이터    │
└────────┬────────┘
         │ GET /api/sensors/{zone}
         ↓
┌─────────────────┐
│ Express Server  │
│ (Port 3000)     │
│ - Proxy         │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Web Browser     │
│ (Dashboard)     │
│ - 실시간 표시    │
│ - 차트/그래프    │
└─────────────────┘
```

---

## 📱 테스트 방법

### 1. 더미 데이터 테스트 (센서 없이)
현재 설정된 상태:
- 센서 미연결 시 "센서 미연결 상태.." 표시
- 과거 데이터: 6일치 고정된 가짜 데이터 표시

### 2. 실제 센서 테스트
```bash
# 라즈베리파이에서 실행
python raspberry_pi_sensor.py
```

### 3. API 테스트 (Postman / cURL)
```bash
# 센서 데이터 전송 테스트
curl -X POST http://localhost:8000/api/sensors/testbox \
  -H "Content-Type: application/json" \
  -d '{
    "zone": "testbox",
    "temperature": 25.5,
    "gas": 30.2,
    "dust": 12.5,
    "flame": false
  }'

# 데이터 조회 테스트
curl http://localhost:8000/api/sensors/testbox
```

---

## 🎓 개발 팁

### 개발 모드 실행
```bash
# Express 자동 재시작 (nodemon)
npm run dev

# FastAPI 자동 재시작 (uvicorn --reload)
uvicorn api_server:app --reload --port 8000
```

### 로그 확인
- **Express**: 콘솔 출력
- **FastAPI**: 콘솔 출력 (터미널에서 확인)
- **Browser**: F12 → Console 탭

### 디버깅
```javascript
// dashboard.js에서 디버깅
console.log('센서 데이터:', sensorData);
console.log('연결 상태:', isConnected);
```

---

## 📞 지원

문제가 발생하면:
1. 브라우저 콘솔 (F12) 확인
2. FastAPI 로그 확인
3. Express 서버 로그 확인
4. 네트워크 탭에서 API 요청/응답 확인

---

## 📋 체크리스트

전달 전 확인사항:
- [ ] `node_modules/` 폴더 제외
- [ ] `.env.example` 파일 포함
- [ ] `README.md` 최신 상태
- [ ] 모든 경로가 상대 경로로 설정됨
- [ ] API 엔드포인트 URL이 `localhost`로 설정됨
- [ ] 테스트 완료 (로컬 환경)

---

**마지막 업데이트**: 2025년 10월 27일
**버전**: 2.0.0
