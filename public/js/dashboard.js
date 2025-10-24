// Configuration
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000', // FastAPI 서버 주소
    UPDATE_INTERVAL: 5000, // 5초마다 업데이트
    CHART_UPDATE_INTERVAL: 30000, // 30초마다 차트 업데이트
};

// Global State
let currentZone = 'testbox';
let sensorData = {
    testbox: {
        temperature: 0,
        gas: 0,
        dust: 0,
        flame: false,
        status: 'normal'
    }
};
let historicalData = [];
let updateInterval = null;
let chartUpdateInterval = null;
let isConnected = false; // 센서 연결 상태
let lastUpdateTime = null;
let previousSensorData = {}; // 이전 센서 데이터 (임계값 체크용)
let eventCount = 0;

// Charts
let historicalChart = null;
let detailChart = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeClock();
    initializeCharts();
    initializeEvents(); // 초기 이벤트 생성
    updateCameraCount(); // 초기 카메라 카운트
    updateSystemStatus(); // 초기 시스템 상태
    startDataUpdates();
    loadHistoricalData();
    scheduleDailyUpdate(); // 일간 데이터 갱신 스케줄
});

// Clock
function initializeClock() {
    updateClock();
    setInterval(updateClock, 1000);
}

function updateClock() {
    const now = new Date();
    const timeString = now.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
    document.getElementById('current-time').textContent = timeString;
}

// Data Updates
function startDataUpdates() {
    // 초기 데이터 로드
    fetchSensorData();
    
    // 주기적 업데이트 (새로고침 방지)
    if (updateInterval) clearInterval(updateInterval);
    if (chartUpdateInterval) clearInterval(chartUpdateInterval);
    
    updateInterval = setInterval(fetchSensorData, CONFIG.UPDATE_INTERVAL);
    // 차트는 덜 자주 업데이트 (30초)
    chartUpdateInterval = setInterval(loadHistoricalData, CONFIG.CHART_UPDATE_INTERVAL);
}

async function fetchSensorData() {
    try {
        // FastAPI 엔드포인트에서 센서 데이터 가져오기
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/sensors/${currentZone}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('센서 데이터를 가져올 수 없습니다');
        }
        
        const data = await response.json();
        isConnected = true;
        lastUpdateTime = new Date();
        updateSensorData(data);
        updateConnectionStatus(true);
    } catch (error) {
        console.error('센서 데이터 가져오기 실패:', error);
        isConnected = false;
        updateConnectionStatus(false);
        // 센서 미연결 상태 표시
        showDisconnectedState();
    }
}

function updateConnectionStatus(connected) {
    const statusText = document.getElementById('selected-zone-status-text');
    const statusDot = document.getElementById('selected-zone-status');
    const statusBadge = document.getElementById('status-badge');
    
    if (connected) {
        // 연결됨 - 센서 상태에 따라 표시
        const status = sensorData[currentZone]?.status || 'normal';
        const statusTexts = {
            danger: '위험',
            warning: '경고',
            caution: '주의',
            normal: '정상'
        };
        statusText.textContent = statusTexts[status];
        statusDot.className = `status-dot status-${status}`;
        
        // 상태에 따라 배지 테두리 색상 변경
        if (statusBadge) {
            statusBadge.style.borderColor = getComputedStyle(document.documentElement)
                .getPropertyValue(`--color-${status}`);
        }
    } else {
        // 연결 안됨
        statusText.textContent = '센서 미연결';
        statusDot.className = 'status-dot status-inactive';
        if (statusBadge) {
            statusBadge.style.borderColor = 'var(--border-color)';
        }
    }
}

function showDisconnectedState() {
    // 센서 값을 '미연결' 상태로 표시
    document.getElementById('temp-value').textContent = '--°C';
    document.getElementById('gas-value').textContent = '-- ppm';
    document.getElementById('dust-value').textContent = '-- μg/m³';
    document.getElementById('flame-value').textContent = '미감지';
    
    document.getElementById('detail-temp-value').textContent = '--°C';
    document.getElementById('detail-gas-value').textContent = '-- ppm';
    document.getElementById('detail-dust-value').textContent = '-- μg/m³';
    document.getElementById('detail-flame-value').textContent = '미감지';
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
        status: status
    };
    
    // 임계값 체크 및 이벤트 생성
    checkThresholdAndCreateEvent(data, prevData);
    
    // 이전 데이터 업데이트
    previousSensorData[data.zone] = {
        temperature: parseFloat(data.temperature),
        gas: parseFloat(data.gas),
        dust: parseFloat(data.dust),
        flame: data.flame
    };
    
    // UI 업데이트
    updateSensorDisplay(data);
    updateZoneStatus(data.zone);
    updateOverallStatus();
    updateConnectionStatus(true);
    updateSensorCount();
}

