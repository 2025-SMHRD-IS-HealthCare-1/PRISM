# 최근 이벤트 실시간 연동 완료

## 📋 개요

더미 데이터를 제거하고 실제 센서 데이터와 연동하여 실시간 이벤트를 생성하도록 개선했습니다.

---

## ✨ 주요 변경사항

### 1. 더미 데이터 제거

- **이전**: 시스템 시작 시 7개의 하드코딩된 이벤트 생성
- **이후**: "시스템 시작 - 센서 연결 대기 중..." 메시지만 표시

### 2. 실시간 이벤트 생성

#### 🌡️ 센서 임계값 변동 이벤트

센서 데이터가 임계값을 초과하면 자동으로 이벤트 생성:

```javascript
// 온도 임계값
- 위험 (danger): 35°C 이상
- 경고 (warning): 30°C 이상
- 주의 (caution): 25°C 이상

// 가스 농도 임계값
- 위험 (danger): 200 이상
- 경고 (warning): 150 이상
- 주의 (caution): 100 이상

// 미세먼지 (PM2.5) 임계값
- 위험 (danger): 35 μg/m³ 이상
- 경고 (warning): 25 μg/m³ 이상
- 주의 (caution): 15 μg/m³ 이상
```

**이벤트 예시**:

- `🌡️ TEST BOX 고온 (36.5°C)`
- `💨 TEST BOX 가스 농도 위험 (205)`
- `💨 TEST BOX PM2.5 높음 (38)`
- `🔥 TEST BOX 불꽃 감지!`

#### 🔥 CCTV 화재 감지 이벤트

CCTV 화재 감지 시스템에서 WebSocket을 통해 실시간 알림:

```javascript
// API 서버로 화재 감지 전송
POST /alert/cctv_fire
{
  "zone": "testbox",
  "confidence": 0.95,
  "frame_url": "https://...",
  "timestamp": 1730000000.0
}
```

**이벤트 예시**:

- `🔥 CCTV 화재 감지! (TEST BOX, 신뢰도: 95.0%)`

**브라우저 알림**:

- 제목: "🔥 PRISM 화재 경보"
- 내용: "TEST BOX CCTV에서 화재가 감지되었습니다! (신뢰도: 95.0%)"
- 옵션: `requireInteraction: true` (사용자가 확인할 때까지 유지)

#### 📡 센서 연결 상태 이벤트

센서 연결/연결 끊김 시 자동으로 이벤트 생성:

```javascript
// API 서버로 센서 상태 전송
POST /alert/sensor_connection
{
  "zone": "testbox",
  "device_id": "rpi-01",
  "connected": true,
  "timestamp": 1730000000.0
}
```

**이벤트 예시**:

- `✅ TEST BOX 센서 연결됨 (rpi-01)`
- `⚠️ TEST BOX 센서 연결 끊김 (rpi-01)`

---

## 🔧 기술 구현

### API 서버 (api_server.py)

#### 1. 새로운 데이터 모델

```python
class CCTVFireAlert(BaseModel):
    zone: str
    confidence: float
    frame_url: Optional[str] = None
    timestamp: Optional[float] = None

class SensorConnectionAlert(BaseModel):
    zone: str
    device_id: str
    connected: bool
    timestamp: Optional[float] = None
```

#### 2. 새로운 엔드포인트

**CCTV 화재 감지 알림**:

```python
@app.post("/alert/cctv_fire")
async def cctv_fire_alert(alert: CCTVFireAlert):
    # WebSocket으로 모든 클라이언트에게 알림
    await manager.broadcast({
        "type": "cctv_fire_detected",
        "zone": alert.zone,
        "confidence": alert.confidence,
        "frame_url": alert.frame_url,
        "timestamp": datetime.fromtimestamp(timestamp).isoformat()
    })
```

**센서 연결 상태 알림**:

```python
@app.post("/alert/sensor_connection")
async def sensor_connection_alert(alert: SensorConnectionAlert):
    # WebSocket으로 모든 클라이언트에게 알림
    await manager.broadcast({
        "type": "sensor_connection_status",
        "zone": alert.zone,
        "device_id": alert.device_id,
        "connected": alert.connected,
        "timestamp": datetime.fromtimestamp(timestamp).isoformat()
    })
```

### 프론트엔드 (dashboard.js)

#### 1. 센서 연결 상태 추적

```javascript
// 전역 상태 추가
let sensorConnectionStatus = {
  testbox: { connected: false, lastUpdate: null },
  warehouse: { connected: false, lastUpdate: null },
  inspection: { connected: false, lastUpdate: null },
  machine: { connected: false, lastUpdate: null },
};

// 연결 상태 업데이트 함수
function updateSensorConnectionStatus(zone, connected) {
  sensorConnectionStatus[zone].connected = connected;
  sensorConnectionStatus[zone].lastUpdate = new Date();

  // 연결된 센서 수 업데이트
  updateSensorCount();
}
```

#### 2. WebSocket 메시지 처리

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === "update") {
    // 센서 데이터 업데이트
    // + 임계값 체크 결과 이벤트 생성
    if (message.alert && message.reasons) {
      message.reasons.forEach(reason => {
        addEvent(message.level, `${getZoneName(zone)} ${reason}`);
      });
    }

    // 센서 연결 상태 업데이트
    updateSensorConnectionStatus(zone, true);
  }

  else if (message.type === "cctv_fire_detected") {
    // CCTV 화재 감지 이벤트
    addEvent("danger", `🔥 CCTV 화재 감지! (${zone}, 신뢰도: ${confidence}%)`);

    // 브라우저 알림
    new Notification("🔥 PRISM 화재 경보", {...});
  }

  else if (message.type === "sensor_connection_status") {
    // 센서 연결 상태 이벤트
    if (connected) {
      addEvent("normal", `✅ ${zone} 센서 연결됨`);
    } else {
      addEvent("warning", `⚠️ ${zone} 센서 연결 끊김`);
    }
  }
};
```

#### 3. 연결 시 이벤트 생성

```javascript
ws.onopen = () => {
  addEvent("normal", "센서 연결 완료");
};

ws.onerror = () => {
  addEvent("warning", "센서 연결 오류 발생");
};

ws.onclose = () => {
  addEvent("warning", "센서 연결 종료");
};
```

---

## 📊 통계 정보 자동 업데이트

### 활성 센서 카운트

```javascript
function updateSensorCount() {
  // 연결된 센서 수 계산
  const connectedSensors = Object.values(sensorConnectionStatus).filter(
    (status) => status.connected
  ).length;

  document.getElementById(
    "active-sensors"
  ).textContent = `${connectedSensors}/4개`;
}
```

**표시 예시**:

- 모든 센서 연결: `4/4개`
- 일부 연결 끊김: `2/4개`
- 모두 연결 끊김: `0/4개`

---

## 🧪 테스트 방법

### 1. 센서 데이터 전송 (임계값 이벤트 테스트)

```bash
# 정상 데이터
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "rpi-01",
    "data": {
      "temperature": 24.5,
      "gas": 50,
      "pm25": 12,
      "flame": false
    }
  }'

# 위험 데이터 (임계값 초과)
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "rpi-01",
    "data": {
      "temperature": 36.0,
      "gas": 210,
      "pm25": 38,
      "flame": true
    }
  }'
```

**예상 이벤트**:

- `🔥 TEST BOX 불꽃 감지`
- `🌡️ TEST BOX 고온 (36.0°C)`
- `💨 TEST BOX 가스 농도 위험 (210)`
- `💨 TEST BOX PM2.5 높음 (38)`

### 2. CCTV 화재 감지 테스트

```bash
curl -X POST http://localhost:8000/alert/cctv_fire \
  -H "Content-Type: application/json" \
  -d '{
    "zone": "testbox",
    "confidence": 0.95,
    "frame_url": "https://example.com/fire_frame.jpg"
  }'
