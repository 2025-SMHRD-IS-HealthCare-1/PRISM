"""
테스트용 데이터 전송 스크립트
FastAPI 서버로 더미 데이터를 전송하여 WebSocket 동작 확인
"""

import requests
import time
import random
from datetime import datetime
import os

# 설정 (환경 변수 또는 기본값 사용)
#API_SERVER = os.getenv("API_SERVER", "https://prism-api-ay8q.onrender.com")
API_SERVER = os.getenv("API_SERVER", "https://prism-api-qnxu.onrender.com")
DEVICES = ["rpi-01", "opi-01", "test-device"]

def send_random_data(device_id):
    """랜덤 센서 데이터 생성 및 전송"""
    data = {
        "device_id": device_id,
        "data": {
            "temperature": round(20 + random.uniform(0, 15), 2),
            "gas": round(10 + random.uniform(0, 50), 2),
            "dust": round(5 + random.uniform(0, 20), 2),
            "humidity": round(40 + random.uniform(0, 30), 2),
            "flame": random.random() > 0.95
        },
        "ts": datetime.now().timestamp()
    }
    
    try:
        response = requests.post(f"{API_SERVER}/ingest", json=data, timeout=5)
        if response.status_code == 200:
            print(f"✓ [{device_id}] 데이터 전송 성공")
            return True
        else:
            print(f"✗ [{device_id}] 전송 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ [{device_id}] 오류: {e}")
        return False

def main():
    print("=" * 70)
    print("🧪 PRISM WebSocket 테스트 - 더미 데이터 전송")
    print("=" * 70)
    print(f"📡 서버: {API_SERVER}")
    print(f"🖥️  디바이스: {', '.join(DEVICES)}")
    print("=" * 70)
    print("")
    
    # 서버 연결 확인
    try:
        response = requests.get(f"{API_SERVER}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 서버 연결 확인")
            health = response.json()
            print(f"   활성 장치: {health.get('active_devices', 0)}")
            print(f"   WebSocket 연결: {health.get('websocket_connections', 0)}")
        else:
            print(f"⚠️ 서버 응답 이상: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ 연결 실패: FastAPI 서버가 실행되지 않았습니다")
        print("   FastAPI 서버를 먼저 실행하세요: python server/api_server.py")
        return
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return
    
    print("")
    print("📊 데이터 전송 시작... (Ctrl+C로 종료)")
    print("-" * 70)
    print("")
    
    try:
        counter = 0
        while True:
            counter += 1
            print(f"\n[전송 #{counter}] {datetime.now().strftime('%H:%M:%S')}")
            
            # 각 디바이스에서 데이터 전송
            for device_id in DEVICES:
                send_random_data(device_id)
            
            # 5초 대기
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("")
        print("=" * 70)
        print("🛑 테스트 종료")
        print("=" * 70)

if __name__ == "__main__":
    main()
