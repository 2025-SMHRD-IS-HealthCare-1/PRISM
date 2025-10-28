# 🎉 PRISM 시스템 배포 완료!

## 📊 배포 정보

### 🌐 프론트엔드 (Vercel)

- **URL**: https://prism-753nujdsn-pangs-projects-6d3df8bf.vercel.app
- **상태**: ✅ 배포 완료
- **플랫폼**: Vercel
- **빌드 시간**: ~4초

### 🚀 API 서버 (Render)

- **URL**: https://prism-api-ay8q.onrender.com
- **WebSocket**: wss://prism-api-ay8q.onrender.com/ws
- **상태**: ✅ 배포 완료 및 실행 중
- **플랫폼**: Render
- **활성 디바이스**: 3개
- **총 데이터 포인트**: 275개
- **WebSocket 연결**: 1개

---

## 🧪 테스트 결과

### ✅ 센서 데이터 전송 테스트

```bash
# 테스트 스크립트 실행
python3 scripts/test_sender.py

# 결과: 35회 전송 성공
✓ [rpi-01] 데이터 전송 성공
✓ [opi-01] 데이터 전송 성공
✓ [test-device] 데이터 전송 성공
```

### ✅ 임계값 이벤트 테스트

```bash
# 위험 수준 데이터 전송
curl -X POST https://prism-api-ay8q.onrender.com/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "rpi-01",
    "data": {
      "temperature": 36.5,    # 위험 (>35°C)
      "gas": 210,             # 위험 (>200)
      "pm25": 38,             # 위험 (>35)
      "pm1": 55,              # 위험 (>50)
      "pm10": 105,            # 위험 (>100)
      "gas_delta": 60,        # 위험 (>50)
      "flame": true           # 화염 감지!
    }
  }'
```

**예상 이벤트**:

- 🔥 TEST BOX 불꽃 감지
- 🌡️ TEST BOX 고온 (36.5°C)
- 💨 TEST BOX 가스 농도 위험 (210)
- 💨 TEST BOX PM2.5 높음 (38)
- 💨 TEST BOX PM1.0 높음 (55)
- 💨 TEST BOX PM10 높음 (105)
- 📈 TEST BOX 가스 급증 (Δ=60)

---

## 🚀 실시간 기능

### 1. 센서 데이터 실시간 전송

라즈베리 파이에서 API 서버로 자동 전송:

```python
# iot_devices/raspberry_pi_sensor.py
API_SERVER = "https://prism-api-ay8q.onrender.com"
SEND_INTERVAL = 5  # 5초마다 전송
```

### 2. WebSocket 실시간 업데이트

브라우저에서 WebSocket 자동 연결:

```javascript
// public/js/dashboard.js
WS_URL = "wss://prism-api-ay8q.onrender.com/ws";
```

### 3. 실시간 이벤트 생성

- ✅ 센서 임계값 초과 시 자동 이벤트
- ✅ 센서 연결/끊김 상태 추적
- ✅ CCTV 화재 감지 (준비됨)
- ✅ 브라우저 알림 지원

---

## 📱 접속 방법

### 데스크톱

1. 브라우저 열기 (Chrome, Edge, Safari)
2. URL 입력: https://prism-753nujdsn-pangs-projects-6d3df8bf.vercel.app
3. WebSocket 자동 연결 (약 1-2초)

### 모바일

1. 스마트폰 브라우저 열기
2. 위 URL 접속
3. 반응형 디자인으로 자동 최적화

### 라즈베리 파이 연동

```bash
# 환경 변수 설정
export API_SERVER=https://prism-api-ay8q.onrender.com
export DEVICE_ID=rpi-01

# 센서 프로그램 실행
python3 iot_devices/raspberry_pi_sensor.py
```

---

## 🎯 주요 기능 확인

### 1. 센서 데이터 표시

- ✅ 온도 (°C)
- ✅ 가스 농도
- ✅ 미세먼지 (PM2.5 기반 계산)
- ✅ 화염 감지 (True/False)

### 2. 최근 이벤트 발생

- ✅ 실시간 이벤트 스트림
- ✅ 임계값 초과 자동 감지
- ✅ 센서 연결 상태 추적
- ❌ 더미 데이터 제거됨

### 3. 통계 정보

- **일일 이벤트**: 실시간 카운트
- **활성 센서**: 연결된 센서 수 (X/4개)
- **활성 카메라**: 0/4개 (향후 구현)
- **시스템 상태**: 센서 연결 기반 판단

### 4. 과거 데이터 그래프

- 주간 평균 상태 값 (최근 7일)
- 위험/경고/주의/정상 트렌드

---

## 🧪 추가 테스트 명령어

### CCTV 화재 감지 테스트

```bash
curl -X POST https://prism-api-ay8q.onrender.com/alert/cctv_fire \
  -H "Content-Type: application/json" \
  -d '{
    "zone": "testbox",
    "confidence": 0.95,
    "frame_url": "https://example.com/fire_frame.jpg"
  }'
```

**예상 결과**:

- 이벤트: `🔥 CCTV 화재 감지! (TEST BOX, 신뢰도: 95.0%)`
- 브라우저 알림 팝업

### 센서 연결 상태 테스트

```bash
# 센서 연결
curl -X POST https://prism-api-ay8q.onrender.com/alert/sensor_connection \
  -H "Content-Type: application/json" \
  -d '{
    "zone": "testbox",
    "device_id": "rpi-01",
    "connected": true
  }'

# 센서 연결 끊김
curl -X POST https://prism-api-ay8q.onrender.com/alert/sensor_connection \
  -H "Content-Type: application/json" \
  -d '{
    "zone": "testbox",
    "device_id": "rpi-01",
    "connected": false
  }'
```

