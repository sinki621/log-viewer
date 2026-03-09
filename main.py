import webview

# 명칭이 통일된 최종 Log Viewer 코드
html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Log Viewer</title>
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
        <button onclick="document.getElementById('realInput').click()">Open Log File</button>
        <button onclick="sortLogs()">Sort by Time</button>
        <span id="status">Ready</span>
    </header>
    <div id="viewport"><div id="spacer"></div><div id="content"></div></div>
    <footer><input type="text" id="searchInput" placeholder="Search keyword (Enter)..."></footer>

    <script>
        let allLogs = [];
        let displayLogs = [];
        const rowHeight = 20;
        const viewport = document.getElementById('viewport');
        const spacer = document.getElementById('spacer');
        const content = document.getElementById('content');

        document.getElementById('realInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            const startTime = performance.now();
            document.getElementById('status').innerText = "Analyzing...";

            const reader = new FileReader();
            reader.onload = function(evt) {
                const decoder = new TextDecoder('utf-8', { fatal: false, ignoreBOM: true });
                const text = decoder.decode(evt.target.result);
                allLogs = text.split(/\\r?\\n/);
                displayLogs = allLogs;
                updateScroll();
                const duration = ((performance.now() - startTime)/1000).toFixed(2);
                document.getElementById('status').innerText = `Loaded: ${allLogs.length.toLocaleString()} lines (${duration}s)`;
            };
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
            document.getElementById('status').innerText = "Sorting...";
            setTimeout(() => {
                displayLogs.sort((a, b) => a.substring(0, 19).localeCompare(b.substring(0, 19)));
                render();
                document.getElementById('status').innerText = "Sorted";
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
    # 창 제목을 'Log Viewer'로 설정
    window = webview.create_window('Log Viewer', html=html_content, width=1280, height=800)
    webview.start()
