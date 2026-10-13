#!/usr/bin/env python3
"""
dashboard.py - Multi-PC Orchestration Status Dashboard + Remote Control
http://localhost:8787          ?꾩껜 PC ?꾪솴
http://localhost:8787/pc/ID   PC ?곸꽭 + ?먭꺽 吏??
"""

import http.server, json, urllib.request, urllib.parse, urllib.error, os, subprocess, base64, threading, time, socket, uuid, glob as globmod, re as _re, sys
from pathlib import Path
from datetime import datetime, timezone

OWNER       = "bernakilljos"
REPO        = "orchestration-status"
PORT        = 8787
_FALLBACK   = ""  # PAT???섍꼍蹂??GITHUB_PERSONAL_ACCESS_TOKEN)?먯꽌留?濡쒕뱶. 鍮꾩뼱?덉쑝硫?GitHub 湲곕뒫 鍮꾪솢??

# ?? 濡쒖뺄 硫붾え由???μ냼 ??
_status_store   = {}   # pc_id ??status dict
_screen_store   = {}   # pc_id ??{monitor_idx: bytes}
_cmd_store      = {}   # pc_id ??command dict (pending)
_remote_status  = {}   # pc_id ??remote status dict
_incoming_store = {}   # pc_id ??[{filename, content}, ...]  (?쒖뒪???湲곗뿴)
_ctrl_store     = {}   # pc_id ??{action: ...}  (而⑦듃濡?紐낅졊 ?湲곗뿴)
_deleted_pcs    = set()  # ?섎룞 ??젣??pc_id ???щ벑濡?李⑤떒
_store_lock     = threading.Lock()
_tunnel_url     = ""   # cloudflared tunnel URL

def _mask_pat(text):
    """PAT ?좏겙???ы븿??臾몄옄?댁뿉??ghp_/gho_/github_pat_ ?깆쓣 留덉뒪??""
    return _re.sub(r'(ghp_|gho_|github_pat_)[A-Za-z0-9_]+', r'\1****', str(text))
_gh_cache       = {}   # pc_id ??status dict (GitHub 留덉?留??깃났 罹먯떆)
_screen_gh_cache = {}  # "pc_id/monitor" ??(bytes, timestamp) ??GitHub ?ㅽ겕由?TTL 罹먯떆
_SCREEN_GH_TTL  = 5.0  # GitHub ?ㅽ겕由?理쒖냼 ?ъ“??媛꾧꺽(珥? ??rate limit 諛⑹?


# ?? GitHub helpers ????????????????????????????????????????????
_gh_rate_paused = False   # True?대㈃ GitHub API ?몄텧 李⑤떒
_gh_rate_reset  = 0       # rate limit 由ъ뀑 unix timestamp

def get_pat():
    pat = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN","")
    if not pat:
        try:
            r = subprocess.run(["powershell","-NoProfile","-Command",
                "[System.Environment]::GetEnvironmentVariable('GITHUB_PERSONAL_ACCESS_TOKEN','User')"],
                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5)
            pat = r.stdout.strip()
        except: pass
    return pat or _FALLBACK

def gh_headers():
    return {"Authorization":f"token {get_pat()}","Accept":"application/vnd.github.v3+json"}

def _gh_check_rate(resp_headers):
    """?묐떟 ?ㅻ뜑?먯꽌 rate limit ?붾웾 ?뺤씤, 200 ?댄븯?대㈃ ?쇱떆 以묐떒"""
    global _gh_rate_paused, _gh_rate_reset
    remaining = resp_headers.get("X-RateLimit-Remaining")
    if remaining is not None and int(remaining) < 200:
        _gh_rate_paused = True
        _gh_rate_reset = int(resp_headers.get("X-RateLimit-Reset", 0))
        print(f"[WARN] GitHub rate limit ?붾웾 {remaining} ??API ?몄텧 ?쇱떆 以묐떒 (由ъ뀑: {datetime.fromtimestamp(_gh_rate_reset).strftime('%H:%M:%S')})")

def _gh_is_available():
    """rate limit 以묐떒 ?곹깭 ?뺤씤, 由ъ뀑 ?쒓컙 吏?ъ쑝硫??먮룞 ?댁젣"""
    global _gh_rate_paused
    if not _gh_rate_paused:
        return True
    if time.time() >= _gh_rate_reset:
        _gh_rate_paused = False
        print("[OK] GitHub rate limit 由ъ뀑 ??API ?몄텧 ?ш컻")
        return True
    return False

def gh_get(path):
    if not _gh_is_available():
        raise Exception("GitHub rate limit ?쇱떆 以묐떒")
    req = urllib.request.Request(f"https://api.github.com/repos/{OWNER}/{REPO}/{path}",headers=gh_headers())
    try:
        with urllib.request.urlopen(req,timeout=10) as r:
            _gh_check_rate(r.headers)
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            _gh_check_rate(e.headers)
        raise

def gh_put(path, content_bytes, message, sha=None):
    if not _gh_is_available():
        raise Exception("GitHub rate limit ?쇱떆 以묐떒")
    body = {"message":message,"content":base64.b64encode(content_bytes).decode()}
    if sha: body["sha"] = sha
    req = urllib.request.Request(
        f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}",
        data=json.dumps(body).encode(),
        headers={**gh_headers(),"Content-Type":"application/json"}, method="PUT")
    try:
        with urllib.request.urlopen(req,timeout=10) as r:
            _gh_check_rate(r.headers)
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            _gh_check_rate(e.headers)
        raise

def gh_sha(path):
    try:
        return gh_get(f"contents/{path}").get("sha","")
    except: return ""

def fetch_all():
    # 濡쒖뺄 硫붾え由?(??PC ?ㅼ떆媛?+ HTTP POST濡?諛쏆? ?먭꺽 PC)
    local = {}
    with _store_lock:
        for pc_id, data in _status_store.items():
            local[pc_id] = data
    # GitHub 罹먯떆 (60珥덈쭏??諛깃렇?쇱슫??媛깆떊, 吏곸젒 ?몄텧 X ??rate limit 諛⑹?)
    merged = {**_gh_cache, **local}
    out = list(merged.values())
    out.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return out, None

def make_remote(pc_id):
    pid = urllib.parse.quote(pc_id)
    body_top = f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;flex-wrap:wrap">
  <a href="/pc/{pid}" class="back-btn">???ㅻ줈</a>
  <div style="font-size:16px;font-weight:700">?뼢 ?먭꺽 ?쒖뼱 ??{pc_id}</div>
  <div id="state" style="font-size:12px;color:var(--muted)">?곌껐 以?..</div>
  <div id="monitor-tabs" style="display:flex;gap:6px;margin-left:8px"></div>
  <button onclick="if(confirm('?먭꺽 ?먯씠?꾪듃瑜?以묐떒?좉퉴??'))sendCmd({{action:'stop'}})" style="margin-left:auto;background:rgba(248,113,113,.15);border:1px solid #f87171;color:#f87171;padding:6px 14px;border-radius:8px;cursor:pointer;font-size:12px">??以묐떒</button>
</div>
<div style="position:relative;width:100%;border:2px solid var(--border);border-radius:8px;box-sizing:border-box;overflow:hidden">
  <img id="screen" src="/remote-screen/{pc_id}/0" style="display:block;cursor:default;max-width:100%;width:100%;height:auto;object-fit:contain"
    onmousedown="dragStart(event)" onmousemove="dragMove(event)" onmouseup="dragEnd(event)"
    oncontextmenu="handleClick(event,true);return false"
    onerror="this.onerror=null">
  <div id="click-flash" style="position:absolute;width:20px;height:20px;border-radius:50%;background:rgba(79,142,247,.6);pointer-events:none;display:none;transform:translate(-50%,-50%)"></div>
</div>
<div style="margin-top:12px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
  <input id="key-input" placeholder="?띿뒪???낅젰 ??Enter"
    style="flex:1;background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:8px;font-size:13px;font-family:Consolas,monospace;outline:none"
    onkeydown="handleKey(event)">
  <button onclick="refreshScreen()" style="background:var(--bg3);border:1px solid var(--border);color:var(--muted);padding:8px 14px;border-radius:8px;cursor:pointer;font-size:12px">?벜</button>
</div>
<div id="keyboard" style="margin-top:10px;background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:16px;user-select:none;width:100%;box-sizing:border-box;overflow-x:auto"></div>
<style>
.kb{{background:#1e293b;border:1px solid #334155;color:#cbd5e1;border-radius:6px;cursor:pointer;font-size:12px;font-family:Consolas,monospace;height:42px;display:inline-flex;align-items:center;justify-content:center;transition:all .1s;box-shadow:0 2px 0 #0f172a;position:relative;top:0;white-space:nowrap;padding:0 8px}}
.kb:hover{{background:#2d3f55;border-color:#4f8ef7;color:#e2e8f0}}
.kb:active{{box-shadow:none;top:2px;background:#1a2535}}
.kb.active{{background:rgba(79,142,247,.3);border-color:#4f8ef7;color:#4f8ef7;box-shadow:0 0 8px rgba(79,142,247,.4)}}
.kb-row{{display:flex;gap:5px;margin-bottom:5px}}
</style>
<div id="msg" style="position:fixed;bottom:24px;right:24px;z-index:999;pointer-events:none"></div>
<script>
const PC_ID = '{pc_id}';
let curMonitor = 0, screenCount = 1, msgTimer;


function log(t, ok=true) {{
  const el = document.getElementById('msg');
  el.innerHTML = '<div style="background:'+(ok?'rgba(52,211,153,.15)':'rgba(248,113,113,.15)')+';border:1px solid '+(ok?'#34d399':'#f87171')+';color:'+(ok?'#34d399':'#f87171')+';padding:8px 16px;border-radius:10px;font-size:12px;font-weight:600;backdrop-filter:blur(8px);box-shadow:0 4px 20px rgba(0,0,0,.3)">'+t+'</div>';
  clearTimeout(msgTimer);
  msgTimer = setTimeout(() => {{ el.innerHTML=''; }}, 2500);
}}
function setReady(ok) {{ var el=document.getElementById('state'); el.textContent=ok?'???곌껐??:'???먯씠?꾪듃 ?놁쓬'; el.style.color=ok?'var(--green)':'var(--red)'; }}
function selectMonitor(idx) {{ curMonitor=idx; document.querySelectorAll('.mon-tab').forEach((b,i)=>{{ b.style.background=i===idx?'rgba(79,142,247,.3)':'var(--bg3)'; b.style.borderColor=i===idx?'#4f8ef7':'var(--border)'; }}); refreshScreen(); }}
function buildTabs(count) {{ var tabs=document.getElementById('monitor-tabs'); tabs.innerHTML=''; for(var i=0;i<count;i++){{ var b=document.createElement('button'); b.className='mon-tab'; b.textContent='紐⑤땲??+(i+1); b.style.cssText='background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:4px 12px;border-radius:6px;cursor:pointer;font-size:12px'; (function(idx){{b.onclick=function(){{selectMonitor(idx);}};}})(i); tabs.appendChild(b); }} selectMonitor(0); }}
var _screenFails=0;
function refreshScreen() {{ var img=document.getElementById('screen'); var url='/remote-screen/'+PC_ID+'/'+curMonitor+'?t='+Date.now(); var tmp=new Image(); tmp.onload=function(){{img.src=url;setReady(true);_screenFails=0;}}; tmp.onerror=function(){{_screenFails++;if(_screenFails>15)setReady(false);}}; tmp.src=url; }}
function sendCmd(obj) {{ var labels={{click:'?대┃',dblclick:'?붾툝?대┃',key:'?? '+obj.key,stop:'?먯씠?꾪듃 以묐떒'}}; var label=labels[obj.action]||obj.action; fetch('/remote-cmd/'+PC_ID,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(obj)}}).then(function(r){{return r.json();}}).then(function(d){{ log(d.ok?'??'+label:'???ㅽ뙣: '+d.error,d.ok); setTimeout(refreshScreen,1000); }}).catch(function(){{}}); }}
var dragX0,dragY0,dragging=false,dragBtn=0;
function getPos(e){{ var img=document.getElementById('screen'); var r=img.getBoundingClientRect(); return {{x:(e.clientX-r.left)/r.width, y:(e.clientY-r.top)/r.height}}; }}
function dragStart(e){{ if(e.button===2)return; var p=getPos(e); dragX0=p.x; dragY0=p.y; dragging=false; dragBtn=e.button; }}
function dragMove(e){{ if(dragBtn!==0)return; var p=getPos(e); if(Math.abs(p.x-dragX0)>0.005||Math.abs(p.y-dragY0)>0.005) dragging=true; }}
function dragEnd(e){{
  if(e.button===2){{ handleClick(e,true); return; }}
  var p=getPos(e);
  if(dragging){{
    sendCmd({{action:'drag',x0:dragX0,y0:dragY0,x1:p.x,y1:p.y,monitor:curMonitor}});
    dragging=false;
  }} else {{
    var f=document.getElementById('click-flash');
    var img=document.getElementById('screen'); var r=img.getBoundingClientRect();
    f.style.left=(e.clientX-r.left)+'px'; f.style.top=(e.clientY-r.top)+'px';
    f.style.display='block'; setTimeout(function(){{f.style.display='none';}},400);
    sendCmd({{action:'click',x:p.x,y:p.y,btn:'left',monitor:curMonitor}});
  }}
}}
function handleClick(e,right) {{ var p=getPos(e); sendCmd({{action:'click',x:p.x,y:p.y,btn:'right',monitor:curMonitor}}); }}
function handleKey(e) {{ if(e.key==='Enter'){{ var v=document.getElementById('key-input').value; if(v){{sendCmd({{action:'key',key:v}});document.getElementById('key-input').value='';}} }} }}
</script>"""

    body_kb = """<script>
var mCtrl=false,mAlt=false,mShift=false;
function toggleMod(mod) {
  if(mod==='ctrl') { mCtrl=!mCtrl; ['m-ctrl','m-ctrl2'].forEach(function(id){ var el=document.getElementById(id); if(el) el.classList.toggle('active',mCtrl); }); }
  if(mod==='alt')  { mAlt=!mAlt;   ['m-alt','m-alt2'].forEach(function(id){ var el=document.getElementById(id); if(el) el.classList.toggle('active',mAlt); }); }
  if(mod==='shift'){ mShift=!mShift; document.querySelectorAll('.m-shift').forEach(function(b){ b.classList.toggle('active',mShift); }); updateShift(); }
}
function updateShift() {
  document.querySelectorAll('[data-norm]').forEach(function(b){ b.textContent=mShift?b.dataset.shift:b.dataset.norm; });
}
function sk(rawKey) {
  var key=rawKey;
  if(rawKey.length===1) {
    if(mShift && /[a-z]/.test(rawKey)) key=rawKey.toUpperCase();
    if(mCtrl) key='^'+key.toLowerCase();
    if(mAlt)  key='%'+key;
  } else {
    if(mCtrl) key='^'+key;
    if(mAlt)  key='%'+key;
    if(mShift && rawKey!=='shift') key='+'+key;
  }
  sendCmd({action:'key',key:key});
  if(mCtrl||mAlt||mShift){ mCtrl=false;mAlt=false;mShift=false; document.querySelectorAll('.kb.active').forEach(function(b){b.classList.remove('active');}); updateShift(); }
}
function buildKeyboard() {
  var rows = [
    [['Esc','{ESC}',2],['F1','{F1}'],['F2','{F2}'],['F3','{F3}'],['F4','{F4}'],null,['F5','{F5}'],['F6','{F6}'],['F7','{F7}'],['F8','{F8}'],null,['F9','{F9}'],['F10','{F10}'],['F11','{F11}'],['F12','{F12}'],null,['PrtSc','{PRTSC}']],
    [['` ~','`'],['1 !','1'],['2 @','2'],['3 #','3'],['4 $','4'],['5 %','5'],['6 ^','6'],['7 &','7'],['8 *','8'],['9 (','9'],['0 )','0'],['- _','-'],['= +','='],['Backspace','{BACKSPACE}',2.5]],
    [['Tab','{TAB}',1.5],['q','q'],['w','w'],['e','e'],['r','r'],['t','t'],['y','y'],['u','u'],['i','i'],['o','o'],['p','p'],['[ {','['],['] }',']'],['| \\\\','\\\\',1.5]],
    [['Caps','{CAPSLOCK}',1.75],['a','a'],['s','s'],['d','d'],['f','f'],['g','g'],['h','h'],['j','j'],['k','k'],['l','l'],['; :',';'],["' \\"","'"],['Enter','{ENTER}',2.25]],
    [['Shift','shift',2.25,'m-shift'],['z','z'],['x','x'],['c','c'],['v','v'],['b','b'],['n','n'],['m','m'],[', <',','],['> .','.'],['? /','/'],[' Shift ','shift',2.75,'m-shift']],
    [['Ctrl','ctrl',1.5,'m-ctrl'],['Win','{LWIN}',1.25],['Alt','alt',1.25,'m-alt'],['Space',' ',6.5],['?쒖쁺','{HANGUL}',1.25],['?쒖옄','{HANJA}',1.25],['Win','{RWIN}',1.25],['Ctrl','ctrl',1.5,'m-ctrl2']]
  ];
  var nav = [
    [['Ins','{INSERT}'],['Home','{HOME}'],['PgUp','{PGUP}']],
    [['Del','{DELETE}'],['End','{END}'],['PgDn','{PGDN}']],
    [['',''],['??,'{UP}'],['','']],
    [['??,'{LEFT}'],['??,'{DOWN}'],['??,'{RIGHT}']]
  ];
  var num = [
    [['NumLk','{NUMLOCK}'],['Num/','{DIVIDE}'],['Num*','{MULTIPLY}'],['Num-','{SUBTRACT}']],
    [['7','{NUMPAD7}'],['8','{NUMPAD8}'],['9','{NUMPAD9}'],['+','{ADD}']],
    [['4','{NUMPAD4}'],['5','{NUMPAD5}'],['6','{NUMPAD6}'],['','']],
    [['1','{NUMPAD1}'],['2','{NUMPAD2}'],['3','{NUMPAD3}'],['Ent','{ENTER}']],
    [['0','{NUMPAD0}'],['',''],['.','{DECIMAL}'],['','']]
  ];
  var kb=document.getElementById('keyboard');
  var unit=44, gap=5;
  var wrap=document.createElement('div'); wrap.style.cssText='display:flex;gap:14px;align-items:flex-start;width:100%';
  var main=document.createElement('div');
  rows.forEach(function(row,ri) {
    var div=document.createElement('div'); div.className='kb-row';
    if(ri===0) div.style.marginBottom='8px';
    row.forEach(function(k) {
      if(k===null){ var sp=document.createElement('div');sp.style.width='12px';div.appendChild(sp);return; }
      var label=k[0],key=k[1],w=k[2]||1,id=k[3];
      var btn=document.createElement('button'); btn.className='kb';
      var parts=label.split(' ');
      var isMod=(key==='ctrl'||key==='alt'||key==='shift');
      if(!isMod && parts.length===2 && parts[0].length===1 && parts[1].length===1) {
        btn.dataset.norm=parts[0]; btn.dataset.shift=parts[1]; btn.textContent=parts[0];
        btn.onclick=function(){sk(key);};
      } else {
        btn.textContent=label;
        if(isMod) btn.onclick=function(){toggleMod(key);}; else btn.onclick=function(){sk(key);};
      }
      btn.style.width=(w*unit+(w-1)*gap)+'px';
      if(id) btn.id=id;
      if(key==='shift') btn.classList.add('m-shift');
      div.appendChild(btn);
    });
    main.appendChild(div);
  });
  wrap.appendChild(main);
  function buildNavBlock(data, pt) {{
    var d=document.createElement('div'); d.style.cssText='display:flex;flex-direction:column;gap:4px;padding-top:'+pt+'px';
    data.forEach(function(row) {{
      var div=document.createElement('div'); div.className='kb-row'; div.style.marginBottom='0';
      row.forEach(function(k) {{
        if(!k[0]){{var sp=document.createElement('div');sp.style.width='44px';div.appendChild(sp);return;}}
        var btn=document.createElement('button');btn.className='kb';btn.textContent=k[0];btn.style.width='44px';
        if(k[1])btn.onclick=function(){{sk(k[1]);}};else btn.disabled=true;
        div.appendChild(btn);
      }});
      d.appendChild(div);
    }});
    return d;
  }}
  wrap.appendChild(buildNavBlock(nav, 50));
  wrap.appendChild(buildNavBlock(num, 50));
  kb.appendChild(wrap);
}
buildKeyboard();
fetch('/remote-status/'+PC_ID).then(function(r){return r.json();}).then(function(d){ buildTabs(d.count||1); if(d.state&&d.state!=='unknown')setReady(true); }).catch(function(){ buildTabs(1); });
setInterval(refreshScreen,200);
</script>"""

    full_body = '<style>.container{max-width:100%!important;padding:4px!important;overflow:hidden!important;box-sizing:border-box!important}</style>' + body_top + body_kb
    return BASE.format(title=f"?먭꺽?쒖뼱 ??{pc_id}", css=CSS, body=full_body, ajax_poll="")

