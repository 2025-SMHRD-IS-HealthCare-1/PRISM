// Configuration
const CONFIG = {
  API_BASE_URL:
    window.location.hostname === "localhost"
      ? "http://localhost:8000" // FastAPI 백엔드 서버
      : "https://prism-api-ay8q.onrender.com", // Render 배포 서버
  WS_BASE_URL:
    window.location.hostname === "localhost"
      ? "ws://localhost:8000" // WebSocket 로컬
      : "wss://prism-api-ay8q.onrender.com", // WebSocket Render
  UPDATE_INTERVAL: 5000, // 5초마다 업데이트
  CHART_UPDATE_INTERVAL: 30000, // 30초마다 차트 업데이트
  EVENT_UPDATE_INTERVAL: 60000, // 1분마다 이벤트 업데이트
  SENSOR_TIMEOUT: 60000, // 60초(1분) 동안 데이터 없으면 미연결로 간주
  EVENT_DUPLICATE_TIMEOUT: 60000, // 1분 내 중복 이벤트 무시
};

// Global State
let currentZone = "testbox";
let sensorData = {
  testbox: {
    temperature: 0,
    gas: 0,
    dust: 0,
    pm25: 0,
    pm1: 0,
    pm10: 0,
    gas_delta: 0,
    flame: false,
    status: "normal",
  },
};
let historicalData = [];
let historicalDataCache = {}; // 과거 데이터 캐시 (날짜별로 저장)
let updateInterval = null;
let chartUpdateInterval = null;
let eventUpdateInterval = null; // 이벤트 업데이트 인터벌
let isConnected = false; // 센서 연결 상태
let lastUpdateTime = null;
let previousSensorData = {}; // 이전 센서 데이터 (임계값 체크용)
let eventCount = 0;
let lastDailyUpdate = null; // 마지막 일간 업데이트 시간
let websocket = null; // WebSocket 연결
let reconnectTimer = null; // 재연결 타이머

// 센서 연결 상태 추적 {zone: {connected: true/false, lastUpdate: timestamp}}
let sensorConnectionStatus = {
  testbox: { connected: false, lastUpdate: null },
  warehouse: { connected: false, lastUpdate: null },
  inspection: { connected: false, lastUpdate: null },
  machine: { connected: false, lastUpdate: null },
};

// 이벤트 중복 방지를 위한 최근 이벤트 추적 {eventKey: timestamp}
let recentEvents = {};

// 불꽃 감지 이벤트 고정 (최상단 표시)
let fireAlertEvent = null;

// 센서 타임아웃 체크 인터벌
let sensorTimeoutCheckInterval = null;

// Charts
let historicalChart = null;
let detailChart = null;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  initializeClock();
  initializeCharts();
  initializeEvents(); // 초기 이벤트 생성
  updateCameraCount(); // 초기 카메라 카운트
  updateSystemStatus(); // 초기 시스템 상태

  // ✅ 초기 미연결 상태 표시 (WebSocket 연결 전)
  showDisconnectedState();

  connectWebSocket(); // WebSocket 연결 (연결되면 데이터 수신 시 자동 복구)
  startDataUpdates();
  loadHistoricalData();
  scheduleDailyUpdate(); // 일간 데이터 갱신 스케줄
  startEventUpdates(); // 이벤트 업데이트 시작
  startSensorTimeoutCheck(); // 센서 타임아웃 체크 시작
});

// Clock
function initializeClock() {
  updateClock();
  setInterval(updateClock, 1000);
}

function updateClock() {
  const now = new Date();
  const timeString = now.toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
  document.getElementById("current-time").textContent = timeString;
}

// ═══════════════════════ WebSocket 연결 ═══════════════════════
function connectWebSocket() {
  try {
    console.log(`🔌 WebSocket 연결 시도: ${CONFIG.WS_BASE_URL}/ws`);
    websocket = new WebSocket(`${CONFIG.WS_BASE_URL}/ws`);

    websocket.onopen = () => {
      console.log("✅ WebSocket 연결 성공");
      isConnected = true;
      // WebSocket 연결은 서버 통신 연결이지 센서 연결이 아님
      // 센서 연결 상태는 데이터를 받을 때만 updateSensorConnectionStatus에서 처리
      // ⚠️ 중요: WebSocket 연결 != 센서 연결 (센서는 데이터 수신 시점에만 연결로 간주)

      // 재연결 타이머 클리어
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }

      // ⚠️ WebSocket 연결 시 센서 미연결 메시지를 표시하지 않음
      // (기존 센서 연결 상태 유지 - 데이터가 들어오면 자동으로 연결됨)
    };

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log("📨 WebSocket 메시지:", message);

        if (message.type === "update") {
          // 실시간 센서 데이터 업데이트
          const deviceId = message.device_id;
          const data = message.data;

          // device_id에서 zone 추출 (예: rpi-01 -> testbox로 매핑)
          let zone = "testbox"; // 기본값을 testbox로 설정
          if (deviceId && deviceId.includes("rpi")) {
            zone = "testbox"; // 라즈베리 파이는 testbox에 매핑
          } else if (deviceId && deviceId.includes("opi")) {
            zone = "warehouse"; // 오렌지 파이는 warehouse에 매핑 (예시)
          }

          console.log(`📊 [${deviceId}] → zone: ${zone}, data:`, data);

          // 센서 데이터 업데이트
          updateSensorDataFromWebSocket(zone, data, message);

          // 🔥 위험 알람 체크 및 이벤트 생성
          if (message.alert && message.reasons && message.reasons.length > 0) {
            showDangerAlert(message.level, message.reasons);

            // 각 경고 이유를 이벤트로 추가
            message.reasons.forEach((reason) => {
              addEvent(
                message.level || "warning",
                `${getZoneName(zone)} ${reason}`
              );
            });
          }

          // updateSensorConnectionStatus는 updateSensorDataFromWebSocket 내부에서 처리
        } else if (message.type === "init") {
          // 초기 데이터 수신
          console.log("📊 초기 데이터 수신:", message.data);
          addEvent("normal", "센서 데이터 로드 완료");
        } else if (message.type === "pong") {
          // ping/pong 응답
          console.log("🏓 Pong 수신");
        } else if (message.type === "cctv_fire_detected") {
          // 🔥 CCTV 화재 감지 이벤트
          const zone = message.zone || "unknown";
          const confidence = message.confidence || 0;
          addEvent(
            "danger",
            `CCTV 화재 감지! (${getZoneName(zone)}, 신뢰도: ${(
              confidence * 100
            ).toFixed(1)}%)`
          );

          // 브라우저 알림
          if (Notification.permission === "granted") {
            new Notification("PRISM 화재 경보", {
              body: `${getZoneName(
                zone
              )} CCTV에서 화재가 감지되었습니다! (신뢰도: ${(
                confidence * 100
              ).toFixed(1)}%)`,
              icon: "/image/prism_logo.png",
              tag: "fire-alert",
              requireInteraction: true,
            });
          }
        } else if (message.type === "sensor_disconnected") {
          // 센서 연결 끊김 이벤트
          const zone = message.zone || "unknown";
          addEvent("warning", `${getZoneName(zone)} 센서 연결 끊김`);
          updateSensorConnectionStatus(zone, false);
        } else if (message.type === "sensor_connection_status") {
          // 센서 연결 상태 변경 이벤트
          const zone = message.zone || "unknown";
          const connected = message.connected;
          const deviceId = message.device_id;

          if (connected) {
            addEvent(
              "normal",
              `${getZoneName(zone)} 센서 연결됨 (${deviceId})`
            );
          } else {
            addEvent(
              "warning",
              `${getZoneName(zone)} 센서 연결 끊김 (${deviceId})`
            );
          }

          updateSensorConnectionStatus(zone, connected);
        }
      } catch (error) {
        console.error("WebSocket 메시지 파싱 실패:", error);
      }
    };

    websocket.onerror = (error) => {
      console.error("❌ WebSocket 오류:", error);
      isConnected = false;

      // ⚠️ 중요: WebSocket 오류 시 센서 연결 상태를 초기화하지 않음
      // 센서 연결 상태는 타임아웃(60초)으로만 관리
    };

    websocket.onclose = () => {
      console.log("🔌 WebSocket 연결 종료");
      isConnected = false;

      // ✅ WebSocket 연결 종료 시 모든 센서를 미연결로 전환
      Object.keys(sensorConnectionStatus).forEach((zone) => {
        if (sensorConnectionStatus[zone].connected) {
          updateSensorConnectionStatus(zone, false);
        }
      });

      // 현재 선택된 구역의 UI를 미연결 상태로 표시
      showDisconnectedState();

      // 5초 후 재연결 시도
      if (!reconnectTimer) {
        reconnectTimer = setTimeout(() => {
          console.log("🔄 WebSocket 재연결 시도...");
          connectWebSocket();
        }, 5000);
      }
    };
  } catch (error) {
    console.error("WebSocket 연결 실패:", error);
    isConnected = false;
    addEvent("warning", "서버 연결 실패");
  }
}

