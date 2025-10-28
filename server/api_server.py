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

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
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

# ============================================
# 인메모리 데이터 저장
# ============================================

# 각 디바이스의 최신 데이터 저장 {device_id: data}
LATEST: Dict[str, Dict[str, Any]] = {}

# 히스토리 데이터 저장 {device_id: [data, data, ...]}
HISTORY: Dict[str, List[Dict[str, Any]]] = {}

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
    
    # 데이터 저장
    stored_data = {
        "device_id": device_id,
        "data": data.data,
        "timestamp": timestamp,
        "datetime": datetime.fromtimestamp(timestamp).isoformat()
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
    print(f"📊 [{device_id}] 데이터 수신: {data.data}")
    
    # 🔥 WebSocket으로 모든 연결된 브라우저에게 실시간 전송
    await manager.broadcast({
        "type": "update",
        "device_id": device_id,
        "data": data.data,
        "timestamp": datetime.fromtimestamp(timestamp).isoformat()
    })
    
    return {
        "status": "success",
        "device_id": device_id,
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
