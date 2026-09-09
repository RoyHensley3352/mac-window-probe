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
API = 'https://api.gologin.com'
HDR = {'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'}
RESOLUTIONS = [r.strip() for r in os.environ.get(
    'RESOLUTIONS', '1440x900,1280x800,1024x640').split(',') if r.strip()]
NAME_PREFIX = 'ada-macprobe'


def list_profiles():
    try:
        r = requests.get('%s/browser/v2' % API, headers=HDR, timeout=40)
        body = r.json()
        return body.get('profiles', body) if isinstance(body, dict) else body
    except Exception as e:
        print('list failed: %s' % e, flush=True)
        return []


def sweep_leftovers():
    n = 0
    for p in list_profiles() or []:
        try:
            if str(p.get('name', '')).startswith(NAME_PREFIX):
                requests.delete('%s/browser/%s' % (API, p['id']), headers=HDR, timeout=40)
                print('swept leftover %s %s' % (p['id'], p.get('name')), flush=True)
                n += 1
        except Exception as e:
            print('sweep failed: %s' % e, flush=True)
    return n


def make_profile(res):
    try:
        prof = gl0.createProfileRandomFingerprint({'os': 'mac', 'name': '%s-%s' % (NAME_PREFIX, res)})
    except Exception as e:
        print('create raised for %s: %s' % (res, e), flush=True)
        return None
    if not isinstance(prof, dict) or 'id' not in prof:
        print('create returned no id for %s: %s' % (res, str(prof)[:300]), flush=True)
        return None
    return prof['id']


def set_resolution(pid, res):
    try:
        body = requests.get('%s/browser/%s' % (API, pid), headers=HDR, timeout=40).json()
        nav = body.get('navigator') or {}
        nav['resolution'] = res
        body['navigator'] = nav
        return requests.put('%s/browser/%s' % (API, pid), headers=HDR,
                            data=json.dumps(body), timeout=40).status_code
    except Exception as e:
        return '%s: %s' % (type(e).__name__, e)


def read_resolution(pid):
    try:
        b = requests.get('%s/browser/%s' % (API, pid), headers=HDR, timeout=40).json()
        return (b.get('navigator') or {}).get('resolution')
    except Exception:
        return None


def drop(pid):
    try:
        requests.delete('%s/browser/%s' % (API, pid), headers=HDR, timeout=40)
        print('deleted %s' % pid, flush=True)
    except Exception as e:
        print('delete failed %s: %s' % (pid, e), flush=True)


print('menubar=%s' % os.environ.get('MENUBAR', '?'), flush=True)
print('swept=%d' % sweep_leftovers(), flush=True)

results = []
fixed = os.environ.get('PROFILE_ID', '').strip()
if fixed:
    res = read_resolution(fixed)
    for hl in (False, True):
        o = measure(fixed, hl, 'headless' if hl else 'headed')
        o['profile'] = fixed; o['profile_resolution'] = res
        results.append(o)
else:
    for res in RESOLUTIONS:
        pid = make_profile(res)
        if not pid:
            continue
        code = set_resolution(pid, res)
        actual = read_resolution(pid)
        print('profile=%s wanted=%s put=%s actual=%s' % (pid, res, code, actual), flush=True)
        for hl in (False, True):
            o = measure(pid, hl, 'headless' if hl else 'headed')
            o['profile'] = pid; o['profile_resolution'] = actual
            results.append(o)
        drop(pid)

print(json.dumps(results, indent=1))
print()
print('%-10s %-9s %-26s %-7s %-5s %-34s %s' % (
    'profRes', 'mode', 'browser', 'eqWidth', 'dW', 'geom', 'scr'))
for r in results:
    d = r.get('data') or {}
    print('%-10s %-9s %-26s %-7s %-5s %-34s %s' % (
        r.get('profile_resolution'), r['label'], r.get('browser'),
        d.get('equalWidth'), d.get('frameDeltaW'), d.get('geom'), d.get('scr')))
    if r.get('error'):
        print('   ERROR: %s' % r['error'])
print()
print('--- policy / pointer ---')
for r in results:
    d = r.get('data') or {}
    print('%-10s %-9s nfeat=%-5s ptr=%s' % (r.get('profile_resolution'), r['label'],
                                            d.get('nfeat'), d.get('ptr')))
