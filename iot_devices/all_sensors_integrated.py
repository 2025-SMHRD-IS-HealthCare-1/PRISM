#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
all_sensors_integrated.py
Raspberry Pi: Flame(GPIO) + MQ-2(MCP3008/SPI) + DS18B20(1-Wire) + PMS7003M(UART) + Buzzer
★ 최적화: 센서 데이터를 Render 서버로 HTTP POST 전송 (WebSocket 실시간 연동)
Ctrl+C 로 종료

═══════════════════════ 데이터 구조 ═══════════════════════
서버로 전송되는 JSON 형식:
{
  "device_id": "rpi-01",
  "data": {
    "flame": false,              # 불꽃 감지 (boolean)
    "gas": 126,                  # 가스 농도 원시값 (0~1023)
    "gas_voltage": 0.406,        # 가스 센서 전압 (V)
    "temperature": 23.56,        # 온도 (°C)
    "pm1": 4,                    # 미세먼지 PM1.0 (μg/m³)
    "pm25": 1,                   # 미세먼지 PM2.5 (μg/m³)
    "pm10": 4,                   # 미세먼지 PM10 (μg/m³)
    "gas_delta": 22              # 가스 변화량 (baseline 대비)
  },
  "ts": 1761621399.5664232
}
═══════════════════════════════════════════════════════════
"""

import threading
import time
import sys
import glob
import struct
import json
import os
from datetime import datetime
import RPi.GPIO as GPIO
import spidev
import serial
import requests

# ───────────────────────── 서버 설정 ─────────────────────────
API_SERVER = os.getenv("API_SERVER", "https://prism-api-ay8q.onrender.com")
DEVICE_ID = os.getenv("DEVICE_ID", "rpi-01")
SEND_INTERVAL = 5.0  # 5초마다 서버로 전송
MAX_RETRIES = 3      # 전송 실패 시 최대 재시도 횟수
RETRY_DELAY = 2.0    # 재시도 대기 시간 (초)

print("=" * 70)
print("PRISM 통합 센서 시스템 시작")
print("=" * 70)
print(f"서버: {API_SERVER}")
print(f"장치 ID: {DEVICE_ID}")
print(f"전송 주기: {SEND_INTERVAL}초")
print("=" * 70)

# ───────────────────────── 기본 GPIO ─────────────────────────
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# ───────────────────────── 핀/옵션 ─────────────────────────
# Flame + LED
FLAME_SENSOR_PIN = 17          # DO (BCM)
FLAME_LED_PIN    = 27
FLAME_ACTIVE_LOW = False       # 감지 시 LOW면 True, HIGH면 False

# Buzzer
BUZZER_PIN        = 20
BUZZER_IS_PASSIVE = True       # 패시브(True)/액티브(False)
BUZZER_ACTIVE_LOW = False      # 액티브가 LOW에서 울리면 True
PASSIVE_FREQ_HZ   = 3000
PASSIVE_DUTY      = 70

# MQ-2 (MCP3008/SPI)
SPI_BUS, SPI_DEV  = 0, 0       # /dev/spidev0.0
SPI_MAX_HZ        = 1_350_000
MQ2_CHANNEL       = 0          # CH0

# DS18B20 (1-Wire)
W1_BASE = '/sys/bus/w1/devices/'

# PMS7003M (UART)
PMS_PORT = "/dev/serial0"      # 필요 시 '/dev/ttyAMA0' 또는 '/dev/ttyS0'
PMS_BAUD = 9600

# ═══════════════════════ 임계값 설정 ═══════════════════════
# 불꽃 감지 (flame)
FLAME_ALERT       = True       # 불꽃 감지 시 알람 ON

# 온도 (temperature) - 섭씨 기준
TEMP_THRESHOLD    = 35.0       # °C (None이면 온도 알람 무시)
TEMP_WARNING      = 30.0       # °C (경고 수준)

# 가스 농도 (gas, gas_voltage)
GAS_THRESHOLD_RAW = 200        # MQ-2 원시값 (0~1023)
GAS_VOLTAGE_MAX   = 2.5        # V (전압 기준)
GAS_DELTA_ALERT   = 50         # baseline 대비 급격한 증가량(Δ) 감지

# 미세먼지 (pm1, pm25, pm10) - μg/m³ 기준
PM1_THRESHOLD     = 50         # PM1.0 초미세입자
PM25_THRESHOLD    = 35         # PM2.5 (WHO 기준: 15, 한국 보통: 35)
PM10_THRESHOLD    = 100        # PM10 (WHO 기준: 45, 한국 보통: 100)

# 알람 래칭(최소 울림시간)
ALARM_LATCH_SEC   = 3.0        # 초

# MQ-2 가스 센서 보정 파라미터
MQ2_BASELINE_SEC  = 10         # 시작 후 10초는 기준선 학습
MQ2_EMA_ALPHA     = 0.20       # EMA 평활 계수 (0.1~0.3 권장)

# ───────────────────────── 공유 상태 ─────────────────────────
STATE = {
    "flame": None,
    "mq2_raw": None, 
    "mq2_voltage": None,
    "temp_c": None,
    "pm1": None, 
    "pm25": None, 
    "pm10": None,
    # MQ-2 보정 내부 상태
    "mq2_baseline": None, 
    "mq2_ema": None, 
    "mq2_delta": None, 
    "_mq2_t0": None
}
STATE_LOCK = threading.Lock()
RUN = True

# 통계 정보
STATS = {
    "total_sent": 0,
    "failed_sent": 0,
    "last_success": None,
    "last_error": None
}
STATS_LOCK = threading.Lock()

def set_state(**kwargs):
    """Thread-safe state update"""
    with STATE_LOCK:
        STATE.update(kwargs)

def update_stats(**kwargs):
    """Thread-safe stats update"""
    with STATS_LOCK:
        STATS.update(kwargs)

# ───────────────────────── 부저 ─────────────────────────
GPIO.setup(BUZZER_PIN, GPIO.OUT)
_pwm = None  # 패시브 PWM 핸들

def set_buzzer(on: bool):
    """부저 제어"""
    global _pwm
    if BUZZER_IS_PASSIVE:
        if on and _pwm is None:
            _pwm = GPIO.PWM(BUZZER_PIN, PASSIVE_FREQ_HZ)
            _pwm.start(PASSIVE_DUTY)
        elif not on and _pwm is not None:
            _pwm.stop()
            _pwm = None
    else:
        if BUZZER_ACTIVE_LOW:
            GPIO.output(BUZZER_PIN, GPIO.LOW if on else GPIO.HIGH)
        else:
            GPIO.output(BUZZER_PIN, GPIO.HIGH if on else GPIO.LOW)

# 짧은 셀프테스트
set_buzzer(False)
print("부저 테스트...")
for _ in range(2):
    set_buzzer(True)
    time.sleep(0.12)
    set_buzzer(False)
    time.sleep(0.12)
print("부저 테스트 완료")

# ───────────────────────── LED ─────────────────────────
GPIO.setup(FLAME_LED_PIN, GPIO.OUT)

def set_led(on: bool):
    """LED 제어"""
    GPIO.output(FLAME_LED_PIN, GPIO.HIGH if on else GPIO.LOW)

# ───────────────────────── Flame ─────────────────────────
def flame_thread():
    """불꽃 센서 모니터링 스레드"""
    GPIO.setup(FLAME_SENSOR_PIN, GPIO.IN)
    set_led(False)

    def read_flame():
        raw = GPIO.input(FLAME_SENSOR_PIN)
        return (raw == 0) if FLAME_ACTIVE_LOW else (raw == 1)

    last = None
    print("불꽃 센서 시작")
    
    while RUN:
        now = read_flame()
        if now != last:
            set_state(flame=now)
            set_led(now)
            if now:
                print("불꽃 감지!")
            last = now
        time.sleep(0.1)

# ───────────────────────── MQ-2 보정 함수 ─────────────────────────
def mq2_calibration_update(raw: int):
    """MQ-2 가스 센서 보정 (EMA 기반)"""
    now = time.time()
    
    if STATE.get("_mq2_t0") is None:
        set_state(_mq2_t0=now, mq2_baseline=raw, mq2_ema=raw, mq2_delta=0)
        return

    ema_prev = STATE.get("mq2_ema") or raw
    ema = (MQ2_EMA_ALPHA * raw) + (1 - MQ2_EMA_ALPHA) * ema_prev

    base_prev = STATE.get("mq2_baseline") or raw
    if now - (STATE.get("_mq2_t0") or now) < MQ2_BASELINE_SEC:
        # 초기 10초는 baseline 학습
        baseline = (0.02 * raw) + (0.98 * base_prev)
    else:
        baseline = base_prev

    delta = int(ema - baseline)
    set_state(mq2_ema=int(ema), mq2_baseline=int(baseline), mq2_delta=delta)

# ───────────────────────── MQ-2 (SPI) ─────────────────────────
def mq2_thread():
    """MQ-2 가스 센서 모니터링 스레드"""
    spi = spidev.SpiDev()
    try:
        spi.open(SPI_BUS, SPI_DEV)
        spi.max_speed_hz = SPI_MAX_HZ
        print("MQ-2 가스 센서 시작")
        
        while RUN:
            adc = spi.xfer2([1, (8 + MQ2_CHANNEL) << 4, 0])
            value = ((adc[1] & 3) << 8) + adc[2]
            voltage = value * 3.3 / 1023.0
            set_state(mq2_raw=value, mq2_voltage=round(voltage, 3))
            mq2_calibration_update(value)
            time.sleep(1.0)
    except Exception as e:
        sys.stderr.write(f"[MQ-2] 오류: {e}\n")
    finally:
        try:
            spi.close()
        except:
            pass

# ───────────────────────── DS18B20 ─────────────────────────
W1_DEVICE_FILE = None

def ensure_onewire_ready(timeout=5.0):
    """1-Wire 장치 준비 대기"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        devs = glob.glob(os.path.join(W1_BASE, '28*'))
        if devs:
            return os.path.join(devs[0], 'w1_slave')
        time.sleep(0.2)
    return None

