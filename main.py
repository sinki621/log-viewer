import webview
import json

# 최적화된 가상 스크롤 및 고속 렌더링 HTML
html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Consolas', monospace; background-color: #1e1e1e; color: #d4d4d4; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        header { padding: 10px 20px; background: #2d2d2d; display: flex; gap: 15px; align-items: center; border-bottom: 1px solid #3e3e3e; }
        
        /* 가상 스크롤 컨테이너 */
        #viewport { flex: 1; overflow-y: auto; position: relative; background: #1e1e1e; }
        #spacer { position: absolute; top: 0; left: 0; width: 100%; pointer-events: none; }
        #content { position: absolute; top: 0; left: 0; width: 100%; will-change: transform; }
        
        .log-line { 
            height: 20px; /* 고정 높이가 성능 핵심 */
            line-height: 20px;
            padding: 0 15px;
            font-size: 13px;
            white-space: pre;
            border-bottom: 1px solid #2a2a2a;
            box-sizing: border-box;
        }
        .error { color: #ff5555; font-weight: bold; background: rgba(255,85,85,0.1); }
        .warning { color: #ffb86c; background: rgba(255,184,108,0.1); }
        
        footer { padding: 10px; background: #2d2d2d; border-top: 1px solid #3e3e3e; }
        input { width: 100%; padding: 8px; background: #3c3c3c; border: 1px solid #555; color: #fff; border-radius: 4px; outline: none; }
        button { cursor: pointer; padding: 6px 12px; background: #007acc; border: none; color: white; border-radius: 4px; font-size: 12px; }
        #status { font-size: 12px; color: #888; margin-left: auto; }
    </style>
</head>
<body>
    <header>
        <button onclick="pywebview.api.open_file()">로그 열기</button>
        <button onclick="sortLogs()">시간순 정렬</button>
        <span id="status">파일을 로드하세요.</span>
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
        const rowHeight = 20; // .log-line height와 일치시켜야 함
        const viewport = document.getElementById('viewport');
        const spacer = document.getElementById('spacer');
        const content = document.getElementById('content');

        // Python에서 호출하는 데이터 로드 함수
        function loadLogData(lines) {
            allLogs = lines;
            displayLogs = lines;
            updateScroll();
            document.getElementById('status').innerText = `총 ${allLogs.length.toLocaleString()} 줄 로드됨`;
        }

        // 가상 스크롤 핵심 로직
        function render() {
            const scrollTop = viewport.scrollTop;
            const viewportHeight = viewport.offsetHeight;
            
            const startIndex = Math.floor(scrollTop / rowHeight);
            const endIndex = Math.min(displayLogs.length, Math.ceil((scrollTop + viewportHeight) / rowHeight) + 5);
            
            const visibleLines = displayLogs.slice(startIndex, endIndex);
            
            content.style.transform = `translateY(${startIndex * rowHeight}px)`;
            
            content.innerHTML = visibleLines.map(line => {
                let safe = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                let highlighted = safe.replace(/(error)/gi, '<span class="error">$1</span>')
                                      .replace(/(warning)/gi, '<span class="warning">$1</span>');
                return `<div class="log-line">${highlighted}</div>`;
            }).join('');
        }

        function updateScroll() {
            spacer.style.height = `${displayLogs.length * rowHeight}px`;
            render();
        }

        viewport.addEventListener('scroll', render);
        window.addEventListener('resize', render);

        // 정렬 성능 최적화
        function sortLogs() {
            document.getElementById('status').innerText = "고속 정렬 중...";
            setTimeout(() => {
                displayLogs.sort((a, b) => {
                    const tsA = a.substring(0, 19); // ISO8601의 YYYY-MM-DDTHH:MM:SS 부분만 비교
                    const tsB = b.substring(0, 19);
                    return tsA.localeCompare(tsB);
                });
                render();
                document.getElementById('status').innerText = "정렬 완료";
            }, 10);
        }

        // 필터링 성능 최적화
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
        if file_path:
            try:
                # 대용량 파일 고속 읽기
                with open(file_path[0], 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.read().splitlines()
                # JSON 직렬화를 통해 안정적으로 데이터 전송
                window.evaluate_js(f"loadLogData({json.dumps(lines)})")
            except Exception as e:
                window.evaluate_js(f"alert('Error: {str(e)}')")

if __name__ == '__main__':
    api = Api()
    window = webview.create_window('Ultra-Fast Log Viewer', html=html_content, js_api=api, width=1280, height=800)
    webview.start()