function updateSensorDataFromWebSocket(zone, data, message) {
  // 이전 데이터 저장
  const prevData = previousSensorData[zone] || {};

  // 센서 데이터 저장
  const status = calculateStatus(data);
  sensorData[zone] = {
    temperature: parseFloat(data.temperature) || 0,
    gas: parseFloat(data.gas) || 0,
    dust: parseFloat(data.pm25 || data.dust) || 0,
    pm25: parseFloat(data.pm25) || 0,
    pm1: parseFloat(data.pm1) || 0,
    pm10: parseFloat(data.pm10) || 0,
    gas_delta: parseFloat(data.gas_delta) || 0,
    flame: data.flame || false,
    status: status,
  };

  // 🔥 불꽃이 꺼지면 고정된 불꽃 이벤트 제거
  if (prevData.flame === true && data.flame === false) {
    if (fireAlertEvent && fireAlertEvent.parentNode) {
      fireAlertEvent.parentNode.removeChild(fireAlertEvent);
      fireAlertEvent = null;
      addEvent("normal", `${getZoneName(zone)} 불꽃 감지 해제`);
    }
  }

  // 임계값 체크 및 이벤트 생성 (zone 파라미터 추가)
  checkThresholdAndCreateEvent(data, prevData, zone);

  // 이전 데이터 업데이트
  previousSensorData[zone] = {
    temperature: parseFloat(data.temperature) || 0,
    gas: parseFloat(data.gas) || 0,
    dust: parseFloat(data.pm25 || data.dust) || 0,
    pm25: parseFloat(data.pm25) || 0,
    pm1: parseFloat(data.pm1) || 0,
    pm10: parseFloat(data.pm10) || 0,
    gas_delta: parseFloat(data.gas_delta) || 0,
    flame: data.flame || false,
  };

  // UI 업데이트 (현재 선택된 구역만)
  if (zone === currentZone) {
    updateSensorDisplay(data);
    // 연결 상태 UI는 updateSensorConnectionStatus에서 처리
  }

  updateZoneStatus(zone);
  updateOverallStatus();

  // 센서 연결 상태 업데이트 (타임스탬프 갱신 및 연결 상태 관리)
  updateSensorConnectionStatus(zone, true);
}

function showDangerAlert(level, reasons) {
  // 위험 알람 표시
  console.warn(`🚨 ${level} 알람:`, reasons);

  // 이벤트 추가
  const eventText = reasons.join(" | ");
  addEvent(level, eventText);

  // 브라우저 알림 (권한이 있는 경우)
  if (Notification.permission === "granted") {
    new Notification("🚨 PRISM 위험 알림", {
      body: eventText,
      icon: "/image/prism_logo.png",
    });
  }
}

// Data Updates
function startDataUpdates() {
  // WebSocket을 사용하므로 HTTP 폴링은 비활성화
  // WebSocket이 실시간으로 데이터를 전송하므로 주기적 fetch는 불필요

  // 초기 데이터 로드 (선택 사항 - WebSocket으로 받을 수 있음)
  // fetchSensorData();

  // 주기적 업데이트는 WebSocket이 처리하므로 주석 처리
  // if (updateInterval) clearInterval(updateInterval);
  // updateInterval = setInterval(fetchSensorData, CONFIG.UPDATE_INTERVAL);

  // 차트는 덜 자주 업데이트 (30초)
  if (chartUpdateInterval) clearInterval(chartUpdateInterval);
  chartUpdateInterval = setInterval(
    loadHistoricalData,
    CONFIG.CHART_UPDATE_INTERVAL
  );
}

