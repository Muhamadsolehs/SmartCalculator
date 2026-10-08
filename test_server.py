import urllib.request
import json

def run_tests():
    base = 'http://localhost:8000'
    print("Menguji HTTP Server dan Endpoints Kalkulator...")

    # 1. Cek index.html
    res = urllib.request.urlopen(base + '/')
    assert res.status == 200
    html = res.read().decode('utf-8')
    assert 'Kalkulator Saintifik Python' in html
    print("[PASS] GET / (index.html)")

    # 2. Cek style.css
    res = urllib.request.urlopen(base + '/style.css')
    assert res.status == 200
    css = res.read().decode('utf-8')
    assert 'light-theme' in css or ':root' in css
    print("[PASS] GET /style.css")

    # 3. Cek script.js
    res = urllib.request.urlopen(base + '/script.js')
    assert res.status == 200
    js = res.read().decode('utf-8')
    assert 'executeCalculation' in js
    print("[PASS] GET /script.js")

    # 4. Cek info API
    res = urllib.request.urlopen(base + '/api/info')
    assert res.status == 200
    info = json.loads(res.read().decode('utf-8'))
    assert info['success'] is True
    print(f"[PASS] GET /api/info -> IP: {info['local_ip']}, Desktop: {info['desktop_url']}")

    # 5. Cek Perhitungan Saintifik
    calc_tests = [
        ('125 * 8 - 50', 'DEG', 950),
        ('sin(90) + cos(0)', 'DEG', 2),
        ('sqrt(144) + 2^4', 'DEG', 28),
        ('5!', 'DEG', 120),
        ('log(1000)', 'DEG', 3),
        ('100 / 4', 'DEG', 25)
    ]

    for expr, unit, expected in calc_tests:
        req = urllib.request.Request(
            base + '/api/calculate',
            data=json.dumps({'expression': expr, 'angle_unit': unit}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        assert data['success'] is True, f"Perhitungan gagal: {expr}"
        val = data['result']
        assert abs(val - expected) < 1e-9, f"Hasil salah: {val} != {expected}"
        print(f"[PASS] POST /api/calculate -> {expr} = {data['display']}")

    # 6. Cek Riwayat
    res = urllib.request.urlopen(base + '/api/history')
    hist_data = json.loads(res.read().decode('utf-8'))
    assert len(hist_data['history']) >= len(calc_tests)
    print(f"[PASS] GET /api/history -> Berhasil menyimpan {len(hist_data['history'])} riwayat")

    print("\nSELURUH PENGUJIAN OTOMATIS BERHASIL DENGAN SEMPURNA!")

if __name__ == '__main__':
    run_tests()
