import webview

# 모든 인코딩에 대응하는 초고속 범용 로더
html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Universal Fast Log Viewer</title>
    <style>
        body { font-family: 'Consolas', monospace; background-color: #1e1e1e; color: #d4d4d4; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; user-select: text !important; }
        header { padding: 10px 20px; background: #2d2d2d; display: flex; gap: 15px; align-items: center; border-bottom: 1px solid #3e3e3e; }
        #viewport { flex: 1; overflow-y: auto; position: relative; background: #1e1e1e; }
        #spacer { position: absolute; top: 0; left: 0; width: 100%; pointer-events: none; }
        #content { position: absolute; top: 0; left: 0; width: 100%; will-change: transform; }
        .log-line { height: 20px; line-height: 20px; padding: 0 15px; font-size: 13px; white-space: pre; border-bottom: 1px solid #2a2a2a; box-sizing: border-box; overflow: hidden; }
        .error { color: #ff5555; font-weight: bold; background: rgba(255,85,85,0.1); }
        .warning { color: #ffb86c; background: rgba(255, 184, 108, 0.1); }
        footer { padding: 10px; background: #2d2d2d; border-top: 1px solid #3e3e3e; }
        input { width: 100%; padding: 8px; background: #3c3c3c; border: 1px solid #555; color: #fff; border-radius: 4px; outline: none; }
        button { cursor: pointer; padding: 6px 12px; background: #007acc; border: none; color: white; border-radius: 4px; font-size: 12px; }
        #status { font-size: 12px; color: #888; margin-left: auto; }
        #realInput { display: none; }
    </style>
</head>
<body>
    <header>
        <input type="file" id="realInput" accept=".txt,.log,*">
        <button onclick="document.getElementById('realInput').click()">파일 열기 (전체 호환)</button>
        <button onclick="sortLogs()">시간순 정렬</button>
        <span id="status">대기 중</span>
    </header>
    <div id="viewport"><div id="spacer"></div><div id="content"></div></div>
    <footer><input type="text" id="searchInput" placeholder="검색어 입력 후 Enter..."></footer>

    <script>
        let allLogs = [];
        let displayLogs = [];
        const rowHeight = 20;
        const viewport = document.getElementById('viewport');
        const spacer = document.getElementById('spacer');
        const content = document.getElementById('content');

        // [핵심] 인코딩 호환성을 위한 바이너리 로딩 로직
        document.getElementById('realInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            const startTime = performance.now();
            document.getElementById('status').innerText = "파일 분석 중...";

            const reader = new FileReader();
            reader.onload = function(evt) {
                // 바이너리 데이터를 읽어 UTF-8로 디코딩하되, 에러 발생 시 깨진 문자 대체(fatal: false)
                const decoder = new TextDecoder('utf-8', { fatal: false, ignoreBOM: true });
                const text = decoder.decode(evt.target.result);
                
                // 고속 줄바꿈 분리
                allLogs = text.split(/\\r?\\n/);
                displayLogs = allLogs;
                
                updateScroll();
                const duration = ((performance.now() - startTime)/1000).toFixed(2);
                document.getElementById('status').innerText = `로드 완료: ${allLogs.length.toLocaleString()} 줄 (${duration}초)`;
            };
            
            // 파일을 바이너리(ArrayBuffer)로 직접 읽음
            reader.readAsArrayBuffer(file);
        });

        function render() {
            const scrollTop = viewport.scrollTop;
            const vHeight = viewport.offsetHeight;
            const startIndex = Math.floor(scrollTop / rowHeight);
            const endIndex = Math.min(displayLogs.length, Math.ceil((scrollTop + vHeight) / rowHeight) + 15);
            
            const visibleLines = displayLogs.slice(startIndex, endIndex);
            content.style.transform = `translateY(${startIndex * rowHeight}px)`;
            
            let html = '';
            for(let i=0; i<visibleLines.length; i++) {
                const line = visibleLines[i];
                // 특수문자 이스케이프 및 강조
                const safe = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                const highlighted = safe.replace(/(error)/gi, '<span class="error">$1</span>')
                                        .replace(/(warning)/gi, '<span class="warning">$1</span>');
                html += `<div class="log-line">${highlighted}</div>`;
            }
            content.innerHTML = html;
        }

        function updateScroll() {
            spacer.style.height = `${displayLogs.length * rowHeight}px`;
            render();
        }

        viewport.onscroll = render;
        window.onresize = render;

        function sortLogs() {
            document.getElementById('status').innerText = "정렬 중...";
            setTimeout(() => {
                displayLogs.sort((a, b) => a.substring(0, 19).localeCompare(b.substring(0, 19)));
                render();
                document.getElementById('status').innerText = "정렬 완료";
            }, 10);
        }

        document.getElementById('searchInput').onkeydown = (e) => {
            if (e.key === 'Enter') {
                const k = e.target.value.toLowerCase().trim();
                displayLogs = k ? allLogs.filter(l => l.toLowerCase().includes(k)) : allLogs;
                viewport.scrollTop = 0;
                updateScroll();
            }
        };
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    window = webview.create_window('Pro Universal Log Viewer', html=html_content, width=1280, height=800)
    webview.start()
