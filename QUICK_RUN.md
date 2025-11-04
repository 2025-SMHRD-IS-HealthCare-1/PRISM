# 🚀 PRISM 빠른 실행 가이드

모든 파일을 정리했습니다! 이제 올바른 경로로 실행하세요.

## 📂 새로운 폴더 구조

```
PRISM/
├── server/              # ✅ 서버 파일들
├── iot_devices/         # ✅ IoT 디바이스 스크립트
├── public/              # ✅ 웹 프론트엔드
├── scripts/             # ✅ 유틸리티 스크립트
├── docs/                # ✅ 문서들
└── tests/               # ✅ 테스트 파일
```

## 🎯 실행 명령어 (업데이트됨!)

### 1️⃣ 서버 실행

```bash
python server/api_server.py
```

### 2️⃣ 테스트 데이터 전송

```bash
python scripts/test_sender.py
```

### 3️⃣ 라즈베리파이에서 실행

```bash
export API_SERVER="http://192.168.1.XXX:8000"
export DEVICE_ID="rpi-01"
python iot_devices/raspberry_pi_sensor.py
```

## 📚 문서 위치

- **상세 구조**: [STRUCTURE.md](STRUCTURE.md)
- **빠른 시작**: [docs/QUICKSTART.md](docs/QUICKSTART.md)
- **WebSocket 가이드**: [docs/WEBSOCKET_GUIDE.md](docs/WEBSOCKET_GUIDE.md)
- **설치 가이드**: [docs/INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md)

---

**⚠️ 중요:** 파일 경로가 변경되었으니 위의 새 경로를 사용하세요!
