"""Loopback-only demo server; no additional web framework dependencies."""
import argparse
import json
import secrets
import subprocess
import sys
import threading
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = secrets.token_urlsafe(32)
BUSY = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def send(self, status, data, content_type='application/json; charset=utf-8'):
        body = data.encode() if isinstance(data, str) else json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; connect-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def valid_host(self):
        return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

    def do_GET(self):
        if not self.valid_host():
            return self.send(403, {'error': '僅接受本機網址'})
        if self.path == '/':
            return self.send(200, (ROOT / 'webdemo/index.html').read_text(encoding='utf-8').replace('__TOKEN__', TOKEN), 'text/html; charset=utf-8')
        if self.path == '/api/status':
            try:
                with urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=3) as r:
                    models = json.load(r)['models']
                ready = any(m['name'] == 'gemma4:e4b' for m in models)
                return self.send(200, {'ready': ready, 'message': '模型就緒 · gemma4:e4b' if ready else '請先下載 gemma4:e4b；仍可使用離線重播'})
            except Exception:
                return self.send(200, {'ready': False, 'message': 'Ollama 尚未啟動；仍可使用離線重播'})
        if self.path == '/api/defaults':
            return self.send(200, {'document': (ROOT / 'scenario2-rag/docs/02-contaminated-note.txt').read_text(encoding='utf-8')})
        return self.send(404, {'error': '找不到頁面'})

    def do_POST(self):
        origin = f'http://127.0.0.1:{self.server.server_port}'
        if not self.valid_host() or self.headers.get('Origin') != origin or self.headers.get('X-Demo-Token') != TOKEN:
            return self.send(403, {'error': '請從本機 DEMO 頁面操作'})
        if self.path != '/api/run':
            return self.send(404, {'error': '找不到 API'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 32000:
                raise ValueError('輸入過長')
            data = json.loads(self.rfile.read(length))
            if data.get('scene') not in ('s1', 's2', 's3') or data.get('mode') not in ('live', 'replay'):
                raise ValueError('無效的場景或模式')
            for field in ('prompt', 'document'):
                if not isinstance(data.get(field), str) or len(data[field]) > 8000:
                    raise ValueError('輸入格式錯誤或過長')
            if not data['prompt'].strip():
                raise ValueError('請輸入提示詞')
        except (ValueError, TypeError, AttributeError) as exc:
            return self.send(400, {'error': str(exc)})
        if not BUSY.acquire(blocking=False):
            return self.send(409, {'error': '模型正在執行另一個實驗，請稍後再試'})
        try:
            result = subprocess.run([sys.executable, str(ROOT / 'webdemo/worker.py')],
                                    input=json.dumps(data, ensure_ascii=False), text=True, encoding='utf-8',
                                    capture_output=True, cwd=ROOT, timeout=300)
            if result.returncode:
                return self.send(502, {'error': '執行失敗。請確認 Ollama 已啟動且 gemma4:e4b 已下載。', 'detail': result.stderr[-1500:]})
            self.send(200, json.loads(result.stdout))
        except subprocess.TimeoutExpired:
            self.send(504, {'error': '執行超過 5 分鐘，已停止。請稍後重試或使用離線重播。'})
        finally:
            BUSY.release()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError:
        raise SystemExit('無法啟動：連接埠已被使用。請關閉先前的 DEMO 視窗後重試。')
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'DevFest 高雄 2026｜它拒絕了，但思考鏈出賣了它｜本機互動實驗室：{url}\n保持此視窗開啟；Ctrl+C 可停止。', flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