```

**예상 결과**:

- 이벤트 목록: `🔥 CCTV 화재 감지! (TEST BOX, 신뢰도: 95.0%)`
- 브라우저 알림 팝업 표시

### 3. 센서 연결 상태 테스트

```bash
# 센서 연결
curl -X POST http://localhost:8000/alert/sensor_connection \
  -H "Content-Type: application/json" \
  -d '{
    "zone": "testbox",
    "device_id": "rpi-01",
    "connected": true
  }'

# 센서 연결 끊김
curl -X POST http://localhost:8000/alert/sensor_connection \
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

---

## 🎯 주요 개선 효과

1. **실시간 모니터링**: 더미 데이터 제거로 실제 센서 상태만 표시
2. **위험 감지 자동화**: 임계값 초과 시 자동으로 이벤트 생성 및 알림
3. **CCTV 연동**: 화재 감지 시스템과 실시간 연동
4. **센서 상태 추적**: 연결/끊김 상태 실시간 모니터링
5. **통계 정확성**: 실제 연결된 센서 수 표시

---

## 📝 다음 단계

### CCTV 화재 감지 시스템 구현

```python
# cctv_fire_detection.py (예시)
import requests
import cv2
from fire_detection_model import detect_fire

def send_fire_alert(zone, confidence, frame_path):
    """화재 감지 시 API 서버로 알림 전송"""
    response = requests.post(
        "http://localhost:8000/alert/cctv_fire",
        json={
            "zone": zone,
            "confidence": confidence,
            "frame_url": upload_frame_to_cloud(frame_path)
        }
    )
    return response.json()

# CCTV 프레임에서 화재 감지
while True:
    frame = capture_frame()
    fire_detected, confidence = detect_fire(frame)

    if fire_detected and confidence > 0.8:
        send_fire_alert("testbox", confidence, frame)
```

### 라즈베리 파이에서 센서 연결 상태 전송

```python
# raspberry_pi_sensor.py에 추가
def send_connection_status(connected):
    """센서 연결 상태 전송"""
    try:
        response = requests.post(
            f"{API_URL}/alert/sensor_connection",
            json={
                "zone": ZONE,
                "device_id": DEVICE_ID,
                "connected": connected
            }
        )
        return response.json()
    except Exception as e:
        print(f"연결 상태 전송 실패: {e}")

# 센서 초기화 성공 시
if sensor_init_success:
    send_connection_status(True)

# 센서 오류 발생 시
except SensorError:
    send_connection_status(False)
```

---

## ✅ 완료 체크리스트

- [x] 더미 이벤트 데이터 제거
- [x] 센서 임계값 변동 이벤트 연동
- [x] CCTV 화재 감지 이벤트 WebSocket 메시지 처리
- [x] 센서 연결 상태 추적 기능 구현
- [x] API 서버 `/alert/cctv_fire` 엔드포인트 추가
- [x] API 서버 `/alert/sensor_connection` 엔드포인트 추가
- [x] 브라우저 알림 (Notification API) 연동
- [x] 활성 센서 카운트 실시간 업데이트
- [x] WebSocket 연결/종료 시 이벤트 생성
- [ ] CCTV 화재 감지 시스템 구축 (향후)
- [ ] 라즈베리 파이 센서 연결 상태 전송 구현 (향후)

---

## 🚀 배포

변경사항을 배포하려면:

```bash
# Git 커밋
git add .
git commit -m "feat: 실시간 이벤트 연동 - 센서 임계값, CCTV 화재 감지, 센서 연결 상태"
git push

# Vercel 배포 (프론트엔드)
vercel --prod

# Render 배포 (API 서버)
# Git push 시 자동 배포됨
```
