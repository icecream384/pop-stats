"""
Launch local HTTP server for 人口统计 tool.
Usage: python server.py [port]
Default port: 8080
"""
import http.server
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

print(f'启动人口统计查询工具服务器...')
print(f'地址: http://localhost:{PORT}')
print(f'按 Ctrl+C 停止')
print()

http.server.HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
