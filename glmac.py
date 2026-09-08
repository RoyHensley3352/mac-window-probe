import base64, io, json, os, shutil, socket, subprocess, sys, time
import requests
from websocket import create_connection
from gologin import GoLogin

TOKEN = os.environ['GOLOGIN_TOKEN'].strip()
HTML = io.open('web/m.html', encoding='utf-8').read() if os.path.exists('web/m.html') else ''
URL = 'data:text/html;base64,' + base64.b64encode(HTML.encode()).decode()


def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p


def measure(profile_id, headless, label):
    port = free_port()
    extra = ['--no-sandbox', '--disable-dev-shm-usage', '--remote-allow-origins=*']
    if headless:
        extra.append('--headless=new')
    gl = GoLogin({'token': TOKEN, 'profile_id': profile_id, 'port': port, 'extra_params': extra})
    out = {'label': label, 'headless': headless}
    try:
        dbg = gl.start()
        out['dbg'] = str(dbg)
        time.sleep(5)
        ver = requests.get('http://127.0.0.1:%d/json/version' % port, timeout=25).json()
        out['browser'] = ver.get('Browser')
        tabs = requests.get('http://127.0.0.1:%d/json' % port, timeout=25).json()
        pages = [t for t in tabs if t.get('type') == 'page']
        ws = create_connection(ver['webSocketDebuggerUrl'], suppress_origin=True, max_size=None)
        ws.settimeout(60)

        def rpc(mid, method, params, sid=None):
            m = {'id': mid, 'method': method, 'params': params}
            if sid:
                m['sessionId'] = sid
            ws.send(json.dumps(m)); t0 = time.time()
            while time.time() - t0 < 50:
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
            time.sleep(2)
            m = rpc(4, 'Runtime.evaluate', {'expression': "document.getElementById('d').textContent", 'returnByValue': True}, sid)
            v = (m.get('result', {}).get('result', {}) or {}).get('value')
            if v and 'geom' in v:
                val = v; break
        ws.close()
        out['data'] = json.loads(val) if val else None
    except Exception as e:
        out['error'] = '%s: %s' % (type(e).__name__, e)
    finally:
        try:
            gl.stop()
        except Exception:
            pass
    return out


gl0 = GoLogin({'token': TOKEN})
pid = os.environ.get('PROFILE_ID', '').strip()
created = False
if not pid:
    prof = gl0.createProfileRandomFingerprint({'os': 'mac', 'name': 'ada-macprobe'})
    pid = prof['id'] if isinstance(prof, dict) else prof
    created = True
print('profile=%s created=%s' % (pid, created), flush=True)
res = [measure(pid, False, 'headed'), measure(pid, True, 'headless')]
if created:
    try:
        gl0.delete(pid); print('profile deleted', flush=True)
    except Exception as e:
        print('delete failed: %s' % e, flush=True)
print(json.dumps(res, indent=1))
print()
for r in res:
    d = r.get('data') or {}
    print('%-9s browser=%-26s equalWidth=%-6s dW=%-4s dH=%-4s geom=%-34s scr=%s' % (
        r['label'], r.get('browser'), d.get('equalWidth'), d.get('frameDeltaW'),
        d.get('frameDeltaH'), d.get('geom'), d.get('scr')))
    if r.get('error'):
        print('   ERROR: %s' % r['error'])
