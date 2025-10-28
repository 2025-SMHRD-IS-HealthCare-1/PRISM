"""
라즈베리파이/오렌지파이용 로컬 FastAPI 서버
센서 데이터를 읽고 로컬에서 API로 제공하며, 주기적으로 Render 서버로 전송

사용법:
    python iot_devices/raspberry_pi_api.py
    
엔드포인트:
    GET /health - 서버 상태 확인
    GET /sensors - 현재 센서 데이터 조회
    GET /snapshot - 센서 스냅샷 파일 조회
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import time
import threading
import requests
from datetime import datetime
import random

# ============================================
# 설정
# ============================================

APP_NAME = "prism-raspberry-pi-sensor-api"
SNAPSHOT = "/tmp/prism_sensors.json"  # 센서 데이터 스냅샷 파일
STALE_SEC = 10  # 10초 이상 갱신 없으면 오래된 데이터로 간주

# 환경 변수 또는 기본값
DEVICE_ID = os.getenv("DEVICE_ID", "rpi-01")
RENDER_SERVER = os.getenv("API_SERVER", "https://prism-api-ay8q.onrender.com")
SENSOR_READ_INTERVAL = 5  # 5초마다 센서 읽기
SEND_TO_CLOUD_INTERVAL = 5  # 5초마다 클라우드로 전송

app = FastAPI(title=APP_NAME, version="1.0.0")

# CORS 설정 (필요시 도메인 제한)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# 센서 데이터 읽기 함수 (하드웨어 연동)
# ============================================

def read_temperature_sensor():
    """온도 센서 읽기 (실제 하드웨어 연동 필요)"""
    # 테스트용 더미 데이터
    return round(20 + random.uniform(0, 15), 2)


def read_gas_sensor():
    """가스 센서 읽기 (실제 하드웨어 연동 필요)"""
    return round(10 + random.uniform(0, 50), 2)


def read_dust_sensor():
    """미세먼지 센서 읽기 (실제 하드웨어 연동 필요)"""
    return round(5 + random.uniform(0, 20), 2)


def read_humidity_sensor():
    """습도 센서 읽기 (실제 하드웨어 연동 필요)"""
    return round(40 + random.uniform(0, 30), 2)


def read_flame_sensor():
    """불꽃 감지 센서 읽기 (실제 하드웨어 연동 필요)"""
    return random.random() > 0.95


def collect_sensor_data():
    """모든 센서 데이터 수집"""
    return {
        "temperature": read_temperature_sensor(),
        "gas": read_gas_sensor(),
        "dust": read_dust_sensor(),
        "humidity": read_humidity_sensor(),
        "flame": read_flame_sensor(),
    }


# ============================================
# 센서 데이터 스냅샷 관리
# ============================================

def update_snapshot():
    """센서 데이터를 읽어서 스냅샷 파일에 저장"""
    while True:
        try:
            sensor_data = collect_sensor_data()
            snapshot_data = {
                "device_id": DEVICE_ID,
                "data": sensor_data,
                "timestamp": time.time(),
                "datetime": datetime.now().isoformat(),
            }
            
            # 스냅샷 파일에 저장
            with open(SNAPSHOT, "w", encoding="utf-8") as f:
                json.dump(snapshot_data, f, indent=2)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 센서 데이터 업데이트: {sensor_data}")
            
        except Exception as e:
            print(f"❌ 센서 데이터 수집 오류: {e}")
        
        time.sleep(SENSOR_READ_INTERVAL)


def send_to_cloud():
    """주기적으로 Render 서버로 데이터 전송"""
    while True:
        try:
            # 스냅샷 파일 읽기
            if not os.path.exists(SNAPSHOT):
                print("⏳ 스냅샷 파일 대기 중...")
                time.sleep(SEND_TO_CLOUD_INTERVAL)
                continue
            
            with open(SNAPSHOT, "r", encoding="utf-8") as f:
                snapshot_data = json.load(f)
            
            # Render 서버로 전송
            payload = {
                "device_id": snapshot_data["device_id"],
                "data": snapshot_data["data"],
                "ts": snapshot_data["timestamp"],
            }
            
            response = requests.post(
                f"{RENDER_SERVER}/ingest",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✓ [{datetime.now().strftime('%H:%M:%S')}] 클라우드 전송 성공")
            else:
                print(f"⚠️ 클라우드 전송 실패: {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            print(f"❌ 클라우드 서버 연결 실패 (오프라인 모드)")
        except Exception as e:
            print(f"❌ 클라우드 전송 오류: {e}")
        
        time.sleep(SEND_TO_CLOUD_INTERVAL)


# ============================================
# FastAPI 엔드포인트
# ============================================

@app.get("/health")
def health():
    """서버 헬스 체크"""
    snapshot_exists = os.path.exists(SNAPSHOT)
    snapshot_age = None
    
    if snapshot_exists:
        mtime = os.path.getmtime(SNAPSHOT)
        snapshot_age = time.time() - mtime
    
    return {
        "ok": True,
        "device_id": DEVICE_ID,
        "timestamp": time.time(),
        "snapshot_exists": snapshot_exists,
        "snapshot_age_sec": snapshot_age,
        "cloud_server": RENDER_SERVER,
    }


@app.get("/sensors")
def get_sensors():
    """현재 센서 데이터 조회"""
    if not os.path.exists(SNAPSHOT):
        raise HTTPException(
            status_code=503,
            detail="센서 데이터가 아직 준비되지 않았습니다. 잠시 후 다시 시도하세요."
        )
    
    try:
        # 파일 수정 시간 확인
        mtime = os.path.getmtime(SNAPSHOT)
        age = time.time() - mtime
        
        if age > STALE_SEC:
            raise HTTPException(
                status_code=503,
                detail=f"센서 데이터가 오래되었습니다 ({age:.1f}초 전). 센서 프로세스를 확인하세요."
            )
        
        # 스냅샷 파일 읽기
        with open(SNAPSHOT, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return JSONResponse(data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"센서 데이터 읽기 오류: {str(e)}")


@app.get("/snapshot")
def get_snapshot():
    """센서 스냅샷 파일 내용 조회 (디버깅용)"""
    if not os.path.exists(SNAPSHOT):
        raise HTTPException(status_code=404, detail="스냅샷 파일이 없습니다")
    
    try:
        with open(SNAPSHOT, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 파일 메타데이터 추가
        mtime = os.path.getmtime(SNAPSHOT)
        data["_metadata"] = {
            "file_path": SNAPSHOT,
            "last_modified": mtime,
            "age_seconds": time.time() - mtime,
        }
        
        return JSONResponse(data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 서버 시작
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    
    print("=" * 70)
    print("🚀 PRISM 라즈베리파이 센서 API 서버")
    print("=" * 70)
    print(f"📡 로컬 서버: http://0.0.0.0:{port}")
    print(f"🔗 클라우드 서버: {RENDER_SERVER}")
    print(f"🖥️  디바이스 ID: {DEVICE_ID}")
    print(f"📊 센서 읽기 주기: {SENSOR_READ_INTERVAL}초")
    print(f"☁️  클라우드 전송 주기: {SEND_TO_CLOUD_INTERVAL}초")
    print(f"📁 스냅샷 파일: {SNAPSHOT}")
    print("=" * 70)
    print("")
    
    # 백그라운드 스레드 시작
    print("🔧 센서 데이터 수집 스레드 시작...")
    sensor_thread = threading.Thread(target=update_snapshot, daemon=True)
    sensor_thread.start()
    
    print("☁️  클라우드 전송 스레드 시작...")
    cloud_thread = threading.Thread(target=send_to_cloud, daemon=True)
    cloud_thread.start()
    
    print("")
    print("✅ 서버 시작 준비 완료!")
    print(f"   • GET http://localhost:{port}/health - 헬스 체크")
    print(f"   • GET http://localhost:{port}/sensors - 센서 데이터 조회")
    print(f"   • GET http://localhost:{port}/snapshot - 스냅샷 파일 조회")
    print("")
    
    # FastAPI 서버 실행
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