**예상 결과**:

- 연결: `✅ TEST BOX 센서 연결됨 (rpi-01)`, 활성 센서: `1/4개`
- 끊김: `⚠️ TEST BOX 센서 연결 끊김 (rpi-01)`, 활성 센서: `0/4개`

### API 서버 상태 확인

```bash
curl https://prism-api-ay8q.onrender.com/health
```

**응답 예시**:

```json
{
  "status": "healthy",
  "timestamp": "2025-10-28T05:48:42.018309",
  "active_devices": 3,
  "websocket_connections": 1,
  "total_data_points": 275
}
```

### 최신 데이터 조회

```bash
# 모든 디바이스
curl https://prism-api-ay8q.onrender.com/latest

# 특정 디바이스
curl https://prism-api-ay8q.onrender.com/latest/rpi-01

# 히스토리 (최근 100개)
curl https://prism-api-ay8q.onrender.com/history/rpi-01?limit=100
```

---

## 📊 현재 시스템 상태

### API 서버

- ✅ 정상 작동
- ✅ WebSocket 연결 활성
- ✅ 3개 디바이스 연결 중
- ✅ 275개 데이터 포인트 수집

### 프론트엔드

- ✅ Vercel 배포 완료
- ✅ WebSocket 자동 연결
- ✅ 실시간 데이터 표시
- ✅ 이벤트 스트림 작동

### 라즈베리 파이

- ⏳ 연결 대기 중
- 📡 API 서버 주소: https://prism-api-ay8q.onrender.com
- 🔧 환경 변수 설정 필요

---

## 🔧 라즈베리 파이 설정

### 1. 환경 변수 설정

```bash
# ~/.bashrc 또는 ~/.profile에 추가
export API_SERVER=https://prism-api-ay8q.onrender.com
export DEVICE_ID=rpi-01
```

### 2. 센서 프로그램 실행

```bash
cd /home/pi/PRISM
python3 iot_devices/raspberry_pi_sensor.py
```

### 3. 자동 시작 설정 (systemd)

```bash
sudo nano /etc/systemd/system/prism-sensor.service
```

```ini
[Unit]
Description=PRISM Sensor Data Collection
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/PRISM
Environment="API_SERVER=https://prism-api-ay8q.onrender.com"
Environment="DEVICE_ID=rpi-01"
ExecStart=/usr/bin/python3 /home/pi/PRISM/iot_devices/raspberry_pi_sensor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 등록 및 시작
sudo systemctl enable prism-sensor
sudo systemctl start prism-sensor
sudo systemctl status prism-sensor
```

---

## 🎉 배포 완료 체크리스트

- [x] GitHub 저장소 푸시
- [x] Render API 서버 배포
- [x] Vercel 프론트엔드 배포
- [x] WebSocket 연결 테스트
- [x] 센서 데이터 전송 테스트
- [x] 임계값 이벤트 생성 테스트
- [x] CCTV 화재 감지 엔드포인트 추가
- [x] 센서 연결 상태 엔드포인트 추가
- [x] 실시간 이벤트 스트림 작동
- [ ] 라즈베리 파이 연결 (다음 단계)
- [ ] CCTV 화재 감지 시스템 연동 (향후)

---

## 📞 문제 해결

### WebSocket 연결 안됨

1. 브라우저 콘솔 확인 (F12)
2. `wss://prism-api-ay8q.onrender.com/ws` 연결 상태 확인
3. API 서버 상태 확인: `curl https://prism-api-ay8q.onrender.com/health`

### 센서 데이터 안보임

1. 라즈베리 파이 프로그램 실행 확인
2. API_SERVER 환경 변수 확인
3. 최신 데이터 API로 확인: `curl https://prism-api-ay8q.onrender.com/latest`

### 이벤트 생성 안됨

1. 브라우저 콘솔에서 WebSocket 메시지 확인
2. 임계값 초과 데이터 전송 테스트
3. 이벤트 목록 스크롤 확인 (최대 10개 표시)

---

## 🚀 다음 단계

1. **라즈베리 파이 연결**

   - 실제 센서 데이터 전송 시작
   - 자동 시작 서비스 설정

2. **CCTV 화재 감지 시스템 구축**

   - YOLOv8 또는 사전 학습된 모델 사용
   - 화재 감지 시 `/alert/cctv_fire` 호출

3. **추가 기능 개발**
   - 알림 설정 (이메일, SMS)
   - 데이터 분석 및 리포트
   - 사용자 관리 시스템

---

## 📝 배포 이력

### 2025-10-28 14:39 (KST)

- ✅ 프론트엔드 Vercel 배포
- ✅ API 서버 Render 배포
- ✅ 실시간 이벤트 연동 완료
- ✅ 센서 임계값 자동 감지
- ✅ WebSocket 실시간 스트림

### 커밋 메시지

```
feat: 실시간 이벤트 연동 완료 - 센서 임계값, CCTV 화재 감지, 센서 연결 상태 추적

- 더미 이벤트 데이터 제거
- 센서 임계값 변동 시 자동 이벤트 생성
- CCTV 화재 감지 WebSocket 메시지 처리
- 센서 연결 상태 실시간 추적 및 통계 업데이트
- 4개 센서로 대시보드 간소화 (온도, 가스, 미세먼지, 화염)
```

---

**🎊 축하합니다! PRISM 시스템이 성공적으로 배포되었습니다! 🎊**
