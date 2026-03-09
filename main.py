import webview
import os

# HTML/JS 내용을 변수에 저장 (이스케이프 처리를 위해 f-string 미사용)
html_content = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>High-Speed Log Viewer</title>
    <style>
        body { font-family: 'Consolas', 'Monaco', monospace; background-color: #1e1e1e; color: #d4d4d4; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        header { padding: 12px 20px; background: #2d2d2d; display: flex; gap: 15px; align-items: center; border-bottom: 1px solid #3e3e3e; }
        #log-container { flex: 1; overflow-y: auto; padding: 15px; white-space: pre; font-size: 13px; line-height: 1.5; background: #1e1e1e; }
        .log-line { border-bottom: 1px solid #2a2a2a; padding: 2px 0; display: block; }
        .error { color: #ff5555; font-weight: bold; background-color: rgba(255, 85, 85, 0.1); }
        .warning { color: #ffb86c; background-color: rgba(255, 184, 108, 0.1); }
        footer { padding: 10px 20px; background: #2d2d2d; border-top: 1px solid #3e3e3e; }
        input[type="text"] { width: 100%; padding: 10px; background: #3c3c3c; border: 1px solid #555; color: #fff; border-radius: 4px; outline: none; }
        button { cursor: pointer; padding: 6px 16px; background: #007acc; border: none; color: white; border-radius: 4px; font-size: 13px; }
        #status { font-size: 12px; color: #888; margin-left: auto; }
    </style>
</head>
<body>
    <header>
        <input type="file" id="fileInput" accept=".txt,.log">
        <button onclick="sortLogs()">시간순 정렬</button>
        <span id="status">로그 파일을 로드하세요.</span>
    </header>
    <div id="log-container"></div>
    <footer>
        <input type="text" id="searchInput" placeholder="검색 키워드 입력 후 Enter (에러 필터링)">
    </footer>

    <script>
        let logData = [];

        // 1. 파일 읽기 (인코딩 문제 방지를 위해 FileReader 사용)
        document.getElementById('fileInput').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;

            document.getElementById('status').innerText = "파일 읽는 중...";
            const reader = new FileReader();
            reader.onload = (event) => {
                const content = event.target.result;
                // 줄바꿈 기호 상관없이 분리
                logData = content.split(/\\r?\\n/).filter(line => line.trim().length > 0);
                document.getElementById('status').innerText = `로드 완료: ${logData.length.toLocaleString()} 줄`;
                renderLogs(logData);
            };
            reader.readAsText(file);
        });

        // 2. 렌더링 (보안 및 하이라이팅)
        function renderLogs(data) {
            const container = document.getElementById('log-container');
            container.innerHTML = '';
            const fragment = document.createDocumentFragment();

            data.forEach(line => {
                const div = document.createElement('div');
                div.className = 'log-line';
                
                // HTML 특수기호 보호
                let safeLine = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                
                // 에러/경고 색상 입히기
                let highlighted = safeLine
                    .replace(/(error)/gi, '<span class="error">$1</span>')
                    .replace(/(warning)/gi, '<span class="warning">$1</span>');
                
                div.innerHTML = highlighted;
                fragment.appendChild(div);
            });
            container.appendChild(fragment);
            container.scrollTop = 0; // 로드 시 맨 위로
        }

        // 3. 시간 정렬 (ISO 8601 패턴 매칭)
        function sortLogs() {
            if (logData.length === 0) return;
            document.getElementById('status').innerText = "정렬 중...";
            
            setTimeout(() => {
                logData.sort((a, b) => {
                    // ISO 8601 타임스탬프 추출 (YYYY-MM-DDTHH:MM:SS...)
                    const tsA = a.match(/\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}/);
                    const tsB = b.match(/\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}/);
                    
                    if (tsA && tsB) return tsA[0].localeCompare(tsB[0]);
                    return a.localeCompare(b); // 타임스탬프 없으면 문자열 비교
                });
                renderLogs(logData);
                document.getElementById('status').innerText = "정렬 완료";
            }, 50);
        }

        // 4. 필터링 (검색 기능)
        document.getElementById('searchInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const keyword = e.target.value.toLowerCase().trim();
                if (!keyword) {
                    renderLogs(logData);
                    return;
                }
                const filtered = logData.filter(line => line.toLowerCase().includes(keyword));
                renderLogs(filtered);
                document.getElementById('status').innerText = `필터링 결과: ${filtered.length.toLocaleString()} 줄`;
            }
        });
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    # PyWebView 실행
    webview.create_window('Log Viewer Portable', html=html_content, width=1200, height=800)
    webview.start()