def fetch_incoming(pc_id):
    """incoming ??濡쒖뺄 硫붾え由щ쭔 (GitHub API ?ъ슜 ????"""
    with _store_lock:
        local = _incoming_store.get(pc_id, [])
    return [{"name": item["filename"], "_local": True} for item in local]

def fetch_history(pc_id, limit=20):
    """?대젰 ??git clone 罹먯떆?먯꽌 ?쎄린 (GitHub API ?ъ슜 ????"""
    return []


# ?? ?좏떥 ?????????????????????????????????????????????????????
def age_sec(t):
    try:
        dt = datetime.strptime(t,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc)-dt).total_seconds()
    except: return 9999

def fmt_ago(t):
    a = age_sec(t)
    if a < 60:   return f"{int(a)}珥???
    if a < 3600: return f"{int(a//60)}遺???
    return f"{int(a//3600)}?쒓컙 ??

def nl(text): return text.replace("\\n","\n") if text else ""

def ts_now(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def ts_file(): return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


# ?? SVG 紐⑤땲??????????????????????????????????????????????????
def monitor_svg(color, uid, running, pending, done):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 190" width="180" height="171">
  <defs><filter id="g{uid}"><feGaussianBlur stdDeviation="5" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
  <rect x="20" y="10" width="160" height="110" rx="10" fill="#0d1626" stroke="{color}" stroke-width="3" filter="url(#g{uid})"/>
  <rect x="30" y="20" width="140" height="90" rx="6" fill="#060d1f"/>
  <text x="100" y="52" text-anchor="middle" font-family="Segoe UI,sans-serif" font-size="11" fill="#64748b">?ㅽ뻾 以?/text>
  <text x="100" y="74" text-anchor="middle" font-family="Segoe UI,sans-serif" font-size="28" font-weight="bold" fill="{color}">{running}</text>
  <text x="58"  y="100" text-anchor="middle" font-family="Segoe UI,sans-serif" font-size="9" fill="#64748b">?湲?/text>
  <text x="58"  y="112" text-anchor="middle" font-family="Segoe UI,sans-serif" font-size="16" font-weight="bold" fill="#fbbf24">{pending}</text>
  <text x="142" y="100" text-anchor="middle" font-family="Segoe UI,sans-serif" font-size="9" fill="#64748b">?꾨즺</text>
  <text x="142" y="112" text-anchor="middle" font-family="Segoe UI,sans-serif" font-size="16" font-weight="bold" fill="#64748b">{done}</text>
  <rect x="88" y="120" width="24" height="16" fill="#1e3050"/>
  <rect x="68" y="136" width="64" height="8" rx="4" fill="#1e3050"/>
  <circle cx="185" cy="20" r="7" fill="{color}" opacity=".9"/></svg>"""


# ?? CSS ???????????????????????????????????????????????????????
CSS = """
:root{--bg:#060d1f;--bg2:#0d1626;--bg3:#162035;--border:#1e3050;
  --text:#e2e8f0;--muted:#64748b;--blue:#4f8ef7;--green:#34d399;
  --yellow:#fbbf24;--orange:#fb923c;--purple:#a78bfa;--red:#f87171;--cyan:#22d3ee}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.topbar{background:linear-gradient(90deg,#0a1628,#0f1e38);border-bottom:1px solid var(--border);
  padding:0 28px;height:56px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.logo{font-size:18px;font-weight:800;background:linear-gradient(90deg,var(--blue),var(--cyan));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.container{padding:28px;max-width:1400px;margin:0 auto}
.stat-row{display:flex;gap:14px;margin-bottom:32px;flex-wrap:wrap}
.stat-card{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:18px 24px;flex:1;min-width:130px;position:relative;overflow:hidden}
.stat-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1.2px;margin-bottom:8px;font-weight:600}
.stat-value{font-size:34px;font-weight:800;line-height:1}
.stat-sub{font-size:11px;color:var(--muted);margin-top:5px}
.section-title{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1.2px;margin-bottom:14px;font-weight:700}
.pc-grid{display:flex;flex-wrap:wrap;gap:28px;align-items:flex-start;margin-bottom:32px}
.pc-wrap{display:flex;flex-direction:column;align-items:center;cursor:pointer}
.pc-label{margin-top:6px;font-size:13px;font-weight:700;text-align:center}
.pc-ago{font-size:10px;color:var(--muted);margin-top:2px;text-align:center}
.pc-badges{display:flex;flex-wrap:wrap;gap:4px;justify-content:center;margin-top:6px;max-width:200px}
.badge{padding:3px 10px;border-radius:20px;font-size:10px;font-weight:700}
.b-codex {background:rgba(251,146,60,.12);color:var(--orange);border:1px solid rgba(251,146,60,.3)}
.b-gemini{background:rgba(79,142,247,.12);color:var(--blue);border:1px solid rgba(79,142,247,.3)}
.b-claude{background:rgba(167,139,250,.12);color:var(--purple);border:1px solid rgba(167,139,250,.3)}
.b-idle  {background:var(--bg3);color:var(--muted);border:1px solid var(--border)}
.back-btn{display:inline-flex;align-items:center;gap:6px;color:var(--muted);font-size:13px;
  text-decoration:none;margin-bottom:22px;padding:7px 14px;border:1px solid var(--border);border-radius:8px;transition:all .2s}
.back-btn:hover{color:var(--text);border-color:var(--blue)}
.detail-name{font-size:28px;font-weight:800;margin-bottom:6px}
.detail-meta{font-size:13px;color:var(--muted)}
table{width:100%;border-collapse:collapse;background:var(--bg2);border-radius:12px;overflow:hidden;border:1px solid var(--border);margin-bottom:20px}
th{padding:10px 16px;text-align:left;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;background:var(--bg3);border-bottom:1px solid var(--border)}
td{padding:10px 16px;border-bottom:1px solid rgba(30,48,80,.5);font-size:13px}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(255,255,255,.02)}
.chip{display:inline-block;background:var(--bg3);border:1px solid var(--border);border-radius:6px;padding:3px 10px;font-size:11px;margin:3px}
.chip-run{border-color:rgba(52,211,153,.4);color:var(--green);background:rgba(52,211,153,.06)}
.chip-done{color:var(--muted)}
.empty{color:var(--muted);font-size:13px;padding:4px 0}
.error-box{background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.3);border-radius:12px;padding:24px;color:var(--red);margin-bottom:24px}
/* ??*/
.tab-bar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.tab-btn{background:var(--bg3);border:1px solid var(--border);color:var(--muted);padding:7px 16px;border-radius:8px;cursor:pointer;font-size:12px;font-family:inherit;transition:all .2s}
.tab-btn:hover{border-color:var(--blue);color:var(--text)}
.tab-btn.active{background:rgba(79,142,247,.15);border-color:var(--blue);color:var(--blue)}
.tab-pane{display:none;margin-bottom:24px}
.tab-pane.active{display:block}
.summary-box{background:var(--bg3);border:1px solid var(--border);border-radius:10px;padding:16px;
  font-size:12px;line-height:1.7;color:#94a3b8;white-space:pre-wrap;word-break:break-all;
  max-height:360px;overflow-y:auto;font-family:'Consolas',monospace}
