# PRISM 배포 가이드 📦

PRISM 프로젝트를 인터넷에 공개하여 다른 사람들과 공유하는 방법입니다.

## 🎯 배포 방법 선택

### 추천: Render.com (무료)
- ✅ 무료 플랜 제공
- ✅ Express + FastAPI 모두 지원
- ✅ 자동 HTTPS
- ✅ GitHub 연동으로 자동 배포
- ⚠️ 15분 미사용시 슬립 모드 (무료 플랜)

### 대안: Railway, Fly.io, Heroku
- Railway: 월 $5 무료 크레딧
- Fly.io: 제한적 무료 플랜
- Heroku: 유료 (무료 플랜 종료)

---

## 🚀 Render.com으로 배포하기

### 1단계: GitHub에 프로젝트 업로드

#### Git 초기화 (처음 한 번만)
```powershell
cd c:\Users\smhrd\Desktop\Web\PRISM
git init
git add .
git commit -m "Initial commit - PRISM project"
```

#### GitHub 저장소 생성 및 연결
1. https://github.com 접속 후 로그인
2. 우측 상단 `+` → `New repository` 클릭
3. Repository name: `PRISM`
4. Public 선택 (또는 Private)
5. `Create repository` 클릭
6. 터미널에서 실행:

```powershell
git remote add origin https://github.com/당신의아이디/PRISM.git
git branch -M main
git push -u origin main
```

### 2단계: Render 계정 생성
1. https://render.com 접속
2. `Get Started for Free` 클릭
3. GitHub 계정으로 로그인

### 3단계: Web Service 배포

#### Express 웹 서버 배포
1. Dashboard에서 `New +` → `Web Service` 클릭
2. GitHub 저장소 연결 (PRISM 선택)
3. 설정 입력:
   - **Name**: `prism-web`
   - **Environment**: `Node`
   - **Build Command**: `npm install`
   - **Start Command**: `node app.js`
   - **Plan**: `Free`
4. `Create Web Service` 클릭

#### FastAPI 센서 서버 배포
1. Dashboard에서 `New +` → `Web Service` 클릭
2. 같은 GitHub 저장소 연결 (PRISM 선택)
3. 설정 입력:
   - **Name**: `prism-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`
4. `Create Web Service` 클릭

### 4단계: 환경변수 설정

#### prism-web 설정
1. Dashboard에서 `prism-web` 클릭
2. 좌측 메뉴 `Environment` 클릭
3. 환경변수 추가:
   - `API_URL`: `https://prism-api.onrender.com` (FastAPI 서버 URL)

#### prism-api 설정
환경변수 필요시 추가

### 5단계: 프론트엔드 API 주소 업데이트

배포된 FastAPI 서버 주소로 업데이트 필요합니다.
`public/js/dashboard.js` 파일에서:

```javascript
const CONFIG = {
    API_BASE_URL: 'https://prism-api.onrender.com',  // 배포된 FastAPI URL
    UPDATE_INTERVAL: 5000,
    CHART_UPDATE_INTERVAL: 30000,
};
```

변경 후 다시 커밋:
```powershell
git add .
git commit -m "Update API URL for production"
git push
```

Render가 자동으로 재배포합니다!

### 6단계: 접속 확인
- 웹사이트: `https://prism-web.onrender.com`
- API 서버: `https://prism-api.onrender.com/docs`

---

## 🔧 배포 후 설정

### CORS 설정 (api_server.py)
FastAPI 서버에서 배포된 웹사이트 주소 허용:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://prism-web.onrender.com",  # 배포된 웹 주소
        "http://localhost:3000"  # 로컬 개발용
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 라즈베리파이 설정 (raspberry_pi_sensor.py)
센서 데이터를 배포된 서버로 전송:

```python
API_SERVER = "https://prism-api.onrender.com"  # 배포된 API 주소
```

---

## 📱 다른 배포 옵션

### Vercel (프론트엔드만)
정적 파일만 배포 가능, FastAPI는 별도 배포 필요

```powershell
npm install -g vercel
cd c:\Users\smhrd\Desktop\Web\PRISM
vercel
```

### Netlify (프론트엔드만)
```powershell
npm install -g netlify-cli
cd c:\Users\smhrd\Desktop\Web\PRISM
netlify deploy
```

### Railway (풀스택)
```powershell
npm install -g @railway/cli
railway login
railway init
railway up
```

---

## ⚠️ 무료 플랜 제한사항

### Render Free Plan
- ✅ 무제한 대역폭
- ⚠️ 15분 미사용시 슬립 모드 (첫 요청시 느림)
- ⚠️ 월 750시간 제한 (한 서버 기준)
- ✅ 자동 HTTPS
- ✅ 커스텀 도메인 지원

### 슬립 모드 해결
1. 유료 플랜 사용 ($7/month)
2. Uptime Robot 등으로 주기적 핑
3. Railway, Fly.io 등 다른 플랫폼 사용

---

## 🎉 완료!

배포가 완료되면:
1. 웹사이트 URL 공유: `https://prism-web.onrender.com`
2. API 문서 공유: `https://prism-api.onrender.com/docs`
3. 라즈베리파이 센서 연결 테스트

---

## 🐛 문제 해결

### 배포 실패
- Render 로그 확인 (Dashboard → Logs)
- `requirements.txt`, `package.json` 확인
- 포트 설정 확인 (`process.env.PORT` 사용)

### CORS 오류
- FastAPI `allow_origins`에 웹 URL 추가
- 브라우저 개발자 도구 네트워크 탭 확인

### API 연결 안됨
- `dashboard.js`의 `API_BASE_URL` 확인
- FastAPI 서버 상태 확인
- 방화벽/보안 그룹 설정 확인

---

## 📞 도움말

- Render 공식 문서: https://render.com/docs
- GitHub 가이드: https://docs.github.com
- FastAPI 배포: https://fastapi.tiangolo.com/deployment/

배포 과정에서 문제가 생기면 에러 메시지를 공유해주세요!
