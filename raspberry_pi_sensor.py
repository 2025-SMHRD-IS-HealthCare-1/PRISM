"""
라즈베리파이 센서 데이터 수집 및 전송 예제
실제 센서와 연결하여 데이터를 FastAPI 서버로 전송
"""

import requests
import time
import json
from datetime import datetime

# 설정
API_SERVER = "http://localhost:8000"  # FastAPI 서버 주소
ZONE_ID = "testbox"
SEND_INTERVAL = 5  # 5초마다 전송

# 센서 GPIO 핀 설정 (예제)
# import RPi.GPIO as GPIO
# import Adafruit_DHT  # 온도 센서
# import board
# import busio
# import adafruit_ads1x15.ads1115 as ADS
# from adafruit_ads1x15.analog_in import AnalogIn

def read_temperature_sensor():
    """
    온도 센서에서 데이터 읽기
    예: DHT22 센서 사용
    """
    # 실제 센서 코드 예제:
    # sensor = Adafruit_DHT.DHT22
    # pin = 4
    # humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    # return temperature if temperature is not None else 0
    
    # 테스트용 더미 데이터
    import random
    return round(20 + random.uniform(0, 15), 1)

def read_gas_sensor():
    """
    가스 센서에서 데이터 읽기
    예: MQ-2, MQ-135 센서 사용 (ADC 필요)
    """
    # 실제 센서 코드 예제:
    # i2c = busio.I2C(board.SCL, board.SDA)
    # ads = ADS.ADS1115(i2c)
    # chan = AnalogIn(ads, ADS.P0)
    # voltage = chan.voltage
    # ppm = voltage * 100  # 실제 변환 공식 필요
    # return ppm
    
    # 테스트용 더미 데이터
    import random
    return round(10 + random.uniform(0, 50), 1)

def read_dust_sensor():
    """
    미세먼지 센서에서 데이터 읽기
    예: GP2Y1010AU0F, PMS5003 센서 사용
    """
    # 실제 센서 코드 예제:
    # import serial
    # ser = serial.Serial('/dev/ttyUSB0', 9600)
    # data = ser.read(32)
    # # 데이터 파싱
    # pm25 = (data[6] * 256 + data[7]) / 10.0
    # return pm25
    
    # 테스트용 더미 데이터
    import random
    return round(5 + random.uniform(0, 20), 2)

def read_flame_sensor():
    """
    불꽃 감지 센서에서 데이터 읽기
    예: KY-026 Flame Sensor 사용
    """
    # 실제 센서 코드 예제:
    # GPIO.setmode(GPIO.BCM)
    # FLAME_PIN = 17
    # GPIO.setup(FLAME_PIN, GPIO.IN)
    # flame_detected = GPIO.input(FLAME_PIN) == GPIO.LOW
    # return flame_detected
    
    # 테스트용 더미 데이터
    import random
    return random.random() > 0.95

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
            print(f"  미세먼지: {data['dust']} g/m³")
            print(f"  불꽃: {'감지됨!' if data['flame'] else '미감지'}")
            print("-" * 50)
            return True
        else:
            print(f"✗ 전송 실패: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ 연결 오류: {e}")
        return False

def main():
    """
    메인 루프: 주기적으로 센서 데이터 수집 및 전송
    """
    print("=" * 50)
    print("PRISM 센서 데이터 수집 시스템 시작")
    print(f"서버: {API_SERVER}")
    print(f"구역: {ZONE_ID}")
    print(f"전송 주기: {SEND_INTERVAL}초")
    print("=" * 50)
    
    # GPIO 초기화 (실제 센서 사용시)
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setwarnings(False)
    
    try:
        while True:
            # 센서 데이터 수집
            sensor_data = collect_sensor_data()
            
            # 서버로 전송
            send_data_to_server(sensor_data)
            
            # 임계값 체크 (알림)
            if sensor_data['flame']:
                print("⚠️  경고: 불꽃이 감지되었습니다!")
            if sensor_data['temperature'] > 50:
                print("⚠️  경고: 온도가 위험 수준입니다!")
            if sensor_data['gas'] > 100:
                print("⚠️  경고: 가스 농도가 위험 수준입니다!")
            
            # 대기
            time.sleep(SEND_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n프로그램 종료")
        # GPIO 정리 (실제 센서 사용시)
        # GPIO.cleanup()

if __name__ == "__main__":
    main()
