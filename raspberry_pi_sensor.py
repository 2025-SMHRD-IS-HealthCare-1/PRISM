"""
라즈베리파이/오렌지파이 센서 데이터 수집 및 전송
SSH를 통한 원격 관리 지원
"""

import requests
import time
import json
import os
import socket
from datetime import datetime

# ============================================
# 설정
# ============================================

# FastAPI 서버 주소 (환경 변수로 설정 가능)
API_SERVER = os.getenv("API_SERVER", "http://192.168.1.10:8000")  # FastAPI 서버 IP로 변경
ZONE_ID = os.getenv("ZONE_ID", "testbox")  # 구역 ID
DEVICE_ID = os.getenv("DEVICE_ID", "raspberry_pi_01")  # 장치 ID

SEND_INTERVAL = 5  # 5초마다 데이터 전송
HEARTBEAT_INTERVAL = 60  # 60초마다 하트비트 전송

# ============================================
# 센서 초기화 (실제 센서 사용시 주석 해제)
# ============================================

# 라즈베리파이 GPIO 설정
# import RPi.GPIO as GPIO
# import Adafruit_DHT  # 온도/습도 센서

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
# 데이터 수집 및 전송
# ============================================

def collect_sensor_data():
    """
    모든 센서에서 데이터 수집
    """
    data = {
        "zone": ZONE_ID,
        "temperature": read_temperature_sensor(),
        "gas": read_gas_sensor(),
        "dust": read_dust_sensor(),
        "flame": read_flame_sensor(),
        "timestamp": datetime.now().isoformat()
    }
    return data

def send_data_to_server(data):
    """
    센서 데이터를 FastAPI 서버로 전송
    """
    try:
        url = f"{API_SERVER}/api/sensors/{ZONE_ID}"
        response = requests.post(url, json=data, timeout=5)
        
        if response.status_code == 200:
            print(f"✓ 데이터 전송 성공: {datetime.now().strftime('%H:%M:%S')}")
            print(f"  온도: {data['temperature']}°C")
            print(f"  가스: {data['gas']} ppm")
            print(f"  미세먼지: {data['dust']} μg/m³")
            print(f"  불꽃: {'감지됨!' if data['flame'] else '미감지'}")
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
    """
    try:
        url = f"{API_SERVER}/api/device/{DEVICE_ID}/heartbeat"
        response = requests.post(url, timeout=5)
        
        if response.status_code == 200:
            print(f"💓 하트비트 전송 성공: {datetime.now().strftime('%H:%M:%S')}")
            return True
        else:
            print(f"✗ 하트비트 실패: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ 하트비트 오류: {e}")
        return False

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
    print("=" * 60)
    print("🚀 PRISM 센서 데이터 수집 시스템 시작")
    print("=" * 60)
    print(f"📡 FastAPI 서버: {API_SERVER}")
    print(f"🏭 구역 ID: {ZONE_ID}")
    print(f"🖥️  장치 ID: {DEVICE_ID}")
    print(f"🌐 로컬 IP: {get_local_ip()}")
    print(f"⏱️  전송 주기: {SEND_INTERVAL}초")
    print("=" * 60)
    print("")
    
    # GPIO 초기화 (실제 센서 사용시 주석 해제)
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setwarnings(False)
    
    last_heartbeat = time.time()
    
    try:
        # 초기 하트비트 전송
        send_heartbeat()
        
        while True:
            # 센서 데이터 수집
            sensor_data = collect_sensor_data()
            
            # 서버로 전송
            send_data_to_server(sensor_data)
            
            # 임계값 체크 (알림)
            if sensor_data['flame']:
                print("⚠️  [위험] 불꽃이 감지되었습니다!")
            if sensor_data['temperature'] > 50:
                print(f"⚠️  [위험] 온도가 위험 수준입니다! ({sensor_data['temperature']}°C)")
            if sensor_data['gas'] > 100:
                print(f"⚠️  [위험] 가스 농도가 위험 수준입니다! ({sensor_data['gas']} ppm)")
            if sensor_data['dust'] > 100:
                print(f"⚠️  [경고] 미세먼지 농도가 높습니다! ({sensor_data['dust']} μg/m³)")
            
            # 하트비트 전송 (일정 시간마다)
            current_time = time.time()
            if current_time - last_heartbeat >= HEARTBEAT_INTERVAL:
                send_heartbeat()
                last_heartbeat = current_time
            
            # 대기
            time.sleep(SEND_INTERVAL)
            
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
   ExecStart=/usr/bin/python3 /home/pi/prism/raspberry_pi_sensor.py
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
   ssh pi@192.168.1.100 "python3 /home/pi/prism/raspberry_pi_sensor.py"
"""

if __name__ == "__main__":
    main()
