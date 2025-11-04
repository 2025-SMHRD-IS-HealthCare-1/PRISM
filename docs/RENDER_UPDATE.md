# 🚀 Render API 서버 업데이트 가이드

## Render 서버 재배포 방법

### 자동 배포 (GitHub 연동)

Render는 GitHub에 푸시하면 **자동으로 재배포**됩니다.

1. ✅ 코드 변경 완료
2. ✅ GitHub에 푸시 완료
3. ⏳ Render가 자동으로 감지하여 재배포 시작 (약 2-3분 소요)

### Render 대시보드에서 확인

1. **Render 대시보드 접속**

   - https://dashboard.render.com

2. **PRISM API 서비스 선택**

   - 서비스 목록에서 `prism-api` 클릭

3. **배포 상태 확인**

   - "Events" 탭에서 배포 진행 상황 확인
   - "Deploy in progress..." 메시지 확인
   - 완료되면 "Live" 상태로 변경

4. **로그 확인**
   - "Logs" 탭 클릭
   - 서버 시작 메시지 확인:
     ```
     🚀 PRISM FastAPI 서버 시작 (WebSocket 지원)
     📡 HTTP 서버: http://0.0.0.0:10000
     🔌 WebSocket: ws://0.0.0.0:10000/ws
     ```

### 수동 재배포 (필요시)

1. Render 대시보드에서 서비스 선택
2. "Manual Deploy" 버튼 클릭
3. "Deploy latest commit" 선택

---

## ✅ 배포 완료 확인

### 1. API 서버 헬스 체크

```bash
curl https://prism-api-ay8q.onrender.com/health
```

**예상 출력:**

```json
{
  "status": "healthy",
  "timestamp": "2025-10-28T12:34:56.789Z",
  "active_devices": 0,
  "websocket_connections": 0,
  "total_data_points": 0
}
```

### 2. API 문서 확인

브라우저에서 접속:

```
https://prism-api-ay8q.onrender.com/docs
```

새로운 엔드포인트 확인:

- ✅ `POST /events/fire`
- ✅ `POST /stream/video`
- ✅ `GET /events/fire/latest`
- ✅ `GET /events/fire/history`
- ✅ `GET /stream/video/latest`

### 3. 오렌지파이 테스트

```bash
# 오렌지파이에서 실행
python3 fire_gui1.py
```

---

## 🔧 오렌지파이 설정 변경

`fire_gui1.py` 파일에서 다음 부분을 수정하세요:

```python
# ✅ 변경 전
API_SERVER = "http://localhost:8000"

# ✅ 변경 후
API_SERVER = "https://prism-api-ay8q.onrender.com"
```

전체 설정:

```python
API_SERVER = "https://prism-api-ay8q.onrender.com"
FIRE_EVENT_ENDPOINT = f"{API_SERVER}/events/fire"
VIDEO_STREAM_ENDPOINT = f"{API_SERVER}/stream/video"
API_KEY = "supersecret_key_please_change_me"

HEADERS = {
    "Content-Type": "application/json",
    "X-Api-Key": API_KEY
}
```

---

## 🎯 전체 흐름 테스트

### 1단계: API 서버 확인

```bash
curl https://prism-api-ay8q.onrender.com/health
```

### 2단계: 오렌지파이 실행

```bash
# 오렌지파이에서
python3 fire_gui1.py
```

### 3단계: 화재 감지 테스트

- 화재/연기 이미지를 카메라에 보여주기
- 오렌지파이 콘솔에서 "✅ 화재 이벤트 전송 성공" 확인

### 4단계: 웹 대시보드 확인

- https://prism-jnhr0jkrd-pangs-projects-6d3df8bf.vercel.app
- TEST BOX가 빨간색(위험)으로 변경 확인
- 이벤트: "🔥 Fire 감지!" 표시 확인
- CCTV 버튼 클릭하여 실시간 영상 확인

---

## 🐛 문제 해결

### Render 배포가 시작되지 않을 때

1. **GitHub 연동 확인**

   - Render 대시보드 → Settings → Build & Deploy
   - "Auto-Deploy" 활성화 확인

2. **수동 배포 실행**
   - "Manual Deploy" → "Deploy latest commit"

### 오렌지파이 연결 오류

```python
# 연결 테스트
import requests

try:
    response = requests.get("https://prism-api-ay8q.onrender.com/health", timeout=10)
    print(f"✅ 연결 성공: {response.status_code}")
    print(response.json())
except Exception as e:
    print(f"❌ 연결 실패: {e}")
```

### API Key 오류 (401)

```python
# API Key 확인
API_KEY = "supersecret_key_please_change_me"

HEADERS = {
    "Content-Type": "application/json",
    "X-Api-Key": API_KEY  # 헤더에 포함 필수
}
```

---

## 📊 배포 타임라인

- ✅ **00:00** - GitHub 푸시
- ✅ **00:30** - Render 자동 배포 감지
- ⏳ **01:00** - 빌드 시작
- ⏳ **02:00** - 배포 진행
- ✅ **03:00** - 배포 완료 (Live)

**예상 소요 시간: 약 3분**

---

## 🎉 완료!

Render 배포가 완료되면 오렌지파이 화재 감지가 실시간으로 대시보드에 반영됩니다! 🔥