function calculateStatus(data) {
    // 임계값 기준으로 상태 계산
    const temp = parseFloat(data.temperature);
    const gas = parseFloat(data.gas);
    const dust = parseFloat(data.dust);
    const flame = data.flame;
    
    if (flame || temp > 50 || gas > 100 || dust > 50) {
        return 'danger';
    } else if (temp > 40 || gas > 70 || dust > 30) {
        return 'warning';
    } else if (temp > 30 || gas > 50 || dust > 20) {
        return 'caution';
    }
    return 'normal';
}

function updateSensorDisplay(data) {
    // 센서 패널 업데이트
    document.getElementById('temp-value').textContent = `${data.temperature}°C`;
    document.getElementById('gas-value').textContent = `${data.gas} ppm`;
    document.getElementById('dust-value').textContent = `${data.dust} g/m³`;
    document.getElementById('flame-value').textContent = data.flame ? '감지됨!' : '미감지';
    
    // 현재 상태값 표시 업데이트
    updateStatusDisplay(data);
    
    // 상세 팝업 업데이트
    document.getElementById('detail-temp-value').textContent = `${data.temperature}°C`;
    document.getElementById('detail-gas-value').textContent = `${data.gas} ppm`;
    document.getElementById('detail-dust-value').textContent = `${data.dust} g/m³`;
    document.getElementById('detail-flame-value').textContent = data.flame ? '감지됨!' : '미감지';
    
    // 불꽃 감지시 스타일 변경
    const flameElements = document.querySelectorAll('[id$="flame-value"]');
    flameElements.forEach(el => {
        if (data.flame) {
            el.style.color = 'var(--color-danger)';
            el.style.fontWeight = 'bold';
        } else {
            el.style.color = '';
            el.style.fontWeight = '';
        }
    });
}

function updateStatusDisplay(data) {
    const status = calculateStatus(data);
    const statusColors = {
        danger: '#ef4444',
        warning: '#f59e0b',
        caution: '#eab308',
        normal: '#10b981'
    };
    
    const statusTexts = {
        danger: '위험',
        warning: '경고',
        caution: '주의',
        normal: '정상'
    };
    
    // 상태 텍스트와 바 색상 표시
    const statusTextEl = document.getElementById('status-text-display');
    if (statusTextEl) {
        statusTextEl.textContent = statusTexts[status];
        statusTextEl.style.color = statusColors[status];
        // ::before 가상 요소의 배경색 설정
        statusTextEl.style.setProperty('--status-bar-color', statusColors[status]);
    }
}

function updateZoneStatus(zone) {
    if (!isConnected) return;
    
    const status = sensorData[zone].status;
    const statusClass = `status-${status}`;
    
    // 구역 박스 상태 업데이트
    const zoneBox = document.querySelector(`.zone-${zone}`);
    if (zoneBox) {
        const statusIndicator = zoneBox.querySelector('.zone-status');
        statusIndicator.className = `zone-status ${statusClass}`;
    }
}

function updateOverallStatus() {
    const counts = {
        danger: 0,
        warning: 0,
        caution: 0,
        normal: 0
    };
    
    let activeSensors = 0;
    Object.values(sensorData).forEach(zone => {
        counts[zone.status]++;
        activeSensors++;
    });
    
    document.getElementById('danger-count').textContent = counts.danger;
    document.getElementById('warning-count').textContent = counts.warning;
    document.getElementById('caution-count').textContent = counts.caution;
    document.getElementById('normal-count').textContent = counts.normal;
    
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
    
    console.log(`다음 일간 데이터 갱신: ${next7AM.toLocaleString('ko-KR')}`);
    
    // 첫 실행 예약
    setTimeout(() => {
        loadHistoricalData();
        console.log('일간 데이터 갱신 완료 (오전 7:00)');
        
        // 이후 24시간마다 반복
        setInterval(() => {
            loadHistoricalData();
            console.log('일간 데이터 갱신 완료 (오전 7:00)');
        }, 24 * 60 * 60 * 1000); // 24시간
    }, timeUntilNext7AM);
}

