"""
PRISM 센서 데이터 FastAPI 서버
라즈베리파이에서 센서 데이터를 받아 웹 대시보드로 전달
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
import random
import asyncio

app = FastAPI(title="PRISM Sensor API", version="1.0.0")

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

# 웹 대시보드에서 센서 데이터 가져오기 (GET)
@app.get("/api/sensors/{zone}")
async def get_sensor_data(zone: str):
    """
    웹 대시보드에서 현재 센서 데이터를 가져오는 엔드포인트
    """
    if zone not in sensor_data_store:
        # 데이터가 없으면 더미 데이터 반환 (테스트용)
        return {
            "zone": zone,
            "temperature": round(20 + random.uniform(0, 15), 1),
            "gas": round(10 + random.uniform(0, 50), 1),
            "dust": round(5 + random.uniform(0, 20), 2),
            "flame": random.random() > 0.95,
            "timestamp": datetime.now().isoformat()
        }
    
    data = sensor_data_store[zone]
    return {
        "zone": data.zone,
        "temperature": data.temperature,
        "gas": data.gas,
        "dust": data.dust,
        "flame": data.flame,
        "timestamp": data.timestamp.isoformat()
    }

# 과거 데이터 가져오기
@app.get("/api/history/{zone}")
async def get_historical_data(zone: str, hours: int = 24):
    """
    지정된 시간 동안의 과거 센서 데이터를 가져오는 엔드포인트
    """
    if zone not in historical_data_store:
        # 더미 데이터 생성 (테스트용)
        now = datetime.now()
        dummy_data = []
        
        for i in range(hours):
            timestamp = now - timedelta(hours=hours-i)
            dummy_data.append({
                "timestamp": timestamp.isoformat(),
                "temperature": round(20 + random.uniform(0, 15), 1),
                "gas": round(10 + random.uniform(0, 50), 1),
                "dust": round(5 + random.uniform(0, 20), 2)
            })
        
        return dummy_data
    
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