def read_temp_c():
    """온도 센서 읽기"""
    global W1_DEVICE_FILE
    if not W1_DEVICE_FILE or not os.path.exists(W1_DEVICE_FILE):
        W1_DEVICE_FILE = ensure_onewire_ready()
        if not W1_DEVICE_FILE:
            return None
    try:
        with open(W1_DEVICE_FILE, 'r') as f:
            lines = f.readlines()
        if not lines or not lines[0].strip().endswith('YES'):
            time.sleep(0.1)
            with open(W1_DEVICE_FILE, 'r') as f:
                lines = f.readlines()
        if lines and lines[0].strip().endswith('YES'):
            pos = lines[1].find('t=')
            if pos != -1:
                return float(lines[1][pos+2:]) / 1000.0
    except Exception as e:
        sys.stderr.write(f"[TEMP] 읽기 실패: {e}\n")
    return None

def temp_thread():
    """온도 센서 모니터링 스레드"""
    miss_logged = False
    print("온도 센서 시작")
    
    while RUN:
        t = read_temp_c()
        if t is not None:
            set_state(temp_c=round(t, 2))
            miss_logged = False
        else:
            if not miss_logged:
                sys.stderr.write("[TEMP] 1-Wire 장치 미검출/CRC 대기…\n")
                miss_logged = True
        time.sleep(1.0)

