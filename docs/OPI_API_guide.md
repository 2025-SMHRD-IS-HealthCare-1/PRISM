# 🔥 대시보드 API 연동 수정 가이드

## 📊 현재 API 서버 구조

### API 엔드포인트

```
Base URL: https://prism-api-ay8q.onrender.com
API Key: supersecret_key_please_change_me
```

| 메서드 | 엔드포인트             | 설명                              |
| ------ | ---------------------- | --------------------------------- |
| POST   | `/ingest`              | 데이터 수집 (오렌지파이에서 전송) |
| GET    | `/latest`              | 모든 장치의 최신 데이터 조회      |
| GET    | `/history/{device_id}` | 특정 장치의 히스토리 조회         |
| WS     | `/ws`                  | 실시간 웹소켓 스트림              |
| GET    | `/docs`                | API 문서 (Swagger UI)             |

---

## 🔄 오렌지파이가 전송하는 데이터 형식

### 1. 화재 감지 이벤트 (Fire Detection)

```json
{
  "ts": "2025-10-28T12:34:56.789Z",
  "source": "orangepi_fire_detector_01",
  "type": "fire_detection",
  "label": "Fire",
  "score": 0.89,
  "bbox": [120, 45, 320, 280],
  "frame_size": [640, 480]
}
```

### 2. 비디오 스트림 (Video Stream)

```json
{
  "ts": "2025-10-28T12:34:56.789Z",
  "source": "orangepi_fire_detector_01",
  "type": "video_stream",
  "frame": "base64_encoded_image...",
  "width": 640,
  "height": 480
}
```

---

## 📥 대시보드에서 데이터 읽는 방법

### 방법 1: REST API로 읽기 (권장)

#### A. 최신 데이터 조회 (모든 장치)

```javascript
// JavaScript 예시
async function fetchLatestData() {
  const response = await fetch("https://prism-api-ay8q.onrender.com/latest", {
    headers: {
      "X-Api-Key": "supersecret_key_please_change_me",
    },
  });
  const data = await response.json();

  // 반환 형식:
  // {
  //   "rpi-01": { device_id, data, timestamp, datetime },
  //   "opi-01": { device_id, data, timestamp, datetime },
  //   "orangepi_fire_detector_01": { device_id, data, timestamp, datetime }
  // }

  return data;
}
```

```python
# Python 예시
import requests

def fetch_latest_data():
    url = "https://prism-api-ay8q.onrender.com/latest"
    headers = {"X-Api-Key": "supersecret_key_please_change_me"}

    response = requests.get(url, headers=headers)
    return response.json()
```

#### B. 특정 장치 히스토리 조회

```javascript
// JavaScript 예시
async function fetchDeviceHistory(deviceId, limit = 100) {
  const response = await fetch(
    `https://prism-api-ay8q.onrender.com/history/${deviceId}?limit=${limit}`,
    {
      headers: {
        "X-Api-Key": "supersecret_key_please_change_me",
      },
    }
  );
  const data = await response.json();
  return data;
}

// 사용 예시
const history = await fetchDeviceHistory("orangepi_fire_detector_01", 50);
```

```python
# Python 예시
def fetch_device_history(device_id, limit=100):
    url = f"https://prism-api-ay8q.onrender.com/history/{device_id}"
    params = {"limit": limit}
    headers = {"X-Api-Key": "supersecret_key_please_change_me"}

    response = requests.get(url, params=params, headers=headers)
    return response.json()
```

---

### 방법 2: WebSocket으로 실시간 스트림 (실시간 대시보드)

```javascript
// JavaScript/React 예시
const ws = new WebSocket("wss://prism-api-ay8q.onrender.com/ws");

ws.onopen = () => {
  console.log("✓ WebSocket 연결됨");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  // 실시간 데이터 처리
  console.log("실시간 데이터:", data);

  // 화재 감지 데이터인지 확인
  if (data.type === "fire_detection") {
    updateFireAlert(data);
  }

  // 비디오 스트림인지 확인
  if (data.type === "video_stream") {
    updateVideoDisplay(data);
  }
};

ws.onerror = (error) => {
  console.error("WebSocket 에러:", error);
};

