import webview
import json
import os

# HTML/JS 소스 (텍스트 선택 및 복사 기능 활성화)
html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: 'Consolas', monospace; 
            background-color: #1e1e1e; 
            color: #d4d4d4; 
            margin: 0; 
            display: flex; 
            flex-direction: column; 
            height: 100vh; 
            overflow: hidden;
            /* 텍스트 선택 허용 */
            user-select: text !important;
            -webkit-user-select: text !important;
        }
        header { padding: 10px 20px; background: #2d2d2d; display: flex; gap: 15px; align-items: center; border-bottom: 1px solid #3e3e3e; }
        
        #progress-container { flex: 1; height: 20px; background: #3c3c3c; border-radius: 10px; overflow: hidden; display: none; position: relative; }
        #progress-bar { width: 0%; height: 100%; background: #007acc; transition: width 0.1s; }
        #progress-text { position: absolute; width: 100%; text-align: center; font-size: 11px; line-height: 20px; color: white; }

        #viewport { flex: 1; overflow-y: auto; position: relative; background: #1e1e1e; }
        #spacer { position: absolute; top: 0; left: 0; width: 100%; pointer-events: none; }
        #content { position: absolute; top: 0; left: 0; width: 100%; will-change: transform; }
        
        .log-line { 
            height: 20px; 
            line-height: 20px; 
            padding: 0 15px; 
            font-size: 13px; 
            white-space: pre; 
            border-bottom: 1px solid #2a2a2a; 
            box-sizing: border-box;
            /* 개별 라인 선택 허용 */
            user-select: text;
            -webkit-user-select: text;
        }
        .error { color: #ff5555; font-weight: bold; background: rgba(255,85,85,0.1); }
        .warning { color: #ffb86c; background: rgba(255,184,108,0.1); }
        
        footer { padding: 10px; background: #2d2d2d; border-top: 1px solid #3e3e3e; }
        input { width: 100%; padding: 8px; background: #3c3c3c; border: 1px solid #555; color: #fff; border-radius: 4px; outline: none; }
        button { cursor: pointer; padding: 6px 12px; background: #007acc; border: none; color: white; border-radius: 4px; font-size: 12px; white-space: nowrap; }
        #status { font-size: 12px; color: #888; white-space: nowrap; }
    </style>
</head>
<body>
    <header>
        <button id="openBtn" onclick="pywebview.api.open_file()">로그 열기</button>
        <div id="progress-container">
            <div id="progress-bar"></div>
            <div id="progress-text">0%</div>
        </div>
        <button onclick="sortLogs()">시간순 정렬</button>
        <span id="status">대기 중</span>
    </header>
    
    <div id="viewport">
        <div id="spacer"></div>
        <div id="content"></div>
    </div>

    <footer>
        <input type="text" id="searchInput" placeholder="검색 키워드 입력 후 Enter...">
    </footer>

    <script>
        let allLogs = [];
        let displayLogs = [];
        const rowHeight = 20;
        const viewport = document.getElementById('viewport');
        const spacer = document.getElementById('spacer');
        const content = document.getElementById('content');
        const pContainer = document.getElementById('progress-container');
        const pBar = document.getElementById('progress-bar');
        const pText = document.getElementById('progress-text');

        function updateLoading(percent, current, total) {
            pContainer.style.display = 'block';
            pBar.style.width = percent + '%';
            pText.innerText = `로딩 중... ${percent}% (${current.toLocaleString()} / ${total.toLocaleString()} 줄)`;
            if (percent >= 100) {
                setTimeout(() => { pContainer.style.display = 'none'; }, 1000);
            }
        }

        function render() {
            const scrollTop = viewport.scrollTop;
            const viewportHeight = viewport.offsetHeight;
            const startIndex = Math.floor(scrollTop / rowHeight);
            const endIndex = Math.min(displayLogs.length, Math.ceil((scrollTop + viewportHeight) / rowHeight) + 15);
            
            const visibleLines = displayLogs.slice(startIndex, endIndex);
            content.style.transform = `translateY(${startIndex * rowHeight}px)`;
            
            content.innerHTML = visibleLines.map(line => {
                let safe = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                return `<div class="log-line">${safe.replace(/(error)/gi, '<span class="error">$1</span>').replace(/(warning)/gi, '<span class="warning">$1</span>')}</div>`;
            }).join('');
        }

        function updateScroll() {
            spacer.style.height = `${displayLogs.length * rowHeight}px`;
            render();
        }

        viewport.addEventListener('scroll', render);
        window.addEventListener('resize', render);

        function sortLogs() {
            document.getElementById('status').innerText = "정렬 중...";
            setTimeout(() => {
                displayLogs.sort((a, b) => a.substring(0, 19).localeCompare(b.substring(0, 19)));
                render();
                document.getElementById('status').innerText = "정렬 완료";
            }, 10);
        }

        document.getElementById('searchInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const k = e.target.value.toLowerCase().trim();
                displayLogs = k ? allLogs.filter(l => l.toLowerCase().includes(k)) : allLogs;
                viewport.scrollTop = 0;
                updateScroll();
            }
        });
    </script>
</body>
</html>
"""

class Api:
    def open_file(self):
        file_path = window.create_file_dialog(webview.OPEN_DIALOG, file_types=('Log Files (*.txt;*.log)', 'All files (*.*)'))
        if not file_path: return

        try:
            with open(file_path[0], 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.read().splitlines()
            
            total = len(lines)
            chunk_size = 50000 
            
            window.evaluate_js("allLogs = []; displayLogs = []; updateLoading(0, 0, 0);")
            
            for i in range(0, total, chunk_size):
                chunk = lines[i:i + chunk_size]
                percent = int((min(i + chunk_size, total) / total) * 100)
                window.evaluate_js(f"allLogs.push(...{json.dumps(chunk)}); updateLoading({percent}, {min(i + chunk_size, total)}, {total});")
            
            window.evaluate_js("displayLogs = allLogs; updateScroll();")
            
        except Exception as e:
            window.evaluate_js(f"alert('Error: {str(e)}')")

if __name__ == '__main__':
    api = Api()
    # easy_drag=False 설정을 통해 텍스트 선택이 더 원활하게 함
    window = webview.create_window('Pro Log Viewer', html=html_content, js_api=api, width=1280, height=800)
    # 텍스트 선택 기능을 강제로 활성화하기 위해 브라우저 컨텍스트 메뉴 허용
    webview.start(debug=False)