# ───────────────────────── PMS7003M ─────────────────────────
def read_pms7003(ser):
    """PMS7003M 센서 데이터 파싱"""
    b = ser.read(1)
    if b != b'\x42':
        return None
    if ser.read(1) != b'\x4d':
        return None
    frame = ser.read(30)
    if len(frame) != 30:
        return None
    
    length = struct.unpack('>H', frame[0:2])[0]
    if length != 28:
        return None
    
    data = frame[0:28]
    checksum = struct.unpack('>H', frame[28:30])[0]
    calc = (0x42 + 0x4D + sum(data)) & 0xFFFF
    if checksum != calc:
        return None
    
    vals = struct.unpack('>HHHHHHHHHHHHHH', data)
    return vals[3], vals[4], vals[5]  # pm1, pm25, pm10

def pms_thread():
    """미세먼지 센서 모니터링 스레드"""
    try:
        ser = serial.Serial(PMS_PORT, baudrate=PMS_BAUD, timeout=2.0)
        ser.reset_input_buffer()
        print("PMS7003M 미세먼지 센서 시작")
    except Exception as e:
        sys.stderr.write(f"[PMS] 포트 열기 실패: {e}\n")
        return
    
    try:
        while RUN:
            r = read_pms7003(ser)
            if r:
                pm1, pm25, pm10 = r
                set_state(pm1=pm1, pm25=pm25, pm10=pm10)
            time.sleep(1.0)
    except Exception as e:
        sys.stderr.write(f"[PMS] 오류: {e}\n")
    finally:
        try:
            ser.close()
        except:
            pass

