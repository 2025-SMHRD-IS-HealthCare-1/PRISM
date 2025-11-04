"""
PRISM 센서 데이터 FastAPI 서버
라즈베리파이/오렌지파이에서 센서 데이터를 받아 웹 대시보드로 전달
SSH를 통한 원격 장치 관리 기능 포함
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import random
import asyncio
import os

app = FastAPI(
    title="PRISM Sensor API", 
    version="2.0.0",
    description="IoT 센서 데이터 수집 및 관리 API"
)

# CORS 설정 (Express 서버와 통신)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영시에는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# 데이터 모델
# ============================================

class SensorData(BaseModel):
    zone: str
    temperature: float
    gas: float
    dust: float
    flame: bool
    timestamp: Optional[datetime] = None

class HistoricalData(BaseModel):
    timestamp: datetime
    temperature: float
    gas: float
    dust: float

class DeviceInfo(BaseModel):
    device_id: str
    device_type: str  # raspberry_pi, orange_pi
    ip_address: str
    status: str  # online, offline
    last_seen: datetime
    zone: str

class SSHCommand(BaseModel):
    command: str

# ============================================
# 인메모리 데이터 저장
# ============================================

sensor_data_store: Dict[str, SensorData] = {}
historical_data_store: Dict[str, List[Dict]] = {}
device_info_store: Dict[str, DeviceInfo] = {
    "raspberry_pi_01": DeviceInfo(
        device_id="raspberry_pi_01",
        device_type="raspberry_pi",
        ip_address="192.168.1.100",
        status="online",
        last_seen=datetime.now(),
        zone="testbox"
    ),
    "orange_pi_01": DeviceInfo(
        device_id="orange_pi_01",
        device_type="orange_pi",
        ip_address="192.168.1.101",
        status="offline",
        last_seen=datetime.now() - timedelta(hours=1),
        zone="warehouse"
    )
}

# ============================================
# 센서 데이터 엔드포인트
# ============================================

@app.post("/api/sensors/{zone}")
async def update_sensor_data(zone: str, data: SensorData):
    """
    라즈베리파이/오렌지파이에서 센서 데이터를 전송하는 엔드포인트
    Express 서버를 통해 또는 직접 호출 가능
    """
    data.zone = zone
    data.timestamp = datetime.now()
    
    print(f"📊 센서 데이터 수신 [{zone}]: 온도={data.temperature}°C, 가스={data.gas}ppm, 먼지={data.dust}μg/m³")
    
    # 현재 데이터 저장
    sensor_data_store[zone] = data
    
    # 히스토리 데이터 저장
    if zone not in historical_data_store:
        historical_data_store[zone] = []
    
    historical_data_store[zone].append({
        "timestamp": data.timestamp,
        "temperature": data.temperature,
        "gas": data.gas,
        "dust": data.dust
    })
    
    # 최근 24시간 데이터만 유지
    cutoff_time = datetime.now() - timedelta(hours=24)
    historical_data_store[zone] = [
        d for d in historical_data_store[zone]
        if d["timestamp"] > cutoff_time
    ]
    
    # 임계값 체크 및 경고
    if data.flame:
        print(f"⚠️  [위험] {zone} - 불꽃 감지!")
    if data.temperature > 50:
        print(f"⚠️  [위험] {zone} - 온도 위험 수준: {data.temperature}°C")
    if data.gas > 100:
        print(f"⚠️  [위험] {zone} - 가스 농도 위험: {data.gas}ppm")
    
    return {"status": "success", "message": "센서 데이터가 업데이트되었습니다", "zone": zone}

@app.get("/api/sensors/{zone}")
async def get_sensor_data(zone: str):
    """
    웹 대시보드에서 현재 센서 데이터를 가져오는 엔드포인트
    실제 연결된 센서가 없으면 404 에러 반환 (더미 데이터 제거)
    """
    if zone not in sensor_data_store:
        # 센서가 연결되지 않은 경우 404 에러 반환
        raise HTTPException(status_code=404, detail=f"센서 데이터를 찾을 수 없습니다. 구역: {zone}")
    
    data = sensor_data_store[zone]
    return {
        "zone": data.zone,
        "temperature": data.temperature,
        "gas": data.gas,
        "dust": data.dust,
        "flame": data.flame,
        "timestamp": data.timestamp.isoformat(),
        "connected": True
    }

@app.get("/api/history/{zone}")
async def get_historical_data(zone: str, hours: int = 24, days: int = None):
    """
    지정된 시간 동안의 과거 센서 데이터를 가져오는 엔드포인트
    실제 데이터가 없으면 빈 배열 반환 (더미 데이터 제거)
    """
    if days:
        hours = days * 24  # 일 단위를 시간으로 변환
    
    if zone not in historical_data_store or len(historical_data_store[zone]) == 0:
        # 데이터가 없으면 빈 배열 반환
        return []
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    filtered_data = [
        {
            "timestamp": d["timestamp"].isoformat(),
            "temperature": d["temperature"],
            "gas": d["gas"],
            "dust": d["dust"]
        }
        for d in historical_data_store[zone]
        if d["timestamp"] > cutoff_time
    ]
    
    return filtered_data

# ============================================
# 장치 관리 엔드포인트
# ============================================

@app.get("/api/devices")
async def get_devices():
    """
    모든 연결된 장치(라즈베리파이/오렌지파이) 목록 조회
    """
    devices = []
    for device_id, device in device_info_store.items():
        # 마지막 연결 시간 기준으로 온라인/오프라인 판단
        time_diff = datetime.now() - device.last_seen
        is_online = time_diff.total_seconds() < 300  # 5분 이내
        
        devices.append({
            "device_id": device.device_id,
            "device_type": device.device_type,
            "ip_address": device.ip_address,
            "status": "online" if is_online else "offline",
            "last_seen": device.last_seen.isoformat(),
            "zone": device.zone
        })
    
    return devices

@app.get("/api/device/{device_id}")
async def get_device_info(device_id: str):
    """
    특정 장치 정보 조회
    """
    if device_id not in device_info_store:
        raise HTTPException(status_code=404, detail="장치를 찾을 수 없습니다")
    
    device = device_info_store[device_id]
    time_diff = datetime.now() - device.last_seen
    is_online = time_diff.total_seconds() < 300
    
    return {
        "device_id": device.device_id,
        "device_type": device.device_type,
        "ip_address": device.ip_address,
        "status": "online" if is_online else "offline",
        "last_seen": device.last_seen.isoformat(),
        "zone": device.zone
    }

@app.post("/api/device/{device_id}/command")
async def execute_ssh_command(device_id: str, command_data: SSHCommand):
    """
    SSH를 통해 라즈베리파이/오렌지파이에 명령 실행
    실제 구현시 paramiko 또는 asyncssh 라이브러리 사용
    """
    if device_id not in device_info_store:
        raise HTTPException(status_code=404, detail="장치를 찾을 수 없습니다")
    
    device = device_info_store[device_id]
    
    print(f"🔧 SSH 명령 실행 요청 [{device_id}]: {command_data.command}")
    
    # 실제 SSH 명령 실행 (예제)
    # import paramiko
    # ssh = paramiko.SSHClient()
    # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh.connect(device.ip_address, username='pi', password='raspberry')
    # stdin, stdout, stderr = ssh.exec_command(command_data.command)
    # output = stdout.read().decode()
    # ssh.close()
    
    # 테스트용 더미 응답
    return {
        "status": "success",
        "device_id": device_id,
        "command": command_data.command,
        "output": f"명령 실행 완료 (시뮬레이션)\n{command_data.command}",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/device/{device_id}/heartbeat")
async def device_heartbeat(device_id: str):
    """
    장치 하트비트 (연결 상태 갱신)
    라즈베리파이/오렌지파이에서 주기적으로 호출
    """
    if device_id in device_info_store:
        device_info_store[device_id].last_seen = datetime.now()
        device_info_store[device_id].status = "online"
    else:
        # 새로운 장치 등록 (자동 발견)
        device_info_store[device_id] = DeviceInfo(
            device_id=device_id,
            device_type="unknown",
            ip_address="0.0.0.0",
            status="online",
            last_seen=datetime.now(),
            zone="unknown"
        )
    
    return {"status": "ok", "device_id": device_id}

# ============================================
# CCTV 관련 엔드포인트
# ============================================

@app.get("/api/cctv/{zone}/stream")
async def get_cctv_stream(zone: str):
    """
    CCTV 스트림을 제공하는 엔드포인트
    실제로는 IP 카메라 또는 라즈베리파이 카메라 모듈과 연동
    """
    # 실제 구현시 카메라 스트림 반환
    raise HTTPException(status_code=503, detail="CCTV 스트림이 연결되지 않았습니다")

# ============================================
# 구역 관리 엔드포인트
# ============================================

@app.get("/api/zones")
async def get_zones():
    """
    모든 구역 목록과 상태를 반환
    """
    zones = [
        {
            "id": "testbox",
            "name": "TEST BOX",
            "active": True,
            "status": "normal",
            "has_data": "testbox" in sensor_data_store
        },
        {
            "id": "warehouse",
            "name": "원자재 창고",
            "active": False,
            "status": "inactive",
            "has_data": "warehouse" in sensor_data_store
        },
        {
            "id": "inspection",
            "name": "제품 검사실",
            "active": False,
            "status": "inactive",
            "has_data": "inspection" in sensor_data_store
        },
        {
            "id": "machine",
            "name": "기계/전기실",
            "active": False,
            "status": "inactive",
            "has_data": "machine" in sensor_data_store
        }
    ]
    
    return zones

# ============================================
# 헬스 체크
# ============================================

@app.get("/health")
async def health_check():
    """
    서버 상태 확인
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_zones": len(sensor_data_store),
        "total_devices": len(device_info_store),
        "online_devices": sum(1 for d in device_info_store.values() 
                            if (datetime.now() - d.last_seen).total_seconds() < 300)
    }

