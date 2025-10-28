# 🔧 라즈베리파이 센서 통합 가이드

## 📦 수정된 파일

### `all_sensors_integrated.py`

- ✅ 기존 파일 기반 → **HTTP POST 방식으로 변경**
- ✅ Render 서버(`https://prism-api-ay8q.onrender.com`)로 직접 전송
- ✅ 5초마다 자동 전송
- ✅ 환경 변수로 서버 주소 설정 가능

### 제거된 파일

- ❌ `app_251027.py` - 더 이상 로컬 FastAPI 서버 불필요

---

## 🚀 라즈베리파이 설정

### 1단계: 필수 패키지 설치

```bash
# 시스템 패키지
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev

# Python 라이브러리
pip3 install RPi.GPIO spidev pyserial requests

# 또는 requirements 파일 사용
pip3 install -r requirements_rpi.txt
```

### 2단계: 환경 변수 설정

```bash
# 임시 설정 (현재 세션만)
export API_SERVER="https://prism-api-ay8q.onrender.com"
export DEVICE_ID="rpi-01"

# 영구 설정 (~/.bashrc에 추가)
echo 'export API_SERVER="https://prism-api-ay8q.onrender.com"' >> ~/.bashrc
echo 'export DEVICE_ID="rpi-01"' >> ~/.bashrc
source ~/.bashrc
```

### 3단계: 스크립트 실행

```bash
cd /home/pi/PRISM/iot_devices/rpi_ex
python3 all_sensors_integrated.py
```

---

## 📊 데이터 형식

### 전송되는 데이터 구조

```json
{
  "device_id": "rpi-01",
  "data": {
    "flame": false,              // 불꽃 감지 (boolean)
    "gas": 126,                  // 가스 농도 원시값 (0~1023)
    "gas_voltage": 0.406,        // 가스 센서 전압 (V)
    "temperature": 23.56,        // 온도 (°C)
    "pm1": 4,                    // 미세먼지 PM1.0 (μg/m³)
    "pm25": 1,                   // 미세먼지 PM2.5 (μg/m³)
    "pm10": 4,                   // 미세먼지 PM10 (μg/m³)
    "gas_delta": 22              // 가스 변화량 (baseline 대비)
  },
  "ts": 1761621399.5664232
}
```

### 서버 API 엔드포인트

- **POST** `https://prism-api-ay8q.onrender.com/ingest`
- **Headers**: `Content-Type: application/json`

---

## ⚠️ 임계값 설정

현재 설정된 알람 임계값 (`all_sensors_integrated.py` 내부):

### 불꽃 감지 (flame)
- `FLAME_ALERT = True` - 불꽃 감지 시 즉시 알람

### 온도 (temperature)
- `TEMP_THRESHOLD = 35.0°C` - 알람 발생
- `TEMP_WARNING = 30.0°C` - 경고 수준

### 가스 농도 (gas, gas_voltage)
- `GAS_THRESHOLD_RAW = 200` - 원시값 기준 (0~1023)
- `GAS_VOLTAGE_MAX = 2.5V` - 전압 기준
- `GAS_DELTA_ALERT = 50` - 급격한 증가 감지

### 미세먼지 (pm1, pm25, pm10)
- `PM1_THRESHOLD = 50 μg/m³` - PM1.0 초미세입자
- `PM25_THRESHOLD = 35 μg/m³` - PM2.5 (한국 보통 기준)
- `PM10_THRESHOLD = 100 μg/m³` - PM10 (한국 보통 기준)

**수정 방법:** `all_sensors_integrated.py` 파일 상단의 임계값 변수 수정

---

## 🔧 하드웨어 연결

### GPIO 핀 맵

| 센서/장치    | 타입    | GPIO 핀      | 설명                |
| ------------ | ------- | ------------ | ------------------- |
| Flame Sensor | Digital | GPIO 17      | 불꽃 감지 센서      |
| Flame LED    | Output  | GPIO 27      | 상태 표시 LED       |
| Buzzer       | PWM     | GPIO 20      | 경보 부저           |
| MQ-2 Gas     | SPI     | SPI0 (CH0)   | 가스 센서 (MCP3008) |
| DS18B20      | 1-Wire  | -            | 온도 센서           |
| PMS7003M     | UART    | /dev/serial0 | 미세먼지 센서       |

### SPI 활성화

```bash
sudo raspi-config
# → Interfacing Options → SPI → Enable
```

### 1-Wire 활성화

```bash
sudo raspi-config
# → Interfacing Options → 1-Wire → Enable

# 또는 직접 설정
echo "dtoverlay=w1-gpio" | sudo tee -a /boot/config.txt
sudo reboot
```

### UART 활성화

```bash
# Bluetooth 비활성화 (UART0를 센서에 사용)
echo "dtoverlay=disable-bt" | sudo tee -a /boot/config.txt
sudo systemctl disable hciuart
sudo reboot
```

