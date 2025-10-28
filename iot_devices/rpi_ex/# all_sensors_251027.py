# all_sensors.py
# Raspberry Pi: Flame(GPIO) + MQ-2(MCP3008/SPI) + DS18B20(1-Wire) + PMS7003M(UART) + Buzzer
#  - Passive buzzer(기본): PWM 3 kHz
#  - MQ-2 자동 기준선/EMA/Δ(증가량) 감지 + 절대값 임계 동시 사용
#  - 1초마다 필요한 값만 JSON 출력
# Ctrl+C 로 종료

import threading, time, sys, glob, struct, json, os
import RPi.GPIO as GPIO
import spidev, serial

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

# 임계치 (원하는 값으로 조정)
GAS_THRESHOLD_RAW = 300        # MQ-2 원시값 절대 임계
PM25_THRESHOLD    = 80         # μg/m³
FLAME_ALERT       = True       # 불꽃 감지 시 알람
TEMP_THRESHOLD    = 30.0       # None이면 온도 무시

# 알람 래칭(최소 울림시간)
ALARM_LATCH_SEC   = 2.0

# MQ-2 보정/감지 파라미터
MQ2_BASELINE_SEC  = 10         # 시작 후 30초는 기준선 학습
MQ2_EMA_ALPHA     = 0.20       # EMA 평활 계수 (0.1~0.3 권장)
MQ2_DELTA_ALERT   = 60         # baseline 대비 증가량(Δ) 임계

# ───────────────────────── 공유 상태 ─────────────────────────
STATE = {
    "flame": None,
    "mq2_raw": None, "mq2_voltage": None,
    "temp_c": None,
    "pm1": None, "pm25": None, "pm10": None,

    # MQ-2 보정 내부 상태
    "mq2_baseline": None, "mq2_ema": None, "mq2_delta": None, "_mq2_t0": None
}
STATE_LOCK = threading.Lock()
RUN = True

def set_state(**kwargs):
    with STATE_LOCK:
        STATE.update(kwargs)

# ───────────────────────── 부저 ─────────────────────────
GPIO.setup(BUZZER_PIN, GPIO.OUT)
_pwm = None  # 패시브 PWM 핸들

def set_buzzer(on: bool):
    global _pwm
    if BUZZER_IS_PASSIVE:
        if on and _pwm is None:
            _pwm = GPIO.PWM(BUZZER_PIN, PASSIVE_FREQ_HZ)
            _pwm.start(PASSIVE_DUTY)
        elif not on and _pwm is not None:
            _pwm.stop(); _pwm = None
    else:
        if BUZZER_ACTIVE_LOW:
            GPIO.output(BUZZER_PIN, GPIO.LOW if on else GPIO.HIGH)
        else:
            GPIO.output(BUZZER_PIN, GPIO.HIGH if on else GPIO.LOW)

# 짧은 셀프테스트 (원치 않으면 주석)
set_buzzer(False)
for _ in range(2):
    set_buzzer(True);  time.sleep(0.12)
    set_buzzer(False); time.sleep(0.12)

# ───────────────────────── LED ─────────────────────────
GPIO.setup(FLAME_LED_PIN, GPIO.OUT)
def set_led(on: bool):
    GPIO.output(FLAME_LED_PIN, GPIO.HIGH if on else GPIO.LOW)  # 필요 시 반전

# ───────────────────────── Flame ─────────────────────────
def flame_thread():
    GPIO.setup(FLAME_SENSOR_PIN, GPIO.IN)
    set_led(False)

    def read_flame():
        raw = GPIO.input(FLAME_SENSOR_PIN)  # 0/1
        return (raw == 0) if FLAME_ACTIVE_LOW else (raw == 1)

    last = None
    while RUN:
        now = read_flame()
        if now != last:
            set_state(flame=now)
            set_led(now)
            last = now
        time.sleep(0.1)

# ───────────────────────── MQ-2 보정 함수 ─────────────────────────
def mq2_calibration_update(raw: int):
    now = time.time()
    if STATE.get("_mq2_t0") is None:
        set_state(_mq2_t0=now, mq2_baseline=raw, mq2_ema=raw, mq2_delta=0)
        return

    ema_prev = STATE.get("mq2_ema") or raw
    ema = (MQ2_EMA_ALPHA * raw) + (1 - MQ2_EMA_ALPHA) * ema_prev

    base_prev = STATE.get("mq2_baseline") or raw
    if now - (STATE.get("_mq2_t0") or now) < MQ2_BASELINE_SEC:
        baseline = (0.02 * raw) + (0.98 * base_prev)  # 학습기
    else:
        baseline = base_prev                           # 고정(필요시 아주 느리게 추적 가능)

    delta = int(ema - baseline)
    set_state(mq2_ema=int(ema), mq2_baseline=int(baseline), mq2_delta=delta)

