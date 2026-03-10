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

    def troubleshoot_file(self, file_path):
        stats = {"size": os.path.getsize(file_path), "encoding_guess": "Unknown", "is_binary": False}
        with open(file_path, 'rb') as f:
            raw = f.read(4096)
            if b'\x00' in raw: stats["is_binary"] = True
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
            total_lines = len(self.line_offsets)
            window.evaluate_js(f"initViewer({total_lines}, '{os.path.basename(self.file_path)}', {info['size']})")
        except Exception as e:
            window.evaluate_js(f"alert('로드 오류: {str(e)}')")

    def get_lines(self, start_idx, count):
        if not self.mm: return []
        lines = []
        end_idx = min(start_idx + count, len(self.line_offsets))
        for i in range(start_idx, end_idx):
            start = self.line_offsets[i]
            stop = self.line_offsets[i+1] if i+1 < len(self.line_offsets) else self.mm.size()
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

    def search_text(self, keyword):
        if not self.mm or not keyword: return []
        results = []
        search_bytes = keyword.lower().encode('utf-8')
        pos = 0
        while len(results) < 1000:
            pos = self.mm.find(search_bytes, pos)
            if pos == -1: break
            line_idx = bisect.bisect_right(self.line_offsets, pos) - 1
            if not results or results[-1] != line_idx:
                results.append(line_idx)
            pos += len(search_bytes)
        return results

html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Consolas', monospace; background: #1e1e1e; color: #d4d4d4; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; user-select: text !important; }
        header { padding: 10px 20px; background: #2d2d2d; display: flex; gap: 10px; align-items: center; border-bottom: 1px solid #3e3e3e; }
        #main { flex: 1; display: flex; overflow: hidden; }
        #viewport { flex: 1; overflow-y: auto; position: relative; }
        #spacer { position: absolute; width: 100%; pointer-events: none; }
        #content { position: absolute; width: 100%; will-change: transform; }
        .log-line { height: 20px; line-height: 20px; padding: 0 15px; font-size: 12px; white-space: pre; border-bottom: 1px solid #2a2a2a; }
        .error { color: #ff5555; font-weight: bold; }
        #search-panel { width: 280px; background: #252526; border-left: 1px solid #3e3e3e; display: none; flex-direction: column; }
        .res-item { padding: 6px; cursor: pointer; border-bottom: 1px solid #333; font-size: 11px; }
        footer { padding: 8px 15px; background: #2d2d2d; border-top: 1px solid #3e3e3e; display: flex; gap: 10px; }
        input { flex: 1; padding: 6px; background: #3c3c3c; border: 1px solid #555; color: #fff; outline: none; }
        button { cursor: pointer; padding: 5px 12px; background: #007acc; border: none; color: white; }
    </style>
</head>
<body>
    <header>
        <button onclick="pywebview.api.open_log()">Open File</button>
        <span id="status" style="font-size: 11px; color: #888;">Ready</span>
    </header>
    <div id="main">
        <div id="viewport"><div id="spacer"></div><div id="content"></div></div>
        <div id="search-panel">
            <div id="res-list" style="overflow-y:auto; flex:1;"></div>
        </div>
    </div>
    <footer>
        <input type="text" id="sInput" placeholder="검색어 입력 (Enter)">
        <button onclick="doSearch()">Search</button>
    </footer>
    <script>
        const rowH = 20; let total = 0;
        const vp = document.getElementById('viewport');
        const ct = document.getElementById('content');
        function setStatus(m) { document.getElementById('status').innerText = m; }
        function initViewer(cnt, name, size) {
            total = cnt; document.getElementById('spacer').style.height = (total * rowH) + 'px';
            vp.scrollTop = 0; setStatus(`${name} (${(size/1024/1024).toFixed(1)}MB)`); render();
        }
        async function render() {
            if (total === 0) return;
            const start = Math.floor(vp.scrollTop / rowH);
            const count = Math.ceil(vp.offsetHeight / rowH) + 10;
            const lines = await pywebview.api.get_lines(start, count);
            ct.style.transform = `translateY(${start * rowH}px)`;
            ct.innerHTML = lines.map(l => `<div class="log-line">${l.replace(/&/g, "&amp;").replace(/</g, "&lt;")}</div>`).join('');
        }
        async function doSearch() {
            const k = document.getElementById('sInput').value; if(!k) return;
            const idxs = await pywebview.api.search_text(k);
            const panel = document.getElementById('search-panel');
            const list = document.getElementById('res-list');
            if(idxs.length > 0) {
                panel.style.display = 'flex';
                list.innerHTML = idxs.map(i => `<div class="res-item" onclick="jump(${i})">Line ${i.toLocaleString()}</div>`).join('');
            } else { panel.style.display = 'none'; alert("결과 없음"); }
        }
        function jump(i) { vp.scrollTop = i * rowH; render(); }
        vp.onscroll = render;
        document.getElementById('sInput').onkeydown = (e) => { if(e.key === 'Enter') doSearch(); };
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    api = LogApi()
    window = webview.create_window('Log Viewer', html=html_content, js_api=api, width=1280, height=800)
    webview.start()
