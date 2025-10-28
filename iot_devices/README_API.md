# 🔧 라즈베리파이 센서 API 사용 가이드

## 📋 개요

이 파일(`raspberry_pi_api.py`)은 라즈베리파이에서 로컬 FastAPI 서버를 실행하여:

1. 센서 데이터를 주기적으로 읽고
2. 로컬 API로 제공하며
3. 자동으로 Render 클라우드 서버로 전송합니다

## 🆚 차이점

| 파일                     | 용도                            | 실행 방식           |
| ------------------------ | ------------------------------- | ------------------- |
| `raspberry_pi_sensor.py` | 센서 데이터만 읽고 전송         | 백그라운드 스크립트 |
| `raspberry_pi_api.py`    | 로컬 API + 센서 + 클라우드 전송 | FastAPI 서버 실행   |

## 🚀 실행 방법

### 1. 기본 실행

```bash
# 라즈베리파이에서
cd /home/pi/PRISM
python iot_devices/raspberry_pi_api.py
```

### 2. 환경 변수 설정

```bash
export DEVICE_ID="rpi-01"
export API_SERVER="https://prism-api-ay8q.onrender.com"
export PORT="8080"

python iot_devices/raspberry_pi_api.py
```

### 3. systemd 서비스로 등록

`/etc/systemd/system/prism-sensor-api.service` 파일 생성:

```ini
[Unit]
Description=PRISM Raspberry Pi Sensor API
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/PRISM
Environment="DEVICE_ID=rpi-01"
Environment="API_SERVER=https://prism-api-ay8q.onrender.com"
Environment="PORT=8080"
ExecStart=/usr/bin/python3 /home/pi/PRISM/iot_devices/raspberry_pi_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

서비스 시작:

```bash
sudo systemctl daemon-reload
sudo systemctl enable prism-sensor-api
sudo systemctl start prism-sensor-api
sudo systemctl status prism-sensor-api
```

## 📊 API 엔드포인트

서버 실행 후 다음 엔드포인트를 사용할 수 있습니다:

### 1. 헬스 체크

```bash
curl http://localhost:8080/health
```

**응답 예시:**

```json
{
  "ok": true,
  "device_id": "rpi-01",
  "timestamp": 1698465123.456,
  "snapshot_exists": true,
  "snapshot_age_sec": 2.34,
  "cloud_server": "https://prism-api-ay8q.onrender.com"
}
```

### 2. 센서 데이터 조회

```bash
curl http://localhost:8080/sensors
```

**응답 예시:**

```json
{
  "device_id": "rpi-01",
  "data": {
    "temperature": 24.5,
    "gas": 32.1,
    "dust": 12.8,
    "humidity": 55.3,
    "flame": false
  },
  "timestamp": 1698465123.456,
  "datetime": "2025-10-28T10:52:03.456789"
}
```

### 3. 스냅샷 파일 조회

```bash
curl http://localhost:8080/snapshot
```

**응답 예시:**

```json
{
  "device_id": "rpi-01",
  "data": {
    "temperature": 24.5,
    "gas": 32.1,
    "dust": 12.8,
    "humidity": 55.3,
    "flame": false
  },
  "timestamp": 1698465123.456,
  "datetime": "2025-10-28T10:52:03.456789",
  "_metadata": {
    "file_path": "/tmp/prism_sensors.json",
    "last_modified": 1698465123.456,
    "age_seconds": 2.34
  }
}
```

## 🔄 동작 방식

```
┌─────────────────────────────────────────┐
│   라즈베리파이 (raspberry_pi_api.py)   │
├─────────────────────────────────────────┤
│                                         │
│  [센서 하드웨어]                        │
│       ↓                                 │
│  [센서 데이터 수집 스레드]              │
│       ↓                                 │
│  /tmp/prism_sensors.json (스냅샷)      │
│       ↓                                 │
│  ┌───────────────┬─────────────────┐   │
│  ↓               ↓                 ↓   │
│  [로컬 API]  [클라우드 전송]  [파일]   │
│   :8080        스레드           저장   │
└─────────────────────────────────────────┘
       ↓                 ↓
   로컬 네트워크    클라우드 서버
   접속 가능     (Render.com)
