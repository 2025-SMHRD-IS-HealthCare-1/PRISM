# 🚀 Render.com에 FastAPI 배포하기

## 📌 왜 Render를 사용하나요?

라즈베리파이가 **어떤 와이파이 네트워크**에 연결되어도 센서 데이터를 전송할 수 있도록  
**고정된 도메인 주소**가 필요합니다.

### 배포 전 vs 배포 후

**배포 전:**

```python
# 라즈베리파이 설정
API_SERVER="http://192.168.1.10:8000"  # ❌ 로컬 IP (와이파이 바뀌면 안됨)
```

**배포 후:**

```python
# 라즈베리파이 설정
API_SERVER="https://prism-api-xxxx.onrender.com"  # ✅ 어디서든 접속 가능!
```

---

## 🌐 Render 배포 단계

### 1단계: Render 계정 생성

1. https://render.com 접속
2. **GitHub 계정으로 로그인** (또는 이메일)
3. 무료 플랜 선택

### 2단계: GitHub에 코드 푸시 (아직 안했다면)

```bash
cd "/Users/ipang/Desktop/대학교/활동/대외 활동/엣지 AI기반 헬스케어 서비스개발자과정/PRISM"

# Git 초기화
git init
git add .
git commit -m "PRISM FastAPI server with WebSocket"

# GitHub 저장소 연결 (본인의 저장소 URL로 변경)
git remote add origin https://github.com/YOUR_USERNAME/PRISM.git
git branch -M main
git push -u origin main
```

### 3단계: Render에서 새 Web Service 생성

1. Render 대시보드에서 **"New +"** 클릭
2. **"Web Service"** 선택
3. GitHub 저장소 연결 (PRISM 선택)
4. 다음 설정 입력:

**기본 설정:**

- **Name**: `prism-api`
- **Region**: `Singapore` (한국과 가장 가까움)
- **Branch**: `main`
- **Root Directory**: (비워두기)
- **Runtime**: `Python 3`

**빌드 & 배포 설정:**

- **Build Command**:
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  uvicorn server.api_server:app --host 0.0.0.0 --port $PORT
  ```

**고급 설정:**

- **Health Check Path**: `/health`
- **Plan**: `Free` (무료)

5. **"Create Web Service"** 클릭

### 4단계: 배포 완료 확인

배포가 완료되면 (약 3-5분 소요):

```
✅ Your service is live at https://prism-api-xxxx.onrender.com
```

**테스트:**

```bash
# 헬스 체크
curl https://prism-api-xxxx.onrender.com/health

# API 문서 접속
https://prism-api-xxxx.onrender.com/docs
```

---

## 🔧 라즈베리파이 설정 업데이트

배포된 도메인 주소를 라즈베리파이에 설정:

```bash
# 라즈베리파이에서 실행
export API_SERVER="https://prism-api-xxxx.onrender.com"
export DEVICE_ID="rpi-01"

python iot_devices/raspberry_pi_sensor.py
```

**영구 설정 (재부팅 후에도 유지):**

```bash
# ~/.bashrc 파일에 추가
echo 'export API_SERVER="https://prism-api-xxxx.onrender.com"' >> ~/.bashrc
echo 'export DEVICE_ID="rpi-01"' >> ~/.bashrc
source ~/.bashrc
```

---

## 📊 WebSocket 연결 (웹 대시보드)

웹 페이지에서 WebSocket 연결:

```javascript
// public/js/dashboard.js 또는 public/websocket_test.html 수정
const ws = new WebSocket("wss://prism-api-xxxx.onrender.com/ws");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("실시간 데이터:", data);
};
```

**주의:** HTTP는 `http://`, WebSocket은 `ws://`  
**HTTPS는 `https://`, Secure WebSocket은 `wss://`**

---

## ⚙️ render.yaml 사용 (자동 배포)

프로젝트에 `render.yaml`이 이미 있으므로:

1. Render 대시보드에서 **"Blueprint"** 선택
2. GitHub 저장소 연결
3. `render.yaml` 자동 감지 → **"Apply"** 클릭

`render.yaml` 내용:

```yaml
services:
  - type: web
    name: prism-api
    env: python
    region: singapore
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn server.api_server:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
    healthCheckPath: /health
```

---

## 🆓 무료 플랜 제한사항

- ✅ **무료**
- ⚠️ 15분 동안 요청이 없으면 **슬립 모드** (첫 요청 시 약 30초 소요)
- ⚠️ 매월 750시간 무료 (약 31일)
- ✅ 자동 HTTPS 인증서
- ✅ 무제한 대역폭

**슬립 모드 해결 방법:**

- UptimeRobot 같은 무료 모니터링 서비스 사용
- 5분마다 `/health` 엔드포인트 호출

---

## 🔐 환경 변수 설정 (선택사항)

Render 대시보드에서 환경 변수 추가:

- `PYTHON_VERSION`: `3.11.0`
- `LOG_LEVEL`: `info`

---

## 📌 배포 후 체크리스트

- [ ] FastAPI 서버가 Render에 배포됨
- [ ] 도메인 주소 확인 (`https://prism-api-xxxx.onrender.com`)
- [ ] `/health` 엔드포인트 테스트
- [ ] API 문서 접속 (`/docs`)
- [ ] 라즈베리파이 `API_SERVER` 환경 변수 업데이트
- [ ] 라즈베리파이에서 데이터 전송 테스트
- [ ] 웹 페이지 WebSocket 연결 주소 업데이트

---

## 🆘 문제 해결

### "Application failed to respond"

→ Start Command 확인: `uvicorn server.api_server:app --host 0.0.0.0 --port $PORT`

### "Module not found"

→ `requirements.txt` 파일 확인, 모든 패키지 포함 여부 체크

### 슬립 모드에서 깨어나지 않음

→ Render 로그 확인, 첫 요청 시 30초 정도 대기

### WebSocket 연결 실패

→ `wss://` (secure websocket) 사용 확인

---

## 🎉 완료!

이제 라즈베리파이가 **어떤 네트워크**에 연결되어도  
`https://prism-api-xxxx.onrender.com`로 데이터를 전송할 수 있습니다! 🚀

```bash
# 라즈베리파이에서
export API_SERVER="https://prism-api-xxxx.onrender.com"
python iot_devices/raspberry_pi_sensor.py
```
