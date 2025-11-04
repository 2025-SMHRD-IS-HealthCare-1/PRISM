const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3000;

//vercel 도메인
const vercelDomain = 'https://prism-blond-five.vercel.app/';

// FastAPI 서버 주소 (환경 변수로 설정 가능)
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

/* 미들웨어 설정 */
app.use(cors({
    origin: '*', // Vercel 배포시 실제 도메인으로 변경
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    credentials: true
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 정적 파일 제공 (HTML, CSS, JS)
app.use(express.static(path.join(__dirname, 'public')));

// 루트 경로
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ============================================
// API 프록시 라우트 (Express -> FastAPI)
// ============================================

// 헬스 체크
app.get('/api/health', async (req, res) => {
    try {
        const response = await axios.get(`${FASTAPI_URL}/health`, { timeout: 5000 });
        res.json({
            express: 'healthy',
            fastapi: response.data
        });
    } catch (error) {
        res.status(503).json({
            express: 'healthy',
            fastapi: 'unavailable',
            error: error.message
        });
    }
});

// 구역 목록 조회
app.get('/api/zones', async (req, res) => {
    try {
        const response = await axios.get(`${FASTAPI_URL}/api/zones`, { timeout: 5000 });
        res.json(response.data);
    } catch (error) {
        console.error('구역 목록 조회 실패:', error.message);
        res.status(500).json({ error: '구역 목록을 가져올 수 없습니다' });
    }
});

// 센서 데이터 조회 (특정 구역)
app.get('/api/sensors/:zone', async (req, res) => {
    try {
        const { zone } = req.params;
        const response = await axios.get(`${FASTAPI_URL}/api/sensors/${zone}`, { timeout: 5000 });
        res.json(response.data);
    } catch (error) {
        console.error(`센서 데이터 조회 실패 [${req.params.zone}]:`, error.message);
        res.status(500).json({ error: '센서 데이터를 가져올 수 없습니다' });
    }
});

// 센서 데이터 업데이트 (라즈베리파이/오렌지파이에서 전송)
app.post('/api/sensors/:zone', async (req, res) => {
    try {
        const { zone } = req.params;
        const sensorData = req.body;
        
        console.log(`📊 센서 데이터 수신 [${zone}]:`, sensorData);
        
        // FastAPI로 전달
        const response = await axios.post(
            `${FASTAPI_URL}/api/sensors/${zone}`,
            sensorData,
            { timeout: 5000 }
        );
        
        res.json(response.data);
    } catch (error) {
        console.error(`센서 데이터 업데이트 실패 [${req.params.zone}]:`, error.message);
        res.status(500).json({ error: '센서 데이터를 업데이트할 수 없습니다' });
    }
});

// 과거 데이터 조회
app.get('/api/history/:zone', async (req, res) => {
    try {
        const { zone } = req.params;
        const { hours, days } = req.query;
        
        let url = `${FASTAPI_URL}/api/history/${zone}`;
        const params = [];
        if (hours) params.push(`hours=${hours}`);
        if (days) params.push(`days=${days}`);
        if (params.length > 0) url += `?${params.join('&')}`;
        
        const response = await axios.get(url, { timeout: 10000 });
        res.json(response.data);
    } catch (error) {
        console.error(`과거 데이터 조회 실패 [${req.params.zone}]:`, error.message);
        res.status(500).json({ error: '과거 데이터를 가져올 수 없습니다' });
    }
});

// CCTV 스트림
app.get('/api/cctv/:zone/stream', async (req, res) => {
    try {
        const { zone } = req.params;
        const response = await axios.get(
            `${FASTAPI_URL}/api/cctv/${zone}/stream`,
            { 
                responseType: 'stream',
                timeout: 30000 
            }
        );
        
        response.data.pipe(res);
    } catch (error) {
        console.error(`CCTV 스트림 실패 [${req.params.zone}]:`, error.message);
        res.status(503).json({ error: 'CCTV 스트림을 가져올 수 없습니다' });
    }
});

// SSH 명령 실행 (라즈베리파이/오렌지파이 원격 관리)
app.post('/api/device/:deviceId/command', async (req, res) => {
    try {
        const { deviceId } = req.params;
        const { command } = req.body;
        
        console.log(`🔧 SSH 명령 실행 [${deviceId}]: ${command}`);
        
        // FastAPI로 전달
        const response = await axios.post(
            `${FASTAPI_URL}/api/device/${deviceId}/command`,
            { command },
            { timeout: 30000 }
        );
        
        res.json(response.data);
    } catch (error) {
        console.error(`SSH 명령 실행 실패 [${req.params.deviceId}]:`, error.message);
        res.status(500).json({ error: 'SSH 명령 실행에 실패했습니다' });
    }
});

// 장치 상태 조회
app.get('/api/devices', async (req, res) => {
    try {
        const response = await axios.get(`${FASTAPI_URL}/api/devices`, { timeout: 5000 });
        res.json(response.data);
    } catch (error) {
        console.error('장치 목록 조회 실패:', error.message);
        res.status(500).json({ error: '장치 목록을 가져올 수 없습니다' });
    }
});

// 404 에러 처리
app.use((req, res) => {
    res.status(404).json({ error: '페이지를 찾을 수 없습니다' });
});

// 에러 핸들링 미들웨어
app.use((err, req, res, next) => {
    console.error('서버 에러:', err);
    res.status(500).json({ error: '서버 내부 오류가 발생했습니다' });
});

// 서버 시작
app.listen(port, () => {
    console.log('='.repeat(60));
    console.log('🚀 PRISM Express 백엔드 서버가 시작되었습니다!');
    console.log('='.repeat(60));
    console.log(`📡 Express 서버: http://localhost:${port}`);
    console.log(`🔗 FastAPI 서버: ${FASTAPI_URL}`);
    console.log(`🔗 Vercel 배포 서버: ${vercelDomain}`);
    console.log(`📁 정적 파일: ${path.join(__dirname, 'public')}`);
    
});