# ───────────────────────── 알람(래칭) ─────────────────────────
_prev_alarm = None
_latch_until = 0.0

def alarm_check():
    """임계값 체크 및 알람 제어"""
    global _prev_alarm, _latch_until
    
    with STATE_LOCK:
        flame = bool(STATE.get("flame") or False)
        mq2_delta = STATE.get("mq2_delta") or 0
        mq2_raw = STATE.get("mq2_raw") or 0
        gas_volt = STATE.get("mq2_voltage") or 0.0
        pm1 = STATE.get("pm1") or 0
        pm25 = STATE.get("pm25") or 0
        pm10 = STATE.get("pm10") or 0
        tempc = STATE.get("temp_c")

    alarm = False
    alarm_reasons = []
    
    # 1. 불꽃 감지
    if flame == FLAME_ALERT:
        alarm = True
        alarm_reasons.append("불꽃 감지")
    
    # 2. 가스 농도
    if mq2_raw > GAS_THRESHOLD_RAW:
        alarm = True
        alarm_reasons.append(f"가스 농도 높음 ({mq2_raw})")
    
    # 3. 가스 전압
    if gas_volt > GAS_VOLTAGE_MAX:
        alarm = True
        alarm_reasons.append(f"가스 전압 높음 ({gas_volt:.2f}V)")
    
    # 4. 가스 급증
    if mq2_delta > GAS_DELTA_ALERT:
        alarm = True
        alarm_reasons.append(f"가스 급증 (Delta={mq2_delta})")
    
    # 5. 온도
    if (TEMP_THRESHOLD is not None) and (tempc is not None):
        if tempc > TEMP_THRESHOLD:
            alarm = True
            alarm_reasons.append(f"고온 ({tempc}°C)")
        elif tempc > TEMP_WARNING:
            alarm_reasons.append(f"온도 경고 ({tempc}°C)")
    
    # 6. 미세먼지
    if pm1 > PM1_THRESHOLD:
        alarm = True
        alarm_reasons.append(f"PM1.0 높음 ({pm1})")
    
    if pm25 > PM25_THRESHOLD:
        alarm = True
        alarm_reasons.append(f"PM2.5 높음 ({pm25})")
    
    if pm10 > PM10_THRESHOLD:
        alarm = True
        alarm_reasons.append(f"PM10 높음 ({pm10})")

    now = time.time()
    if alarm:
        _latch_until = max(_latch_until, now + ALARM_LATCH_SEC)
    latched = alarm or (now < _latch_until)

    if _prev_alarm != latched:
        status = "[알람 ON]" if latched else "[알람 OFF]"
        reasons = " | ".join(alarm_reasons) if alarm_reasons else "정상"
        print(f"[ALARM] {status} - {reasons}")
        _prev_alarm = latched

    set_buzzer(latched)