@app.get("/")
async def root():
    """
    루트 경로
    """
    return {
        "message": "PRISM Sensor API",
        "version": "2.0.0",
        "docs": "/docs",
        "architecture": "Frontend(Vercel) → Express(Node.js) → FastAPI(Python) ← IoT Devices(SSH)"
    }

# ============================================
# 서버 시작
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    print("=" * 60)
    print("🚀 PRISM FastAPI 서버 시작")
    print("=" * 60)
    print(f"📡 서버 주소: http://0.0.0.0:{port}")
    print(f"📚 API 문서: http://localhost:{port}/docs")
    print("=" * 60)
    print("")
    print("💡 시스템 아키텍처:")
    print("   프론트엔드(Vercel) → Express → FastAPI")
    print("   라즈베리파이/오렌지파이 → FastAPI (JSON/SSH)")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=port)

# CORS 설정 (프론트엔드에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영시에는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터 모델
class SensorData(BaseModel):
    zone: str
    temperature: float
    gas: float
    dust: float
    flame: bool
    timestamp: datetime

class HistoricalData(BaseModel):
    timestamp: datetime
    temperature: float
    gas: float
    dust: float

# 인메모리 데이터 저장 (실제로는 데이터베이스 사용 권장)
sensor_data_store = {}
historical_data_store = {}

