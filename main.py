import webview # pip install pywebview

if __name__ == '__main__':
    # index.html 파일을 로드하여 창 생성
    webview.create_window('Fast Log Viewer', 'index.html', width=1200, height=800)
    webview.start()
