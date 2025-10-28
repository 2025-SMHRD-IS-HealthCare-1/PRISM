# 오렌지파이 설정 가이드

## fire_gui1.py 수정 방법

`fire_gui1.py` 파일에서 다음 부분을 찾아 수정하세요:

### 수정 전:
```python
# 기존 fire_api.py 서버 주소
API_SERVER = "http://localhost:8000"
FIRE_EVENT_ENDPOINT = f"{API_SERVER}/events/fire"
VIDEO_STREAM_ENDPOINT = f"{API_SERVER}/stream/video"
```

### 수정 후:
```python
# PRISM API 서버 주소로 변경
API_SERVER = "https://prism-api-ay8q.onrender.com"
FIRE_EVENT_ENDPOINT = f"{API_SERVER}/events/fire"
VIDEO_STREAM_ENDPOINT = f"{API_SERVER}/stream/video"
API_KEY = "supersecret_key_please_change_me"
```

## 전체 코드 예시

```python
import requests
import json
import base64
from datetime import datetime

# ✅ PRISM API 서버 주소 (Render 배포)
API_SERVER = "https://prism-api-ay8q.onrender.com"
FIRE_EVENT_ENDPOINT = f"{API_SERVER}/events/fire"
VIDEO_STREAM_ENDPOINT = f"{API_SERVER}/stream/video"
API_KEY = "supersecret_key_please_change_me"

# 헤더에 API Key 포함
HEADERS = {
    "Content-Type": "application/json",
    "X-Api-Key": API_KEY
}

def send_fire_event(label, score, bbox, frame_size):
    """화재/연기 감지 이벤트 전송"""
    data = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "source": "orangepi_fire_detector_01",
        "label": label,  # "Fire" or "Smoke"
        "score": float(score),
        "bbox": bbox,  # [x1, y1, x2, y2]
        "frame_size": frame_size  # [width, height]
    }
    
    try:
        response = requests.post(
            FIRE_EVENT_ENDPOINT,
            json=data,
            headers=HEADERS,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ 화재 이벤트 전송 성공: {label} ({score:.2%})")
        else:
            print(f"❌ 전송 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 전송 오류: {e}")

def send_video_stream(frame, width, height):
    """비디오 스트림 전송 (Base64 인코딩)"""
    # 이미지를 Base64로 인코딩
    import cv2
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    
    data = {
        "device_id": "orangepi_fire_detector_01",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "frame": frame_base64,
        "width": width,
        "height": height
    }
    
    try:
        response = requests.post(
            VIDEO_STREAM_ENDPOINT,
            json=data,
            headers=HEADERS,
            timeout=5
        )
        
        if response.status_code == 200:
            print("📹 비디오 스트림 전송 성공")
        else:
            print(f"❌ 전송 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 전송 오류: {e}")

# YOLOv5 추론 루프에서 사용 예시
def process_detection(results, frame):
    """
    YOLOv5 결과 처리 및 전송
    """
    for *box, conf, cls in results.xyxy[0]:
        if conf > 0.5:  # 신뢰도 50% 이상만
            label = "Fire" if int(cls) == 0 else "Smoke"
            bbox = [int(box[0]), int(box[1]), int(box[2]), int(box[3])]
            frame_size = [frame.shape[1], frame.shape[0]]  # [width, height]
            
            # 화재/연기 감지 이벤트 전송
            send_fire_event(label, float(conf), bbox, frame_size)
    
    # 비디오 스트림 전송 (2초마다 또는 감지 시)
    send_video_stream(frame, frame.shape[1], frame.shape[0])
```

## 테스트 방법

1. **오렌지파이에서 실행**
   ```bash
   python3 fire_gui1.py
   ```

2. **로그 확인**
   - "✅ 화재 이벤트 전송 성공" 메시지 확인
   - "📹 비디오 스트림 전송 성공" 메시지 확인

3. **웹 대시보드 확인**
   - https://prism-jnhr0jkrd-pangs-projects-6d3df8bf.vercel.app
   - TEST BOX가 빨간색(위험)으로 변경되는지 확인
   - 이벤트 목록에 "🔥 Fire 감지!" 표시 확인
   - CCTV 버튼 클릭 시 실시간 영상 확인

4. **API 서버 로그 확인** (선택)
   ```bash
   # Render 대시보드에서 로그 확인
   # https://dashboard.render.com
   ```

## 문제 해결

### 연결 오류가 발생할 때
```python
# 로컬 테스트용 (FastAPI 서버 로컬 실행 시)
API_SERVER = "http://localhost:8000"

# 프로덕션용 (Render 배포)
API_SERVER = "https://prism-api-ay8q.onrender.com"
```

### API Key 오류
```python
# API Key가 일치하는지 확인
API_KEY = "supersecret_key_please_change_me"

# 헤더에 포함
HEADERS = {
    "Content-Type": "application/json",
    "X-Api-Key": API_KEY
}
```

### 타임아웃 오류
```python
# timeout 값 증가
response = requests.post(
    FIRE_EVENT_ENDPOINT,
    json=data,
    headers=HEADERS,
    timeout=10  # 10초로 증가
)
```
