import webview
import os
import tkinter as tk
from tkinter import filedialog

# HTML/JS 소스
html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Consolas', monospace; background-color: #1e1e1e; color: #d4d4d4; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        header { padding: 12px; background: #2d2d2d; display: flex; gap: 10px; align-items: center; border-bottom: 1px solid #3e3e3e; }
        #log-container { flex: 1; overflow-y: auto; padding: 15px; white-space: pre; font-size: 13px; line-height: 1.5; }
        .log-line { border-bottom: 1px solid #2a2a2a; padding: 2px 0; }
        .error { color: #ff5555; font-weight: bold; background: rgba(255,85,85,0.1); }
        .warning { color: #ffb86c; background: rgba(255,184,108,0.1); }
        footer { padding: 10px; background: #2d2d2d; border-top: 1px solid #3e3e3e; }
        input { width: 100%; padding: 10px; background: #3c3c3c; border: 1px solid #555; color: #fff; border-radius: 4px; outline: none; }
        button { cursor: pointer; padding: 6px 16px; background: #007acc; border: none; color: white; border-radius: 4px; }
        #status { font-size: 12px; color: #888; margin-left: auto; }
    </style>
</head>
<body>
    <header>
        <button onclick="pywebview.api.open_file()">로그 파일 열기</button>
        <button onclick="sortLogs()">시간순 정렬</button>
        <span id="status">파일을 선택해주세요.</span>
    </header>
    <div id="log-container"></div>
    <footer>
        <input type="text" id="searchInput" placeholder="검색어 입력 후 Enter...">
    </footer>

    <script>
        let logData = [];

        // Python에서 데이터를 받아와서 화면에 그림
        function loadLogData(lines) {
            logData = lines;
            document.getElementById('status').innerText = `로드 완료: ${logData.length.toLocaleString()} 줄`;
            renderLogs(logData);
        }

        function renderLogs(data) {
            const container = document.getElementById('log-container');
            container.innerHTML = '';
            const fragment = document.createDocumentFragment();

            data.forEach(line => {
                const div = document.createElement('div');
                div.className = 'log-line';
                let safe = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                div.innerHTML = safe.replace(/(error)/gi, '<span class="error">$1</span>')
                                   .replace(/(warning)/gi, '<span class="warning">$1</span>');
                fragment.appendChild(div);
            });
            container.appendChild(fragment);
            container.scrollTop = 0;
        }

        function sortLogs() {
            document.getElementById('status').innerText = "정렬 중...";
            setTimeout(() => {
                logData.sort((a, b) => {
                    const tsA = a.match(/\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}/);
                    const tsB = b.match(/\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}/);
                    return (tsA && tsB) ? tsA[0].localeCompare(tsB[0]) : a.localeCompare(b);
                });
                renderLogs(logData);
                document.getElementById('status').innerText = "정렬 완료";
            }, 50);
        }

        document.getElementById('searchInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const k = e.target.value.toLowerCase().trim();
                renderLogs(k ? logData.filter(l => l.toLowerCase().includes(k)) : logData);
            }
        });
    </script>
</body>
</html>
"""

class Api:
    def open_file(self):
        # 파일 선택창 띄우기
        file_path = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=('Log Files (*.txt;*.log)', 'All files (*.*)'))
        
        if file_path:
            try:
                # UTF-8로 읽기 시도, 실패 시 latin-1로 읽기 (범용성)
                with open(file_path[0], 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                
                # JS 함수 호출하여 데이터 전달
                window.evaluate_js(f"loadLogData({lines})")
            except Exception as e:
                window.evaluate_js(f"alert('파일 읽기 오류: {str(e)}')")

if __name__ == '__main__':
    api = Api()
    window = webview.create_window('Fast Log Viewer', html=html_content, js_api=api, width=1200, height=800)
    webview.start()
