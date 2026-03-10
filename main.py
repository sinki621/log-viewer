import webview
import json
import os
import mmap

class LogApi:
    def __init__(self):
        self.file_path = None
        self.f = None
        self.mm = None
        self.line_offsets = []

    def open_log(self):
        result = window.create_file_dialog(webview.OPEN_DIALOG)
        if not result: return
        
        self.file_path = result[0]
        window.evaluate_js("setStatus('파일 인덱싱 중...')")
        
        try:
            if self.f: self.f.close()
            file_size = os.path.getsize(self.file_path)
            self.f = open(self.file_path, 'rb')
            self.mm = mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ)
            
            # 고속 인덱싱
            self.line_offsets = [0]
            pos = self.mm.find(b'\\n')
            while pos != -1:
                self.line_offsets.append(pos + 1)
                pos = self.mm.find(b'\\n', pos + 1)
            
            total_lines = len(self.line_offsets)
            window.evaluate_js(f"initViewer({total_lines}, '{os.path.basename(self.file_path)}', {file_size})")
            
        except Exception as e:
            window.evaluate_js(f"alert('파일 로드 실패: {str(e)}')")

    def get_lines(self, start_idx, count):
        if not self.mm: return []
        lines = []
        end_idx = min(start_idx + count, len(self.line_offsets))
        for i in range(start_idx, end_idx):
            start = self.line_offsets[i]
            stop = self.line_offsets[i+1] if i+1 < len(self.line_offsets) else self.mm.size()
            # cp949/utf-8 혼용 대응
            line_bytes = self.mm[start:stop]
            try:
                line = line_bytes.decode('utf-8').strip('\\r\\n')
            except:
                line = line_bytes.decode('cp949', errors='replace').strip('\\r\\n')
            lines.append(line)
        return lines

    def search_text(self, keyword):
        """[핵심] Python 백엔드 전체 검색"""
        if not self.mm or not keyword: return []
        
        results = []
        keyword_bytes = keyword.lower().encode('utf-8')
        
        # 파일 전체에서 키워드 위치 검색
        self.mm.seek(0)
        pos = 0
        while True:
            # find는 C 수준에서 구현되어 매우 빠름
            pos = self.mm.find(keyword_bytes, pos)
            if pos == -1: break
            
            # 발견된 위치가 몇 번째 줄인지 이진 탐색으로 계산
            import bisect
            line_idx = bisect.bisect_right(self.line_offsets, pos) - 1
            if not results or results[-1] != line_idx: # 중복 라인 제거
                results.append(line_idx)
            
            pos += len(keyword_bytes)
            if len(results) > 1000: break # 성능을 위해 결과는 1000개까지만
            
        return results

html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Consolas', monospace; background: #1e1e1e; color: #d4d4d4; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; user-select: text !important; }
        header { padding: 10px 20px; background: #2d2d2d; display: flex; gap: 15px; align-items: center; border-bottom: 1px solid #3e3e3e; }
        #main-container { flex: 1; display: flex; overflow: hidden; }
        #viewport { flex: 1; overflow-y: auto; position: relative; background: #1e1e1e; }
        #spacer { position: absolute; width: 100%; pointer-events: none; }
        #content { position: absolute; width: 100%; will-change: transform; }
        .log-line { height: 20px; line-height: 20px; padding: 0 15px; font-size: 12px; white-space: pre; border-bottom: 1px solid #2a2a2a; box-sizing: border-box; }
        .error { color: #ff5555; font-weight: bold; background: rgba(255,85,85,0.1); }
        footer { padding: 8px 15px; background: #2d2d2d; border-top: 1px solid #3e3e3e; display: flex; gap: 10px; align-items: center; }
        input { flex: 1; padding: 6px; background: #3c3c3c; border: 1px solid #555; color: #fff; border-radius: 4px; outline: none; }
        button { cursor: pointer; padding: 5px 12px; background: #007acc; border: none; color: white; border-radius: 4px; font-size: 12px; }
        #status { font-size: 11px; color: #888; }
        #search-results { width: 250px; background: #252526; border-left: 1px solid #3e3e3e; display: none; flex-direction: column; }
        .result-item { padding: 5px 10px; cursor: pointer; border-bottom: 1px solid #333; font-size: 11px; }
        .result-item:hover { background: #37373d; }
    </style>
</head>
<body>
    <header>
        <button onclick="pywebview.api.open_log()">Open Log File</button>
        <span id="status">Ready</span>
    </header>
    <div id="main-container">
        <div id="viewport"><div id="spacer"></div><div id="content"></div></div>
        <div id="search-results">
            <div style="padding: 10px; font-size: 12px; font-weight: bold; border-bottom: 1px solid #3e3e3e;">Search Results</div>
            <div id="results-list" style="flex:1; overflow-y: auto;"></div>
        </div>
    </div>
    <footer>
        <input type="text" id="searchInput" placeholder="Search keyword and press Enter (Global Search)...">
        <button onclick="performSearch()">Search</button>
    </footer>

    <script>
        let totalLines = 0;
        const rowHeight = 20;
        const viewport = document.getElementById('viewport');
        const content = document.getElementById('content');
        const resultsPanel = document.getElementById('search-results');
        const resultsList = document.getElementById('results-list');

        function setStatus(msg) { document.getElementById('status').innerText = msg; }

        function initViewer(count, name, size) {
            totalLines = count;
            document.getElementById('spacer').style.height = (totalLines * rowHeight) + 'px';
            viewport.scrollTop = 0;
            setStatus(`${name} (${(size / 1024 / 1024).toFixed(1)}MB) - ${totalLines.toLocaleString()} lines`);
            render();
        }

        async function render() {
            if (totalLines === 0) return;
            const scrollTop = viewport.scrollTop;
            const startIndex = Math.floor(scrollTop / rowHeight);
            const count = Math.ceil(viewport.offsetHeight / rowHeight) + 10;
            
            const lines = await pywebview.api.get_lines(startIndex, count);
            content.style.transform = `translateY(${startIndex * rowHeight}px)`;
            content.innerHTML = lines.map(line => {
                const safe = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                return `<div class="log-line">${safe.replace(/(error)/gi, '<span class="error">$1</span>')}</div>`;
            }).join('');
        }

        async function performSearch() {
            const k = document.getElementById('searchInput').value;
            if (!k) return;
            setStatus("Searching...");
            const indices = await pywebview.api.search_text(k);
            
            if (indices.length > 0) {
                resultsPanel.style.display = 'flex';
                resultsList.innerHTML = indices.map(idx => 
                    `<div class="result-item" onclick="jumpTo(${idx})">Line ${idx.toLocaleString()}</div>`
                ).join('');
                setStatus(`${indices.length} results found.`);
            } else {
                alert("No results found.");
                resultsPanel.style.display = 'none';
            }
        }

        function jumpTo(idx) {
            viewport.scrollTop = idx * rowHeight;
            render();
        }

        document.getElementById('searchInput').onkeydown = (e) => { if(e.key === 'Enter') performSearch(); };
        viewport.onscroll = render;
        window.onresize = render;
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    api = LogApi()
    window = webview.create_window('Log Viewer (Global Search)', html=html_content, js_api=api, width=1280, height=800)
    webview.start()