ws.onclose = () => {
  console.log("WebSocket 연결 종료");
  // 재연결 로직
  setTimeout(() => connectWebSocket(), 3000);
};
```

```python
# Python 예시 (websockets 라이브러리 필요)
import asyncio
import websockets
import json

async def stream_data():
    uri = "wss://prism-api-ay8q.onrender.com/ws"

    async with websockets.connect(uri) as websocket:
        print("✓ WebSocket 연결됨")

        async for message in websocket:
            data = json.loads(message)

            # 데이터 타입별 처리
            if data.get('type') == 'fire_detection':
                print(f"🔥 화재 감지: {data}")
            elif data.get('type') == 'video_stream':
                print(f"📹 비디오 스트림 수신")

# 실행
asyncio.run(stream_data())
```

---

## 🎨 대시보드 UI 구현 예시

### React 컴포넌트 예시

```jsx
import React, { useState, useEffect } from "react";

function FireDetectionDashboard() {
  const [latestData, setLatestData] = useState(null);
  const [fireEvents, setFireEvents] = useState([]);
  const [videoFrame, setVideoFrame] = useState(null);

  // WebSocket 연결
  useEffect(() => {
    const ws = new WebSocket("wss://prism-api-ay8q.onrender.com/ws");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "fire_detection") {
        // 화재 감지 이벤트 추가
        setFireEvents((prev) => [data, ...prev].slice(0, 10)); // 최근 10개만 유지
      }

      if (data.type === "video_stream") {
        // 비디오 프레임 업데이트
        setVideoFrame(`data:image/jpeg;base64,${data.frame}`);
      }
    };

    return () => ws.close();
  }, []);

  // 주기적으로 최신 데이터 조회 (백업용)
  useEffect(() => {
    const fetchData = async () => {
      const response = await fetch(
        "https://prism-api-ay8q.onrender.com/latest",
        {
          headers: { "X-Api-Key": "supersecret_key_please_change_me" },
        }
      );
      const data = await response.json();
      setLatestData(data);
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // 5초마다 갱신

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard">
      <h1>🔥 화재 감지 대시보드</h1>

      {/* 실시간 비디오 */}
      <div className="video-container">
        <h2>실시간 카메라</h2>
        {videoFrame && <img src={videoFrame} alt="Live Stream" />}
      </div>

      {/* 화재 감지 이벤트 목록 */}
      <div className="fire-events">
        <h2>화재 감지 이벤트</h2>
        {fireEvents.map((event, index) => (
          <div key={index} className="event-card">
            <span className={`label ${event.label.toLowerCase()}`}>
              {event.label}
            </span>
            <span className="confidence">
              {(event.score * 100).toFixed(1)}%
            </span>
            <span className="time">{new Date(event.ts).toLocaleString()}</span>
          </div>
        ))}
      </div>

      {/* 모든 장치 상태 */}
      <div className="device-status">
        <h2>장치 상태</h2>
        {latestData &&
          Object.entries(latestData).map(([deviceId, device]) => (
            <div key={deviceId} className="device-card">
              <h3>{deviceId}</h3>
              <pre>{JSON.stringify(device.data, null, 2)}</pre>
              <small>{device.datetime}</small>
            </div>
          ))}
      </div>
    </div>
  );
}

export default FireDetectionDashboard;
```

---

## 🔑 수정해야 할 부분 체크리스트

### ✅ 대시보드 코드에서 수정할 사항

#### 1. API 엔드포인트 변경

```diff
- const API_URL = 'https://prism-api-ay8q.onrender.com/events/fire';
+ const API_URL = 'https://prism-api-ay8q.onrender.com/latest';
```

#### 2. 데이터 구조 변경

```javascript
// 기존 (예상)
data.events.forEach(event => { ... })

// 변경 후
Object.entries(data).forEach(([deviceId, device]) => {
  // device.data에 실제 센서 데이터
  // device.timestamp, device.datetime
})
```

#### 3. WebSocket 추가 (실시간 업데이트)

```javascript
// WebSocket 연결 추가
const ws = new WebSocket("wss://prism-api-ay8q.onrender.com/ws");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  // 오렌지파이 화재 감지 데이터 필터링
  if (
    data.source === "orangepi_fire_detector_01" &&
    data.type === "fire_detection"
  ) {
    // UI 업데이트
    addFireEvent(data);
  }
};
```

#### 4. 헤더에 API Key 추가

```javascript
fetch(API_URL, {
  headers: {
    "X-Api-Key": "supersecret_key_please_change_me",
  },
});
```

---

## 🧪 테스트 방법

### 1. API 응답 확인

```bash
# 최신 데이터 조회
curl -s "https://prism-api-ay8q.onrender.com/latest" \
  -H "X-Api-Key: supersecret_key_please_change_me"