# ───────────────────────── 서버 전송 ─────────────────────────
def send_to_server(data, retry=0):
    """
    센서 데이터를 Render 서버로 전송
    
    Args:
        data: 센서 데이터 딕셔너리
        retry: 현재 재시도 횟수
    
    Returns:
        bool: 전송 성공 여부
    """
    try:
        payload = {
            "device_id": DEVICE_ID,
            "data": data,
            "ts": time.time()
        }
        
        response = requests.post(
            f"{API_SERVER}/ingest",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            with STATS_LOCK:
                STATS["total_sent"] += 1
                STATS["last_success"] = datetime.now().isoformat()
            print(f"[OK] 서버 전송 성공 (#{STATS['total_sent']})")
            return True
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        error_msg = "서버 타임아웃 (10초)"
        if retry < MAX_RETRIES:
            print(f"[WARN] {error_msg} - 재시도 {retry + 1}/{MAX_RETRIES}...")
            time.sleep(RETRY_DELAY)
            return send_to_server(data, retry + 1)
        else:
            sys.stderr.write(f"[ERROR] {error_msg} - 최대 재시도 초과\n")
            update_stats(failed_sent=STATS["failed_sent"] + 1, last_error=error_msg)
            return False
            
    except requests.exceptions.ConnectionError as e:
        error_msg = f"서버 연결 실패: {str(e)[:50]}"
        if retry < MAX_RETRIES:
            print(f"[WARN] {error_msg} - 재시도 {retry + 1}/{MAX_RETRIES}...")
            time.sleep(RETRY_DELAY)
            return send_to_server(data, retry + 1)
        else:
            sys.stderr.write(f"[ERROR] {error_msg} - 최대 재시도 초과\n")
            update_stats(failed_sent=STATS["failed_sent"] + 1, last_error=error_msg)
            return False
            
    except Exception as e:
        error_msg = f"전송 오류: {str(e)[:50]}"
        sys.stderr.write(f"[ERROR] {error_msg}\n")
        update_stats(failed_sent=STATS["failed_sent"] + 1, last_error=error_msg)
        return False

# ───────────────────────── 메인 ─────────────────────────
def main():
    """메인 실행 함수"""
    global RUN
    
    # 1-Wire 준비
    _ = ensure_onewire_ready()

    # 센서 스레드 시작
    threads = [
        threading.Thread(target=flame_thread, daemon=True, name="FlameThread"),
        threading.Thread(target=mq2_thread, daemon=True, name="MQ2Thread"),
        threading.Thread(target=temp_thread, daemon=True, name="TempThread"),
        threading.Thread(target=pms_thread, daemon=True, name="PMSThread"),
    ]
    
    for th in threads:
        th.start()
        time.sleep(0.1)  # 스레드 시작 간격

    print("=" * 70)
    print("모든 센서 스레드 시작 완료!")
    print(f"{SEND_INTERVAL}초마다 서버로 데이터 전송 중...")
    print("종료하려면 Ctrl+C를 누르세요")
    print("=" * 70)
    
    last_send = 0
    loop_count = 0
    
    try:
        while True:
            loop_count += 1
            
            # 센서 데이터 읽기
            with STATE_LOCK:
                s = dict(STATE)

            # 서버 전송용 데이터 (내부 상태 제외)
            sensor_data = {
                "flame": s.get("flame"),
                "gas": s.get("mq2_raw"),
                "gas_voltage": s.get("mq2_voltage"),
                "temperature": s.get("temp_c"),
                "pm1": s.get("pm1"),
                "pm25": s.get("pm25"),
                "pm10": s.get("pm10"),
                "gas_delta": s.get("mq2_delta"),
            }
            
            # 콘솔 출력 (간결하게)
            if loop_count % 5 == 0:  # 5초마다만 출력
                flame_status = '[FLAME]' if sensor_data['flame'] else '[OK]'
                print(f"[DATA] [{datetime.now().strftime('%H:%M:%S')}] " +
                      f"온도:{sensor_data['temperature']}C " +
                      f"가스:{sensor_data['gas']} " +
                      f"PM2.5:{sensor_data['pm25']} " +
                      f"{flame_status}")

            # 주기적으로 서버 전송
            now = time.time()
            if now - last_send >= SEND_INTERVAL:
                success = send_to_server(sensor_data)
                last_send = now
                
                # 통계 출력 (10회 전송마다)
                if STATS["total_sent"] % 10 == 0 and STATS["total_sent"] > 0:
                    success_rate = (STATS["total_sent"] / 
                                  (STATS["total_sent"] + STATS["failed_sent"]) * 100)
                    print(f"[STATS] 성공 {STATS['total_sent']}회, " +
                          f"실패 {STATS['failed_sent']}회, " +
                          f"성공률 {success_rate:.1f}%")

            # 알람 체크
            alarm_check()
            
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\n[STOP] 사용자 종료 요청...")
    except Exception as e:
        sys.stderr.write(f"\n[ERROR] 예상치 못한 오류: {e}\n")
    finally:
        print("정리 중...")
        RUN = False
        time.sleep(0.5)
        set_buzzer(False)
        set_led(False)
        GPIO.cleanup()
        
        # 최종 통계
        print("=" * 70)
        print("최종 통계:")
        print(f"   전송 성공: {STATS['total_sent']}회")
        print(f"   전송 실패: {STATS['failed_sent']}회")
        if STATS['last_success']:
            print(f"   마지막 성공: {STATS['last_success']}")
        if STATS['last_error']:
            print(f"   마지막 오류: {STATS['last_error']}")
        print("=" * 70)
        print("정리 완료 - 프로그램 종료")

if __name__ == "__main__":
    main()
