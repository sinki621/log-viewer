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
        """파일의 인코딩과 상태를 정밀 진단"""
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
        window.evaluate_js("setStatus('파일 분석 및 인덱싱 중...')")
        
        try:
            if self.f: self.f.close()
            info = self.troubleshoot_file(self.file_path)
            
            self.f = open(self.file_path, 'rb')
            self.mm = mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ)
            
            # 고속 라인 인덱싱
            self.line_offsets = [0]
            pos = self.mm.find(b'\n')
            while pos != -1:
                self.line_offsets.append(pos + 1)
                pos = self.mm.find(b'\n', pos + 1)
            
            total_lines = len(self.line_offsets)
            window.evaluate_js(f"initViewer({total_lines}, '{os.path.basename(self.file_path)}', {info['size']})")
            print(f"진단 결과: {info['encoding_guess']}, 라인 수: {total_lines}")

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
            
            # 다중 인코딩 디코딩 시도 (Windows-1252 포함)
            line = ""
            for enc in ['utf-8', 'cp949', 'windows-1252', 'latin-1']:
                try:
                    line = raw_bytes.decode(enc).strip('\r\n')
                    break
                except:
                    continue
            if not line and raw_bytes: # 실패 시 대체 문자로 강제 출력
                line = raw_bytes.decode('utf-8', errors='replace').strip('\r\n')
            lines.append(line)
        return lines

    def search_text(self, keyword):
        """Python 백엔드 고속 전체 검색"""
        if not self.mm or not keyword: return []
        results = []
        # 검색어 인코딩 시도
        search_bytes = keyword.lower().encode('utf-8')
        self.mm.seek(0)
        pos = 0
        while len(results) < 1000: # 최대 1000개까지만 표시
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
        .error { color: #ff555
