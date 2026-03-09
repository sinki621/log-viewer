import webview
import os
import sys

# 앞서 만든 index.html의 전체 코드를 이 변수에 붙여넣습니다.
html_content = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Fast Log Viewer</title>
    <style>
        body { font-family: 'Consolas', monospace; background-color: #1e1e1e; color: #d4d4d4; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        header { padding: 12px; background: #2d2d2d; display: flex; gap: 10px; align-items: center; border-bottom: 1px solid #3e3e3e; }
        #log-container { flex: 1; overflow-y: auto; padding: 15px; white-space: pre; font-size: 13px; line-height: 1.5; background: #1e1e1e; }
        .log-line { border-bottom: 1px solid #2a2a2a; padding: 1px 0; }
        .error { color: #ff5555; font-weight: bold; }
        .warning { color: #ffb86c; }
        footer { padding: 10px; background: #2d2d2d; border-top: 1px solid #3e3e3e; }
        input[type="text"] { width: 100%; padding: 8px; background: #3c3c3c; border: 1px solid #555; color: #fff; }
        button { cursor: pointer; padding: 5px 15px; background: #007acc; border: none; color: white; border-radius: 4px; }
    </style>
</head>
<body>
    <header>
        <input type="file" id="fileInput" accept=".txt,.log">
        <button onclick="sortLogs()">시간순 정렬</button>
        <span id="status" style="font-size:12px; color:#888;">로그 파일을 선택하세요.</span>
    </header>
    <div id="log-container"></div>
    <footer>
        <input type="text" id="searchInput" placeholder="검색 키워드 입력 후 Enter...">
    </footer>

    <script>
        let logData = [];
        const fileInput = document.getElementById('fileInput');
        const logContainer = document.getElementById('log-container');
        const searchInput = document.getElementById('searchInput');
        const status = document.getElementById('status');

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (event) => {
                const content = event.target.result;
                logData = content.split(/\\r?\\n/).filter(line => line.trim().length > 0);
                status.innerText = `로드 완료: ${logData.length.toLocaleString()} 줄`;
                renderLogs(logData);
            };
            reader.readAsText(file);
        });

        function renderLogs(data) {
            logContainer.innerHTML = '';
            const fragment = document.createDocumentFragment();
            data.forEach(line => {
                const div = document.createElement('div');
                div.className = 'log-line';
                let safeLine = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                div.innerHTML = safeLine.replace(/(error)/gi, '<span class="error">$1</span>')
                                       .replace(/(warning)/gi, '<span class="warning">$1</span>');
                fragment.appendChild(div);
            });
            logContainer.appendChild(fragment);
        }

        function sortLogs() {
            if (logData.length === 0) return;
            logData.sort((a, b) => {
                const dateA = a.match(/\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}/);
                const dateB = b.match(/\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}/);
                return (dateA && dateB) ? dateA[0].localeCompare(dateB[0]) : a.localeCompare(b);
            });
            renderLogs(logData);
        }

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const keyword = e.target.value.toLowerCase().trim();
                const filtered = keyword ? logData.filter(l => l.toLowerCase().includes(keyword)) : logData;
                renderLogs(filtered);
            }
        });
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    # HTML 문자열을 직접 로드
    webview.create_window('Log Viewer Portable', html=html_content, width=1200, height=800)
    webview.start()
