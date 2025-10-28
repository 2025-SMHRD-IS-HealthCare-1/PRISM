"""
PRISM 센서 데이터 FastAPI 서버 (WebSocket 지원)
라즈베리파이/오렌지파이에서 센서 데이터를 받아 웹 대시보드로 실시간 전달

🧩 시스템 구조:
[라즈베리 파이]            [오렌지 파이]
      │                     │
      │  ┌──────────────────┘
      ▼  ▼
┌──────────────────────────┐
│     FastAPI 서버          │
│  (HTTP + WebSocket 지원)  │
└──────────────────────────┘
             │
             ▼ (WebSocket 실시간 스트리밍)
     🌐 웹페이지 (브라우저)
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import asyncio
import json
import os

app = FastAPI(
    title="PRISM Sensor API", 
    version="3.0.0",
    description="IoT 센서 데이터 수집 및 실시간 전달 API (WebSocket 지원)"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# 데이터 모델
# ============================================

class IngestData(BaseModel):
    """라즈베리파이/오렌지파이에서 전송하는 데이터 모델"""
    device_id: str  # 예: "rpi-01", "opi-01"
    data: Dict[str, Any]  # 센서 데이터 (유연한 구조)
    ts: Optional[float] = None  # 타임스탬프 (Unix timestamp)

class SensorData(BaseModel):
    """센서 데이터 모델 (기존 호환성)"""
    zone: str
    temperature: float
    gas: float
    dust: float
    flame: bool
    timestamp: Optional[datetime] = None

class CCTVFireAlert(BaseModel):
    """CCTV 화재 감지 알림 모델"""
    zone: str
    confidence: float
    frame_url: Optional[str] = None
    timestamp: Optional[float] = None

class SensorConnectionAlert(BaseModel):
    """센서 연결 상태 알림 모델"""
    zone: str
    device_id: str
    connected: bool
    timestamp: Optional[float] = None

class BuzzerTrigger(BaseModel):
    """라즈베리파이 부저 트리거 모델"""
    zone: str
    reason: str
    duration: Optional[int] = 3000  # 기본 3초

class FireEvent(BaseModel):
    """오렌지파이 화재 감지 이벤트 모델"""
    ts: str
    source: str
    label: str  # "Fire" 또는 "Smoke"
    score: float  # 신뢰도 0.0 ~ 1.0
    bbox: List[int]  # [x1, y1, x2, y2]
    frame_size: List[int]  # [width, height]

class VideoStream(BaseModel):
    """오렌지파이 비디오 스트림 모델"""
    ts: str
    source: str
    type: str  # "video_stream"
    frame: str  # base64 encoded image
    width: int
    height: int

# ============================================
# 인메모리 데이터 저장
# ============================================

# 각 디바이스의 최신 데이터 저장 {device_id: data}
LATEST: Dict[str, Dict[str, Any]] = {}

# 히스토리 데이터 저장 {device_id: [data, data, ...]}
HISTORY: Dict[str, List[Dict[str, Any]]] = {}

# 🔥 오렌지파이 화재 이벤트 저장
FIRE_EVENTS: List[Dict[str, Any]] = []
LATEST_FIRE_EVENT: Optional[Dict[str, Any]] = None
LATEST_VIDEO_STREAM: Optional[Dict[str, Any]] = None

# WebSocket 연결 관리 (활성 브라우저 연결)
active_connections: List[WebSocket] = []

# ============================================
# WebSocket 연결 관리자
# ============================================

class ConnectionManager:
    """WebSocket 연결을 관리하는 클래스"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """새로운 WebSocket 연결 수락"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket 연결됨. 총 연결 수: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결 해제"""
        self.active_connections.remove(websocket)
        print(f"❌ WebSocket 연결 해제. 총 연결 수: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """모든 연결된 클라이언트에게 메시지 브로드캐스트"""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                print(f"⚠️ 메시지 전송 실패: {e}")
                disconnected.append(connection)
        
        # 실패한 연결 제거
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()

# ============================================
# WebSocket 엔드포인트
# ============================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 연결 엔드포인트
    브라우저에서 ws://서버IP:8000/ws 로 연결
    """
    await manager.connect(websocket)
    
    try:
        # 연결 직후 현재 모든 데이터 전송
        if LATEST:
            await websocket.send_text(json.dumps({
                "type": "init",
                "data": LATEST,
                "timestamp": datetime.now().isoformat()
            }))
        
        # 연결 유지 및 ping/pong 처리
        while True:
            data = await websocket.receive_text()
            
            # 클라이언트에서 ping 메시지 받으면 pong 응답
            if data == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket 오류: {e}")
        manager.disconnect(websocket)

# ============================================
# 데이터 수집 엔드포인트 (라즈베리파이/오렌지파이)
# ============================================

def check_thresholds(device_id: str, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    센서 데이터 임계값 체크 및 위험 수준 판단
    
    반환값:
    {
        "alert": True/False,
        "level": "danger"/"warning"/"caution"/"normal",
        "reasons": ["불꽃 감지", "가스 높음", ...]
    }
    """
    # 임계값 설정
    THRESHOLDS = {
        "flame": True,              # 불꽃 감지 시 위험
        "temperature": {
            "danger": 35.0,         # 위험
            "warning": 30.0,        # 경고
            "caution": 25.0         # 주의
        },
        "gas": {
            "danger": 200,          # 원시값 기준
            "warning": 150,
            "caution": 100
        },
        "gas_delta": {
            "danger": 50,           # 급격한 증가
            "warning": 30
        },
        "pm1": {
            "danger": 50,
            "warning": 35
        },
        "pm25": {
            "danger": 35,           # PM2.5
            "warning": 25,
            "caution": 15
        },
        "pm10": {
            "danger": 100,
            "warning": 75,
            "caution": 50
        }
    }
    
    alert = False
    level = "normal"
    reasons = []
    
    # 1. 불꽃 감지
    if sensor_data.get("flame") == True:
        alert = True
        level = "danger"
        reasons.append("🔥 불꽃 감지")
    
    # 2. 온도
    temp = sensor_data.get("temperature")
    if temp is not None:
        if temp > THRESHOLDS["temperature"]["danger"]:
            alert = True
            level = "danger"
            reasons.append(f"🌡️ 고온 ({temp}°C)")
        elif temp > THRESHOLDS["temperature"]["warning"]:
            if level not in ["danger"]:
                level = "warning"
            reasons.append(f"⚠️ 온도 경고 ({temp}°C)")
        elif temp > THRESHOLDS["temperature"]["caution"]:
            if level == "normal":
                level = "caution"
    
    # 3. 가스 농도
    gas = sensor_data.get("gas")
    if gas is not None:
        if gas > THRESHOLDS["gas"]["danger"]:
            alert = True
            level = "danger"
            reasons.append(f"💨 가스 농도 위험 ({gas})")
        elif gas > THRESHOLDS["gas"]["warning"]:
            if level not in ["danger"]:
                level = "warning"
            reasons.append(f"⚠️ 가스 농도 경고 ({gas})")
        elif gas > THRESHOLDS["gas"]["caution"]:
            if level == "normal":
                level = "caution"
    
    # 4. 가스 급증
    gas_delta = sensor_data.get("gas_delta")
    if gas_delta is not None:
        if gas_delta > THRESHOLDS["gas_delta"]["danger"]:
            alert = True
            level = "danger"
            reasons.append(f"📈 가스 급증 (Δ={gas_delta})")
        elif gas_delta > THRESHOLDS["gas_delta"]["warning"]:
            if level not in ["danger"]:
                level = "warning"
    
    # 5. 미세먼지 PM1.0
    pm1 = sensor_data.get("pm1")
    if pm1 is not None and pm1 > THRESHOLDS["pm1"]["danger"]:
        alert = True
        level = "danger"
        reasons.append(f"💨 PM1.0 높음 ({pm1})")
    
    # 6. 미세먼지 PM2.5
    pm25 = sensor_data.get("pm25")
    if pm25 is not None:
        if pm25 > THRESHOLDS["pm25"]["danger"]:
            alert = True
            level = "danger"
            reasons.append(f"💨 PM2.5 높음 ({pm25})")
        elif pm25 > THRESHOLDS["pm25"]["warning"]:
            if level not in ["danger"]:
                level = "warning"
        elif pm25 > THRESHOLDS["pm25"]["caution"]:
            if level == "normal":
                level = "caution"
    
    # 7. 미세먼지 PM10
    pm10 = sensor_data.get("pm10")
    if pm10 is not None:
        if pm10 > THRESHOLDS["pm10"]["danger"]:
            alert = True
            level = "danger"
            reasons.append(f"💨 PM10 높음 ({pm10})")
        elif pm10 > THRESHOLDS["pm10"]["warning"]:
            if level not in ["danger"]:
                level = "warning"
        elif pm10 > THRESHOLDS["pm10"]["caution"]:
            if level == "normal":
                level = "caution"
    
    return {
        "alert": alert,
        "level": level,
        "reasons": reasons
    }

@app.post("/ingest")
async def ingest_data(data: IngestData):
    """
    🔥 메인 데이터 수집 엔드포인트
    
    라즈베리파이/오렌지파이에서 이 엔드포인트로 데이터 전송
    
    요청 예시:
    {
        "device_id": "rpi-01",
        "data": {"temp": 24.8, "hum": 51.2, "gas": 15.5},
        "ts": 1730000000.0
    }
    """
    device_id = data.device_id
    timestamp = data.ts if data.ts else datetime.now().timestamp()
    
    # 임계값 체크
    threshold_result = check_thresholds(device_id, data.data)
    
    # 데이터 저장
    stored_data = {
        "device_id": device_id,
        "data": data.data,
        "timestamp": timestamp,
        "datetime": datetime.fromtimestamp(timestamp).isoformat(),
        "alert": threshold_result["alert"],
        "level": threshold_result["level"],
        "reasons": threshold_result["reasons"]
    }
    
    # 최신 데이터 업데이트
    LATEST[device_id] = stored_data
    
    # 히스토리에 추가
    if device_id not in HISTORY:
        HISTORY[device_id] = []
    
    HISTORY[device_id].append(stored_data)
    
    # 최근 1000개 데이터만 유지 (메모리 관리)
    if len(HISTORY[device_id]) > 1000:
        HISTORY[device_id] = HISTORY[device_id][-1000:]
    
    # 로그 출력
    if threshold_result["alert"]:
        print(f"🚨 [{device_id}] 위험 감지! {' | '.join(threshold_result['reasons'])}")
    print(f"📊 [{device_id}] 데이터 수신: {data.data}")
    
    # 🔥 WebSocket으로 모든 연결된 브라우저에게 실시간 전송
    await manager.broadcast({
        "type": "update",
        "device_id": device_id,
        "data": data.data,
        "alert": threshold_result["alert"],
        "level": threshold_result["level"],
        "reasons": threshold_result["reasons"],
        "timestamp": datetime.fromtimestamp(timestamp).isoformat()
    })
    
    return {
        "status": "success",
        "device_id": device_id,
        "alert": threshold_result["alert"],
        "level": threshold_result["level"],
        "timestamp": datetime.fromtimestamp(timestamp).isoformat()
    }

# ============================================
# 데이터 조회 엔드포인트
# ============================================

@app.get("/latest")
async def get_latest():
    """모든 디바이스의 최신 데이터 조회"""
    return LATEST

@app.get("/latest/{device_id}")
async def get_latest_by_device(device_id: str):
    """특정 디바이스의 최신 데이터 조회"""
    if device_id not in LATEST:
        raise HTTPException(status_code=404, detail=f"디바이스 '{device_id}'의 데이터를 찾을 수 없습니다")
    
    return LATEST[device_id]

@app.get("/history/{device_id}")
async def get_history(device_id: str, limit: int = 100):
    """특정 디바이스의 히스토리 데이터 조회"""
    if device_id not in HISTORY:
        raise HTTPException(status_code=404, detail=f"디바이스 '{device_id}'의 히스토리를 찾을 수 없습니다")
    
    # 최근 limit개 데이터 반환
    return HISTORY[device_id][-limit:]

@app.get("/devices")
async def get_devices():
    """연결된 모든 디바이스 목록"""
    devices = []
    for device_id, data in LATEST.items():
        devices.append({
            "device_id": device_id,
            "last_update": data.get("datetime"),
            "data_keys": list(data.get("data", {}).keys())
        })
    
    return devices

# ============================================
# 이벤트 알림 엔드포인트 (CCTV, 센서 연결 상태)
# ============================================

@app.post("/alert/cctv_fire")
async def cctv_fire_alert(alert: CCTVFireAlert):
    """
    🔥 CCTV 화재 감지 알림
    
    CCTV 화재 감지 시스템에서 화재 감지 시 호출
    모든 연결된 브라우저에게 실시간 알림 전송
    """
    timestamp = alert.timestamp if alert.timestamp else datetime.now().timestamp()
    
    print(f"🔥 CCTV 화재 감지! [{alert.zone}] 신뢰도: {alert.confidence:.2%}")
    
    # WebSocket으로 모든 클라이언트에게 화재 알림 전송
    await manager.broadcast({
        "type": "cctv_fire_detected",
        "zone": alert.zone,
        "confidence": alert.confidence,
        "frame_url": alert.frame_url,
        "timestamp": datetime.fromtimestamp(timestamp).isoformat()
    })
    
    return {
        "status": "success",
        "message": "화재 알림이 전송되었습니다",
        "zone": alert.zone,
        "confidence": alert.confidence
    }

@app.post("/alert/sensor_connection")
async def sensor_connection_alert(alert: SensorConnectionAlert):
    """
    📡 센서 연결 상태 알림
    
    센서 연결/연결 끊김 시 호출
    모든 연결된 브라우저에게 실시간 알림 전송
    """
    timestamp = alert.timestamp if alert.timestamp else datetime.now().timestamp()
    
    status_text = "연결됨" if alert.connected else "연결 끊김"
    print(f"📡 센서 상태 변경 [{alert.device_id}]: {status_text}")
    
    # WebSocket으로 모든 클라이언트에게 센서 상태 알림 전송
    await manager.broadcast({
        "type": "sensor_connection_status",
        "zone": alert.zone,
        "device_id": alert.device_id,
        "connected": alert.connected,
        "timestamp": datetime.fromtimestamp(timestamp).isoformat()
    })
    
    return {
        "status": "success",
        "message": f"센서 상태 알림이 전송되었습니다 ({status_text})",
        "device_id": alert.device_id,
        "connected": alert.connected
    }

# ============================================
# 기존 API 호환성 유지 (Express/웹 대시보드용)
# ============================================

@app.post("/api/sensors/{zone}")
async def update_sensor_data(zone: str, data: SensorData):
    """
    기존 API 호환성 유지: 라즈베리파이/오렌지파이에서 센서 데이터 전송
    (Express 서버와의 호환성을 위해 유지)
    """
    data.zone = zone
    data.timestamp = datetime.now()
    
    print(f"📊 센서 데이터 수신 [{zone}]: 온도={data.temperature}°C, 가스={data.gas}ppm, 먼지={data.dust}μg/m³")
    
    # 새로운 형식으로 변환하여 저장
    device_id = f"zone-{zone}"
    stored_data = {
        "device_id": device_id,
        "data": {
            "temperature": data.temperature,
            "gas": data.gas,
            "dust": data.dust,
            "flame": data.flame
        },
        "timestamp": data.timestamp.timestamp(),
        "datetime": data.timestamp.isoformat()
    }
    
    LATEST[device_id] = stored_data
    
    if device_id not in HISTORY:
        HISTORY[device_id] = []
    HISTORY[device_id].append(stored_data)
    
    # WebSocket 브로드캐스트
    await manager.broadcast({
        "type": "update",
        "zone": zone,
        "device_id": device_id,
        "data": stored_data["data"],
        "timestamp": data.timestamp.isoformat()
    })
    
    return {"status": "success", "message": "센서 데이터가 업데이트되었습니다", "zone": zone}

@app.get("/api/sensors/{zone}")
async def get_sensor_data(zone: str):
    """
    기존 API 호환성 유지: 특정 구역의 센서 데이터 조회
    """
    device_id = f"zone-{zone}"
    
    if device_id not in LATEST:
        raise HTTPException(status_code=404, detail=f"센서 데이터를 찾을 수 없습니다. 구역: {zone}")
    
    data = LATEST[device_id]["data"]
    timestamp = LATEST[device_id]["datetime"]
    
    return {
        "zone": zone,
        "temperature": data.get("temperature", 0),
        "gas": data.get("gas", 0),
        "dust": data.get("dust", 0),
        "flame": data.get("flame", False),
        "timestamp": timestamp,
        "connected": True
    }

@app.get("/api/history/{zone}")
async def get_historical_data(zone: str, hours: int = 24, days: int = None):
    """
    기존 API 호환성 유지: 과거 센서 데이터 조회
    """
    device_id = f"zone-{zone}"
    
    if device_id not in HISTORY or len(HISTORY[device_id]) == 0:
        return []
    
    if days:
        hours = days * 24
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    cutoff_timestamp = cutoff_time.timestamp()
    
    filtered_data = [
        {
            "timestamp": d["datetime"],
            "temperature": d["data"].get("temperature", 0),
            "gas": d["data"].get("gas", 0),
            "dust": d["data"].get("dust", 0)
        }
        for d in HISTORY[device_id]
        if d["timestamp"] > cutoff_timestamp
    ]
    
    return filtered_data

@app.get("/api/zones")
async def get_zones():
    """
    모든 구역 목록과 상태를 반환
    """
    zones = []
    for device_id in LATEST.keys():
        if device_id.startswith("zone-"):
            zone_name = device_id.replace("zone-", "")
            zones.append({
                "id": zone_name,
                "name": zone_name.upper(),
                "active": True,
                "status": "normal",
                "has_data": True
            })
    
    # 기본 구역 (데이터 없는 경우)
    default_zones = ["testbox", "warehouse", "inspection", "machine"]
    existing_zones = [z["id"] for z in zones]
    
    for zone in default_zones:
        if zone not in existing_zones:
            zones.append({
                "id": zone,
                "name": zone.upper(),
                "active": False,
                "status": "inactive",
                "has_data": False
            })
    
    return zones

# ============================================
# � 오렌지파이 화재 감지 API
# ============================================

@app.post("/events/fire")
async def receive_fire_event(
    event: FireEvent,
    x_api_key: Optional[str] = Header(default=None)
):
    """
    오렌지파이에서 화재/연기 감지 이벤트 수신
    
    fire_gui1.py에서 화재 또는 연기를 감지하면 이 엔드포인트로 전송
    수신한 데이터를 WebSocket으로 브라우저에 실시간 전달
    """
    global LATEST_FIRE_EVENT, FIRE_EVENTS
    
    # API Key 검증 (선택적)
    API_KEY = "supersecret_key_please_change_me"
    if x_api_key and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # 이벤트 저장
    event_data = event.dict()
    LATEST_FIRE_EVENT = event_data
    FIRE_EVENTS.append(event_data)
    
    # 최근 100개만 유지
    if len(FIRE_EVENTS) > 100:
        FIRE_EVENTS = FIRE_EVENTS[-100:]
    
    print(f"🔥 화재 감지 이벤트 수신: {event.label} (신뢰도: {event.score:.2%})")
    
    # WebSocket으로 브라우저에 실시간 전달
    websocket_message = {
        "type": "fire_detection",
        "ts": event.ts,
        "source": event.source,
        "label": event.label,
        "score": event.score,
        "bbox": event.bbox,
        "frame_size": event.frame_size
    }
    
    await manager.broadcast(websocket_message)
    
    return {
        "ok": True,
        "received_at": datetime.now().isoformat()
    }

@app.post("/stream/video")
async def receive_video_stream(
    stream: VideoStream,
    x_api_key: Optional[str] = Header(default=None)
):
    """
    오렌지파이에서 비디오 스트림 수신
    
    Base64로 인코딩된 카메라 영상을 실시간으로 수신하여
    WebSocket으로 브라우저에 전달
    """
    global LATEST_VIDEO_STREAM
    
    # API Key 검증 (선택적)
    API_KEY = "supersecret_key_please_change_me"
    if x_api_key and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # 스트림 저장
    stream_data = stream.dict()
    LATEST_VIDEO_STREAM = stream_data
    
    print(f"📹 비디오 스트림 수신: {stream.source} ({stream.width}x{stream.height})")
    
    # WebSocket으로 브라우저에 실시간 전달
    websocket_message = {
        "type": "video_stream",
        "source": stream.source,
        "timestamp": stream.ts,
        "frame": stream.frame,
        "width": stream.width,
        "height": stream.height
    }
    
    await manager.broadcast(websocket_message)
    
    return {
        "ok": True,
        "received_at": datetime.now().isoformat()
    }

@app.get("/events/fire/latest")
async def get_latest_fire_event():
    """최신 화재 감지 이벤트 조회"""
    if LATEST_FIRE_EVENT:
        return LATEST_FIRE_EVENT
    return {"message": "No fire event received yet"}

@app.get("/events/fire/history")
async def get_fire_history():
    """화재 이벤트 히스토리 조회"""
    return {
        "total": len(FIRE_EVENTS),
        "events": FIRE_EVENTS
    }

@app.get("/stream/video/latest")
async def get_latest_video_stream():
    """최신 비디오 스트림 조회"""
    if LATEST_VIDEO_STREAM:
        return LATEST_VIDEO_STREAM
    return {"message": "No video stream received yet"}

# ============================================
# �🔔 라즈베리파이 부저 트리거 API
# ============================================

@app.post("/api/buzzer/trigger")
async def trigger_buzzer(trigger: BuzzerTrigger):
    """
    라즈베리파이 부저를 울리는 명령을 WebSocket으로 전달
    
    화재/연기 감지 시 프론트엔드가 이 API를 호출하면
    WebSocket을 통해 라즈베리파이에게 부저 울림 명령 전달
    """
    message = {
        "type": "buzzer_trigger",
        "zone": trigger.zone,
        "reason": trigger.reason,
        "duration": trigger.duration,
        "timestamp": datetime.now().isoformat()
    }
    
    # 모든 WebSocket 연결(라즈베리파이 포함)에게 브로드캐스트
    await manager.broadcast(message)
    
    return {
        "status": "success",
        "message": f"부저 트리거 명령 전송 완료 ({trigger.zone})",
        "data": message
    }

# ============================================
# 헬스 체크 및 루트
# ============================================

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_devices": len(LATEST),
        "websocket_connections": len(manager.active_connections),
        "total_data_points": sum(len(h) for h in HISTORY.values())
    }

@app.get("/")
async def root():
    """루트 경로 - API 정보"""
    return {
        "message": "PRISM Sensor API with WebSocket",
        "version": "3.0.0",
        "docs": "/docs",
        "architecture": {
            "data_flow": "IoT Devices → /ingest (HTTP POST) → FastAPI → /ws (WebSocket) → Web Browser",
            "endpoints": {
                "ingest": "POST /ingest - 데이터 수집",
                "websocket": "WS /ws - 실시간 스트림",
                "latest": "GET /latest - 최신 데이터",
                "history": "GET /history/{device_id} - 히스토리"
            }
        },
        "connected_devices": len(LATEST),
        "websocket_clients": len(manager.active_connections)
    }

# ============================================
# 서버 실행 (삭제된 중복 코드 정리)
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    print("=" * 70)
    print("🚀 PRISM FastAPI 서버 시작 (WebSocket 지원)")
    print("=" * 70)
    print(f"📡 HTTP 서버: http://0.0.0.0:{port}")
    print(f"🔌 WebSocket: ws://0.0.0.0:{port}/ws")
    print(f"📚 API 문서: http://localhost:{port}/docs")
    print("=" * 70)
    print("")
    print("💡 시스템 아키텍처:")
    print("   [라즈베리 파이]  [오렌지 파이]")
    print("          │              │")
    print("          └──────┬───────┘")
    print("                 ▼")
    print("          [FastAPI 서버]")
    print("         (HTTP + WebSocket)")
    print("                 │")
    print("                 ▼")
    print("          [웹 브라우저]")
    print("       (실시간 대시보드)")
    print("")
    print("📌 데이터 전송 방법:")
    print(f"   curl -X POST http://localhost:{port}/ingest \\")
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"device_id":"rpi-01","data":{"temp":25.5,"hum":60}}\'')
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
