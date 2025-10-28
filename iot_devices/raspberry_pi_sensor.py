"""
라즈베리파이/오렌지파이 센서 데이터 수집 및 전송
FastAPI 서버의 /ingest 엔드포인트로 데이터 전송

🔥 새로운 구조:
- HTTP POST로 /ingest 엔드포인트에 데이터 전송
- FastAPI 서버가 WebSocket으로 브라우저에 실시간 전달
- WebSocket으로 부저 트리거 명령 수신
"""

import requests
import time
import json
import os
import socket
import threading
from datetime import datetime

try:
    import websocket  # pip install websocket-client
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("⚠️  websocket-client가 설치되지 않았습니다. 부저 기능이 비활성화됩니다.")
    print("   설치: pip install websocket-client")

# ============================================
# 설정
# ============================================

# FastAPI 서버 주소 (환경 변수로 설정 가능)
API_SERVER = os.getenv("API_SERVER", "http://localhost:8000")  # FastAPI 서버 IP로 변경
DEVICE_ID = os.getenv("DEVICE_ID", "rpi-01")  # 장치 ID: rpi-01, opi-01 등

SEND_INTERVAL = 5  # 5초마다 데이터 전송

# 부저 GPIO 핀 (실제 센서 사용시 설정)
BUZZER_PIN = 18  # GPIO 18번 핀

# ============================================
# 센서 초기화 (실제 센서 사용시 주석 해제)
# ============================================

# 라즈베리파이 GPIO 설정
# import RPi.GPIO as GPIO
# import Adafruit_DHT  # 온도/습도 센서
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(BUZZER_PIN, GPIO.OUT)
# GPIO.output(BUZZER_PIN, GPIO.LOW)

# 오렌지파이 GPIO 설정
# import OPi.GPIO as GPIO
# GPIO.setmode(GPIO.BOARD)

# ============================================
# 센서 읽기 함수
# ============================================

def read_temperature_sensor():
    """
    온도 센서에서 데이터 읽기
    예: DHT22 센서 사용
    
    실제 센서 코드 예제:
    sensor = Adafruit_DHT.DHT22
    pin = 4
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    return temperature if temperature is not None else 0
    """
    # 테스트용 더미 데이터
    import random
    return round(20 + random.uniform(0, 15), 1)

def read_gas_sensor():
    """
    가스 센서에서 데이터 읽기
    예: MQ-2, MQ-135 센서 사용 (ADC 필요)
    
    실제 센서 코드 예제:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c)
    chan = AnalogIn(ads, ADS.P0)
    voltage = chan.voltage
    ppm = voltage * 100  # 실제 변환 공식 필요
    return ppm
    """
    # 테스트용 더미 데이터
    import random
    return round(10 + random.uniform(0, 50), 1)

def read_dust_sensor():
    """
    미세먼지 센서에서 데이터 읽기
    예: GP2Y1010AU0F, PMS5003 센서 사용
    
    실제 센서 코드 예제:
    import serial
    ser = serial.Serial('/dev/ttyUSB0', 9600)
    data = ser.read(32)
    # 데이터 파싱
    pm25 = (data[6] * 256 + data[7]) / 10.0
    return pm25
    """
    # 테스트용 더미 데이터
    import random
    return round(5 + random.uniform(0, 20), 2)

def read_flame_sensor():
    """
    불꽃 감지 센서에서 데이터 읽기
    예: KY-026 Flame Sensor 사용
    
    실제 센서 코드 예제:
    GPIO.setmode(GPIO.BCM)
    FLAME_PIN = 17
    GPIO.setup(FLAME_PIN, GPIO.IN)
    flame_detected = GPIO.input(FLAME_PIN) == GPIO.LOW
    return flame_detected
    """
    # 테스트용 더미 데이터
    import random
    return random.random() > 0.95

# ============================================
# 🔔 부저 제어 함수
# ============================================

def trigger_buzzer(duration_ms=3000):
    """
    부저를 울립니다
    
    실제 GPIO 코드 (주석 해제):
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(duration_ms / 1000.0)
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    """
    print(f"🔔 부저 울림! ({duration_ms}ms)")
    # 실제 구현 시 아래 주석 해제
    # GPIO.output(BUZZER_PIN, GPIO.HIGH)
    # time.sleep(duration_ms / 1000.0)
    # GPIO.output(BUZZER_PIN, GPIO.LOW)

# ============================================
# WebSocket 리스너 (부저 트리거 명령 수신)
# ============================================

