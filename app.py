"""
Aplikasi Web Server Kalkulator Python
Menggunakan Python Standard Library (http.server, socket, json, urllib)
Mendukung akses Desktop & Smartphone (Mobile) melalui browser & PWA
"""

import os
import sys
import json
import socket
import webbrowser
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import mimetypes

# Pastikan console Windows mendukung karakter Unicode/UTF-8 tanpa error
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Import mesin kalkulator
from calculator_engine import calculate

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Memori penyimpanan riwayat kalkulasi (in-memory)
calculation_history = []
MAX_HISTORY_ITEMS = 50


def get_local_ip():
    """Mendapatkan alamat IP lokal komputer di jaringan Wi-Fi/LAN."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


class CalculatorRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Format log ringkas dan rapi
        sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]} {args[1]} -> {args[2]}\n")

    def send_json(self, status_code: int, data: dict):
        response_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API: Info Jaringan Server
        if path == '/api/info':
            local_ip = get_local_ip()
            self.send_json(200, {
                'success': True,
                'port': PORT,
                'local_ip': local_ip,
                'desktop_url': f"http://localhost:{PORT}",
                'mobile_url': f"http://{local_ip}:{PORT}",
                'server_time': datetime.now().isoformat()
            })
            return

        # API: Ambil Riwayat Perhitungan
        elif path == '/api/history':
            self.send_json(200, {
                'success': True,
                'history': calculation_history
            })
            return

        # Melayani File Statis (HTML, CSS, JS, Icon, Manifest)
        if path == '/' or path == '':
            file_path = os.path.join(STATIC_DIR, 'index.html')
        else:
            rel_path = path.lstrip('/')
            file_path = os.path.join(STATIC_DIR, rel_path)

        # Sanitasi path keamanan
        file_path = os.path.abspath(file_path)
        if not file_path.startswith(STATIC_DIR):
            self.send_error(403, "Akses dilarang")
            return

        if os.path.exists(file_path) and os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'

            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', mime_type)
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(500, f"Gagal membaca file: {e}")
        else:
            self.send_error(404, "File tidak ditemukan")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API: Eksekusi Perhitungan
        if path == '/api/calculate':
            try:
                content_len = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_len)
                data = json.loads(body.decode('utf-8'))
            except Exception:
                self.send_json(400, {'success': False, 'message': 'Format data JSON tidak valid'})
                return

            expression = data.get('expression', '')
            angle_unit = data.get('angle_unit', 'DEG')

            ok, raw_result, display_str = calculate(expression, angle_unit=angle_unit)

            if ok:
                history_item = {
                    'id': len(calculation_history) + 1,
                    'expression': expression,
                    'result': raw_result,
                    'display': display_str,
                    'angle_unit': angle_unit,
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                calculation_history.insert(0, history_item)
                if len(calculation_history) > MAX_HISTORY_ITEMS:
                    calculation_history.pop()

                self.send_json(200, {
                    'success': True,
                    'expression': expression,
                    'result': raw_result,
                    'display': display_str,
                    'angle_unit': angle_unit
                })
            else:
                self.send_json(200, {
                    'success': False,
                    'message': display_str
                })
            return

        # API: Hapus Riwayat Perhitungan
        elif path == '/api/clear-history':
            calculation_history.clear()
            self.send_json(200, {'success': True, 'message': 'Riwayat berhasil dibersihkan'})
            return

        self.send_error(404, "Endpoint API tidak ditemukan")


def run_server(port=PORT, auto_open=True):
    # Pastikan direktori static ada
    os.makedirs(STATIC_DIR, exist_ok=True)

    # Inisialisasi mimetypes tambahan untuk file PWA dan SVG
    mimetypes.add_type('text/javascript', '.js')
    mimetypes.add_type('text/css', '.css')
    mimetypes.add_type('image/svg+xml', '.svg')
    mimetypes.add_type('application/manifest+json', '.json')
    mimetypes.add_type('application/manifest+json', '.webmanifest')

    local_ip = get_local_ip()
    server_address = ('0.0.0.0', port)
    
    try:
        httpd = HTTPServer(server_address, CalculatorRequestHandler)
    except OSError as e:
        print(f"[ERROR] Port {port} sedang digunakan atau terjadi kesalahan: {e}")
        # Coba port alternatif
        alt_port = port + 1
        print(f"Mencoba port alternatif: {alt_port}...")
        httpd = HTTPServer(('0.0.0.0', alt_port), CalculatorRequestHandler)
        port = alt_port

    border = "=" * 62
    print(border)
    print(" 🧮  KALKULATOR SAINTIFIK MODERN PYTHON  (DESKTOP & MOBILE)")
    print(border)
    print(" Server lokal berhasil berjalan!")
    print("")
    print(f" 💻 Untuk Desktop / Komputer:")
    print(f"    👉 http://localhost:{port}")
    print(f"    👉 http://127.0.0.1:{port}")
    print("")
    print(f" 📱 Untuk Smartphone / Mobile (HP di Wi-Fi yang sama):")
    print(f"    👉 http://{local_ip}:{port}")
    print(border)
    print(" Tekan Ctrl + C di terminal ini untuk mematikan server.")
    print(border)

    if auto_open and '--no-browser' not in sys.argv:
        try:
            webbrowser.open(f"http://localhost:{port}")
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Menghentikan server kalkulator...")
        httpd.server_close()
        print("[INFO] Server telah dihentikan. Sampai jumpa!")


if __name__ == '__main__':
    port = PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port=port, auto_open=False)