/* 而⑦듃濡?SVG 踰꾪듉 */
.ctrl-panel{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:10px}
.ctrl-svg-btn{cursor:pointer;transition:transform .15s,filter .15s}
.ctrl-svg-btn:hover{transform:scale(1.12);filter:brightness(1.3)}
.ctrl-svg-btn:active{transform:scale(.96)}
/* ?먭꺽 吏??*/
.task-form{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:22px;margin-bottom:24px;position:relative;overflow:hidden}
.task-form::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--blue),var(--cyan))}
.task-form-title{font-size:14px;font-weight:700;margin-bottom:14px;color:var(--blue);display:flex;align-items:center;gap:8px}
.task-input{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:10px;
  padding:14px;color:var(--text);font-size:13px;font-family:'Consolas',monospace;
  resize:vertical;min-height:180px;outline:none;transition:border-color .2s;line-height:1.6}
.task-input:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(79,142,247,.1)}
.task-input:focus{border-color:var(--blue)}
.task-input::placeholder{color:var(--muted)}
.send-btn{margin-top:10px;background:linear-gradient(90deg,var(--blue),var(--cyan));
  border:none;color:#fff;padding:10px 24px;border-radius:8px;cursor:pointer;
  font-size:13px;font-weight:700;font-family:inherit;transition:opacity .2s}
.send-btn:hover{opacity:.85}
.send-msg{font-size:12px;color:var(--muted);margin-top:8px;min-height:18px}
.incoming-item{background:var(--bg3);border:1px solid var(--border);border-radius:8px;
  padding:10px 14px;margin-bottom:8px;display:flex;align-items:center;justify-content:space-between}
.incoming-name{font-size:12px;color:var(--cyan)}
.del-btn{background:transparent;border:1px solid rgba(248,113,113,.4);color:var(--red);
  padding:3px 10px;border-radius:6px;cursor:pointer;font-size:11px;font-family:inherit}