---

## 🔄 시스템 서비스 등록

### systemd 서비스 생성

```bash
sudo nano /etc/systemd/system/prism-sensors.service
```

**파일 내용:**

```ini
[Unit]
Description=PRISM Sensor Data Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/PRISM/iot_devices/rpi_ex
Environment="API_SERVER=https://prism-api-ay8q.onrender.com"
Environment="DEVICE_ID=rpi-01"
ExecStart=/usr/bin/python3 /home/pi/PRISM/iot_devices/rpi_ex/all_sensors_integrated.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 서비스 활성화

```bash
sudo systemctl daemon-reload
sudo systemctl enable prism-sensors.service
sudo systemctl start prism-sensors.service

# 상태 확인
sudo systemctl status prism-sensors.service

# 로그 확인
sudo journalctl -u prism-sensors.service -f
```

---

## 🧪 테스트

### 1. 로컬 테스트

```bash
python3 all_sensors_integrated.py
```

**예상 출력:**

```
🌐 서버: https://prism-api-ay8q.onrender.com
🔧 장치 ID: rpi-01
======================================================================
🚀 모든 센서 읽기 시작! (Ctrl+C로 종료)
======================================================================
{"flame": false, "gas": 245, "gas_voltage": 0.79, "temperature": 25.3, ...}
✓ 서버 전송 성공
```

### 2. 서버 확인

```bash
# 헬스 체크
curl https://prism-api-ay8q.onrender.com/health

# 최신 데이터 확인
curl https://prism-api-ay8q.onrender.com/latest/rpi-01
```

### 3. 웹 대시보드

브라우저에서 `public/websocket_test.html` 열기

- 실시간으로 `rpi-01` 데이터 카드가 표시됨
- 5초마다 자동 업데이트

---

## ⚙️ 설정 옵션

### 환경 변수

| 변수         | 기본값                              | 설명         |
| ------------ | ----------------------------------- | ------------ |
| `API_SERVER` | https://prism-api-ay8q.onrender.com | 서버 주소    |
| `DEVICE_ID`  | rpi-01                              | 장치 고유 ID |

### 코드 내 조정 가능한 값

```python
SEND_INTERVAL = 5.0          # 서버 전송 주기 (초)
GAS_THRESHOLD_RAW = 300      # 가스 임계값
PM25_THRESHOLD = 80          # 미세먼지 임계값
TEMP_THRESHOLD = 30.0        # 온도 임계값
ALARM_LATCH_SEC = 2.0        # 알람 최소 지속 시간
```

---

## 🆘 문제 해결

### "서버 연결 실패"

```bash
# 인터넷 연결 확인
ping -c 3 google.com

# DNS 확인
nslookup prism-api-ay8q.onrender.com

# 방화벽 확인
sudo ufw status
```

### "센서 읽기 실패"

```bash
# GPIO 권한 확인
sudo usermod -a -G gpio,spi,i2c pi

# 장치 확인
ls -l /dev/spidev*    # SPI
ls -l /dev/serial*    # UART
ls -l /sys/bus/w1/devices/  # 1-Wire
```

### "모듈 없음" 오류

```bash
pip3 install --upgrade RPi.GPIO spidev pyserial requests
```

---

## 📈 모니터링

### 실시간 로그

```bash
# systemd 서비스 로그
sudo journalctl -u prism-sensors.service -f

# 직접 실행 로그
python3 all_sensors_integrated.py 2>&1 | tee sensor.log
```

### 서버 상태

```bash
# 활성 장치 수 확인
curl https://prism-api-ay8q.onrender.com/health | jq '.active_devices'

# 전체 장치 목록
curl https://prism-api-ay8q.onrender.com/devices
```

---

## 🎯 주요 변경사항 요약

| 항목            | 이전             | 이후                 |
| --------------- | ---------------- | -------------------- |
| **통신 방식**   | 파일 기반 (로컬) | HTTP POST (클라우드) |
| **서버**        | 로컬 FastAPI     | Render 클라우드      |
| **데이터 형식** | 파일 JSON        | REST API JSON        |
| **실시간성**    | 없음             | WebSocket 실시간     |
| **네트워크**    | 로컬만           | 인터넷 어디서나      |

---

## ✅ 체크리스트

- [ ] Python 패키지 설치 (`RPi.GPIO`, `spidev`, `pyserial`, `requests`)
- [ ] 환경 변수 설정 (`API_SERVER`, `DEVICE_ID`)
- [ ] SPI/1-Wire/UART 활성화
- [ ] 하드웨어 연결 확인
- [ ] 스크립트 실행 테스트
- [ ] 서버 데이터 수신 확인
- [ ] systemd 서비스 등록 (선택)
- [ ] 웹 대시보드 확인

---

완료! 🎉 이제 라즈베리파이가 어디서든 Render 서버로 센서 데이터를 전송합니다!