# 라즈베리파이에서 센서 데이터 받기 (POST)
@app.post("/api/sensors/{zone}")
async def update_sensor_data(zone: str, data: SensorData):
    """
    라즈베리파이에서 센서 데이터를 전송하는 엔드포인트
    """
    data.zone = zone
    data.timestamp = datetime.now()
    
    # 현재 데이터 저장
    sensor_data_store[zone] = data
    
    # 히스토리 데이터 저장
    if zone not in historical_data_store:
        historical_data_store[zone] = []
    
    historical_data_store[zone].append({
        "timestamp": data.timestamp,
        "temperature": data.temperature,
        "gas": data.gas,
        "dust": data.dust
    })
    
    # 최근 24시간 데이터만 유지
    cutoff_time = datetime.now() - timedelta(hours=24)
    historical_data_store[zone] = [
        d for d in historical_data_store[zone]
        if d["timestamp"] > cutoff_time
    ]
    
    return {"status": "success", "message": "센서 데이터가 업데이트되었습니다"}

# 중복된 엔드포인트 제거됨 - 위쪽의 get_sensor_data 사용

# 중복된 엔드포인트 제거됨 - 위쪽의 get_historical_data 사용

# CCTV 스트림 (예제)
@app.get("/api/cctv/{zone}/stream")
async def get_cctv_stream(zone: str):
    """
    CCTV 스트림을 제공하는 엔드포인트
    실제로는 IP 카메라 또는 라즈베리파이 카메라 모듈과 연동
    """
    # 실제 구현시 카메라 스트림 반환
    # 현재는 플레이스홀더
    raise HTTPException(status_code=503, detail="CCTV 스트림이 연결되지 않았습니다")

# 모든 구역 목록
@app.get("/api/zones")
async def get_zones():
    """
    모든 구역 목록과 상태를 반환
    """
    zones = [
        {
            "id": "testbox",
            "name": "TEST BOX",
            "active": True,
            "status": "normal"
        },
        {
            "id": "warehouse",
            "name": "원자재 창고",
            "active": False,
            "status": "inactive"
        },
        {
            "id": "inspection",
            "name": "제품 검사실",
            "active": False,
            "status": "inactive"
        },
        {
            "id": "machine",
            "name": "기계/전기실",
            "active": False,
            "status": "inactive"
        }
    ]
    
    return zones

# 헬스 체크
@app.get("/health")
async def health_check():
    """
    서버 상태 확인
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_zones": len(sensor_data_store)
    }

# 루트 경로
@app.get("/")
async def root():
    return {
        "message": "PRISM Sensor API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