/* PC 移대뱶 ?섑띁 */
.pc-card-wrap{display:flex;flex-direction:column;align-items:center}
.pc-card-wrap .pc-wrap{text-decoration:none;color:var(--text);transition:transform .2s;display:flex;flex-direction:column;align-items:center}
.pc-card-wrap .pc-wrap:hover{transform:translateY(-6px)}
.pc-card-wrap.stale{opacity:.4;filter:grayscale(.6)}
.pc-ctrl{display:flex;align-items:center;gap:6px;margin-top:8px;padding:6px 10px;background:var(--bg2);border:1px solid var(--border);border-radius:20px}
.pc-ctrl-btn{cursor:pointer;transition:transform .15s,filter .15s;display:flex;align-items:center;justify-content:center}
.pc-ctrl-btn:hover{transform:scale(1.18);filter:brightness(1.4)}
.pc-ctrl-btn:active{transform:scale(.92)}
/* ?좊땲硫붿씠??*/
@keyframes pulse-green{0%,100%{filter:drop-shadow(0 0 6px #34d399)}50%{filter:drop-shadow(0 0 14px #34d399)}}
@keyframes pulse-red  {0%,100%{filter:drop-shadow(0 0 6px #f87171)}50%{filter:drop-shadow(0 0 14px #f87171)}}
.anim-green svg{animation:pulse-green 2s ease-in-out infinite}
.anim-red   svg{animation:pulse-red   1.5s ease-in-out infinite}
/* ??젣 紐⑤떖 */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.6);backdrop-filter:blur(4px);z-index:9999;display:flex;align-items:center;justify-content:center;opacity:0;transition:opacity .2s}
.modal-overlay.show{opacity:1}
.modal-box{background:var(--bg2);border:1px solid var(--border);border-radius:18px;padding:32px;max-width:380px;width:90%;text-align:center;transform:scale(.9);transition:transform .2s}
.modal-overlay.show .modal-box{transform:scale(1)}
.modal-icon{margin-bottom:16px}
.modal-title{font-size:16px;font-weight:700;color:var(--text);margin-bottom:8px}
.modal-desc{font-size:13px;color:var(--muted);margin-bottom:24px;line-height:1.6}
.modal-desc code{color:var(--cyan);font-size:12px}
.modal-btns{display:flex;gap:10px;justify-content:center}
.modal-btn{padding:10px 24px;border-radius:10px;font-size:13px;font-weight:600;cursor:pointer;border:none;transition:all .15s}
.modal-btn-cancel{background:var(--bg3);color:var(--muted)}
.modal-btn-cancel:hover{background:var(--border);color:var(--text)}
.modal-btn-del{background:rgba(248,113,113,.15);color:#f87171;border:1px solid rgba(248,113,113,.3)}
.modal-btn-del:hover{background:rgba(248,113,113,.3)}
"""

BASE = """<!DOCTYPE html><html lang="ko" translate="no"><head>
<meta charset="utf-8"><meta name="google" content="notranslate">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>{css}</style></head><body>
<div class="topbar">
  <div class="logo">??Orchestration Dashboard</div>
  <div style="font-size:12px;color:#64748b" id="clk"></div>
</div>
<script>function tick(){{document.getElementById('clk').textContent=new Date().toLocaleString('ko-KR')}}tick();setInterval(tick,1000)</script>
<div class="container" id="main-container">{body}</div>
{ajax_poll}
</body></html>"""


# ?? 硫붿씤 ?섏씠吏 ???????????????????????????????????????????????
def make_index(statuses, err, body_only=False):
    if err:
        body = f'<div class="error-box"> ?곌껐 ?ㅻ쪟 ??{err}</div>'
        if body_only: return body
        return BASE.format(title="??쒕낫??,css=CSS,body=body,ajax_poll="")

    tc=sum(s.get("running_codex",0) for s in statuses)
    tg=sum(s.get("running_gemini",0) for s in statuses)
    tl=sum(s.get("running_claude",0) for s in statuses)
    tr=tc+tg+tl
    tp=sum(s.get("pending",0) for s in statuses)
    td=sum(s.get("done",0) for s in statuses)

    def scard(accent,label,val,sub=""):
        return f'<div class="stat-card"><div style="position:absolute;top:0;left:0;right:0;height:3px;background:{accent}"></div><div class="stat-label">{label}</div><div class="stat-value">{val}</div>{"<div class=stat-sub>"+sub+"</div>" if sub else ""}</div>'

    stat_row = '<div class="stat-row">' + \
        scard("linear-gradient(90deg,var(--blue),var(--cyan))","?곌껐??PC",f'<span style="color:var(--blue)">{len(statuses)}</span>') + \
        scard("linear-gradient(90deg,var(--green),var(--cyan))","?ㅽ뻾 以?,f'<span style="color:var(--green)">{tr}</span>',f"Claude {tl} 쨌 Codex {tc} 쨌 Gemini {tg}") + \
        scard("linear-gradient(90deg,var(--yellow),var(--orange))","?湲??쒖뒪??,f'<span style="color:var(--yellow)">{tp}</span>') + \
        scard("linear-gradient(90deg,var(--purple),var(--blue))","?꾨즺 ?쒖뒪??,f'<span style="color:var(--muted)">{td}</span>') + \
        '</div>'

    pcs = ""
    for s in statuses:
        pc=s.get("pc","?"); pc_id=s.get("pc_id",pc)
        r_c=s.get("running_codex",0); r_g=s.get("running_gemini",0); r_cl=s.get("running_claude",0)
        running=r_c+r_g+r_cl; pending=s.get("pending",0); done=s.get("done",0)
        updated=s.get("updated_at",""); stale=age_sec(updated)>300; ago=fmt_ago(updated)
        color="#f87171" if stale else ("#34d399" if running else "#4f8ef7")
        anim="anim-red" if stale else ("anim-green" if running else "")
        bdgs=("".join([f'<span class="badge b-claude">Claude {r_cl}</span>' if r_cl else "",
                       f'<span class="badge b-codex">Codex {r_c}</span>' if r_c else "",
                       f'<span class="badge b-gemini">Gemini {r_g}</span>' if r_g else ""])
              or '<span class="badge b-idle">?湲?以?/span>')
        warn=" " if stale else ""
        pid_js = pc_id.replace("'","\\'")

        # 踰꾪듉 ?곹깭: stale=?묐떟?놁쓬(?뺤???, running=?뚯빱?ㅽ뻾以?
        # ?뺤?: ?뺤긽???뚮쭔 ?쒖꽦 / ?ш컻: stale???뚮쭔 ?쒖꽦 / 以묐떒: running>0???뚮쭔 ?쒖꽦
        def ctrl_btn(action, title, svg_inner, active):
            opacity = "1" if active else "0.25"
            click = f"quickCtrl('{pid_js}','{action}',this)" if active else ""
            cursor = "pointer" if active else "default"
            return f'<div class="pc-ctrl-btn" onclick="{click}" title="{title}" style="opacity:{opacity};cursor:{cursor}">{svg_inner}</div>'

        pause_svg  = '<svg width="30" height="30" viewBox="0 0 30 30"><circle cx="15" cy="15" r="14" fill="rgba(248,113,113,.15)" stroke="#f87171" stroke-width="1.5"/><rect x="9" y="8" width="4" height="14" rx="1.5" fill="#f87171"/><rect x="17" y="8" width="4" height="14" rx="1.5" fill="#f87171"/></svg>'
        resume_svg = '<svg width="30" height="30" viewBox="0 0 30 30"><circle cx="15" cy="15" r="14" fill="rgba(52,211,153,.15)" stroke="#34d399" stroke-width="1.5"/><polygon points="10,8 10,22 23,15" fill="#34d399"/></svg>'
        stop_svg   = '<svg width="30" height="30" viewBox="0 0 30 30"><circle cx="15" cy="15" r="14" fill="rgba(249,115,22,.15)" stroke="#f97316" stroke-width="1.5"/><rect x="8" y="8" width="14" height="14" rx="2" fill="#f97316"/></svg>'

        remote_svg = '<svg width="30" height="30" viewBox="0 0 30 30"><circle cx="15" cy="15" r="14" fill="rgba(167,139,250,.15)" stroke="#a78bfa" stroke-width="1.5"/><rect x="7" y="9" width="16" height="10" rx="2" fill="none" stroke="#a78bfa" stroke-width="1.5"/><circle cx="15" cy="14" r="2.5" fill="none" stroke="#a78bfa" stroke-width="1.2"/><line x1="11" y1="19" x2="11" y2="22" stroke="#a78bfa" stroke-width="1.5"/><line x1="19" y1="19" x2="19" y2="22" stroke="#a78bfa" stroke-width="1.5"/><line x1="9" y1="22" x2="21" y2="22" stroke="#a78bfa" stroke-width="1.5"/></svg>'
        remote_btn = f'<a href="/remote/{urllib.parse.quote(pc_id)}" title="?먭꺽 ?쒖뼱" style="display:flex" onclick="event.stopPropagation()"><span class="pc-ctrl-btn">{remote_svg}</span></a>'

        del_svg = f'<svg width="30" height="30" viewBox="0 0 30 30"><circle cx="15" cy="15" r="14" fill="rgba(248,113,113,.1)" stroke="#f87171" stroke-width="1.5"/><line x1="10" y1="10" x2="20" y2="20" stroke="#f87171" stroke-width="2" stroke-linecap="round"/><line x1="20" y1="10" x2="10" y2="20" stroke="#f87171" stroke-width="2" stroke-linecap="round"/></svg>'
        del_btn = '<div class="pc-ctrl-btn" onclick="delPc(\'{}\')" title="PC 紐⑸줉?먯꽌 ??젣">{}</div>'.format(pid_js, del_svg)

        ctrl_btns = (
            f'<div class="pc-ctrl" onclick="event.preventDefault()">'
            + ctrl_btn("pause",  "?쇱떆?뺤?", pause_svg,  not stale)
            + ctrl_btn("resume", "?ш컻",     resume_svg, stale)
            + ctrl_btn("stop",   "?뚯빱 以묐떒", stop_svg,   running > 0)
            + remote_btn
            + del_btn
            + f'<div id="qmsg-{pc_id}" style="font-size:10px;color:#64748b;min-width:50px;text-align:center"></div>'
            + '</div>'
        )
        proj_details = {p.get("name",""): p for p in s.get("project_details",[])}
        proj_names_raw = s.get("projects","").strip()
        proj_list = list(dict.fromkeys(p for p in proj_names_raw.split() if p))
        pc_tag = f'<span style="font-weight:400;color:var(--muted);font-size:11px"> ({pc})</span>'
        if proj_list:
            for proj in proj_list:
                # ?꾨줈?앺듃蹂??섏튂 ?ъ슜
                pd = proj_details.get(proj, {})
                p_rc = pd.get("running_codex",0); p_rg = pd.get("running_gemini",0); p_rcl = pd.get("running_claude",0)
                p_run = p_rc + p_rg + p_rcl; p_pend = pd.get("pending",0); p_done = pd.get("done",0)
                p_color = "#f87171" if stale else ("#34d399" if p_run else "#4f8ef7")
                p_anim = "anim-red" if stale else ("anim-green" if p_run else "")
                p_bdgs = ("".join([f'<span class="badge b-claude">Claude {p_rcl}</span>' if p_rcl else "",
                                   f'<span class="badge b-codex">Codex {p_rc}</span>' if p_rc else "",
                                   f'<span class="badge b-gemini">Gemini {p_rg}</span>' if p_rg else ""])
                          or '<span class="badge b-idle">?湲?以?/span>')
                label = f'{proj}{pc_tag}'
                pcs += f'<div class="pc-card-wrap {p_anim}{" stale" if stale else ""}"><a href="/pc/{urllib.parse.quote(pc_id)}?project={urllib.parse.quote(proj)}" class="pc-wrap">{monitor_svg(p_color,pc_id[:6],p_run,p_pend,p_done)}<div class="pc-label">{label}{warn}</div><div class="pc-ago">{ago}</div><div class="pc-badges">{p_bdgs}</div></a>{ctrl_btns}</div>'
        else:
            pcs += f'<div class="pc-card-wrap {anim}{" stale" if stale else ""}"><a href="/pc/{urllib.parse.quote(pc_id)}" class="pc-wrap">{monitor_svg(color,pc_id[:6],running,pending,done)}<div class="pc-label">{pc}{warn}</div><div class="pc-ago">{ago}</div><div class="pc-badges">{bdgs}</div></a>{ctrl_btns}</div>'

    if not pcs:
        pcs = f'<div style="display:flex;flex-direction:column;align-items:center;opacity:.4">{monitor_svg("#4f8ef7","wait",0,0,0)}<div style="margin-top:8px;font-size:14px;color:#64748b;font-weight:700">?湲?以묒엯?덈떎</div><div style="font-size:12px;color:#475569;margin-top:4px">媛?PC?먯꽌 install.bat???ㅽ뻾?섏꽭??/div></div>'

    metrics_section = '<div class="section-title">硫뷀듃由?(24h)</div><div id="metrics-summary" style="background:#1e293b;border:1px solid #334155;border-radius:6px;padding:12px;margin-bottom:16px;font-family:monospace;font-size:12px;white-space:pre;overflow-x:auto;color:#94a3b8;max-height:200px;overflow-y:auto"><span style="color:#64748b">濡쒕뵫 以?..</span></div>'
    body = stat_row + metrics_section + '<div class="section-title">PC ?꾪솴</div><div class="pc-grid">'+pcs+'</div>'
    if body_only: return body
    ajax_poll = """<script>
function quickCtrl(pcId, action, btn) {
  var msgEl = document.getElementById('qmsg-' + pcId);
  if (msgEl) msgEl.textContent = '?꾩넚 以?..';
  fetch('/control/' + pcId + '/' + action).then(function(r){return r.text();}).then(function(t){
    if (msgEl) msgEl.textContent = t === 'OK' ? '???꾨즺' : '???ㅽ뙣';
    setTimeout(function(){ if (msgEl) msgEl.textContent = ''; }, 3000);
  });
}
function delPc(pcId) {
  var ov = document.createElement('div');
  ov.className = 'modal-overlay';
  var box = document.createElement('div');
  box.className = 'modal-box';
  box.innerHTML = '<div class="modal-icon"><svg width="56" height="56" viewBox="0 0 56 56"><circle cx="28" cy="28" r="26" fill="rgba(248,113,113,.1)" stroke="#f87171" stroke-width="2"/><path d="M28 16v16" stroke="#f87171" stroke-width="3" stroke-linecap="round"/><circle cx="28" cy="38" r="2" fill="#f87171"/></svg></div>'
    + '<div class="modal-title">' + pcId + '</div>'
    + '<div class="modal-desc">PC瑜?紐⑸줉?먯꽌 ??젣?좉퉴??<br><code>?ㅼ떆 ?ㅽ뻾?섎㈃ ?먮룞 ?щ벑濡앸맗?덈떎</code></div>'
    + '<div class="modal-btns"><button class="modal-btn modal-btn-cancel" id="modal-cancel-btn">痍⑥냼</button><button class="modal-btn modal-btn-del" id="modal-del-btn">??젣</button></div>';
  ov.appendChild(box);
  document.body.appendChild(ov);
  setTimeout(function(){ ov.classList.add('show'); }, 10);
  document.getElementById('modal-cancel-btn').onclick = function(){ ov.remove(); };
  document.getElementById('modal-del-btn').onclick = function(){
    ov.remove();
    fetch('/del-pc/' + pcId).then(function(r){return r.text();}).then(function(t){
      if (t === 'OK') location.reload();
    });
  };
  ov.onclick = function(e){ if(e.target===ov) ov.remove(); };
}
function updateMetrics(){
  fetch('/api/metrics?hours=24').then(function(r){return r.json();}).then(function(data){
    var el=document.getElementById('metrics-summary');
    if(!el) return;
    var lines=['Period: last 24h','?????????????????????????????????????????????'];
    var total_cost=0, total_calls=0;
    for(var ai in data){
      var m=data[ai];
      var cost=m.total_cost_usd||0;
      var calls=m.count||0;
      var sr=(m.success_rate*100).toFixed(1);
      total_cost+=cost;
      total_calls+=calls;
      var tokens_in=m.tokens_in||0;
      var tokens_out=m.tokens_out||0;
      var t_in=tokens_in>1000000?(tokens_in/1000000).toFixed(1)+'M':tokens_in>1000?(tokens_in/1000).toFixed(1)+'K':tokens_in;
      var t_out=tokens_out>1000000?(tokens_out/1000000).toFixed(1)+'M':tokens_out>1000?(tokens_out/1000).toFixed(1)+'K':tokens_out;
      lines.push(ai.padEnd(20) + calls.toString().padEnd(10) + sr.padEnd(11)+'% ' + (t_in+'/'+t_out).padEnd(20) + ('$'+cost.toFixed(4)).padEnd(12));
    }
    lines.push('?????????????????????????????????????????????');
    lines.push(('TOTAL').padEnd(20) + total_calls.toString().padEnd(10) + '' + ('$'+total_cost.toFixed(4)).padEnd(12));
    el.innerHTML=lines.join('\\n');
  }).catch(function(e){
    var el=document.getElementById('metrics-summary');
    if(el) el.innerHTML='Error loading metrics';
  });
}
updateMetrics();
setInterval(updateMetrics, 30000);
setInterval(function(){
  if(document.querySelector('.modal-overlay')) return;
  fetch('/api/index-body').then(function(r){return r.text();}).then(function(html){
    var c=document.getElementById('main-container');
    if(c) c.innerHTML=html;
  }).catch(function(){});
}, 1000);
</script>"""
    return BASE.format(title="?ㅼ??ㅽ듃?덉씠????쒕낫??,css=CSS,body=body,ajax_poll=ajax_poll)


# ?? ?곸꽭 ?섏씠吏 ???????????????????????????????????????????????
def make_detail(s, body_only=False, project=""):
    pc=s.get("pc","?"); pc_id=s.get("pc_id",pc); mac=s.get("mac","")
    updated=s.get("updated_at",""); stale=age_sec(updated)>300
    # ?꾨줈?앺듃 ?꾪꽣留?
    if project:
        pd = next((p for p in s.get("project_details",[]) if p.get("name")==project), {})
        r_c=pd.get("running_codex",0); r_g=pd.get("running_gemini",0); r_cl=pd.get("running_claude",0)
        running=r_c+r_g+r_cl; pending=pd.get("pending",0); done=pd.get("done",0)
        projects=project; ago=fmt_ago(updated)
    else:
        r_c=s.get("running_codex",0); r_g=s.get("running_gemini",0); r_cl=s.get("running_claude",0)
        running=r_c+r_g+r_cl; pending=s.get("pending",0); done=s.get("done",0)
        projects=s.get("projects","").strip() or "-"; ago=fmt_ago(updated)
    color="#f87171" if stale else ("#34d399" if running else "#4f8ef7")
    anim="anim-red" if stale else ("anim-green" if running else "")

    # ?붿빟 (?꾨줈?앺듃 ?꾪꽣 ?곸슜)
    if project and pd:
        task_sum   = nl(pd.get("impl_summary","") or s.get("task_summary",""))   or "?곗씠???놁쓬"
        impl_sum   = nl(pd.get("impl_summary",""))   or "?곗씠???놁쓬 (docs/implementation-report.md)"
        review_sum = nl(pd.get("review_summary","")) or "?곗씠???놁쓬 (docs/review-result.txt)"
    else:
        task_sum   = nl(s.get("task_summary",""))   or "?곗씠???놁쓬"
        impl_sum   = nl(s.get("impl_summary",""))   or "?곗씠???놁쓬 (docs/implementation-report.md)"
        review_sum = nl(s.get("review_summary","")) or "?곗씠???놁쓬 (docs/review-result.txt)"

    # ?ㅽ뻾 以??쒖뒪??(?꾨줈?앺듃 ?꾪꽣 ?곸슜)
    _running_tasks = (pd.get("running_tasks",[]) if project and pd else s.get("running_tasks",[]))
    run_rows="".join(f'<tr><td><span class="chip chip-run">{t.get("task","?")}</span></td>'
        f'<td><span class="badge b-{t.get("ai","?")}">{t.get("ai","?").capitalize()}</span></td>'
        f'<td style="color:var(--muted);font-size:12px">{t.get("worker","?")}</td></tr>'
        for t in _running_tasks) or '<tr><td colspan=3 class="empty">?ㅽ뻾 以??놁쓬</td></tr>'

    # ?쒖뒪??移?(?꾨줈?앺듃 ?꾪꽣 ?곸슜)
    _pending_tasks = (pd.get("pending_tasks",[]) if project and pd else s.get("pending_tasks",[]))
    _done_tasks = (pd.get("done_tasks",[]) if project and pd else s.get("done_tasks",[]))
    pend_chips="".join(f'<span class="chip">{t}</span>' for t in _pending_tasks) or '<span class="empty">?놁쓬</span>'
    done_chips="".join(f'<span class="chip chip-done">{t}</span>' for t in _done_tasks) or '<span class="empty">?놁쓬</span>'

    # ?꾨줈?앺듃蹂?移대뱶
    proj_details = s.get("project_details", [])
    proj_section = ""
    if len(proj_details) > 1:
        proj_cards = ""
        for p in proj_details:
            pname   = p.get("name","?")
            pr      = p.get("running", 0)
            pc_     = p.get("running_codex", 0)
            pg      = p.get("running_gemini", 0)
            pl      = p.get("running_claude", 0)
            pp      = p.get("pending", 0)
            p_dn    = p.get("done", 0)
            p_color = "#34d399" if pr else "#4f8ef7"
            bdgs    = ("".join([
                f'<span class="badge b-claude">Claude {pl}</span>' if pl else "",
                f'<span class="badge b-codex">Codex {pc_}</span>' if pc_ else "",
                f'<span class="badge b-gemini">Gemini {pg}</span>' if pg else "",
            ]) or '<span class="badge b-idle">?湲?/span>')
            p_tasks = "".join(f'<span class="chip chip-run">{t}</span>' for t in p.get("running_tasks",[]))
            proj_cards += f"""<div style="background:var(--bg2);border:1px solid {'rgba(52,211,153,.4)' if pr else 'var(--border)'};border-radius:14px;padding:18px;position:relative;overflow:hidden">
  <div style="position:absolute;top:0;left:0;right:0;height:3px;background:{p_color}"></div>
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
    <div style="font-size:15px;font-weight:700;color:var(--text)">{pname}</div>
    <div style="display:flex;gap:6px">{bdgs}</div>
  </div>
  <div style="display:flex;gap:20px;margin-bottom:10px">
    <div><div style="font-size:22px;font-weight:800;color:{p_color}">{pr}</div><div style="font-size:10px;color:var(--muted);text-transform:uppercase">?ㅽ뻾 以?/div></div>
    <div><div style="font-size:22px;font-weight:800;color:var(--yellow)">{pp}</div><div style="font-size:10px;color:var(--muted);text-transform:uppercase">?湲?/div></div>
    <div><div style="font-size:22px;font-weight:800;color:var(--muted)">{p_dn}</div><div style="font-size:10px;color:var(--muted);text-transform:uppercase">?꾨즺</div></div>
  </div>
  {('<div style="margin-top:6px">' + p_tasks + '</div>') if p_tasks else ''}
</div>"""
        proj_section = f'<div class="section-title">?꾨줈?앺듃蹂??꾪솴 ({len(proj_details)}媛?</div><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;margin-bottom:24px">{proj_cards}</div>'

    # ?꾨줈?앺듃 ?좏깮 ?듭뀡
    project_options = "".join(
        f'<option value="{p.get("path","")}">{p.get("name","?")}</option>'
        for p in proj_details
    ) or '<option value="">?꾨줈?앺듃 ?놁쓬</option>'

    # ?대젰
    hist_rows=""
    for f in fetch_history(pc_id):
        n=f.get("name","").replace(".json","")
        try: dt=f"{n[0:4]}-{n[4:6]}-{n[6:8]} {n[9:11]}:{n[11:13]}:{n[13:15]} UTC"
        except: dt=n
        hist_rows+=f'<tr><td style="font-size:12px;color:var(--muted)">{dt}</td><td style="font-size:11px;color:#475569">{f.get("sha","")[:7]}</td></tr>'
    if not hist_rows: hist_rows='<tr><td colspan=2 class="empty">?대젰 ?놁쓬</td></tr>'

    # incoming ?湲?吏??
    incoming = fetch_incoming(pc_id)
    inc_html = ""
    for f in incoming:
        inc_html += '<div class="incoming-item"><span class="incoming-name">?뱞 {}</span><button class="del-btn" onclick="delTask(\'{}\',\'{}\',\'{}\')">痍⑥냼</button></div>'.format(f["name"], pc_id, f["name"], f.get("sha",""))
    if not inc_html:
        inc_html = '<div class="empty">?湲?以묒씤 ?먭꺽 吏???놁쓬</div>'

    # 李⑦듃
    charts = f"""<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-bottom:24px">
  <div style="background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:18px">
    <div class="section-title" style="margin-bottom:12px">?쒖뒪???꾪솴</div>
    <div style="position:relative;height:160px"><canvas id="donut"></canvas></div>
  </div>
  <div style="background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:18px">
    <div class="section-title" style="margin-bottom:12px">AI ?뚯빱</div>
    <div style="position:relative;height:160px"><canvas id="bar"></canvas></div>
  </div>
</div>
<script>
if (typeof Chart !== 'undefined') {{
const co={{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{color:'#94a3b8',font:{{size:11}}}}}}}}}};
new Chart(document.getElementById('donut'),{{type:'doughnut',
  data:{{labels:['?꾨즺','?湲?,'?ㅽ뻾以?],datasets:[{{data:[{done},{pending},{running}],backgroundColor:['#4f8ef7','#fbbf24','#34d399'],borderWidth:0,hoverOffset:4}}]}},
  options:{{...co,cutout:'65%'}}}});
if (typeof Chart !== 'undefined') {{
new Chart(document.getElementById('bar'),{{type:'bar',
  data:{{labels:['Claude ?ㅺ퀎','Codex 援ы쁽','Gemini 寃利?],datasets:[{{data:[{r_cl},{r_c},{r_g}],backgroundColor:['#a78bfa','#fb923c','#4f8ef7'],borderRadius:6,borderSkipped:false}}]}},
  options:{{...co,plugins:{{legend:{{display:false}}}},scales:{{
    x:{{ticks:{{color:'#64748b'}},grid:{{color:'rgba(30,48,80,.5)'}}}},
    y:{{ticks:{{color:'#64748b',stepSize:1}},grid:{{color:'rgba(30,48,80,.5)'}}}}}}}}
}});
}}
</script>"""

    body = f"""
<a href="/" class="back-btn">???꾩껜 紐⑸줉</a>

<!-- ?ㅻ뜑 -->
<div style="display:flex;align-items:flex-start;gap:24px;margin-bottom:28px;flex-wrap:wrap">
  <div class="{anim}" style="flex-shrink:0">{monitor_svg(color,pc_id[:6]+"d",running,pending,done)}</div>
  <div style="flex:1;min-width:240px">
    <div class="detail-name">{projects} <span style="font-size:16px;font-weight:400;color:var(--muted)">({pc})</span></div>
    <div class="detail-meta" style="margin-bottom:12px">?낅뜲?댄듃: {ago} 쨌 ?꾨줈?앺듃: {projects} 쨌 MAC: {mac}{'   ?묐떟?놁쓬' if stale else ''}</div>
    <div class="ctrl-panel">
      <!-- ?쇱떆?뺤?: ?뺤긽???뚮쭔 ?쒖꽦 -->
      <div class="ctrl-svg-btn" onclick="{("ctrl('pause')" if not stale else "")}" title="?쇱떆?뺤?" style="opacity:{('1' if not stale else '0.25')};cursor:{('pointer' if not stale else 'default')}">
        <svg width="64" height="64" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="30" fill="rgba(248,113,113,.1)" stroke="#f87171" stroke-width="2"/>
          <rect x="20" y="18" width="9" height="28" rx="3" fill="#f87171"/>
          <rect x="35" y="18" width="9" height="28" rx="3" fill="#f87171"/>
          <text x="32" y="58" text-anchor="middle" font-size="8" fill="#f87171" font-family="Segoe UI,sans-serif">?쇱떆?뺤?</text>
        </svg>
      </div>
      <!-- ?ш컻: stale(?뺤??????뚮쭔 ?쒖꽦 -->
      <div class="ctrl-svg-btn" onclick="{("ctrl('resume')" if stale else "")}" title="?ш컻" style="opacity:{('1' if stale else '0.25')};cursor:{('pointer' if stale else 'default')}">
        <svg width="64" height="64" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="30" fill="rgba(52,211,153,.1)" stroke="#34d399" stroke-width="2"/>
          <polygon points="22,18 22,46 48,32" fill="#34d399"/>
          <text x="32" y="58" text-anchor="middle" font-size="8" fill="#34d399" font-family="Segoe UI,sans-serif">?ш컻</text>
        </svg>
      </div>
      <!-- ?뚯빱 以묐떒: ?ㅽ뻾 以묒씪 ?뚮쭔 ?쒖꽦 -->
      <div class="ctrl-svg-btn" onclick="{("ctrl('stop')" if running > 0 else "")}" title="?뚯빱 以묐떒" style="opacity:{('1' if running > 0 else '0.25')};cursor:{('pointer' if running > 0 else 'default')}">
        <svg width="64" height="64" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="30" fill="rgba(249,115,22,.1)" stroke="#f97316" stroke-width="2"/>
          <rect x="18" y="18" width="28" height="28" rx="4" fill="#f97316"/>
          <text x="32" y="58" text-anchor="middle" font-size="8" fill="#f97316" font-family="Segoe UI,sans-serif">?뚯빱 以묐떒</text>
        </svg>
      </div>
      <!-- ?먭꺽?쒖뼱 -->
      <a href="/remote/{pc_id}" title="?먭꺽 ?쒖뼱 (?붾㈃+留덉슦???ㅻ낫??" style="text-decoration:none">
      <div class="ctrl-svg-btn">
        <svg width="64" height="64" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="30" fill="rgba(167,139,250,.1)" stroke="#a78bfa" stroke-width="2"/>
          <rect x="14" y="18" width="36" height="22" rx="3" fill="none" stroke="#a78bfa" stroke-width="2"/>
          <circle cx="32" cy="29" r="5" fill="none" stroke="#a78bfa" stroke-width="1.5"/>
          <line x1="22" y1="40" x2="22" y2="46" stroke="#a78bfa" stroke-width="2"/>
          <line x1="42" y1="40" x2="42" y2="46" stroke="#a78bfa" stroke-width="2"/>
          <line x1="18" y1="46" x2="46" y2="46" stroke="#a78bfa" stroke-width="2"/>
          <text x="32" y="58" text-anchor="middle" font-size="8" fill="#a78bfa" font-family="Segoe UI,sans-serif">?먭꺽?쒖뼱</text>
        </svg>
      </div>
      </a>
      <!-- ?덈줈怨좎묠: ??긽 ?쒖꽦 -->
      <div class="ctrl-svg-btn" onclick="location.reload()" title="?덈줈怨좎묠">
        <svg width="64" height="64" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="30" fill="rgba(79,142,247,.1)" stroke="#4f8ef7" stroke-width="2"/>
          <path d="M20 32 A12 12 0 1 1 32 44" fill="none" stroke="#4f8ef7" stroke-width="3" stroke-linecap="round"/>
          <polygon points="18,28 20,36 26,30" fill="#4f8ef7"/>
          <text x="32" y="58" text-anchor="middle" font-size="8" fill="#4f8ef7" font-family="Segoe UI,sans-serif">?덈줈怨좎묠</text>
        </svg>
      </div>
      <div id="ctrl-msg" class="send-msg" style="font-size:12px;color:var(--muted)"></div>
    </div>
    <div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:12px">
      <div class="stat-card" style="min-width:0;padding:12px 18px;flex:none">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--green)"></div>
        <div class="stat-label">?ㅽ뻾 以?/div><div class="stat-value" style="color:var(--green);font-size:24px">{running}</div>
      </div>
      <div class="stat-card" style="min-width:0;padding:12px 18px;flex:none">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--yellow)"></div>
        <div class="stat-label">?湲?/div><div class="stat-value" style="color:var(--yellow);font-size:24px">{pending}</div>
      </div>
      <div class="stat-card" style="min-width:0;padding:12px 18px;flex:none">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--purple)"></div>
        <div class="stat-label">Claude ?ㅺ퀎</div><div class="stat-value" style="color:var(--purple);font-size:24px">{r_cl}</div>
      </div>
      <div class="stat-card" style="min-width:0;padding:12px 18px;flex:none">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--orange)"></div>
        <div class="stat-label">Codex 援ы쁽</div><div class="stat-value" style="color:var(--orange);font-size:24px">{r_c}</div>
      </div>
      <div class="stat-card" style="min-width:0;padding:12px 18px;flex:none">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--blue)"></div>
        <div class="stat-label">Gemini 寃利?/div><div class="stat-value" style="color:var(--blue);font-size:24px">{r_g}</div>
      </div>
    </div>
  </div>
</div>

{charts}

<!-- ?꾨줈?앺듃蹂??꾪솴 -->
{proj_section}

<!-- ?먭꺽 ?쒖뒪??吏??(?꾨줈?앺듃蹂? -->
<div class="task-form">
  <div class="task-form-title">
    <svg width="18" height="18" viewBox="0 0 18 18"><circle cx="9" cy="9" r="8" fill="none" stroke="#4f8ef7" stroke-width="1.5"/><line x1="9" y1="5" x2="9" y2="9" stroke="#4f8ef7" stroke-width="1.5" stroke-linecap="round"/><circle cx="9" cy="12" r="1" fill="#4f8ef7"/></svg>
    ?먭꺽 ?쒖뒪??吏?????꾨줈?앺듃瑜??좏깮?댁꽌 ?꾩넚
  </div>
  <div style="display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap">
    <select id="task-project" style="background:var(--bg3);border:1px solid var(--blue);color:var(--text);padding:10px 14px;border-radius:10px;font-size:13px;outline:none;font-weight:600;flex:1;min-width:200px">
      {project_options}
    </select>
    <select id="task-ai" style="background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:10px 14px;border-radius:10px;font-size:12px;outline:none">
      <option value="any">?쨼 ?먮룞 ?뚯빱</option>
      <option value="claude">?쭬 Claude ?ㅺ퀎</option>
      <option value="codex">??Codex 援ы쁽</option>
      <option value="gemini">?뵇 Gemini 寃利?/option>
    </select>
  </div>
  <textarea id="task-content" class="task-input" placeholder="?쒖뒪??吏?쒖꽌瑜??낅젰?섏꽭??

?덉떆)
## 紐⑺몴
濡쒓렇???섏씠吏 UI 媛쒖꽑

## ?곸꽭
1. 踰꾪듉 ?됱긽???뚮??됱쑝濡?蹂寃?
2. ?먮윭 硫붿떆吏 ?쒓???
3. 諛섏쓳???덉씠?꾩썐 ?곸슜

## ?뚯씪 ?꾩튂
src/views/Login.vue"></textarea>
  <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-top:12px">
    <div class="ctrl-svg-btn" onclick="sendTask()" title="?꾩넚">
      <svg width="72" height="64" viewBox="0 0 72 64">
        <rect x="2" y="2" width="68" height="48" rx="12" fill="rgba(79,142,247,.12)" stroke="#4f8ef7" stroke-width="2"/>
        <polygon points="14,32 36,14 58,32" fill="none" stroke="#4f8ef7" stroke-width="2.5" stroke-linejoin="round"/>
        <line x1="36" y1="14" x2="36" y2="42" stroke="#4f8ef7" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="24" y1="42" x2="48" y2="42" stroke="#22d3ee" stroke-width="2" stroke-linecap="round"/>
        <text x="36" y="60" text-anchor="middle" font-size="9" fill="#4f8ef7" font-family="Segoe UI,sans-serif" font-weight="700">?꾩넚</text>
      </svg>
    </div>
    <div style="font-size:12px;color:var(--muted);line-height:1.6">
      ?좏깮???꾨줈?앺듃??<code style="color:var(--cyan)">.claude/tasks/</code> ?????br>
      ?ㅼ쓬 1遺?二쇨린???대떦 PC ?뚯빱媛 ?먮룞 ?ㅽ뻾?⑸땲??
    </div>
  </div>
  <div id="send-msg" class="send-msg"></div>
</div>

<!-- ?湲?以묒씤 ?먭꺽 吏??-->
<div class="section-title">?벉 ?꾩넚??吏???湲곗뿴</div>
<div style="margin-bottom:24px">{inc_html}</div>

<!-- ?묒뾽 ?댁슜 ?붿빟 ??-->
<div class="section-title">?묒뾽 ?댁슜 ?붿빟</div>
<div class="tab-bar">
  <button class="tab-btn active" onclick="showTab('task',this)">?쭬 Claude ?ㅺ퀎</button>
  <button class="tab-btn" onclick="showTab('impl',this)">??Codex 援ы쁽</button>
  <button class="tab-btn" onclick="showTab('review',this)">?뵇 Gemini 寃利?/button>
  <button class="tab-btn" onclick="showTab('tasks',this)"> ?쒖뒪??紐⑸줉</button>
  <button class="tab-btn" onclick="showTab('hist',this)">?븧 ?대젰</button>
</div>
<div id="tab-task"   class="tab-pane active"><pre class="summary-box">{task_sum}</pre></div>
<div id="tab-impl"   class="tab-pane"><pre class="summary-box">{impl_sum}</pre></div>
<div id="tab-review" class="tab-pane"><pre class="summary-box">{review_sum}</pre></div>
<div id="tab-tasks"  class="tab-pane">
  <div class="section-title">?ㅽ뻾 以?/div>
  <table><tr><th>?쒖뒪??/th><th>AI</th><th>?뚯빱</th></tr>{run_rows}</table>
  <div class="section-title">?湲?/div><div style="margin-bottom:16px">{pend_chips}</div>
  <div class="section-title">?꾨즺 (理쒓렐 10媛?</div><div>{done_chips}</div>
</div>
<div id="tab-hist"   class="tab-pane">
  <table><tr><th>?쒓컖 (UTC)</th><th>而ㅻ컠</th></tr>{hist_rows}</table>
</div>

"""

    if body_only: return body
    ajax_poll = """<script>
var PC_ID = '{pid}';
function showTab(name,btn) {{
  document.querySelectorAll('.tab-pane').forEach(function(e){{e.classList.remove('active')}});
  document.querySelectorAll('.tab-btn').forEach(function(e){{e.classList.remove('active')}});
  document.getElementById('tab-'+name).classList.add('active');
  btn.classList.add('active');
  location.hash = name;
}}
(function(){{
  var h = location.hash.replace('#','');
  var pane = h && document.getElementById('tab-'+h);
  if (pane) {{
    document.querySelectorAll('.tab-pane').forEach(function(e){{e.classList.remove('active')}});
    document.querySelectorAll('.tab-btn').forEach(function(e){{e.classList.remove('active')}});
    pane.classList.add('active');
    var btn = document.querySelector('.tab-btn[onclick*="\\''+h+'\\'"]');
    if (btn) btn.classList.add('active');
  }}
}})();
function ctrl(action) {{
  document.getElementById('ctrl-msg').textContent = action + ' 紐낅졊 ?꾩넚 以?..';
  fetch('/control/'+PC_ID+'/'+action).then(function(r){{return r.text();}}).then(function(t){{
    document.getElementById('ctrl-msg').textContent = t==='OK' ? '???꾩넚 ?꾨즺 (?ㅼ쓬 二쇨린 ?곸슜)' : '???꾩넚 ?ㅽ뙣';
  }});
}}
function sendTask() {{
  var content = document.getElementById('task-content').value.trim();
  var ai = document.getElementById('task-ai').value;
  if (!content) {{ alert('?댁슜???낅젰?섏꽭??); return; }}
  document.getElementById('send-msg').textContent = '?꾩넚 以?..';
  fetch('/send-task', {{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify({{pc_id: PC_ID, content: content, ai: ai, project: document.getElementById('task-project').value}})
  }}).then(function(r){{return r.json();}}).then(function(d){{
    if (d.ok) {{
      var proj = d.project ? ' ??[' + d.project + ']' : '';
      document.getElementById('send-msg').textContent = '???꾩넚 ?꾨즺 ??' + d.filename + proj + ' (?ㅼ쓬 二쇨린??PC?먯꽌 ?먮룞 ?ㅽ뻾)';
      document.getElementById('task-content').value = '';
    }} else {{
      document.getElementById('send-msg').textContent = '???ㅽ뙣: ' + d.error;
    }}
  }});
}}
function delTask(pcId, filename, sha) {{
  if (!confirm(filename + ' 痍⑥냼?섏떆寃좎뼱??')) return;
  fetch('/del-task', {{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify({{pc_id: pcId, filename: filename, sha: sha}})
  }}).then(function(r){{return r.json();}}).then(function(d){{ if(d.ok) location.reload(); }});
}}
setInterval(function(){{
  // textarea???ъ빱??以묒씠硫?媛깆떊 ?ㅽ궢 (?낅젰 ?댁슜 蹂댄샇)
  var active = document.activeElement;
  if (active && (active.tagName==='TEXTAREA' || active.tagName==='INPUT' || active.tagName==='SELECT')) return;
  fetch('/api/detail-body/{pid}{proj_qs}').then(function(r){{return r.text();}}).then(function(html){{
    var c=document.getElementById('main-container');
    if(c) {{
      // ?꾩옱 ???곹깭 蹂댁〈
      var activeTab = '';
      var at = document.querySelector('.tab-btn.active');
      if (at && at.getAttribute('onclick')) {{
        var m = at.getAttribute('onclick').match(/'([^']+)'/);
        if (m) activeTab = m[1];
      }}
      c.innerHTML=html;
      // ??蹂듭썝
      if (activeTab) {{
        var pane = document.getElementById('tab-'+activeTab);
        if (pane) {{
          document.querySelectorAll('.tab-pane').forEach(function(e){{e.classList.remove('active')}});
          document.querySelectorAll('.tab-btn').forEach(function(e){{e.classList.remove('active')}});
          pane.classList.add('active');
          var btn = document.querySelector('.tab-btn[onclick*="\\''+activeTab+'\\'"]');
          if (btn) btn.classList.add('active');
        }}
      }}
      // Chart.js ?ъ큹湲고솕
      if (typeof Chart !== 'undefined') {{
        var scripts = c.querySelectorAll('script');
        scripts.forEach(function(s){{ try {{ eval(s.textContent); }} catch(e){{}} }});
      }}
    }}
  }}).catch(function(){{}});
}}, 5000);
</script>""".format(pid=urllib.parse.quote(pc_id), proj_qs=("?project=" + urllib.parse.quote(project)) if project else "")
    return BASE.format(title=f"{pc} ?먭꺽?쒖뼱",css=CSS,body=body,ajax_poll=ajax_poll)


# ?? HTTP ?몃뱾?????????????????????????????????????????????????
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send_html(self, html):
        try:
            d=html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(d)))
            self.end_headers()
            self.wfile.write(d)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def send_json(self, obj):
        try:
            d=json.dumps(obj).encode()
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Content-Length",str(len(d)))
            self.end_headers()
            self.wfile.write(d)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def read_body(self):
        l=int(self.headers.get("Content-Length",0))
        if not l:
            return {}
        raw=self.rfile.read(l)
        try:
            txt=raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            txt=raw.decode("utf-8", errors="replace")
        if not txt.strip():
            return {}
        try:
            return json.loads(txt)
        except (json.JSONDecodeError, ValueError):
            return {}

    def send_html_fragment(self, html):
        """HTML fragment 諛섑솚 (AJAX body 媛깆떊??"""
        try:
            d=html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Cache-Control","no-cache")
            self.send_header("Content-Length",str(len(d)))
            self.end_headers()
            self.wfile.write(d)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def do_GET(self):
        path=urllib.parse.unquote(self.path)
        # AJAX body 媛깆떊 ?붾뱶?ъ씤????GitHub API ????
        if path=="/api/index-body":
            ss,err=fetch_all()
            self.send_html_fragment(make_index(ss,err,body_only=True))
            return
        if path.startswith("/api/detail-body/"):
            raw_detail=path[17:].strip("/")
            pc_id=raw_detail.split("?")[0]
            qs_detail=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            proj_filter_detail=qs_detail.get("project",[""])[0]
            ss,_=fetch_all()
            s=next((x for x in ss if x.get("pc_id")==pc_id or x.get("pc")==pc_id),None)
            if s:
                self.send_html_fragment(make_detail(s,body_only=True,project=proj_filter_detail))
            else:
                self.send_html_fragment('<a href="/">???ㅻ줈</a><h2 style="color:#f87171;padding:20px">PC ?놁쓬</h2>')
            return
        if path=="/tunnel-url":
            self.send_json({"url": _tunnel_url})
            return
        if path=="/health":
            self.send_json({"ok":True,"tunnel": _tunnel_url})
            return
        if path=="/api/metrics":
            try:
                qs=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                hours=int(qs.get("hours",["24"])[0])
                sys.path.insert(0,str(Path(__file__).parent/".claude"/"scripts"/"lib"))
                from state_db import get_metrics_summary
                summary=get_metrics_summary(hours=hours)
                self.send_json(summary)
            except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
                self.send_json({"error":str(e)})
            return
        if path.startswith("/control/"):
            parts=path[9:].split("/")
            if len(parts)==2:
                pc_id,action=parts
                with _store_lock:
                    _ctrl_store[pc_id]={"action":action,"requested_at":ts_now()}
                self.send_response(200); self.send_header("Content-Type","text/plain"); self.end_headers()
                self.wfile.write(b"OK")
            return
        if path.startswith("/remote/"):
            pc_id = path[8:].strip("/").split("?")[0]
            self.send_html(make_remote(pc_id))
            return
        if path.startswith("/remote-status/"):
            pc_id = path[15:].strip("/").split("?")[0]
            # 濡쒖뺄 硫붾え由??곗꽑, ?놁쑝硫?_screen_store/_gh_cache?먯꽌 議댁옱 ?щ? ?뺤씤
            with _store_lock:
                local = _remote_status.get(pc_id)
                has_screen = pc_id in _screen_store
            if local:
                self.send_json(local)
            elif has_screen or pc_id in _gh_cache:
                # ?ㅽ겕由??곹깭 ?곗씠?곕뒗 ?덉?留?remote_status 誘몃벑濡???湲곕낯 1紐⑤땲?곕줈 ?묐떟
                self.send_json({"pc_id": pc_id, "state": "ready", "count": 1, "screens": []})
            else:
                self.send_json({"count":1, "state": "unknown"})
            return
        if path.startswith("/pull-cmd/"):
            pc_id = path[10:].strip("/").split("?")[0]
            with _store_lock:
                cmd = _cmd_store.pop(pc_id, None)
            self.send_json(cmd if cmd else {})
            return
        if path.startswith("/remote-screen/"):
            rest = path[15:].strip("/").split("?")[0]
            parts = rest.split("/")
            pc_id = parts[0]
            monitor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            # 濡쒖뺄 硫붾え由??곗꽑
            img = None
            with _store_lock:
                screens = _screen_store.get(pc_id, {})
                img = screens.get(monitor) or screens.get(0)
            # 濡쒖뺄 ?ㅽ넗?댁뿉 ?놁쑝硫?404 ??GitHub fallback ?놁쓬 (rate limit 諛⑹?)
            if img:
                self.send_response(200)
                self.send_header("Content-Type","image/jpeg")
                self.send_header("Content-Length",str(len(img)))
                self.send_header("Cache-Control","no-cache")
                self.end_headers()
                try: self.wfile.write(img)
                except: pass
            else:
                self.send_response(404); self.end_headers()
            return
        if path.startswith("/del-pc/"):
            pc_id = path[8:].strip("/")
            # 硫붾え由ъ뿉??利됱떆 ?쒓굅 + ?щ벑濡?李⑤떒
            with _store_lock:
                _status_store.pop(pc_id, None)
                _gh_cache.pop(pc_id, None)
                _deleted_pcs.add(pc_id)
            # GitHub?먯꽌????젣 (git push) ??PAT ?놁쑝硫??ㅽ궢
            def _del_from_gh():
                import tempfile, shutil
                pat = get_pat()
                if not pat:
                    return
                repo_url = f"https://x:{pat}@github.com/{OWNER}/{REPO}.git"
                tmpdir = tempfile.mkdtemp(prefix="gh-del-")
                try:
                    subprocess.run(["git","clone","--depth","1",repo_url,tmpdir],
                        capture_output=True, timeout=30, check=True)
                    target = os.path.join(tmpdir, "status", f"{pc_id}.json")
                    if os.path.isfile(target):
                        os.remove(target)
                        subprocess.run(["git","-C",tmpdir,"add","-A"], capture_output=True, timeout=10, check=True)
                        subprocess.run(["git","-C",tmpdir,"-c","user.name=dashboard","-c","user.email=auto@bot",
                            "commit","-m",f"remove: {pc_id}"], capture_output=True, timeout=10, check=True)
                        subprocess.run(["git","-C",tmpdir,"push"], capture_output=True, timeout=30, check=True)
                except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
                    print(f"[WARN] GitHub delete failed: {_mask_pat(e)}")
                finally:
                    shutil.rmtree(tmpdir, ignore_errors=True)
            threading.Thread(target=_del_from_gh, daemon=True).start()
            self.send_response(200); self.send_header("Content-Type","text/plain"); self.end_headers()
            try: self.wfile.write(b"OK")
            except: pass
            return
        if path.startswith("/rdp/"):
            pc_id = path[5:].strip("/")
            ss,_ = fetch_all()
            s = next((x for x in ss if x.get("pc_id")==pc_id),None)
            ip = s.get("ip","") if s else ""
            pc = s.get("pc", pc_id) if s else pc_id
            if ip:
                rdp = f"full address:s:{ip}\nusername:s:{pc}\nprompt for credentials:i:1\nauthentication level:i:2\n"
                d = rdp.encode()
                self.send_response(200)
                self.send_header("Content-Type","application/rdp")
                self.send_header("Content-Disposition",f'attachment; filename="{pc_id}.rdp"')
                self.send_header("Content-Length",str(len(d)))
                self.end_headers()
                try: self.wfile.write(d)
                except: pass
            else:
                self.send_response(404); self.end_headers()
                try: self.wfile.write(b"IP not available")
                except: pass
            return
        if path.startswith("/pc/"):
            raw=path[4:].strip("/")
            pc_id=raw.split("?")[0]
            qs=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            proj_filter=qs.get("project",[""])[0]
            ss,_=fetch_all()
            s=next((x for x in ss if x.get("pc_id")==pc_id or x.get("pc")==pc_id),None)
            self.send_html(make_detail(s,project=proj_filter) if s else '<a href="/">???ㅻ줈</a><h2 style="color:#f87171;padding:20px">PC ?놁쓬</h2>')
        else:
            ss,err=fetch_all()
            self.send_html(make_index(ss,err))

    def do_POST(self):
        path=urllib.parse.unquote(self.path)

        # push-screen? 諛붿씠?덈━ ??read_body()濡?JSON ?뚯떛?섎㈃ ????
        if path=="/push-screen":
            try:
                l = int(self.headers.get("Content-Length",0))
                img_data = self.rfile.read(l) if l else b""
                pc_id = self.headers.get("X-PC-ID","")
                monitor = int(self.headers.get("X-Monitor","0"))
                if not pc_id or not img_data:
                    self.send_response(400); self.end_headers(); return
                with _store_lock:
                    if pc_id not in _screen_store: _screen_store[pc_id] = {}
                    _screen_store[pc_id][monitor] = img_data
                self.send_response(200); self.end_headers()
                try: self.wfile.write(b"OK")
                except: pass
            except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
                self.send_response(500); self.end_headers()
            return

        data=self.read_body()

        if path=="/push":
            try:
                pc_id = data.get("pc_id","")
                if not pc_id:
                    self.send_json({"ok":False,"error":"pc_id required"}); return
                with _store_lock:
                    if pc_id in _deleted_pcs:
                        self.send_json({"ok":True}); return  # ??젣??PC ?щ벑濡?李⑤떒
                    _status_store[pc_id] = data
                self.send_json({"ok":True})
            except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
                self.send_json({"ok":False,"error":_mask_pat(e)})
            return

        if path=="/tunnel-url":
            self.send_json({"url": _tunnel_url})
            return

        if path=="/push-remote-status":
            try:
                pc_id = data.get("pc_id","")
                if pc_id:
                    with _store_lock:
                        _remote_status[pc_id] = data
                self.send_json({"ok":True})
            except:
                self.send_json({"ok":False})
            return

        # read_body already consumed, re-parse for remaining routes
        if path.startswith("/remote-cmd/"):
            pc_id = path[12:].strip("/")
            try:
                cmd = data
                with _store_lock:
                    _cmd_store[pc_id] = cmd
                # ?곕꼸 ?곌껐 ????PC硫?git?쇰줈 紐낅졊 ?꾨떖
                with _store_lock:
                    is_local = pc_id in _remote_status or pc_id == _local_pc_id()
                if not is_local:
                    def _push_cmd_git():
                        import tempfile, shutil
                        pat = get_pat()
                        if not pat:
                            return
                        repo_url = f"https://x:{pat}@github.com/{OWNER}/{REPO}.git"
                        tmpdir = tempfile.mkdtemp(prefix="gh-cmd-")
                        try:
                            subprocess.run(["git","clone","--depth","1",repo_url,tmpdir],
                                capture_output=True, timeout=30, check=True)
                            cmd_dir = os.path.join(tmpdir, "remote", pc_id)
                            os.makedirs(cmd_dir, exist_ok=True)
                            with open(os.path.join(cmd_dir, "cmd.json"), "w", encoding="utf-8") as f:
                                json.dump(cmd, f)
                            subprocess.run(["git","-C",tmpdir,"add","-A"], capture_output=True, timeout=10, check=True)
                            subprocess.run(["git","-C",tmpdir,"-c","user.name=dashboard","-c","user.email=auto@bot",
                                "commit","-m",f"cmd: {pc_id}"], capture_output=True, timeout=10, check=True)
                            subprocess.run(["git","-C",tmpdir,"push"], capture_output=True, timeout=30, check=True)
                        except: pass
                        finally:
                            shutil.rmtree(tmpdir, ignore_errors=True)
                    threading.Thread(target=_push_cmd_git, daemon=True).start()
                self.send_json({"ok":True})
            except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
                self.send_json({"ok":False,"error":_mask_pat(e)})
            return
        if path=="/send-task":
            try:
                pc_id=data["pc_id"]; content=data["content"]; ai=data.get("ai","any")
                project_path=data.get("project","")
                import os as _os
                project_name=_os.path.basename(project_path.rstrip("/\\")) if project_path else ""
                fname=f"task-{ts_file()}.md"
                meta_parts=[f"ai:{ai}" if ai!="any" else ""]
                if project_name: meta_parts.append(f"project:{project_name}")
                meta_parts=[x for x in meta_parts if x]
                header=f"<!-- {' '.join(meta_parts)} -->\n" if meta_parts else ""
                payload=(header+content)
                # 硫붾え由ъ뿉 ???(GitHub 遺덊븘??
                with _store_lock:
                    if pc_id not in _incoming_store: _incoming_store[pc_id]=[]
                    _incoming_store[pc_id].append({"filename":fname,"content":payload})
                self.send_json({"ok":True,"filename":fname,"project":project_name or pc_id})
            except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
                self.send_json({"ok":False,"error":_mask_pat(e)})

        elif path=="/del-task":
            try:
                pc_id=data["pc_id"]; fname=data["filename"]
                with _store_lock:
                    if pc_id in _incoming_store:
                        _incoming_store[pc_id]=[t for t in _incoming_store[pc_id] if t["filename"]!=fname]
                self.send_json({"ok":True})
            except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
                self.send_json({"ok":False,"error":_mask_pat(e)})

        elif path=="/incoming-recv":
            # ?대씪?댁뼵??PC媛 ?湲?以묒씤 ?쒖뒪???섏떊
            try:
                pc_id=data.get("pc_id","")
                with _store_lock:
                    tasks=list(_incoming_store.get(pc_id,[]))
                self.send_json({"ok":True,"tasks":tasks})
            except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
                self.send_json({"ok":False,"error":_mask_pat(e)})

        elif path=="/incoming-ack":
            # ?대씪?댁뼵??PC媛 ?쒖뒪???섏떊 ?꾨즺 ?뚮┝
            try:
                pc_id=data.get("pc_id",""); fname=data.get("filename","")
                with _store_lock:
                    if pc_id in _incoming_store:
                        _incoming_store[pc_id]=[t for t in _incoming_store[pc_id] if t["filename"]!=fname]
                self.send_json({"ok":True})
            except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
                self.send_json({"ok":False,"error":_mask_pat(e)})

        elif path=="/control-recv":
            # ?대씪?댁뼵??PC媛 而⑦듃濡?紐낅졊 ?섏떊
            try:
                pc_id=data.get("pc_id","")
                with _store_lock:
                    ctrl=_ctrl_store.pop(pc_id,None)
                self.send_json({"ok":True,"action":ctrl.get("action") if ctrl else None})
            except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
                self.send_json({"ok":False,"error":_mask_pat(e)})

        else:
            self.send_json({"ok":False,"error":"unknown endpoint"})


def find_cloudflared():
    """cloudflared ?ㅽ뻾?뚯씪 李얘린 (PATH + ?꾨줈?앺듃 ?대뜑 + WinGet 寃쎈줈)"""
    import shutil
    p = shutil.which("cloudflared")
    if p: return p
    # ?꾨줈?앺듃 ?대뜑 (dashboard.py ? 媛숈? ?꾩튂)
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloudflared.exe")
    if os.path.isfile(local): return local
    # WinGet ?ㅼ튂 寃쎈줈 ?먯깋
    winget_base = os.path.join(os.environ.get("LOCALAPPDATA",""), "Microsoft", "WinGet")
    for d in ["Links", "Packages"]:
        candidate = os.path.join(winget_base, d)
        if os.path.isdir(candidate):
            for root, dirs, files in os.walk(candidate):
                if "cloudflared.exe" in files:
                    return os.path.join(root, "cloudflared.exe")
    return None

def start_tunnel():
    """cloudflared tunnel ?쒖옉 + URL??GitHub?????""
    global _tunnel_url
    cf = find_cloudflared()
    if not cf:
        print("[WARN] cloudflared 誘몄꽕移???濡쒖뺄 ?ㅽ듃?뚰겕 ?꾩슜 紐⑤뱶")
        print(f"       ?ㅼ튂: winget install Cloudflare.cloudflared")
        return
    try:
        proc = subprocess.Popen(
            [cf,"tunnel","--url",f"http://localhost:{PORT}"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            encoding='utf-8', errors='replace')
        import re
        for line in proc.stdout:
            m = re.search(r'(https://[a-z0-9\-]+\.trycloudflare\.com)', line)
            if m:
                _tunnel_url = m.group(1)
                print(f"[OK] Tunnel ??{_tunnel_url}")
                # GitHub??URL ?????PC蹂??뚯씪 (??쒕낫???щ윭 ? 吏??
                _save_tunnel_url_to_gh()
                break
    except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
        print(f"[WARN] Tunnel ?쒖옉 ?ㅽ뙣: {_mask_pat(e)}")

_tunnel_url_saved = False  # GitHub??URL ????깃났 ?щ?

def _ensure_git():
    """git ?놁쑝硫?winget?쇰줈 ?먮룞 ?ㅼ튂"""
    try:
        subprocess.run(["git","--version"], capture_output=True, timeout=5, check=True)
        return
    except:
        print("[+] git 誘몄꽕移????먮룞 ?ㅼ튂 以?..")
        try:
            subprocess.run(["winget","install","--id","Git.Git","-e","--accept-package-agreements","--accept-source-agreements"],
                capture_output=True, timeout=300)
            # PATH 諛섏쁺???꾪빐 ?섍꼍蹂???덈줈 濡쒕뱶
            git_paths = [r"C:\Program Files\Git\cmd", r"C:\Program Files (x86)\Git\cmd"]
            for p in git_paths:
                if os.path.isdir(p) and p not in os.environ.get("PATH",""):
                    os.environ["PATH"] = p + ";" + os.environ["PATH"]
            subprocess.run(["git","--version"], capture_output=True, timeout=5, check=True)
            print("[OK] git ?ㅼ튂 ?꾨즺")
        except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
            print(f"[WARN] git ?먮룞 ?ㅼ튂 ?ㅽ뙣: {_mask_pat(e)}")
            raise

def _save_tunnel_url_to_gh():
    """?곕꼸 URL??git push濡?GitHub?????(API rate limit 臾닿?)."""
    global _tunnel_url_saved
    if not _tunnel_url:
        return
    import tempfile, shutil
    def _try_save():
        global _tunnel_url_saved
        _ensure_git()
        pc_id = _local_pc_id()
        pat = get_pat()
        if not pat:
            print("[WARN] PAT not set ??GitHub URL ????ㅽ궢")
            return
        repo_url = f"https://x:{pat}@github.com/{OWNER}/{REPO}.git"
        tmpdir = tempfile.mkdtemp(prefix="gh-url-")
        try:
            subprocess.run(["git","clone","--depth","1",repo_url,tmpdir],
                capture_output=True, timeout=30, check=True)
            fname = f"dashboard-url-{pc_id}.json"
            with open(os.path.join(tmpdir, fname), "w", encoding="utf-8") as f:
                json.dump({"url":_tunnel_url,"pc":pc_id,"updated_at":ts_now()}, f)
            subprocess.run(["git","-C",tmpdir,"add",fname], capture_output=True, timeout=10, check=True)
            diff = subprocess.run(["git","-C",tmpdir,"diff","--cached","--quiet"], capture_output=True, timeout=10)
            if diff.returncode == 0:
                _tunnel_url_saved = True
                print(f"[OK] GitHub URL ?대? 理쒖떊 ({fname})")
                return
            subprocess.run(["git","-C",tmpdir,"-c","user.name=dashboard","-c","user.email=auto@bot",
                "commit","-m",f"dashboard-url: {pc_id}"], capture_output=True, timeout=10, check=True)
            subprocess.run(["git","-C",tmpdir,"push"], capture_output=True, timeout=30, check=True)
            _tunnel_url_saved = True
            print(f"[OK] GitHub??URL ????꾨즺 ({fname})")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    try:
        _try_save()
    except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
        print(f"[WARN] GitHub URL ????ㅽ뙣: {_mask_pat(e)} ??30珥????ъ떆??)
        def _retry_loop():
            for i in range(120):
                time.sleep(30)
                if _tunnel_url_saved:
                    return
                try:
                    _try_save()
                    return
                except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError) as ex:
                    if i % 10 == 9:
                        print(f"[WARN] GitHub URL ????ъ떆??以?.. ({i+1}?? {_mask_pat(ex)})")
            print("[WARN] GitHub URL ????ъ떆???ш린 (60遺?珥덇낵)")
        threading.Thread(target=_retry_loop, daemon=True).start()

# ?? 濡쒖뺄 PC ID ?앹꽦 ??
def _local_pc_id():
    pc = os.environ.get("COMPUTERNAME", socket.gethostname())
    try:
        result = subprocess.check_output(
            ["powershell", "-Command",
             "(Get-NetAdapter|Where-Object{$_.MacAddress}|Sort-Object InterfaceIndex|Select-Object -First 1).MacAddress -replace '-',''"],
            text=True, encoding='utf-8', errors='replace', timeout=5).strip()
        mac6 = result[:6] if result else "000000"
    except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError):
        mac6 = uuid.getnode().__format__("012x")[:6].upper()
    return f"{pc}-{mac6}"

def _local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError):
        return ""

# ?? 濡쒖뺄 Status ?섏쭛 (status-push ?泥? ??
def _collect_local_status(pc_id):
    config = os.path.join(os.environ.get("USERPROFILE",""), ".claude", "status-projects.txt")
    if not os.path.exists(config):
        return None
    with open(config, encoding="utf-8") as f:
        dirs = [l.strip() for l in f if l.strip()]

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pending=0; run_codex=0; run_gemini=0; run_claude=0; done=0
    projects=""; pending_list=[]; running_list=[]; done_list=[]
    task_summary=""; impl_summary=""; review_summary=""
    recent_report=""; project_details=[]

    for pdir in dirs:
        claude_dir = os.path.join(pdir, ".claude")
        if not os.path.isdir(claude_dir):
            continue
        pname = os.path.basename(pdir.rstrip("/\\"))
        projects += pname + " "
        p_pend=0; p_run_codex=0; p_run_gemini=0; p_run_claude=0; p_done=0
        p_pend_list=[]; p_run_list=[]; p_done_list=[]

        tasks_dir = os.path.join(claude_dir, "tasks")
        done_dir = os.path.join(tasks_dir, "done")
        locks_dir = os.path.join(tasks_dir, "locks")

        # Pending tasks
        for tf in globmod.glob(os.path.join(tasks_dir, "task-*.md")):
            bn = os.path.basename(tf)
            if os.path.exists(os.path.join(done_dir, bn)):
                continue
            try:
                with open(tf, encoding="utf-8", errors="replace") as fh:
                    content = fh.read(2000)
                if "[Task Title]" in content or "[What to build" in content:
                    continue
            except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError):
                continue
            pending += 1; p_pend += 1
            name = os.path.splitext(bn)[0]
            pending_list.append(name); p_pend_list.append(name)
            if not task_summary:
                task_summary = content[:500]

        ti = os.path.join(tasks_dir, "task-instruction.md")
        ti_lock = os.path.join(locks_dir, "task-instruction.lock")
        if os.path.exists(ti) and not os.path.exists(ti_lock):
            try:
                with open(ti, encoding="utf-8", errors="replace") as fh:
                    tic = fh.read(2000)
                if "[Task Title]" not in tic and "[What to build" not in tic:
                    pending += 1; p_pend += 1
                    pending_list.append("task-instruction"); p_pend_list.append("task-instruction")
                    if not task_summary:
                        task_summary = tic[:500]
            except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError):
                pass

        # Running (locks)
        if os.path.isdir(locks_dir):
            for lk in globmod.glob(os.path.join(locks_dir, "*.lock")):
                lname = os.path.splitext(os.path.basename(lk))[0]
                try:
                    with open(lk, encoding="utf-8", errors="replace") as fh:
                        lcontent = fh.readline().strip()
                except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError):
                    lcontent = ""
                if lname.startswith("verify-"):
                    run_gemini += 1; p_run_gemini += 1; ai = "gemini"
                elif "claude-worker-" in lcontent:
                    run_claude += 1; p_run_claude += 1; ai = "claude"
                elif "worker-" in lcontent:
                    run_codex += 1; p_run_codex += 1; ai = "codex"
                else:
                    run_claude += 1; p_run_claude += 1; ai = "claude"
                entry = {"task": lname, "worker": lcontent, "ai": ai, "project": pname}
                running_list.append(entry); p_run_list.append(entry)

        # Done
        if os.path.isdir(done_dir):
            done_files = sorted(globmod.glob(os.path.join(done_dir, "*.md")), key=os.path.getmtime, reverse=True)
            p_done = len(done_files); done += p_done
            p_done_list = [os.path.splitext(os.path.basename(f))[0] for f in done_files[:10]]
            done_list.extend(p_done_list)

        # Reports
        docs_dir = os.path.join(pdir, "docs")
        rpts = []
        p_impl_summary = ""
        p_review_summary = ""
        if os.path.isdir(docs_dir):
            rpts = sorted(globmod.glob(os.path.join(docs_dir, "report-*.md")), key=os.path.getmtime, reverse=True)
            p_report = os.path.basename(rpts[0]) if rpts else ""
            if p_report:
                recent_report = p_report
            impl_file = os.path.join(docs_dir, "implementation-report.md")
            review_file = os.path.join(docs_dir, "review-result.txt")
            if os.path.exists(impl_file):
                try:
                    with open(impl_file, encoding="utf-8", errors="replace") as fh:
                        p_impl_summary = "\n".join(fh.readlines()[:30])
                except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError):
                    pass
            if os.path.exists(review_file):
                try:
                    with open(review_file, encoding="utf-8", errors="replace") as fh:
                        p_review_summary = "\n".join(fh.readlines()[:30])
                except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError):
                    pass
        # ?꾩껜 ?붿빟? 泥?踰덉㎏濡?諛쒓껄??寃??좎?
        if not impl_summary and p_impl_summary:
            impl_summary = p_impl_summary
        if not review_summary and p_review_summary:
            review_summary = p_review_summary

        p_run_total = p_run_codex + p_run_gemini + p_run_claude
        project_details.append({
            "name": pname, "path": pdir, "pending": p_pend,
            "running": p_run_total, "running_codex": p_run_codex,
            "running_gemini": p_run_gemini, "running_claude": p_run_claude,
            "done": p_done, "recent_report": recent_report if rpts else "",
            "pending_tasks": p_pend_list,
            "running_tasks": p_run_list, "done_tasks": p_done_list,
            "impl_summary": p_impl_summary, "review_summary": p_review_summary
        })

    run_total = run_codex + run_gemini + run_claude
    return {
        "pc": os.environ.get("COMPUTERNAME", socket.gethostname()),
        "pc_id": pc_id, "mac": "", "updated_at": ts,
        "pending": pending, "running": run_total,
        "running_codex": run_codex, "running_gemini": run_gemini, "running_claude": run_claude,
        "done": done, "ip": _local_ip(), "projects": projects.strip(),
        "recent_report": recent_report,
        "pending_tasks": pending_list, "running_tasks": running_list, "done_tasks": done_list,
        "project_details": project_details,
        "task_summary": task_summary, "impl_summary": impl_summary, "review_summary": review_summary
    }

