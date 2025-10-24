const express = require('express');
const app = express();
const port = process.env.PORT || 3000;
const path = require('path');

/* 미들웨어 설정 */
app.use(express.json());
app.use(express.urlencoded({ extended: true })); 

// 정적 파일 제공 (HTML, CSS, JS)
app.use(express.static(path.join(__dirname, 'public')));

// 루트 경로 접속시 index.html로 리다이렉트
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 404 에러 처리
app.use((req, res) => {
    res.status(404).send('페이지를 찾을 수 없습니다.');
});

app.listen(port, () => {
    // console.log(`=================================================`);
    console.log(`🚀 PRISM 웹 서버가 시작되었습니다!`);
    console.log(`📡 서버 주소: http://localhost:${port}`);
    console.log(`📁 정적 파일: ${path.join(__dirname, 'public')}`);
    // console.log(`=================================================`);
    // console.log(`\n💡 브라우저에서 http://localhost:${port} 로 접속하세요.`);
    // console.log(`💡 FastAPI 서버도 함께 실행해야 센서 데이터를 볼 수 있습니다.\n`);
});