async function fetchSensorData() {
  // 이 함수는 WebSocket 사용 시 호출되지 않음 (startDataUpdates에서 비활성화됨)
  // WebSocket이 끊어졌을 때 백업용으로만 사용 가능
  try {
    // FastAPI 엔드포인트에서 센서 데이터 가져오기
    const response = await fetch(
      `${CONFIG.API_BASE_URL}/api/sensors/${currentZone}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error("센서 데이터를 가져올 수 없습니다");
    }

    const data = await response.json();
    lastUpdateTime = new Date();
    updateSensorData(data);
    // updateConnectionStatus는 WebSocket에서만 처리
  } catch (error) {
    console.error("센서 데이터 가져오기 실패:", error);
    // 센서 미연결 상태 표시
    showDisconnectedState();
  }
}

function updateConnectionStatus(connected) {
  const statusText = document.getElementById("selected-zone-status-text");
  const statusDot = document.getElementById("selected-zone-status");
  const statusBadge = document.getElementById("status-badge");

  if (connected) {
    // 연결됨 - 센서 상태에 따라 표시
    const status = sensorData[currentZone]?.status || "normal";
    const statusTexts = {
      danger: "위험",
      warning: "경고",
      caution: "주의",
      normal: "연결됨", // "정상" → "연결됨"으로 변경
    };
    statusText.textContent = statusTexts[status];

    // "연결됨" 상태는 파란색, 나머지는 원래 상태 색상
    const displayStatus = status === "normal" ? "connected" : status;
    statusDot.className = `status-dot status-${displayStatus}`;

    // 상태에 따라 배지 테두리 색상 변경
    if (statusBadge) {
      const colorVar =
        status === "normal" ? "--color-connected" : `--color-${status}`;
      statusBadge.style.borderColor = getComputedStyle(
        document.documentElement
      ).getPropertyValue(colorVar);
    }
  } else {
    // 연결 안됨
    statusText.textContent = "센서 미연결";
    statusDot.className = "status-dot status-inactive";
    if (statusBadge) {
      statusBadge.style.borderColor = "var(--border-color)";
    }
  }
}

function showDisconnectedState() {
  // 센서 값을 '센서 미연결 상태..' 로 표시
  const disconnectMessage = "센서 미연결 상태..";
  document.getElementById("temp-value").textContent = disconnectMessage;
  document.getElementById("gas-value").textContent = disconnectMessage;
  document.getElementById("dust-value").textContent = disconnectMessage;
  document.getElementById("flame-value").textContent = disconnectMessage;

  document.getElementById("detail-temp-value").textContent = disconnectMessage;
  document.getElementById("detail-gas-value").textContent = disconnectMessage;
  document.getElementById("detail-dust-value").textContent = disconnectMessage;
  document.getElementById("detail-flame-value").textContent = disconnectMessage;

  // 상태 텍스트도 업데이트
  const statusTextEl = document.getElementById("status-text-display");
  if (statusTextEl) {
    statusTextEl.textContent = "센서 미연결";
    statusTextEl.style.color = "#94a3b8";
  }

  // sensorData 초기화 (더미 데이터 제거)
  sensorData = {};

  // 구역 박스 상태도 미연결로 업데이트
  updateZoneStatusToInactive(currentZone);
}
function updateSensorData(data) {
  // 이전 데이터 저장
  const prevData = previousSensorData[data.zone] || {};

  // 센서 데이터 저장
  const status = calculateStatus(data);
  sensorData[data.zone] = {
    temperature: parseFloat(data.temperature),
    gas: parseFloat(data.gas),
    dust: parseFloat(data.dust),
    flame: data.flame,
    status: status,
  };

  // 임계값 체크 및 이벤트 생성 (zone 파라미터 추가)
  checkThresholdAndCreateEvent(data, prevData, data.zone);

  // 이전 데이터 업데이트
  previousSensorData[data.zone] = {
    temperature: parseFloat(data.temperature),
    gas: parseFloat(data.gas),
    dust: parseFloat(data.dust),
    flame: data.flame,
  };

  // UI 업데이트
  updateSensorDisplay(data);
  updateZoneStatus(data.zone);
  updateOverallStatus();
  // updateConnectionStatus는 WebSocket에서 처리하므로 제거
  updateSensorCount();
}

function calculateStatus(data) {
  // 임계값 기준으로 상태 계산
  // - 위험: AND 조건 (모든 센서가 위험 임계값 초과)
  // - 경고/주의: OR 조건 (하나라도 해당 임계값 초과)
  const temp = parseFloat(data.temperature);
  const gas = parseFloat(data.gas);
  const pm25 = parseFloat(data.pm25 || data.dust);
  const flame = data.flame;

  // 불꽃 감지 시 무조건 위험
  if (flame) {
    return "danger";
  }

  // 위험 (danger) - 모든 센서가 위험 임계값 초과 (AND 조건)
  // temperature: 61+, gas: 401+, pm2.5: 76+
  if (temp > 60 && gas > 400 && pm25 > 75) {
    return "danger";
  }
  // 경고 (warning) - 하나라도 경고 임계값 초과 (OR 조건)
  // temperature: 46-60, gas: 201-400, pm2.5: 51-75
  else if (temp > 45 || gas > 200 || pm25 > 50) {
    return "warning";
  }
  // 주의 (caution) - 하나라도 주의 임계값 초과 (OR 조건)
  // temperature: 36-45, gas: 101-200, pm2.5: 26-50
  else if (temp > 35 || gas > 100 || pm25 > 25) {
    return "caution";
  }

  return "normal";
}

function updateSensorDisplay(data) {
  // 미세먼지 종합 계산 (PM2.5 우선, PM1과 PM10도 고려)
  let dustValue = data.pm25 || data.dust || 0;
  const pm1 = data.pm1 || 0;
  const pm10 = data.pm10 || 0;

  // PM2.5가 없으면 PM1과 PM10의 평균으로 추정
  if (!data.pm25 && !data.dust) {
    if (pm1 > 0 && pm10 > 0) {
      dustValue = Math.round((pm1 + pm10) / 2);
    } else if (pm1 > 0) {
      dustValue = pm1;
    } else if (pm10 > 0) {
      dustValue = Math.round(pm10 / 2); // PM10의 절반 정도가 PM2.5
    }
  }

  // 센서 패널 업데이트
  document.getElementById("temp-value").textContent = `${data.temperature}°C`;
  document.getElementById("gas-value").textContent = `${data.gas} ppm`;
  document.getElementById("dust-value").textContent = `${dustValue} μg/m³`;
  document.getElementById("flame-value").textContent = data.flame
    ? "감지됨!"
    : "미감지";

  // 현재 상태값 표시 업데이트
  updateStatusDisplay(data);

  // 상세 팝업 업데이트
  document.getElementById(
    "detail-temp-value"
  ).textContent = `${data.temperature}°C`;
  document.getElementById("detail-gas-value").textContent = `${data.gas} ppm`;
  document.getElementById(
    "detail-dust-value"
  ).textContent = `${dustValue} μg/m³`;
  document.getElementById("detail-flame-value").textContent = data.flame
    ? "감지됨!"
    : "미감지";

  // 불꽃 감지시 스타일 변경
  const flameElements = document.querySelectorAll('[id$="flame-value"]');
  flameElements.forEach((el) => {
    if (data.flame) {
      el.style.color = "var(--color-danger)";
      el.style.fontWeight = "bold";
    } else {
      el.style.color = "";
      el.style.fontWeight = "";
    }
  });
}

function updateStatusDisplay(data) {
  const status = calculateStatus(data);
  const statusColors = {
    danger: "#ef4444",
    warning: "#f59e0b",
    caution: "#eab308",
    normal: "#10b981",
  };

  const statusTexts = {
    danger: "위험",
    warning: "경고",
    caution: "주의",
    normal: "정상",
  };

  // 상태 텍스트와 바 색상 표시
  const statusTextEl = document.getElementById("status-text-display");
  if (statusTextEl) {
    statusTextEl.textContent = statusTexts[status];
    statusTextEl.style.color = statusColors[status];
    // ::before 가상 요소의 배경색 설정
    statusTextEl.style.setProperty("--status-bar-color", statusColors[status]);
  }
}

function updateZoneStatus(zone) {
  // 센서 연결 상태 먼저 확인
  const isConnectedToZone = sensorConnectionStatus[zone]?.connected || false;

  if (!isConnectedToZone) {
    // 센서 미연결 - 비활성 상태로 표시
    updateZoneStatusToInactive(zone);
    return;
  }

  const status = sensorData[zone]?.status || "normal";
  const statusClass = `status-${status}`;

  // 구역 박스 상태 업데이트
  const zoneBox = document.querySelector(`.zone-${zone}`);
  if (zoneBox) {
    const statusIndicator = zoneBox.querySelector(".zone-status");
    if (statusIndicator) {
      // 센서 연결됨 - LED 표시등 켜기
      statusIndicator.className = `zone-status ${statusClass}`;
    }

    // 🔥 위험 상태일 때 박스 전체를 빨간색으로 표시
    if (status === "danger") {
      zoneBox.style.borderColor = "var(--color-danger)";
      zoneBox.style.backgroundColor = "rgba(239, 68, 68, 0.1)";
      zoneBox.style.boxShadow = "0 0 20px rgba(239, 68, 68, 0.3)";
    } else if (status === "warning") {
      zoneBox.style.borderColor = "var(--color-warning)";
      zoneBox.style.backgroundColor = "rgba(245, 158, 11, 0.05)";
      zoneBox.style.boxShadow = "0 0 15px rgba(245, 158, 11, 0.2)";
    } else if (status === "caution") {
      zoneBox.style.borderColor = "var(--color-caution)";
      zoneBox.style.backgroundColor = "rgba(59, 130, 246, 0.05)";
      zoneBox.style.boxShadow = "";
    } else {
      zoneBox.style.borderColor = "";
      zoneBox.style.backgroundColor = "";
      zoneBox.style.boxShadow = "";
    }
  }
}

// 구역 상태를 비활성(회색)으로 업데이트
function updateZoneStatusToInactive(zone) {
  const zoneBox = document.querySelector(`.zone-${zone}`);
  if (zoneBox) {
    const statusIndicator = zoneBox.querySelector(".zone-status");
    if (statusIndicator) {
      // 센서 미연결 - LED 표시등 끄기 (회색)
      statusIndicator.className = "zone-status status-inactive";
    }

    // 박스 스타일 초기화
    zoneBox.style.borderColor = "";
    zoneBox.style.backgroundColor = "";
    zoneBox.style.boxShadow = "";
  }
}

function updateOverallStatus() {
  const counts = {
    danger: 0,
    warning: 0,
    caution: 0,
    normal: 0,
  };

  // 활성화된 구역만 카운트 (inactive 클래스가 없는 구역)
  const activeZones = document.querySelectorAll(".zone-box:not(.inactive)");
  activeZones.forEach((zoneBox) => {
    const zoneName = zoneBox.dataset.zone;
    if (sensorData[zoneName]) {
      counts[sensorData[zoneName].status]++;
    }
  });

  document.getElementById("danger-count").textContent = counts.danger;
  document.getElementById("warning-count").textContent = counts.warning;
  document.getElementById("caution-count").textContent = counts.caution;
  document.getElementById("normal-count").textContent = counts.normal;

  // 활성 센서 카운트 업데이트
  updateSensorCount();

  // 시스템 상태 업데이트
  updateSystemStatus();
}

// Daily Update Scheduler - 매일 오전 7시에 과거 데이터 갱신
function scheduleDailyUpdate() {
  const now = new Date();
  const next7AM = new Date(now);
  next7AM.setHours(7, 0, 0, 0);

  // 이미 오전 7시를 지났다면 내일 오전 7시로 설정
  if (now.getTime() > next7AM.getTime()) {
    next7AM.setDate(next7AM.getDate() + 1);
  }

  const timeUntilNext7AM = next7AM.getTime() - now.getTime();

  console.log(`다음 일간 데이터 갱신: ${next7AM.toLocaleString("ko-KR")}`);

  // Last Update 시간을 07:00 AM으로 설정
  updateLastUpdateTime();

  // 첫 실행 예약
  setTimeout(() => {
    loadHistoricalData();
    updateLastUpdateTime();
    lastDailyUpdate = new Date();
    console.log("일간 데이터 갱신 완료 (오전 7:00)");

    // 이후 24시간마다 반복
    setInterval(() => {
      loadHistoricalData();
      updateLastUpdateTime();
      lastDailyUpdate = new Date();
      console.log("일간 데이터 갱신 완료 (오전 7:00)");
    }, 24 * 60 * 60 * 1000); // 24시간
  }, timeUntilNext7AM);
}

// Historical Data
async function loadHistoricalData() {
  try {
    const today = new Date().toDateString();

    // 캐시된 데이터가 있고 오늘 날짜이면 사용
    if (historicalDataCache[today]) {
      console.log("캐시된 과거 데이터 사용");
      historicalData = historicalDataCache[today];
      updateHistoricalChart();
      return;
    }

    // 주간 데이터 요청 (7일)
    const response = await fetch(
      `${CONFIG.API_BASE_URL}/api/history/${currentZone}?days=7`
    );

    if (!response.ok) {
      throw new Error("과거 데이터를 가져올 수 없습니다");
    }

    const data = await response.json();

    // 빈 배열이면 고정된 가짜 데이터 생성 (현재 날짜 제외한 6일)
    if (data.length === 0) {
      console.log("센서 데이터 없음 - 고정된 과거 데이터 생성");
      historicalData = generateFixedHistoricalData();
      // 가짜 데이터는 캐시에 저장
      historicalDataCache[today] = historicalData;
      updateHistoricalChart();
      return;
    }

    // 과거 데이터를 캐시에 저장 (날짜별로)
    historicalDataCache[today] = data;
    historicalData = data;

    updateHistoricalChart();
  } catch (error) {
    console.error("과거 데이터 가져오기 실패:", error);
    // 캐시가 있으면 사용
    if (historicalDataCache[today]) {
      historicalData = historicalDataCache[today];
      updateHistoricalChart();
    } else {
      // 캐시도 없으면 고정된 가짜 데이터 생성
      historicalData = generateFixedHistoricalData();
      updateHistoricalChart();
    }
  }
}

// 고정된 과거 데이터 생성 (현재 날짜 제외한 6일)
function generateFixedHistoricalData() {
  const fixedData = [];
  const now = new Date();

  // 고정된 데이터 값 (6일치)
  const fixedValues = [
    { temperature: 23.5, gas: 28.3, dust: 12.8 },
    { temperature: 24.1, gas: 31.2, dust: 14.5 },
    { temperature: 22.8, gas: 26.7, dust: 11.9 },
    { temperature: 25.3, gas: 33.8, dust: 15.2 },
    { temperature: 23.9, gas: 29.5, dust: 13.6 },
    { temperature: 24.7, gas: 32.1, dust: 14.8 },
  ];

  // 6일 전부터 어제까지의 데이터 (현재 날짜는 제외)
  for (let i = 6; i >= 1; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    date.setHours(7, 0, 0, 0); // 07:00 AM으로 설정

    const valueIndex = 6 - i; // 0~5 인덱스
    fixedData.push({
      timestamp: date.toISOString(),
      ...fixedValues[valueIndex],
    });
  }

  return fixedData;
}

// Charts
function initializeCharts() {
  // Historical Chart
  const historicalCtx = document
    .getElementById("historical-chart")
    .getContext("2d");
  historicalChart = new Chart(historicalCtx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "위험",
          data: [],
          borderColor: "#ef4444",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          tension: 0.4,
        },
        {
          label: "경고",
          data: [],
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          tension: 0.4,
        },
        {
          label: "주의",
          data: [],
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          tension: 0.4,
        },
        {
          label: "정상",
          data: [],
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false, // 애니메이션 비활성화
      plugins: {
        legend: {
          labels: {
            color: "#cbd5e1",
          },
        },
      },
      scales: {
        x: {
          ticks: { color: "#cbd5e1" },
          grid: { color: "#475569" },
        },
        y: {
          beginAtZero: true,
          min: 0,
          ticks: {
            color: "#cbd5e1",
            callback: function (value) {
              // 음수는 표시하지 않음
              return value >= 0 ? value : "";
            },
          },
          grid: { color: "#475569" },
        },
      },
    },
  });

  // Detail Chart
  const detailCtx = document.getElementById("detail-chart").getContext("2d");
  detailChart = new Chart(detailCtx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "온도 (°C)",
          data: [],
          borderColor: "#ef4444",
          tension: 0.4,
          yAxisID: "y",
        },
        {
          label: "가스 (ppm)",
          data: [],
          borderColor: "#f59e0b",
          tension: 0.4,
          yAxisID: "y",
        },
        {
          label: "미세먼지 (g/m³)",
          data: [],
          borderColor: "#3b82f6",
          tension: 0.4,
          yAxisID: "y",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false, // 애니메이션 비활성화
      plugins: {
        legend: {
          labels: {
            color: "#cbd5e1",
          },
        },
      },
      scales: {
        x: {
          ticks: { color: "#cbd5e1" },
          grid: { color: "#475569" },
        },
        y: {
          type: "linear",
          position: "left",
          min: 0,
          max: 100,
          ticks: { color: "#cbd5e1" },
          grid: { color: "#475569" },
        },
      },
    },
  });
}

function updateHistoricalChart() {
  if (!historicalChart) return;

  // 데이터가 없으면 빈 차트 표시
  if (historicalData.length === 0) {
    historicalChart.data.labels = ["데이터 없음"];
    historicalChart.data.datasets[0].data = [0];
    historicalChart.data.datasets[1].data = [0];
    historicalChart.data.datasets[2].data = [0];
    historicalChart.data.datasets[3].data = [0];
    historicalChart.update("none");
    return;
  }

  // 주간 데이터 레이블 (일별)
  const labels = historicalData.map((d) => {
    const date = new Date(d.timestamp);
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const weekday = ["일", "월", "화", "수", "목", "금", "토"][date.getDay()];
    return `${month}/${day} (${weekday})`;
  });

  historicalChart.data.labels = labels;
  historicalChart.data.datasets[0].data = historicalData.map((d) =>
    calculateStatus(d) === "danger" ? 1 : 0
  );
  historicalChart.data.datasets[1].data = historicalData.map((d) =>
    calculateStatus(d) === "warning" ? 1 : 0
  );
  historicalChart.data.datasets[2].data = historicalData.map((d) =>
    calculateStatus(d) === "caution" ? 1 : 0
  );
  historicalChart.data.datasets[3].data = historicalData.map((d) =>
    calculateStatus(d) === "normal" ? 1 : 0
  );

  // 'none' 모드로 업데이트하여 애니메이션 제거 (깜빡임 방지)
  historicalChart.update("none");

  // Last Update 시간 업데이트
  updateLastUpdateTime();
}

function updateLastUpdateTime() {
  // 항상 07:00 AM으로 표시
  const lastUpdateElement = document.getElementById("last-update");
  if (lastUpdateElement) {
    lastUpdateElement.textContent = "Last Update: 07:00 AM";
  }
}

function updateDetailChart() {
  if (!detailChart) return;

  // 최근 2시간 데이터 (30분 간격)
  const recentData = historicalData.slice(-4);
  const labels = recentData.map((d, i) => `${i * 30}분 전`);

  detailChart.data.labels = labels;
  detailChart.data.datasets[0].data = recentData.map((d) => d.temperature);
  detailChart.data.datasets[1].data = recentData.map((d) => d.gas);
  detailChart.data.datasets[2].data = recentData.map((d) => d.dust);

  // 'none' 모드로 업데이트하여 애니메이션 제거
  detailChart.update("none");
}

// Popup Functions
function openCCTV(zone) {
  const zoneData = sensorData[zone];

  // 구역이 비활성화 상태이거나 데이터가 없으면 에러 표시
  if (!zoneData || zone !== "testbox") {
    showError(
      "문제가 생겼습니다.<br>카메라가 연결이 되지 않았거나 문제가 생겼습니다."
    );
    return;
  }

  // CCTV 정보 업데이트
  document.getElementById(
    "cctv-id"
  ).textContent = `CCTV-${zone.toUpperCase()}-001`;
  document.getElementById("cctv-location").textContent = getZoneName(zone);

  // CCTV 스트림 URL 설정 (실제 스트림 URL로 변경 필요)
  const cctvStream = document.getElementById("cctv-stream");
  cctvStream.src = `${CONFIG.API_BASE_URL}/api/cctv/${zone}/stream`;
  cctvStream.onerror = () => {
    cctvStream.src =
      'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480"><rect width="640" height="480" fill="%23000"/><text x="50%" y="50%" fill="%23fff" text-anchor="middle" font-size="20">CCTV 연결 대기중...</text></svg>';
  };

  showPopup("cctv-popup");
}

function openDetail(zone) {
  const zoneData = sensorData[zone];

  if (!zoneData || zone !== "testbox") {
    showError("해당 구역의 상세 정보를 불러올 수 없습니다.");
    return;
  }

  // 상세 정보 업데이트
  const zoneName = getZoneName(zone);
  document.getElementById("detail-zone-name").textContent = zoneName;
  document.getElementById("detail-zone").textContent = zoneName;

  // 차트 업데이트
  updateDetailChart();

  showPopup("detail-popup");
}

function openZoneSelector() {
  showPopup("zone-selector-popup");
}

function selectZone(zone) {
  // 비활성화된 구역은 선택 불가
  if (zone !== "testbox") {
    return;
  }

  currentZone = zone;

  // 선택된 구역 표시 업데이트
  document.querySelectorAll(".zone-list-item").forEach((item) => {
    item.classList.remove("active");
  });
  event.target.closest(".zone-list-item").classList.add("active");

  // 센서 패널 업데이트
  document.getElementById("selected-zone-name").textContent = getZoneName(zone);
  updateZoneStatus(zone);

  // 센서 연결 상태 확인 및 UI 업데이트
  const isZoneConnected = sensorConnectionStatus[zone]?.connected || false;
  updateConnectionStatus(isZoneConnected);

  // 연결된 경우 센서 데이터 표시, 미연결 시 미연결 상태 표시
  if (isZoneConnected && sensorData[zone]) {
    updateSensorDisplay(sensorData[zone]);
  } else {
    showDisconnectedState();
  }

  closePopup("zone-selector-popup");
}

function showPopup(popupId) {
  document.getElementById(popupId).classList.add("show");
}

function closePopup(popupId) {
  document.getElementById(popupId).classList.remove("show");
}

function showError(message) {
  document.getElementById("error-text").innerHTML = "<p>" + message + "</p>";
  showPopup("error-popup");
}

// CCTV Controls
function zoomIn() {
  console.log("Zoom In");
  // CCTV 확대 기능 구현
}

function zoomOut() {
  console.log("Zoom Out");
  // CCTV 축소 기능 구현
}

function refreshCCTV() {
  const cctvStream = document.getElementById("cctv-stream");
  const currentSrc = cctvStream.src;
  cctvStream.src = "";
  setTimeout(() => {
    cctvStream.src = currentSrc;
  }, 100);
}

function fullscreenCCTV() {
  const cctvStream = document.getElementById("cctv-stream");
  if (cctvStream.requestFullscreen) {
    cctvStream.requestFullscreen();
  }
}

// Helper Functions
function getZoneName(zone) {
  const zoneNames = {
    testbox: "TEST BOX",
    warehouse: "원자재 창고",
    inspection: "제품 검사실",
    machine: "기계/전기실",
  };
  return zoneNames[zone] || zone;
}

// Event Logging
function addEvent(level, message) {
  // level이 없으면 기본값 "normal"
  if (typeof level === "string" && !message) {
    message = level;
    level = "normal";
  }

  // 🔥 중복 이벤트 방지 (1분 내 동일 메시지 무시)
  const eventKey = `${level}:${message}`;
  const now = Date.now();

  if (recentEvents[eventKey]) {
    const timeSinceLastEvent = now - recentEvents[eventKey];
    if (timeSinceLastEvent < CONFIG.EVENT_DUPLICATE_TIMEOUT) {
      // 1분 내 중복 이벤트는 무시
      return;
    }
  }

  // 이벤트 타임스탬프 기록
  recentEvents[eventKey] = now;

  const eventsList = document.getElementById("events-list");
  const timeString = new Date(now).toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  const eventItem = document.createElement("div");
  eventItem.className = `event-item event-${level}`;

  // 이모지 제거 - 아이콘 없이 메시지만 표시
  eventItem.innerHTML = `
        <span class="event-time">${timeString}</span>
        <span class="event-text">${message}</span>
    `;

  // 🔥 위험(danger) 이벤트는 최상단에 고정
  const isDangerEvent = level === "danger";
  const isFireAlert = message.includes("불꽃") || message.includes("화재");

  if (isDangerEvent) {
    // 불꽃 이벤트인 경우 기존 불꽃 이벤트 제거
    if (isFireAlert && fireAlertEvent && fireAlertEvent.parentNode) {
      fireAlertEvent.parentNode.removeChild(fireAlertEvent);
    }

    // 위험 이벤트를 최상단에 삽입
    eventsList.insertBefore(eventItem, eventsList.firstChild);

    // 불꽃 이벤트는 전역 변수로 저장
    if (isFireAlert) {
      fireAlertEvent = eventItem;
    }

    // 위험 이벤트에 특별 스타일 추가
    eventItem.style.backgroundColor = "rgba(239, 68, 68, 0.1)";
    eventItem.style.borderLeft = "3px solid var(--color-danger)";
  } else {
    // 일반 이벤트는 불꽃 이벤트 다음에 삽입
    if (fireAlertEvent && fireAlertEvent.parentNode) {
      // 불꽃 이벤트 바로 다음에 삽입
      fireAlertEvent.parentNode.insertBefore(
        eventItem,
        fireAlertEvent.nextSibling
      );
    } else {
      // 불꽃 이벤트가 없으면 최상단에 삽입
      eventsList.insertBefore(eventItem, eventsList.firstChild);
    }
  }

  // 최대 10개 항목만 유지 (불꽃 이벤트는 카운트에서 제외)
  const regularEvents = Array.from(eventsList.children).filter(
    (el) => el !== fireAlertEvent
  );
  while (regularEvents.length > 10) {
    const lastEvent = regularEvents[regularEvents.length - 1];
    if (lastEvent !== fireAlertEvent) {
      eventsList.removeChild(lastEvent);
    }
    regularEvents.pop();
  }

  // 일일 이벤트 카운트 증가
  eventCount++;
  updateEventCount();
}

// 초기 이벤트 생성 (더미 데이터 제거)
function initializeEvents() {
  // 시스템 시작 메시지만 표시
  addEvent("normal", "시스템 시작 - 센서 연결 대기 중...");
}

// 임계값 체크 및 이벤트 생성
function checkThresholdAndCreateEvent(currentData, prevData, zoneName) {
  // zoneName이 제공되지 않으면 currentData.zone 사용
  const zone = getZoneName(zoneName || currentData.zone);

  // 온도 체크 (새로운 임계값)
  // 정상: 0-35, 주의: 36-45, 경고: 46-60, 위험: 61+
  if (prevData.temperature !== undefined) {
    if (currentData.temperature > 60 && prevData.temperature <= 60) {
      addEvent("danger", `${zone} 온도 위험 (${currentData.temperature}°C)`);
    } else if (currentData.temperature > 45 && prevData.temperature <= 45) {
      addEvent("warning", `${zone} 온도 경고 (${currentData.temperature}°C)`);
    } else if (currentData.temperature > 35 && prevData.temperature <= 35) {
      addEvent("caution", `${zone} 온도 주의 (${currentData.temperature}°C)`);
    }
  }

  // 가스 체크 (새로운 임계값)
  // 정상: 0-100, 주의: 101-200, 경고: 201-400, 위험: 401+
  if (prevData.gas !== undefined) {
    if (currentData.gas > 400 && prevData.gas <= 400) {
      addEvent("danger", `${zone} 가스 농도 위험 (${currentData.gas})`);
    } else if (currentData.gas > 200 && prevData.gas <= 200) {
      addEvent("warning", `${zone} 가스 농도 경고 (${currentData.gas})`);
    } else if (currentData.gas > 100 && prevData.gas <= 100) {
      addEvent("caution", `${zone} 가스 농도 주의 (${currentData.gas})`);
    }
  }

  // 가스 급증 체크
  if (currentData.gas_delta !== undefined && prevData.gas_delta !== undefined) {
    if (currentData.gas_delta >= 50 && prevData.gas_delta < 50) {
      addEvent("danger", `${zone} 가스 급증 감지 (Δ=${currentData.gas_delta})`);
    } else if (currentData.gas_delta >= 30 && prevData.gas_delta < 30) {
      addEvent("warning", `${zone} 가스 증가 (Δ=${currentData.gas_delta})`);
    }
  }

  // PM2.5 체크 (새로운 임계값)
  // 정상: 0-25, 주의: 26-50, 경고: 51-75, 위험: 76+
  const pm25 = currentData.pm25 || currentData.dust;
  const prevPm25 = prevData.pm25 || prevData.dust;
  if (pm25 !== undefined && prevPm25 !== undefined) {
    if (pm25 > 75 && prevPm25 <= 75) {
      addEvent("danger", `${zone} PM2.5 위험 (${pm25} μg/m³)`);
    } else if (pm25 > 50 && prevPm25 <= 50) {
      addEvent("warning", `${zone} PM2.5 경고 (${pm25} μg/m³)`);
    } else if (pm25 > 25 && prevPm25 <= 25) {
      addEvent("caution", `${zone} PM2.5 주의 (${pm25} μg/m³)`);
    }
  }

  // PM1.0 체크
  if (currentData.pm1 !== undefined && prevData.pm1 !== undefined) {
    if (currentData.pm1 >= 50 && prevData.pm1 < 50) {
      addEvent("danger", `${zone} PM1.0 위험 (${currentData.pm1} μg/m³)`);
    }
  }

  // PM10 체크
  if (currentData.pm10 !== undefined && prevData.pm10 !== undefined) {
    if (currentData.pm10 >= 100 && prevData.pm10 < 100) {
      addEvent("danger", `${zone} PM10 위험 (${currentData.pm10} μg/m³)`);
    } else if (currentData.pm10 >= 75 && prevData.pm10 < 75) {
      addEvent("warning", `${zone} PM10 경고 (${currentData.pm10} μg/m³)`);
    } else if (currentData.pm10 >= 50 && prevData.pm10 < 50) {
      addEvent("caution", `${zone} PM10 주의 (${currentData.pm10} μg/m³)`);
    }
  }

  // 불꽃 감지
  if (!prevData.flame && currentData.flame) {
    addEvent("danger", `${zone} 불꽃 감지!`);
  }
}

// 센서 및 카메라 카운트 업데이트
function updateSensorCount() {
  // 연결된 센서 수 계산 (sensorConnectionStatus 기반)
  const connectedSensors = Object.values(sensorConnectionStatus).filter(
    (status) => status.connected
  ).length;

  // 전체 구역 수
  const totalZones = Object.keys(sensorConnectionStatus).length;

  document.getElementById(
    "active-sensors"
  ).textContent = `${connectedSensors}/${totalZones}개`;
}

// 센서 연결 상태 업데이트
function updateSensorConnectionStatus(zone, connected) {
  if (!sensorConnectionStatus[zone]) {
    sensorConnectionStatus[zone] = { connected: false, lastUpdate: null };
  }

  const wasConnected = sensorConnectionStatus[zone].connected;

  // 타임스탬프 업데이트: connected=true일 때만 갱신
  // connected=false는 타임아웃에서 호출되므로 타임스탬프 갱신 불필요
  if (connected) {
    sensorConnectionStatus[zone].lastUpdate = Date.now();
  }

  // 연결 상태 업데이트
  if (!wasConnected && connected) {
    // 미연결 → 연결 (최초 연결 또는 재연결)
    sensorConnectionStatus[zone].connected = true;
    addEvent("normal", `${getZoneName(zone)} 센서 연결됨`);
    updateSensorCount();

    // 현재 선택된 구역이면 UI 업데이트
    if (zone === currentZone) {
      updateConnectionStatus(true);
    }
  } else if (wasConnected && connected) {
    // 연결 유지 (이미 연결된 상태에서 데이터 계속 수신)
    sensorConnectionStatus[zone].connected = true;
    // 연결 유지 상태에서는 이벤트나 UI 업데이트 불필요
  } else if (wasConnected && !connected) {
    // 연결 → 미연결 (연결 끊김)
    sensorConnectionStatus[zone].connected = false;
    updateSensorCount();

    // 현재 선택된 구역이면 UI 업데이트
    if (zone === currentZone) {
      updateConnectionStatus(false);
    }
  }
}

function updateCameraCount() {
  // TODO: CCTV 연결 상태 추적 구현 필요
  // 현재는 하드코딩
  const activeCameras = 0;
  const totalCameras = 4;
  document.getElementById(
    "active-cameras"
  ).textContent = `${activeCameras}/${totalCameras}개`;
}

function updateEventCount() {
  document.getElementById("daily-events").textContent = `${eventCount}건`;
}

function updateSystemStatus() {
  // 센서 연결 상태 확인
  const systemStatusEl = document.getElementById("system-status");

  if (!isConnected) {
    // 센서 미연결 시 빨간 글씨로 "비정상" 표시 (배경색 없음)
    systemStatusEl.textContent = "비정상";
    systemStatusEl.style.color = "#ef4444"; // 빨간색
    systemStatusEl.style.backgroundColor = "transparent"; // 배경색 제거
    systemStatusEl.className = "stat-value status-danger";
    return;
  }

  // 활성화된 구역만 확인 (inactive 클래스가 없는 구역)
  const activeZones = document.querySelectorAll(".zone-box:not(.inactive)");
  const activeZoneNames = Array.from(activeZones).map(
    (zone) => zone.dataset.zone
  );

  // 활성화된 구역의 센서 데이터만 체크
  const activeSensorData = Object.entries(sensorData).filter(([zoneName, _]) =>
    activeZoneNames.includes(zoneName)
  );

  const hasData = activeSensorData.length > 0;
  const hasDanger = activeSensorData.some(
    ([_, zone]) => zone.status === "danger"
  );
  const hasWarning = activeSensorData.some(
    ([_, zone]) => zone.status === "warning"
  );

  let statusText = "정상";
  let statusClass = "stat-value";

  if (!hasData) {
    statusText = "대기중";
  } else if (hasDanger) {
    statusText = "위험";
    statusClass = "stat-value status-danger";
  } else if (hasWarning) {
    statusText = "경고";
    statusClass = "stat-value status-warning";
  } else {
    statusClass = "stat-value status-online";
  }

  systemStatusEl.textContent = statusText;
  systemStatusEl.className = statusClass;
  systemStatusEl.style.color = ""; // 기본 색상 사용
}

// 이벤트 업데이트 시작 (1분마다)
function startEventUpdates() {
  // 1분마다 새로운 이벤트 추가
  eventUpdateInterval = setInterval(() => {
    // 센서가 연결되어 있고 데이터가 있을 때만 이벤트 생성
    if (isConnected && sensorData[currentZone]) {
      const zone = getZoneName(currentZone);
      const data = sensorData[currentZone];

      // 무작위로 이벤트 생성 (10% 확률)
      if (Math.random() < 0.1) {
        const eventTypes = [
          `${zone} 센서 상태 점검 완료`,
          `${zone} 데이터 동기화 완료`,
          `${zone} 시스템 정상 작동 중`,
        ];
        const randomEvent =
          eventTypes[Math.floor(Math.random() * eventTypes.length)];
        addEvent("normal", randomEvent);
      }
    }
  }, CONFIG.EVENT_UPDATE_INTERVAL); // 1분마다
}

// 센서 타임아웃 체크 (10초마다)
function startSensorTimeoutCheck() {
  sensorTimeoutCheckInterval = setInterval(() => {
    const now = Date.now();

    Object.entries(sensorConnectionStatus).forEach(([zone, status]) => {
      if (status.connected && status.lastUpdate) {
        const timeSinceUpdate = now - status.lastUpdate;

        // 60초(1분) 이상 데이터 없으면 미연결로 처리
        if (timeSinceUpdate > CONFIG.SENSOR_TIMEOUT) {
          console.warn(
            `⚠️ ${zone} 센서 타임아웃 (${Math.floor(timeSinceUpdate / 1000)}초)`
          );

          // updateSensorConnectionStatus를 통해 일관성 있게 처리
          updateSensorConnectionStatus(zone, false);
          addEvent("warning", `${getZoneName(zone)} 센서 연결 끊김`);
          updateZoneStatusToInactive(zone);

          // 현재 선택된 구역의 타임아웃이면 미연결 상태 표시
          if (zone === currentZone) {
            showDisconnectedState();
          }
        }
      }
    });
  }, 10000); // 10초마다 체크
}

// Cleanup
window.addEventListener("beforeunload", () => {
  if (updateInterval) clearInterval(updateInterval);
  if (chartUpdateInterval) clearInterval(chartUpdateInterval);
  if (eventUpdateInterval) clearInterval(eventUpdateInterval);
});

// 팝업 외부 클릭시 닫기
window.addEventListener("click", (e) => {
  if (e.target.classList.contains("popup")) {
    e.target.classList.remove("show");
  }
});