def _status_push_loop():
    pc_id = _local_pc_id()
    print(f"[+] Status push ?쒖옉 (pc: {pc_id}, 0.2珥?媛꾧꺽)")
    while True:
        try:
            data = _collect_local_status(pc_id)
            if data:
                with _store_lock:
                    if pc_id not in _deleted_pcs:
                        _status_store[pc_id] = data
        except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
            pass
        time.sleep(0.2)

# ?? 濡쒖뺄 Screen Capture (remote-agent ?泥? ??
def _capture_screen_pil(monitor_idx=0):
    """PIL 湲곕컲 ?ㅽ겕由?罹≪쿂 (mss ???"""
    try:
        import mss
        with mss.mss() as sct:
            monitors = sct.monitors[1:]  # 0 is virtual
            if monitor_idx >= len(monitors):
                return None, len(monitors)
            img = sct.grab(monitors[monitor_idx])
            from io import BytesIO
            import struct, zlib
            # raw BGRA -> JPEG via PIL or manual
            try:
                from PIL import Image
                pil_img = Image.frombytes("RGB", (img.width, img.height), img.rgb)
                buf = BytesIO()
                pil_img.save(buf, format="JPEG", quality=90)
                return buf.getvalue(), len(monitors)
            except ImportError:
                # mss built-in PNG (fallback, larger)
                return mss.tools.to_png(img.rgb, img.size), len(monitors)
    except ImportError:
        pass
    # PowerShell fallback
    try:
        ps = f'''
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$s=[System.Windows.Forms.Screen]::AllScreens[{monitor_idx}]
$b=$s.Bounds
$bmp=New-Object System.Drawing.Bitmap($b.Width,$b.Height)
$g=[System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.Left,$b.Top,0,0,(New-Object System.Drawing.Size($b.Width,$b.Height)))
$g.Dispose()
$codec=[System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders()|Where-Object{{$_.MimeType -eq 'image/jpeg'}}
$ep=New-Object System.Drawing.Imaging.EncoderParameters(1)
$ep.Param[0]=New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality,90L)
$ms=New-Object System.IO.MemoryStream
$bmp.Save($ms,$codec,$ep);$bmp.Dispose()
[Convert]::ToBase64String($ms.ToArray())
'''
        result = subprocess.check_output(["powershell", "-Command", ps], text=True, encoding='utf-8', errors='replace', timeout=10).strip()
        count_ps = subprocess.check_output(
            ["powershell", "-Command", "[System.Windows.Forms.Screen]::AllScreens.Count"],
            text=True, encoding='utf-8', errors='replace', timeout=5).strip()
        return base64.b64decode(result), int(count_ps)
    except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError):
        return None, 1

