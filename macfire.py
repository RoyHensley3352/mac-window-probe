import json,os,subprocess,sys,tempfile,time,urllib.request,websocket

NAMES = ["ads_power","dolphin_anty","gologin","multilogin","octo","headless"]
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "v3a")
JS = "".join(open(os.path.join(SRC,n+".js"),encoding="utf-8").read()+"\n" for n in NAMES)

EXPR = JS + """
(function(){var o={ua:navigator.userAgent,fired:[]};
["ads_power","dolphin_anty","gologin","multilogin","octo"].forEach(function(n){
  try{ if(window["detect_"+n]()===true) o.fired.push(n) }catch(e){ o.fired.push(n+":ERR") }});
try{ o.headless=window.detect_headless()===true }catch(e){ o.headless="ERR" }
o.core=(navigator.userAgent.match(/Chrome\/([\d.]+)/)||[])[1]||null;
o.screen=[screen.width,screen.height,screen.availWidth,screen.availHeight,screen.availTop,screen.availLeft];
o.win=[outerWidth,innerWidth,outerHeight,innerHeight,screenX,screenY];
o.mq={hoverNone:matchMedia("(hover: none)").matches,pointerNone:matchMedia("(pointer: none)").matches,
      anyNone:matchMedia("(any-pointer: none)").matches,hoverHover:matchMedia("(hover: hover)").matches};
try{var fp=document.featurePolicy,f=fp.features();o.n=f.length;
  o.has={hid:f.indexOf("hid")>=0,usb:f.indexOf("usb")>=0,xr:f.indexOf("xr-spatial-tracking")>=0,
         chvh:f.indexOf("ch-viewport-height")>=0,bt:f.indexOf("bluetooth")>=0,
         attr:f.indexOf("attribution-reporting")>=0,ss:f.indexOf("shared-storage")>=0,
         aria:f.indexOf("aria-notify")>=0,cheh:f.indexOf("ch-ua-high-entropy-values")>=0,
         rae:f.indexOf("record-ad-auction-events")>=0};
}catch(e){o.n=-1}
return JSON.stringify(o);})()"""

def run(binary, headless, port):
    udd = tempfile.mkdtemp(prefix="mp_")
    args = [binary, "--remote-debugging-port=%d"%port, "--user-data-dir="+udd,
            "--no-first-run", "--no-default-browser-check", "--remote-allow-origins=*",
            "about:blank"]
    if headless:
        args.insert(1, "--headless=new")
    p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ver = None
    for _ in range(40):
        try:
            ver = json.load(urllib.request.urlopen("http://127.0.0.1:%d/json/version"%port, timeout=3))
            break
        except Exception:
            time.sleep(1)
    if not ver:
        p.terminate()
        return {"err":"no cdp"}
    ws = websocket.create_connection(ver["webSocketDebuggerUrl"], timeout=40, suppress_origin=True)
    i = [0]
    def send(m, pr=None, sid=None):
        i[0] += 1
        o = {"id":i[0], "method":m, "params":pr or {}}
        if sid: o["sessionId"] = sid
        ws.send(json.dumps(o))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") == i[0]:
                return r
    t = send("Target.createTarget", {"url":"https://example.com/"})["result"]["targetId"]
    sid = send("Target.attachToTarget", {"targetId":t, "flatten":True})["result"]["sessionId"]
    send("Runtime.enable", None, sid)
    time.sleep(4)
    r = send("Runtime.evaluate", {"expression":EXPR, "returnByValue":True, "awaitPromise":True}, sid)
    res = r["result"]["result"]
    ws.close()
    p.terminate()
    return json.loads(res["value"]) if "value" in res else {"err":json.dumps(r)[:200]}

if __name__ == "__main__":
    binary = os.environ.get("CHROME_BIN")
    out = {}
    port = 9333
    for mode in ("headed","headless"):
        port += 1
        out[mode] = run(binary, mode=="headless", port)
        print(mode, json.dumps(out[mode]))
    open("macfire_result.json","w").write(json.dumps(out,indent=1))