# ───────────────────────── MQ-2 (SPI) ─────────────────────────
def mq2_thread():
    spi = spidev.SpiDev()
    try:
        spi.open(SPI_BUS, SPI_DEV)
        spi.max_speed_hz = SPI_MAX_HZ
        while RUN:
            adc = spi.xfer2([1, (8 + MQ2_CHANNEL) << 4, 0])
            value = ((adc[1] & 3) << 8) + adc[2]            # 0~1023
            voltage = value * 3.3 / 1023.0
            set_state(mq2_raw=value, mq2_voltage=round(voltage, 3))

            mq2_calibration_update(value)
            time.sleep(1.0)
    finally:
        try: spi.close()
        except: pass

# ───────────────────────── DS18B20 ─────────────────────────
W1_DEVICE_FILE = None

def ensure_onewire_ready(timeout=5.0):
    # 부팅 시 raspi-config로 1-Wire 활성화가 되어 있으면 modprobe 불필요
    t0 = time.time()
    while time.time() - t0 < timeout:
        devs = glob.glob(os.path.join(W1_BASE, '28*'))
        if devs:
            return os.path.join(devs[0], 'w1_slave')
        time.sleep(0.2)
    return None

def read_temp_c():
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
        sys.stderr.write(f"[TEMP] read 실패: {e}\n")
    return None

def temp_thread():
    miss_logged = False
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
    b = ser.read(1)
    if b != b'\x42': return None
    if ser.read(1) != b'\x4d': return None
    frame = ser.read(30)
    if len(frame) != 30: return None
    length = struct.unpack('>H', frame[0:2])[0]
    if length != 28: return None
    data = frame[0:28]
    checksum = struct.unpack('>H', frame[28:30])[0]
    calc = (0x42 + 0x4D + sum(data)) & 0xFFFF
    if checksum != calc: return None
    vals = struct.unpack('>HHHHHHHHHHHHHH', data)
    return vals[3], vals[4], vals[5]  # pm1, pm25, pm10

def pms_thread():
    try:
        ser = serial.Serial(PMS_PORT, baudrate=PMS_BAUD, timeout=2.0)
        ser.reset_input_buffer()
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
    finally:
        try: ser.close()
        except: pass

# ───────────────────────── 알람(래칭) ─────────────────────────
_prev_alarm = None
_latch_until = 0.0

def alarm_check():
    global _prev_alarm, _latch_until
    with STATE_LOCK:
        flame     = bool(STATE.get("flame") or False)
        mq2_delta = STATE.get("mq2_delta") or 0
        mq2_raw   = STATE.get("mq2_raw") or 0
        pm25      = STATE.get("pm25") or 0
        tempc     = STATE.get("temp_c")

    alarm = False
    if flame == FLAME_ALERT:          alarm = True
    if mq2_delta > MQ2_DELTA_ALERT:   alarm = True   # 변화량 기준
    if mq2_raw   > GAS_THRESHOLD_RAW: alarm = True   # 절대값 기준
    if pm25      > PM25_THRESHOLD:    alarm = True
    if (TEMP_THRESHOLD is not None) and (tempc is not None) and (tempc > TEMP_THRESHOLD):
        alarm = True

    now = time.time()
    if alarm:
        _latch_until = max(_latch_until, now + ALARM_LATCH_SEC)
    latched = alarm or (now < _latch_until)

    if _prev_alarm != latched:
        print(f"[ALARM] -> {latched} (flame={flame}, Δ={mq2_delta}, raw={mq2_raw}, pm25={pm25}, temp={tempc})")
        _prev_alarm = latched

    set_buzzer(latched)

# ───────────────────────── 메인 ─────────────────────────
def main():
    global RUN
    _ = ensure_onewire_ready()  # 초기 확인(없어도 스레드에서 재시도)

    threads = [
        threading.Thread(target=flame_thread, daemon=True),
        threading.Thread(target=mq2_thread,   daemon=True),
        threading.Thread(target=temp_thread,  daemon=True),
        threading.Thread(target=pms_thread,   daemon=True),
    ]
    for th in threads: th.start()

    print("모든 센서 읽기 시작! (Ctrl+C로 종료)")
    try:
        while True:
            with STATE_LOCK:
                s = dict(STATE)

            # 출력은 필요한 필드만 (깔끔 출력)
            visible = {
                "flame": s.get("flame"),
                "mq2_raw": s.get("mq2_raw"),
                "mq2_voltage": s.get("mq2_voltage"),
                "temp_c": s.get("temp_c"),
                "pm1": s.get("pm1"),
                "pm25": s.get("pm25"),
                "pm10": s.get("pm10"),
            }
            print(json.dumps(visible, ensure_ascii=False))

            # ★ 추가: 파일로도 저장 (원자적 교체)
            try:
                with open('/tmp/sensors.json.tmp', 'w', encoding='utf-8') as f:
                    json.dump(visible, f, ensure_ascii=False)
                os.replace('/tmp/sensors.json.tmp', '/tmp/sensors.json')
            except Exception as e:
                sys.stderr.write(f"[SNAPSHOT] write fail: {e}\n")

            alarm_check()
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n종료 중...")
    finally:
        RUN = False
        time.sleep(0.3)
        set_buzzer(False)
        set_led(False)
        GPIO.cleanup()

if __name__ == "__main__":
    main()