def _remote_agent_loop():
    pc_id = _local_pc_id()
    print(f"[+] Remote agent ?쒖옉 (pc: {pc_id}, 0.2珥?媛꾧꺽)")
    # 珥덇린 紐⑤땲???뺣낫
    _, count = _capture_screen_pil(0)
    screens_info = {"pc_id": pc_id, "state": "ready", "count": count, "screens": []}
    with _store_lock:
        _remote_status[pc_id] = screens_info

    while True:
        try:
            # ?ㅽ겕由곗꺑 罹≪쿂 & ???(紐⑤땲??0? count 議고쉶? ?숈떆??罹≪쿂)
            img0, count = _capture_screen_pil(0)
            with _store_lock:
                if pc_id not in _screen_store:
                    _screen_store[pc_id] = {}
                if img0:
                    _screen_store[pc_id][0] = img0
            for i in range(1, count):
                img_data, _ = _capture_screen_pil(i)
                if img_data:
                    with _store_lock:
                        _screen_store[pc_id][i] = img_data
            # remote status 媛깆떊
            with _store_lock:
                _remote_status[pc_id] = {"pc_id": pc_id, "state": "ready", "count": count, "screens": []}
            # 紐낅졊 ?뺤씤 & ?ㅽ뻾
            with _store_lock:
                cmd = _cmd_store.pop(pc_id, None)
            if cmd and cmd.get("action"):
                _handle_local_cmd(cmd)
        except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError):
            pass
        time.sleep(0.2)

