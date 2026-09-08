import json, os, random, shutil, socket, subprocess, sys, time
import requests
from websocket import create_connection

CHROME = os.environ.get('CHROME_BIN') or '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
URL = os.environ.get('PROBE_URL', 'http://127.0.0.1:8000/m.html')


def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p


def run(headless, label):
    port = free_port()
    prof = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mp_%d' % port)
    shutil.rmtree(prof, ignore_errors=True); os.makedirs(prof, exist_ok=True)
    args = [CHROME, '--no-first-run', '--no-default-browser-check',
            '--user-data-dir=' + prof, '--remote-debugging-port=%d' % port,
            '--remote-allow-origins=*', '--window-size=1024,768', URL]
    if headless:
        args.insert(1, '--headless=new')
    p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out = {'label': label, 'headless': headless}
    try:
        ver = None
        for _ in range(40):
            time.sleep(1)
            try:
                ver = requests.get('http://127.0.0.1:%d/json/version' % port, timeout=5).json(); break
            except Exception:
                pass
        if not ver:
            out['error'] = 'no CDP'; return out
        out['browser'] = ver.get('Browser')
        tabs = requests.get('http://127.0.0.1:%d/json' % port, timeout=15).json()
        pages = [t for t in tabs if t.get('type') == 'page']
        ws = create_connection(ver['webSocketDebuggerUrl'], suppress_origin=True, max_size=None)
        ws.settimeout(45)

        def rpc(mid, method, params, sid=None):
            m = {'id': mid, 'method': method, 'params': params}
            if sid:
                m['sessionId'] = sid
            ws.send(json.dumps(m)); t0 = time.time()
            while time.time() - t0 < 40:
                r = json.loads(ws.recv())
                if r.get('id') == mid:
                    return r
            return None

        sid = rpc(2, 'Target.attachToTarget', {'targetId': pages[0]['id'], 'flatten': True})['result']['sessionId']
        rpc(30, 'Target.activateTarget', {'targetId': pages[0]['id']})
        rpc(3, 'Page.navigate', {'url': URL}, sid)
        rpc(31, 'Page.bringToFront', {}, sid)
        val = None
        for _ in range(20):
            time.sleep(1)
            m = rpc(4, 'Runtime.evaluate', {'expression': "document.getElementById('d').textContent", 'returnByValue': True}, sid)
            v = (m.get('result', {}).get('result', {}) or {}).get('value')
            if v and 'geom' in v:
                val = v; break
        ws.close()
        out['data'] = json.loads(val) if val else None
    finally:
        p.terminate(); time.sleep(1); p.kill()
        shutil.rmtree(prof, ignore_errors=True)
    return out


res = [run(False, 'headed'), run(True, 'headless')]
print(json.dumps(res, indent=1))
print()
for r in res:
    d = r.get('data') or {}
    print('%-9s equalWidth=%-6s frameDeltaW=%-4s frameDeltaH=%-4s geom=%-34s scr=%s ptr=%s' % (
        r['label'], d.get('equalWidth'), d.get('frameDeltaW'), d.get('frameDeltaH'),
        d.get('geom'), d.get('scr'), d.get('ptr')))