def on_websocket_message(ws, message):
    """WebSocket 메시지 수신 콜백"""
    try:
        data = json.loads(message)
        
        # 부저 트리거 명령 확인
        if data.get("type") == "buzzer_trigger":
            reason = data.get("reason", "unknown")
            duration = data.get("duration", 3000)
            
            print(f"🔔 부저 트리거 명령 수신: {reason}")
            trigger_buzzer(duration)
            
    except json.JSONDecodeError:
        print(f"⚠️  WebSocket 메시지 파싱 실패: {message}")
    except Exception as e:
        print(f"❌ WebSocket 메시지 처리 오류: {e}")

def on_websocket_error(ws, error):
    """WebSocket 오류 콜백"""
    print(f"❌ WebSocket 오류: {error}")

def on_websocket_close(ws, close_status_code, close_msg):
    """WebSocket 연결 종료 콜백"""
    print("🔌 WebSocket 연결 종료. 5초 후 재연결...")
    time.sleep(5)
    start_websocket_listener()

def on_websocket_open(ws):
    """WebSocket 연결 성공 콜백"""
    print("✅ WebSocket 연결 성공 (부저 리스너 활성화)")

def start_websocket_listener():
    """WebSocket 리스너 시작 (별도 스레드)"""
    if not WEBSOCKET_AVAILABLE:
        return
    
    try:
        ws_url = API_SERVER.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
        
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_websocket_open,
            on_message=on_websocket_message,
            on_error=on_websocket_error,
            on_close=on_websocket_close
        )
        
        # 별도 스레드에서 실행
        ws_thread = threading.Thread(target=ws.run_forever, daemon=True)
        ws_thread.start()
        
    except Exception as e:
        print(f"❌ WebSocket 리스너 시작 실패: {e}")

# ============================================
# 데이터 수집 및 전송
# ============================================

def collect_sensor_data():
    """
    모든 센서에서 데이터 수집
    """
    data = {
        "temperature": read_temperature_sensor(),
        "gas": read_gas_sensor(),
        "dust": read_dust_sensor(),
        "flame": read_flame_sensor(),
        "humidity": 55.0 + (hash(str(datetime.now())) % 20),  # 예시 데이터
    }
    return data

def send_data_to_server(data):
    """
    센서 데이터를 FastAPI 서버의 /ingest 엔드포인트로 전송
    """
    try:
        url = f"{API_SERVER}/ingest"
        
        # 새로운 형식으로 데이터 구성
        payload = {
            "device_id": DEVICE_ID,
            "data": data,
            "ts": datetime.now().timestamp()
        }
        
        response = requests.post(url, json=payload, timeout=5)
        
        if response.status_code == 200:
            print(f"✓ 데이터 전송 성공: {datetime.now().strftime('%H:%M:%S')}")
            print(f"  장치 ID: {DEVICE_ID}")
            print(f"  온도: {data.get('temperature', 0)}°C")
            print(f"  가스: {data.get('gas', 0)} ppm")
            print(f"  미세먼지: {data.get('dust', 0)} μg/m³")
            print(f"  불꽃: {'감지됨!' if data.get('flame', False) else '미감지'}")
            print("-" * 50)
            return True
        else:
            print(f"✗ 전송 실패: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ 연결 오류: {e}")
        return False

def send_heartbeat():
    """
    서버에 하트비트 전송 (장치 연결 상태 유지)
    새 구조에서는 데이터 자체가 heartbeat 역할을 함
    """
    # 별도 heartbeat 엔드포인트는 선택사항
    pass