def _handle_local_cmd(cmd):
    """濡쒖뺄 PC 紐낅졊 ?ㅽ뻾 (click, key, stop ??"""
    action = cmd.get("action", "")
    try:
        if action == "stop":
            subprocess.run(["taskkill", "/F", "/IM", "codex.exe"], capture_output=True)
            subprocess.run(["taskkill", "/F", "/IM", "gemini.exe"], capture_output=True)
        elif action in ("click", "dblclick"):
            x = cmd.get("x", 0); y = cmd.get("y", 0)
            btn = cmd.get("btn", "left"); mon = cmd.get("monitor", 0)
            ps = f'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -MemberDefinition '[DllImport("user32.dll")]public static extern bool SetCursorPos(int x,int y);[DllImport("user32.dll")]public static extern void mouse_event(uint f,int x,int y,uint d,int e);' -Name W -Namespace P
$s=[System.Windows.Forms.Screen]::AllScreens[{mon}].Bounds
$ax=[int]($s.Left+{x}*$s.Width);$ay=[int]($s.Top+{y}*$s.Height)
[P.W]::SetCursorPos($ax,$ay);Start-Sleep -Milliseconds 50
'''
            if btn == "right":
                ps += "[P.W]::mouse_event(8,0,0,0,0);[P.W]::mouse_event(16,0,0,0,0)"
            else:
                ps += "[P.W]::mouse_event(2,0,0,0,0);[P.W]::mouse_event(4,0,0,0,0)"
            if action == "dblclick":
                ps += "\nStart-Sleep -Milliseconds 80\n"
                ps += "[P.W]::mouse_event(2,0,0,0,0);[P.W]::mouse_event(4,0,0,0,0)"
            subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=5)
        elif action == "key":
            key = cmd.get("key", "")
            if key:
                ps = f"Add-Type -AssemblyName System.Windows.Forms;[System.Windows.Forms.SendKeys]::SendWait('{key}')"
                subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=5)
    except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError):
        pass


if __name__=="__main__":
    print(f"[+] ??쒕낫???쒖옉...")
    print(f"[OK] ??쒕낫????http://localhost:{PORT}")
    # cloudflared tunnel 諛깃렇?쇱슫???쒖옉
    tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
    tunnel_thread.start()
    # status-push 諛깃렇?쇱슫???쒖옉
    status_thread = threading.Thread(target=_status_push_loop, daemon=True)
    status_thread.start()
    # remote-agent 諛깃렇?쇱슫???쒖옉
    remote_thread = threading.Thread(target=_remote_agent_loop, daemon=True)
    remote_thread.start()
    # GitHub ?먭꺽 PC ?대쭅 (?쒖옉 利됱떆 + ?댄썑 60珥덈쭏??
    def _gh_poll_once():
        """git clone?쇰줈 ?먭꺽 PC status + ?ㅽ겕由??쎄린"""
        global _gh_cache
        import tempfile, shutil
        pat = get_pat()
        if not pat:
            return
        repo_url = f"https://x:{pat}@github.com/{OWNER}/{REPO}.git"
        tmpdir = tempfile.mkdtemp(prefix="gh-poll-")
        try:
            subprocess.run(["git","clone","--depth","1",repo_url,tmpdir],
                capture_output=True, timeout=30, check=True)
            # status ?쎄린
            status_dir = os.path.join(tmpdir, "status")
            gh = {}
            if os.path.isdir(status_dir):
                for fname in os.listdir(status_dir):
                    if not fname.endswith(".json"): continue
                    try:
                        with open(os.path.join(status_dir, fname), "r", encoding="utf-8-sig") as f:
                            data = json.load(f)
                        pid = data.get("pc_id") or fname.replace(".json","")
                        gh[pid] = data
                    except: pass
            with _store_lock:
                for pid in list(_deleted_pcs):
                    gh.pop(pid, None)
            _gh_cache = gh
            # remote ?ㅽ겕由?+ status ?쎄린
            remote_dir = os.path.join(tmpdir, "remote")
            if os.path.isdir(remote_dir):
                for pid in os.listdir(remote_dir):
                    pc_remote = os.path.join(remote_dir, pid)
                    if not os.path.isdir(pc_remote): continue
                    # ?ㅽ겕由??대?吏
                    screen_file = os.path.join(pc_remote, "screen.jpg")
                    if os.path.isfile(screen_file):
                        with open(screen_file, "rb") as f:
                            img = f.read()
                        with _store_lock:
                            if pid not in _screen_store:
                                _screen_store[pid] = {}
                            _screen_store[pid][0] = img
                    # remote status
                    rs_file = os.path.join(pc_remote, "status.json")
                    if os.path.isfile(rs_file):
                        try:
                            with open(rs_file, "r", encoding="utf-8-sig") as f:
                                rs = json.load(f)
                            with _store_lock:
                                _remote_status[pid] = rs
                        except: pass
        except: pass
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    threading.Thread(target=_gh_poll_once, daemon=True).start()  # ?쒖옉 利됱떆 1??鍮꾨룞湲??ㅽ뻾

    def _gh_poll_loop():
        while True:
            time.sleep(60)
            _gh_poll_once()
    threading.Thread(target=_gh_poll_loop, daemon=True).start()
    print(f"     Ctrl+C 醫낅즺")
    while True:
        try:
            class ReusableHTTPServer(http.server.HTTPServer):
                allow_reuse_address = True
            srv = ReusableHTTPServer(("",PORT),Handler)
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\n[醫낅즺]")
            break
        except (subprocess.CalledProcessError, OSError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError, TimeoutError, KeyError) as e:
            print(f"[ERROR] ?쒕쾭 ?щ옒?? {_mask_pat(e)} ??3珥????ъ떆??)
            time.sleep(3)