// Historical Data
async function loadHistoricalData() {
    try {
        // 주간 데이터 요청 (7일)
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/history/${currentZone}?days=7`);
        
        if (!response.ok) {
            throw new Error('과거 데이터를 가져올 수 없습니다');
        }
        
        const data = await response.json();
        historicalData = data;
        updateHistoricalChart();
    } catch (error) {
        console.error('과거 데이터 가져오기 실패:', error);
        // 테스트용 더미 데이터
        generateMockHistoricalData();
    }
}

function generateMockHistoricalData() {
    const data = [];
    const now = new Date();
    
    // 주간 데이터 생성 (7일 전부터 현재까지, 일별)
    for (let i = 6; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        date.setHours(12, 0, 0, 0); // 정오로 설정
        
        data.push({
            timestamp: date.toISOString(),
            temperature: 20 + Math.random() * 15,
            gas: 10 + Math.random() * 40,
            dust: 5 + Math.random() * 15
        });
    }
    
    historicalData = data;
    updateHistoricalChart();
}

// Charts
function initializeCharts() {
    // Historical Chart
    const historicalCtx = document.getElementById('historical-chart').getContext('2d');
    historicalChart = new Chart(historicalCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: '위험',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4
                },
                {
                    label: '경고',
                    data: [],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4
                },
                {
                    label: '주의',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                },
                {
                    label: '정상',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false, // 애니메이션 비활성화
            plugins: {
                legend: {
                    labels: {
                        color: '#cbd5e1'
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#cbd5e1' },
                    grid: { color: '#475569' }
                },
                y: {
                    ticks: { color: '#cbd5e1' },
                    grid: { color: '#475569' }
                }
            }
        }
    });
    
    // Detail Chart
    const detailCtx = document.getElementById('detail-chart').getContext('2d');
    detailChart = new Chart(detailCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: '온도 (°C)',
                    data: [],
                    borderColor: '#ef4444',
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: '가스 (ppm)',
                    data: [],
                    borderColor: '#f59e0b',
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: '미세먼지 (g/m³)',
                    data: [],
                    borderColor: '#3b82f6',
                    tension: 0.4,
                    yAxisID: 'y'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false, // 애니메이션 비활성화
            plugins: {
                legend: {
                    labels: {
                        color: '#cbd5e1'
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#cbd5e1' },
                    grid: { color: '#475569' }
                },
                y: {
                    type: 'linear',
                    position: 'left',
                    min: 0,
                    max: 100,
                    ticks: { color: '#cbd5e1' },
                    grid: { color: '#475569' }
                }
            }
        }
    });
}

function updateHistoricalChart() {
    if (!historicalChart || historicalData.length === 0) return;
    
    // 주간 데이터 레이블 (일별)
    const labels = historicalData.map(d => {
        const date = new Date(d.timestamp);
        const month = date.getMonth() + 1;
        const day = date.getDate();
        const weekday = ['일', '월', '화', '수', '목', '금', '토'][date.getDay()];
        return `${month}/${day} (${weekday})`;
    });
    
    historicalChart.data.labels = labels;
    historicalChart.data.datasets[0].data = historicalData.map(d => 
        calculateStatus(d) === 'danger' ? 1 : 0
    );
    historicalChart.data.datasets[1].data = historicalData.map(d => 
        calculateStatus(d) === 'warning' ? 1 : 0
    );
    historicalChart.data.datasets[2].data = historicalData.map(d => 
        calculateStatus(d) === 'caution' ? 1 : 0
    );
    historicalChart.data.datasets[3].data = historicalData.map(d => 
        calculateStatus(d) === 'normal' ? 1 : 0
    );
    
    // 'none' 모드로 업데이트하여 애니메이션 제거 (깜빡임 방지)
    historicalChart.update('none');
    
    // Last Update 시간 업데이트
    updateLastUpdateTime();
}

function updateLastUpdateTime() {
    const now = new Date();
    const timeString = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    const lastUpdateElement = document.getElementById('last-update');
    if (lastUpdateElement) {
        lastUpdateElement.textContent = `Last Update: ${timeString}`;
    }
}

function updateDetailChart() {
    if (!detailChart) return;
    
    // 최근 2시간 데이터 (30분 간격)
    const recentData = historicalData.slice(-4);
    const labels = recentData.map((d, i) => `${i * 30}분 전`);
    
    detailChart.data.labels = labels;
    detailChart.data.datasets[0].data = recentData.map(d => d.temperature);
    detailChart.data.datasets[1].data = recentData.map(d => d.gas);
    detailChart.data.datasets[2].data = recentData.map(d => d.dust);
    
    // 'none' 모드로 업데이트하여 애니메이션 제거
    detailChart.update('none');
}

// Popup Functions
function openCCTV(zone) {
    const zoneData = sensorData[zone];
    
    // 구역이 비활성화 상태이거나 데이터가 없으면 에러 표시
    if (!zoneData || zone !== 'testbox') {
        showError('문제가 생겼습니다.<br>카메라가 연결이 되지 않았거나 문제가 생겼습니다.');
        return;
    }
    
    // CCTV 정보 업데이트
    document.getElementById('cctv-id').textContent = `CCTV-${zone.toUpperCase()}-001`;
    document.getElementById('cctv-location').textContent = getZoneName(zone);
    
    // CCTV 스트림 URL 설정 (실제 스트림 URL로 변경 필요)
    const cctvStream = document.getElementById('cctv-stream');
    cctvStream.src = `${CONFIG.API_BASE_URL}/api/cctv/${zone}/stream`;
    cctvStream.onerror = () => {
        cctvStream.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480"><rect width="640" height="480" fill="%23000"/><text x="50%" y="50%" fill="%23fff" text-anchor="middle" font-size="20">CCTV 연결 대기중...</text></svg>';
    };
    
    showPopup('cctv-popup');
}

function openDetail(zone) {
    const zoneData = sensorData[zone];
    
    if (!zoneData || zone !== 'testbox') {
        showError('해당 구역의 상세 정보를 불러올 수 없습니다.');
        return;
    }
    
    // 상세 정보 업데이트
    const zoneName = getZoneName(zone);
    document.getElementById('detail-zone-name').textContent = zoneName;
    document.getElementById('detail-zone').textContent = zoneName;
    
    // 차트 업데이트
    updateDetailChart();
    
    showPopup('detail-popup');
}

function openZoneSelector() {
    showPopup('zone-selector-popup');
}

function selectZone(zone) {
    // 비활성화된 구역은 선택 불가
    if (zone !== 'testbox') {
        return;
    }
    
    currentZone = zone;
    
    // 선택된 구역 표시 업데이트
    document.querySelectorAll('.zone-list-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.zone-list-item').classList.add('active');
    
    // 센서 패널 업데이트
    document.getElementById('selected-zone-name').textContent = getZoneName(zone);
    updateZoneStatus(zone);
    
    closePopup('zone-selector-popup');
    
    // 새로운 구역 데이터 가져오기
    fetchSensorData();
}

function showPopup(popupId) {
    document.getElementById(popupId).classList.add('show');
}

function closePopup(popupId) {
    document.getElementById(popupId).classList.remove('show');
}

function showError(message) {
    document.getElementById('error-text').innerHTML = '<i class="fas fa-exclamation-triangle"></i><p>' + message + '</p>';
    showPopup('error-popup');
}

// CCTV Controls
function zoomIn() {
    console.log('Zoom In');
    // CCTV 확대 기능 구현
}

function zoomOut() {
    console.log('Zoom Out');
    // CCTV 축소 기능 구현
}

function refreshCCTV() {
    const cctvStream = document.getElementById('cctv-stream');
    const currentSrc = cctvStream.src;
    cctvStream.src = '';
    setTimeout(() => {
        cctvStream.src = currentSrc;
    }, 100);
}

function fullscreenCCTV() {
    const cctvStream = document.getElementById('cctv-stream');
    if (cctvStream.requestFullscreen) {
        cctvStream.requestFullscreen();
    }
}

// Helper Functions
function getZoneName(zone) {
    const zoneNames = {
        testbox: 'TEST BOX',
        warehouse: '원자재 창고',
        inspection: '제품 검사실',
        machine: '기계/전기실'
    };
    return zoneNames[zone] || zone;
}

// Event Logging
function addEvent(message) {
    const eventsList = document.getElementById('events-list');
    const now = new Date();
    const timeString = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    
    const eventItem = document.createElement('div');
    eventItem.className = 'event-item';
    eventItem.innerHTML = `
        <span class="event-time">${timeString}</span>
        <span class="event-text">${message}</span>
    `;
    
    eventsList.insertBefore(eventItem, eventsList.firstChild);
    
    // 최대 10개 항목만 유지
    while (eventsList.children.length > 10) {
        eventsList.removeChild(eventsList.lastChild);
    }
    
    // 일일 이벤트 카운트 증가
    eventCount++;
    updateEventCount();
}

// 초기 이벤트 생성
function initializeEvents() {
    const initialEvents = [
        '시스템 시작',
        '센서 연결 확인 완료',
        'TEST BOX 센서 정상',
        '원자재 창고 온도 안정',
        '제품 검사실 먼지 농도 정상',
        '기계/전기실 가스 농도 안정',
        '전체 구역 상태 정상'
    ];
    
    // 역순으로 추가 (최신이 위로 오도록)
    initialEvents.forEach((message, index) => {
        const eventsList = document.getElementById('events-list');
        const now = new Date();
        // 각 이벤트를 1분 간격으로 시간 설정
        now.setMinutes(now.getMinutes() - (initialEvents.length - 1 - index));
        const timeString = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        
        const eventItem = document.createElement('div');
        eventItem.className = 'event-item';
        eventItem.innerHTML = `
            <span class="event-time">${timeString}</span>
            <span class="event-text">${message}</span>
        `;
        
        eventsList.appendChild(eventItem);
    });
    
    eventCount = initialEvents.length;
    updateEventCount();
}

// 임계값 체크 및 이벤트 생성
function checkThresholdAndCreateEvent(currentData, prevData) {
    const zone = getZoneName(currentData.zone);
    
    // 온도 체크
    if (prevData.temperature !== undefined) {
        if (currentData.temperature >= 35 && prevData.temperature < 35) {
            addEvent(`${zone} 온도 위험 (${currentData.temperature}°C)`);
        } else if (currentData.temperature >= 30 && prevData.temperature < 30) {
            addEvent(`${zone} 온도 경고 (${currentData.temperature}°C)`);
        } else if (currentData.temperature >= 28 && prevData.temperature < 28) {
            addEvent(`${zone} 온도 주의 (${currentData.temperature}°C)`);
        }
    }
    
    // 가스 체크
    if (prevData.gas !== undefined) {
        if (currentData.gas >= 500 && prevData.gas < 500) {
            addEvent(`${zone} 가스 농도 위험 (${currentData.gas} ppm)`);
        } else if (currentData.gas >= 300 && prevData.gas < 300) {
            addEvent(`${zone} 가스 농도 경고 (${currentData.gas} ppm)`);
        } else if (currentData.gas >= 200 && prevData.gas < 200) {
            addEvent(`${zone} 가스 농도 주의 (${currentData.gas} ppm)`);
        }
    }
    
    // 먼지 체크
    if (prevData.dust !== undefined) {
        if (currentData.dust >= 200 && prevData.dust < 200) {
            addEvent(`${zone} 먼지 농도 위험 (${currentData.dust} μg/m³)`);
        } else if (currentData.dust >= 150 && prevData.dust < 150) {
            addEvent(`${zone} 먼지 농도 경고 (${currentData.dust} μg/m³)`);
        } else if (currentData.dust >= 100 && prevData.dust < 100) {
            addEvent(`${zone} 먼지 농도 주의 (${currentData.dust} μg/m³)`);
        }
    }
    
    // 불꽃 감지
    if (!prevData.flame && currentData.flame) {
        addEvent(`${zone} 불꽃 감지!`);
    }
}

// 센서 및 카메라 카운트 업데이트
function updateSensorCount() {
    const activeSensors = Object.keys(sensorData).length;
    const totalSensors = 4;
    document.getElementById('active-sensors').textContent = `${activeSensors}/${totalSensors}개`;
}

function updateCameraCount() {
    // TODO: CCTV 연결 상태 추적 구현 필요
    // 현재는 하드코딩
    const activeCameras = 0;
    const totalCameras = 4;
    document.getElementById('active-cameras').textContent = `${activeCameras}/${totalCameras}개`;
}

function updateEventCount() {
    document.getElementById('daily-events').textContent = `${eventCount}건`;
}

function updateSystemStatus() {
    // 전체 시스템 상태 계산
    const hasData = Object.keys(sensorData).length > 0;
    const hasDanger = Object.values(sensorData).some(zone => zone.status === 'danger');
    const hasWarning = Object.values(sensorData).some(zone => zone.status === 'warning');
    
    let statusText = '정상';
    if (!hasData) {
        statusText = '대기중';
    } else if (hasDanger) {
        statusText = '위험';
    } else if (hasWarning) {
        statusText = '경고';
    }
    
    document.getElementById('system-status').textContent = statusText;
}

// Cleanup
window.addEventListener('beforeunload', () => {
    if (updateInterval) clearInterval(updateInterval);
    if (chartUpdateInterval) clearInterval(chartUpdateInterval);
});

// 팝업 외부 클릭시 닫기
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('popup')) {
        e.target.classList.remove('show');
    }
});
