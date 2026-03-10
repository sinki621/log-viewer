import webview
import json
import os
import mmap
import bisect
import chardet

class LogApi:
    def __init__(self):
        self.file_path = None
        self.f = None
        self.mm = None
        self.line_offsets = []
        self.filtered_indices = [] # 필터링된 줄 번호 저장

    def troubleshoot_file(self, file_path):
        stats = {"size": os.path.getsize(file_path), "encoding_guess": "Unknown"}
        with open(file_path, 'rb') as f:
            raw = f.read(4096)
            guess = chardet.detect(raw)
            stats["encoding_guess"] = guess['encoding']
        return stats

    def open_log(self):
        result = window.create_file_dialog(webview.OPEN_DIALOG)
        if not result: return
        self.file_path = result[0]
        window.evaluate_js("setStatus('파일 인덱싱 중...')")
        try:
            if self.f: self.f.close()
            info = self.troubleshoot_file(self.file_path)
            self.f = open(self.file_path, 'rb')
            self.mm = mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ)
            self.line_offsets = [0]
            pos = self.mm.find(b'\n')
            while pos != -1:
                self.line_offsets.append(pos + 1)
                pos = self.mm.find(b'\n', pos + 1)
            self.filtered_indices = [] # 초기화
            total_lines = len(self.line_offsets)
            window.evaluate_js(f"initViewer({total_lines}, '{os.path.basename(self.file_path)}', {info['size']})")
        except Exception as e:
            window.evaluate_js(f"alert('로드 오류: {str(e)}')")

    def get_lines(self, start_idx, count):
        if not self.mm: return []
        lines = []
        # 필터링 모드인지 확인
        target_indices = self.filtered_indices if self.filtered_indices else range(len(self.line_offsets))
        end_idx = min(start_idx + count, len(target_indices))
        
        for i in range(start_idx, end_idx):
            line_pos_idx = target_indices[i]
            start = self.line_offsets[line_pos_idx]
            stop = self.line_offsets[line_pos_idx+1] if line_pos_idx+1 < len(self.line_offsets) else self.mm.size()
            raw_bytes = self.mm[start:stop]
            line = ""
            for enc in ['utf-8', 'cp949', 'windows-1252', 'latin-1']:
                try:
                    line = raw_bytes.decode(enc).strip('\r\n')
                    break
                except: continue
            if not line and raw_bytes:
                line = raw_bytes.decode('utf-8', errors='replace').strip('\r\n')
            lines.append(line)
        return lines

    def search_and_filter(self, keyword):
        """전체 텍스트에서 키워드가 포함된 줄 번호만 추출"""
        if not self.mm: return 0
        if not keyword:
            self.filtered_indices = []
            return len(self.line_offsets)
        
        results = []
        search_bytes = keyword.lower().encode('utf-8')
        pos = 0
        while True:
            pos = self.mm.find(search_bytes, pos)
            if pos == -1: break
            line_idx = bisect.bisect_right(self.line_offsets, pos) - 1
            if not results or results[-1] != line_idx:
                results.append(line_idx)
            pos += len(search_bytes)
            if len(results) > 50000: break # 너무 많으면 중단 (성능 보호)
        
        self.filtered_indices = results
        return len(results)

html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Consolas', monospace; background: #1e1e1e; color: #d4d4d4; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; user-select: text !important; }
        header { padding: 10px 20px; background: #2d2d2d; display: flex; gap: 10px; align-items: center; border-bottom: 1px solid #3e3e3e; }
        #viewport { flex: 1; overflow-y: auto; position: relative; }
        #spacer { position: absolute; width: 100%; pointer-events: none; }
        #content { position: absolute; width: 100%; will-change: transform; }
        .log-line { height: 20px; line-height: 20px; padding: 0 15px; font-size: 12px; white-space: pre; border-bottom: 1px solid #2a2a2a; }
        /* 강조 스타일 */
        .lvl-error { color: #ff5555; font-weight: bold; background: rgba(255, 85, 85, 0.1); }
        .lvl-warn { color: #ffb86c; background: rgba(255, 184, 108, 0.1); }
        footer { padding: 8px 15px; background: #2d2d2d; border-top: 1px solid #3e3e3e; display: flex; gap: 10px; }
        input { flex: 1; padding: 6px; background: #3c3c3c; border: 1px solid #555; color: #fff; outline: none; }
        button { cursor: pointer; padding: 5px 12px; background: #007acc; border: none; color: white; border-radius: 4px; }
        #status { font-size: 11px; color: #888; }
    </style>
</head>
<body>
    <header>
        <button onclick="pywebview.api.open_log()">Open Log</button>
        <span id="status">Ready</span>
    </header>
    <div id="viewport"><div id="spacer"></div><div id="content"></div></div>
    <footer>
        <input type="text" id="sInput" placeholder="필터링할 단어 입력 후 Enter (비우면 전체보기)">
        <button onclick="applyFilter()">Filter</button>
    </footer>
    <script>
        const rowH = 20; let currentTotal = 0;
        const vp = document.getElementById('viewport');
        const ct = document.getElementById('content');
        function setStatus(m) { document.getElementById('status').innerText = m; }

        function initViewer(cnt, name, size) {
            currentTotal = cnt;
            document.getElementById('spacer').style.height = (currentTotal * rowH) + 'px';
            vp.scrollTop = 0;
            setStatus(`${name} (${(size/1024/1024).toFixed(1)}MB) - Total: ${cnt.toLocaleString()} lines`);
            render();
        }

        async function render() {
            if (currentTotal === 0) return;
            const start = Math.floor(vp.scrollTop / rowH);
            const count = Math.ceil(vp.offsetHeight / rowH) + 10;
            const lines = await pywebview.api.get_lines(start, count);
            
            ct.style.transform = `translateY(${start * rowH}px)`;
            ct.innerHTML = lines.map(l => {
                let cls = "log-line";
                if (l.toLowerCase().includes("error")) cls += " lvl-error";
                else if (l.toLowerCase().includes("warning")) cls += " lvl-warn";
                const safe = l.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                return `<div class="${cls}">${safe}</div>`;
            }).join('');
        }

        async function applyFilter() {
            const k = document.getElementById('sInput').value;
            setStatus("Filtering...");
            currentTotal = await pywebview.api.search_and_filter(k);
            document.getElementById('spacer').style.height = (currentTotal * rowH) + 'px';
            vp.scrollTop = 0;
            setStatus(k ? `Filtered: ${currentTotal.toLocaleString()} lines` : `All lines displayed`);
            render();
        }

        vp.onscroll = render;
        window.onresize = render;
        document.getElementById('sInput').onkeydown = (e) => { if(e.key === 'Enter') applyFilter(); };
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    api = LogApi()
    window = webview.create_window('Pro Log Viewer', html=html_content, js_api=api, width=1280, height=800)
    webview.start()