# 특정 장치 히스토리
curl -s "https://prism-api-ay8q.onrender.com/history/orangepi_fire_detector_01" \
  -H "X-Api-Key: supersecret_key_please_change_me"
```

### 2. WebSocket 테스트 (브라우저 콘솔)

```javascript
const ws = new WebSocket("wss://prism-api-ay8q.onrender.com/ws");
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

### 3. 오렌지파이 실행 후 데이터 확인

```bash
# 오렌지파이에서 프로그램 실행
python3 fire_gui1.py

# 다른 터미널에서 실시간 모니터링
watch -n 2 'curl -s "https://prism-api-ay8q.onrender.com/latest" -H "X-Api-Key: supersecret_key_please_change_me" | python3 -m json.tool'
```

---

## 📝 데이터 필드 매핑

### 오렌지파이 화재 감지 → 대시보드

| 오렌지파이 필드 | 타입   | 설명                        | 대시보드 활용                            |
| --------------- | ------ | --------------------------- | ---------------------------------------- |
| `ts`            | string | 타임스탬프 (ISO 8601)       | 이벤트 시간 표시                         |
| `source`        | string | 장치 ID                     | 필터링용                                 |
| `type`          | string | 데이터 타입                 | `fire_detection` / `video_stream` 구분   |
| `label`         | string | 감지 클래스                 | `Fire` / `Smoke`                         |
| `score`         | float  | 신뢰도 (0.0~1.0)            | 퍼센트로 표시                            |
| `bbox`          | array  | 바운딩 박스 [x1,y1,x2,y2]   | 영상에 박스 그리기                       |
| `frame_size`    | array  | 프레임 크기 [width, height] | 좌표 스케일링                            |
| `frame`         | string | Base64 이미지               | `<img src="data:image/jpeg;base64,...">` |

---

## 🚀 배포 전 체크리스트

- [ ] API URL 변경 (`/events/fire` → `/latest`)
- [ ] WebSocket URL 추가 (`wss://.../ws`)
- [ ] API Key 헤더 추가
- [ ] 데이터 구조 변경 반영
- [ ] 오렌지파이 장치 ID 필터링 (`orangepi_fire_detector_01`)
- [ ] 데이터 타입별 처리 (`fire_detection`, `video_stream`)
- [ ] 에러 핸들링 추가
- [ ] WebSocket 재연결 로직 구현
- [ ] 브라우저 콘솔에서 WebSocket 연결 테스트
- [ ] 실제 화재 감지 시 알림 테스트

---

## 🔗 참고 링크

- **API 문서**: https://prism-api-ay8q.onrender.com/docs
- **서버 상태**: https://prism-api-ay8q.onrender.com/
- **최신 데이터**: https://prism-api-ay8q.onrender.com/latest

---

## 💡 추가 팁

### CORS 이슈 발생 시

프론트엔드에서 API 호출 시 CORS 에러가 발생하면 백엔드에서 CORS 설정을 확인하세요.

### 데이터가 안 보일 때

1. 오렌지파이 프로그램이 실행 중인지 확인
2. API Key가 올바른지 확인
3. 브라우저 개발자 도구 Network 탭에서 API 응답 확인
4. WebSocket 연결 상태 확인

### 성능 최적화

- 비디오 스트림은 WebSocket으로만 받기 (REST API는 히스토리용)
- 화재 감지 이벤트는 최근 N개만 표시
- 이미지 압축률 조정 (현재 80%, 필요시 더 낮춤)
