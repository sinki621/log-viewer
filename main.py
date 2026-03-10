import webview
import json
import os
import mmap
import chardet  # 인코딩 정밀 분석용 (pip install chardet 필요)

class LogApi:
    def __init__(self):
        self.mm = None
        self.line_offsets = []

    def troubleshoot_file(self, file_path):
        """파일의 상태를 정밀 진단하는 함수"""
        stats = {
            "size": os.path.getsize(file_path),
            "header_hex": "",
            "encoding_guess": "Unknown",
            "is_binary": False
        }
        
        with open(file_path, 'rb') as f:
            raw = f.read(1024) # 첫 1KB만 읽어서 분석
            stats["header_hex"] = raw[:32].hex(' ') # 16진수 값 확인
            
            # 바이너리 파일인지 체크 (Null byte가 포함되어 있는지)
            if b'\\x00' in raw:
                stats["is_binary"] = True
            
            # 인코딩 추측
            guess = chardet.detect(raw)
            stats["encoding_guess"] = f"{guess['encoding']} ({guess['confidence']*100:.0f}%)"
            
        return stats

    def open_log(self):
        result = window.create_file_dialog(webview.OPEN_DIALOG)
        if not result: return
        
        file_path = result[0]
        window.evaluate_js(f"setStatus('진단 중: {os.path.basename(file_path)}...')")
        
        try:
            # 1단계: 트러블슈팅 정보 수집
            info = self.troubleshoot_file(file_path)
            diag_msg = f"인코딩: {info['encoding_guess']} | 바이너리여부: {info['is_binary']}\\n헤더(Hex): {info['header_hex']}"
            window.evaluate_js(f"console.log('File Diagnosis: {diag_msg}')")
            
            # 2단계: 파일 인덱싱 (mmap 사용)
            with open(file_path, 'rb') as f:
                self.mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                self.line_offsets = [0]
                pos = self.mm.find(b'\\n')
                while pos != -1:
                    self.line_offsets.append(pos + 1)
                    pos = self.mm.find(b'\\n', pos + 1)
            
            total_lines = len(self.line_offsets)
            window.evaluate_js(f"initViewer({total_lines}, '{os.path.basename(file_path)}', {info['size']})")
            
            if info['is_binary']:
                window.evaluate_js("alert('경고: 이 파일은 바이너리 데이터(Null)를 포함하고 있어 텍스트가 깨져 보일 수 있습니다.')")

        except Exception as e:
            window.evaluate_js(f"alert('치명적 로드 오류: {str(e)}')")

    def get_lines(self, start_idx, count):
        if not self.mm: return []
        lines = []
        end_idx = min(start_idx + count, len(self.line_offsets))
        
        for i in range(start_idx, end_idx):
            start = self.line_offsets[i]
            stop = self.line_offsets[i+1] if i+1 < len(self.line_offsets) else self.mm.size()
            
            raw_bytes = self.mm[start:stop]
            # [해결책] 디코딩 실패 시 무조건 'replace'를 사용하여 빈 화면 방지
            try:
                # 일반적인 로그는 UTF-8 또는 CP949(ANSI)
                line = raw_bytes.decode('utf-8').strip('\\r\\n')
            except:
                line = raw_bytes.decode('cp949', errors='replace').strip('\\r\\n')
            
            lines.append(line)
        return lines

# --- UI HTML 코드는 이전과 동일하나, 디버그 로그 확인용 콘솔을 활용하도록 구성됨 ---
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
        #status { font-size: 11px; color: #aaa; margin-left: auto; }
        button { cursor: pointer; padding: 5px 12px; background: #007acc; border: none; color: white; border-radius: 4px; }
    </style>
</head>
<body>
    <header>
        <button onclick="pywebview.api.open_log()">Open Log</button>
        <span id="status">Ready (F12로 디버그 콘솔을 확인하세요)</span>
    </header>
    <div id="viewport"><div id="spacer"></div><div id="content"></div></div>

    <script>
        let totalLines = 0;
        const rowHeight = 20;
        const viewport = document.getElementById('viewport');
        const content = document.getElementById('content');

        function setStatus(msg) { document.getElementById('status').innerText = msg; }

        function initViewer(count, name, size) {
            totalLines = count;
            document.getElementById('spacer').style.height = (totalLines * rowHeight) + 'px';
            viewport.scrollTop = 0;
            setStatus(`${name} (${(size/1024/1024).toFixed(1)}MB) - ${totalLines} lines`);
            render();
        }

        async function render() {
            if (totalLines === 0) return;
            const start = Math.floor(viewport.scrollTop / rowHeight);
            const lines = await pywebview.api.get_lines(start, 50);
            content.style.transform = `translateY(${start * rowHeight}px)`;
            content.innerHTML = lines.map(l => `<div class="log-line">${l.replace(/&/g, "&amp;").replace(/</g, "&lt;")}</div>`).join('');
        }

        viewport.onscroll = render;
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    api = LogApi()
    window = webview.create_window('Troubleshooter Log Viewer', html=html_content, js_api=api)
    # debug=True를 켜서 런타임 에러를 확인 가능하게 함
    webview.start(debug=True)
