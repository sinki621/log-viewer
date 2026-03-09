import webview
import json

# 초고속 스트리밍 엔진 HTML
html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Consolas', monospace; background-color: #1e1e1e; color: #d4d4d4; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; user-select: text !important; }
        header { padding: 10px 20px; background: #2d2d2d; display: flex; gap: 15px; align-items: center; border-bottom: 1px solid #3e3e3e; }
        
        #viewport { flex: 1; overflow-y: auto; position: relative; background: #1e1e1e; }
        #spacer { position: absolute; top: 0; left: 0; width: 100%; pointer-events: none; }
        #content { position: absolute; top: 0; left: 0; width: 100%; will-change: transform; }
        
        .log-line { height: 20px; line-height: 20px; padding: 0 15px; font-size: 13px; white-space: pre; border-bottom: 1px solid #2a2a2a; box-sizing: border-box; user-select: text; }
        .error { color: #ff5555; font-weight: bold; background: rgba(255,85,85,0.1); }
        .warning { color: #ffb86c; background: rgba(255,184,108,0.1); }
        
        footer { padding: 10px; background: #2d2d2d; border-top: 1px solid #3e3e3e; }
        input { width: 100%; padding: 8px; background: #3c3c3c; border: 1px solid #555; color: #fff; border-radius: 4px; outline: none; }
        button { cursor: pointer; padding: 6px 12px; background: #007acc; border: none; color: white; border-radius: 4px; font-size: 12px; }
        #status { font-size: 12px; color: #888; margin-left: auto; }
        
        /* 숨겨진 실제 파일 인풋 */
        #realInput { display: none; }
    </style>
</head>
<body>
    <header>
        <input type="file" id="realInput" accept=".txt,.log">
        <button onclick="document.getElementById('realInput').click()">로그 고속 열기</button>
        <button onclick="sortLogs()">시간순 정렬</button>
        <span id="status">파일을 로드하세요.</span>
    </header>
    
    <div id="viewport">
        <div id="spacer"></div>
        <div id="content"></div>
    </div>

    <footer>
        <input type="text" id="searchInput" placeholder="검색어 입력 후 Enter...">
    </footer>

    <script>
        let allLogs = [];
        let displayLogs = [];
        const rowHeight = 20;
        const viewport = document.getElementById('viewport');
        const spacer = document.getElementById('spacer');
        const content = document.getElementById('content');

        // [핵심] 브라우저 네이티브 엔진을 사용한 초고속 로딩
        document.getElementById('realInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            const startTime = performance.now();
            document.getElementById('status').innerText = "데이터 분석 중...";

            const reader = new FileReader();
            reader.onload = function(evt) {
                // 바이너리 수준에서 줄바꿈 처리 (가장 빠름)
                allLogs = evt.target.result.split(/\\r?\\n/).filter(line => line.length > 0);
                displayLogs = allLogs;
                
                updateScroll();
                const endTime = performance.now();
                document.getElementById('status').innerText = 
                    `로드 완료: ${allLogs.length.toLocaleString()} 줄 (${((endTime - startTime)/1000).toFixed(2)}초)`;
            };
            // 텍스트를 통째로 메모리에 스트리밍
            reader.readAsText(file);
        });

        function render() {
            const scrollTop = viewport.scrollTop;
            const vHeight = viewport.offsetHeight;
            const startIndex = Math.floor(scrollTop / rowHeight);
            const endIndex = Math.min(displayLogs.length, Math.ceil((scrollTop + vHeight) / rowHeight) + 20);
            
            const visibleLines = displayLogs.slice(startIndex, endIndex);
            content.style.transform = `translateY(${startIndex * rowHeight}px)`;
            
            // 고속 루프 렌더링
            let html = '';
            for(let i=0; i<visibleLines.length; i++) {
                let line = visibleLines[i];
                let safe = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                let highlighted = safe.replace(/(error)/gi, '<span class="error">$1</span>')
                                      .replace(/(warning)/gi, '<span class="warning">$1</span>');
                html += `<div class="log-line">${highlighted}</div>`;
            }
            content.innerHTML = html;
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
                // Substring 기반 고속 비교
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

if __name__ == '__main__':
    # 브라우저 기능을 100% 사용하기 위해 별도의 API 없이 윈도우 생성
    window = webview.create_window('Ultra-Speed Log Viewer', html=html_content, width=1280, height=800)
    webview.start()