```

### 동작 흐름

1. **센서 읽기 스레드** (5초마다):

   - 센서 하드웨어에서 데이터 읽기
   - `/tmp/prism_sensors.json`에 저장

2. **클라우드 전송 스레드** (5초마다):

   - 스냅샷 파일 읽기
   - Render 서버로 POST 요청
   - 오프라인 시 오류만 로그하고 계속 실행

3. **FastAPI 서버**:
   - 로컬 네트워크에서 API 제공
   - GET `/health`, `/sensors`, `/snapshot`

## ⚙️ 설정 옵션

### 환경 변수

| 변수         | 기본값                                | 설명              |
| ------------ | ------------------------------------- | ----------------- |
| `DEVICE_ID`  | `rpi-01`                              | 디바이스 고유 ID  |
| `API_SERVER` | `https://prism-api-ay8q.onrender.com` | 클라우드 서버 URL |
| `PORT`       | `8080`                                | 로컬 API 포트     |

### 코드 내 설정

```python
SNAPSHOT = "/tmp/prism_sensors.json"  # 스냅샷 파일 경로
STALE_SEC = 10  # 데이터 유효 시간 (초)
SENSOR_READ_INTERVAL = 5  # 센서 읽기 주기 (초)
SEND_TO_CLOUD_INTERVAL = 5  # 클라우드 전송 주기 (초)
```

## 🔌 실제 센서 연동

현재는 더미 데이터를 생성합니다. 실제 센서를 연동하려면:

### 1. DHT22 온습도 센서

```python
import Adafruit_DHT

def read_temperature_sensor():
    sensor = Adafruit_DHT.DHT22
    pin = 4
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    return temperature if temperature is not None else 0

def read_humidity_sensor():
    sensor = Adafruit_DHT.DHT22
    pin = 4
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    return humidity if humidity is not None else 0
```

### 2. MQ-2 가스 센서 (ADC 필요)

```python
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

def read_gas_sensor():
    chan = AnalogIn(ads, ADS.P0)
    voltage = chan.voltage
    ppm = voltage * 100  # 실제 변환 공식 필요
    return ppm
```

### 3. KY-026 불꽃 센서

```python
import RPi.GPIO as GPIO

FLAME_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(FLAME_PIN, GPIO.IN)

def read_flame_sensor():
    return GPIO.input(FLAME_PIN) == GPIO.LOW  # LOW = 불꽃 감지
```

## 🆘 문제 해결

### "센서 데이터가 아직 준비되지 않았습니다"

→ 서버가 방금 시작되었습니다. 5초 후 다시 시도하세요.

### "센서 데이터가 오래되었습니다"

→ 센서 읽기 스레드가 멈췄습니다. 서버를 재시작하세요.

### "클라우드 서버 연결 실패"

→ 인터넷 연결을 확인하세요. 로컬 API는 계속 작동합니다.

### 로그 확인

```bash
# systemd 서비스로 실행 시
sudo journalctl -u prism-sensor-api -f

# 직접 실행 시 터미널에 로그 출력
```

## 📌 장점

### 로컬 API 제공

- 라즈베리파이와 같은 네트워크의 다른 장치에서 센서 데이터 조회 가능
- 인터넷 없이도 로컬 모니터링 가능

### 자동 클라우드 동기화

- 백그라운드에서 자동으로 Render 서버로 전송
- 네트워크 오류 시에도 로컬 API는 계속 작동

### 스냅샷 파일

- `/tmp/prism_sensors.json`에 최신 데이터 저장
- 다른 프로세스에서도 파일 읽기 가능

## 🎯 사용 예시

### 로컬 네트워크에서 센서 데이터 확인

```python
import requests

# 라즈베리파이 IP가 192.168.1.100이라고 가정
response = requests.get("http://192.168.1.100:8080/sensors")
data = response.json()
print(f"온도: {data['data']['temperature']}°C")
```

### 웹 페이지에서 실시간 표시

```html
<script>
  setInterval(async () => {
    const response = await fetch("http://192.168.1.100:8080/sensors");
    const data = await response.json();
    document.getElementById("temp").textContent = data.data.temperature;
  }, 1000);
</script>
```

---

**참고**: `raspberry_pi_sensor.py`와 `raspberry_pi_api.py`는 동시에 실행하지 마세요. 둘 다 같은 역할을 하므로 하나만 선택하세요!