def get_local_ip():
    """
    로컬 IP 주소 가져오기
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Unknown"

# ============================================
# 메인 루프
# ============================================

def main():
    """
    메인 루프: 주기적으로 센서 데이터 수집 및 전송
    """
    print("=" * 70)
    print("🚀 PRISM 센서 데이터 수집 시스템 시작 (WebSocket 구조)")
    print("=" * 70)
    print(f"📡 FastAPI 서버: {API_SERVER}")
    print(f"🖥️  장치 ID: {DEVICE_ID}")
    print(f"🌐 로컬 IP: {get_local_ip()}")
    print(f"⏱️  전송 주기: {SEND_INTERVAL}초")
    print("")
    print("💡 데이터 흐름:")
    print(f"   [{DEVICE_ID}] → FastAPI (/ingest) → WebSocket → 웹 브라우저")
    print("=" * 70)
    print("")
    
    # 연결 테스트
    print("🔍 서버 연결 테스트 중...")
    try:
        response = requests.get(f"{API_SERVER}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 서버 연결 성공!")
            health_data = response.json()
            print(f"   서버 상태: {health_data.get('status')}")
            print(f"   활성 장치: {health_data.get('active_devices', 0)}")
            print(f"   WebSocket 연결: {health_data.get('websocket_connections', 0)}")
        else:
            print(f"⚠️  서버 응답 이상: {response.status_code}")
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        print("   서버가 실행 중인지 확인하세요!")
        return
    
    print("")
    print("📊 데이터 수집 시작...")
    print("-" * 70)
    print("")
    
    # GPIO 초기화 (실제 센서 사용시 주석 해제)
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setwarnings(False)
    # GPIO.setup(BUZZER_PIN, GPIO.OUT)
    # GPIO.output(BUZZER_PIN, GPIO.LOW)
    
    # 🔔 WebSocket 리스너 시작 (부저 트리거 명령 수신)
    if WEBSOCKET_AVAILABLE:
        print("🔌 WebSocket 리스너 시작 중...")
        start_websocket_listener()
        time.sleep(2)  # 연결 대기
    else:
        print("⚠️  WebSocket 리스너 비활성화 (websocket-client 미설치)")
    
    print("")
    
    last_send = time.time()
    
    try:
        while True:
            current_time = time.time()
            
            # 데이터 전송
            if current_time - last_send >= SEND_INTERVAL:
                # 센서 데이터 수집
                sensor_data = collect_sensor_data()
                
                # 서버로 전송
                success = send_data_to_server(sensor_data)
                
                if success:
                    last_send = current_time
                    
                    # 임계값 체크 (알림)
                    if sensor_data.get('flame', False):
                        print("⚠️  [위험] 불꽃이 감지되었습니다!")
                    if sensor_data.get('temperature', 0) > 50:
                        print(f"⚠️  [위험] 온도가 위험 수준입니다! ({sensor_data['temperature']}°C)")
                    if sensor_data.get('gas', 0) > 100:
                        print(f"⚠️  [위험] 가스 농도가 위험 수준입니다! ({sensor_data['gas']} ppm)")
                    if sensor_data.get('dust', 0) > 100:
                        print(f"⚠️  [경고] 미세먼지 농도가 높습니다! ({sensor_data['dust']} μg/m³)")
                else:
                    # 실패시 5초 후 재시도
                    print("⏳ 5초 후 재시도...")
                    time.sleep(5)
            
            # CPU 사용률 낮추기
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n⏹️  프로그램 종료")
        # GPIO 정리 (실제 센서 사용시 주석 해제)
        # GPIO.cleanup()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        # GPIO 정리 (실제 센서 사용시 주석 해제)
        # GPIO.cleanup()

# ============================================
# SSH 원격 관리 가이드
# ============================================

"""
SSH 원격 관리 설정 방법:

1. 라즈베리파이/오렌지파이에서 SSH 활성화:
   sudo raspi-config
   → Interface Options → SSH → Enable

2. 고정 IP 설정 (권장):
   sudo nano /etc/dhcpcd.conf
   
   추가 내용:
   interface eth0
   static ip_address=192.168.1.100/24
   static routers=192.168.1.1
   static domain_name_servers=8.8.8.8

3. 외부에서 SSH 접속:
   ssh pi@192.168.1.100
   
4. 이 스크립트를 자동 시작하도록 설정:
   sudo nano /etc/systemd/system/prism-sensor.service
   
   추가 내용:
   [Unit]
   Description=PRISM Sensor Data Service
   After=network.target
   
   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/prism
   Environment="API_SERVER=http://192.168.1.10:8000"
   Environment="ZONE_ID=testbox"
   Environment="DEVICE_ID=raspberry_pi_01"
   ExecStart=/usr/bin/python3 /home/pi/prism/iot_devices/raspberry_pi_sensor.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   
5. 서비스 활성화 및 시작:
   sudo systemctl daemon-reload
   sudo systemctl enable prism-sensor
   sudo systemctl start prism-sensor
   
6. 서비스 상태 확인:
   sudo systemctl status prism-sensor
   
7. 로그 확인:
   sudo journalctl -u prism-sensor -f

8. 원격으로 센서 데이터 확인:
   ssh pi@192.168.1.100 "python3 /home/pi/prism/iot_devices/raspberry_pi_sensor.py"
"""

if __name__ == "__main__":
    main()
