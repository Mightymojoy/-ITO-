# -*- coding: utf-8 -*-
"""生成 ITO 电商渠道业绩看板 · 高级版 Demo（自包含、零 CDN 依赖、可交互筛选）

改动：后端仅嵌入全量明细 (channel x date)，所有 KPI/趋势/排行/环形/分组
由前端按筛选的「周期(日/周/月) + 日期区间」实时聚合。
"""
import json, datetime, calendar

BASE = "E:/电商渠道业绩看板/"
with open(BASE + "dashboard_data.json", encoding="utf-8") as f:
    D = json.load(f)

channels = D["channels"]
groups = {g["name"]: g["children"] for g in D["groups"]}
raw = D["data"]

TODAY = "2026-07-24"

# ---------- 全量明细嵌入：{ch: {date: [actual, budget, op, fc, actual_forecast]}} ----------
# 口径与现有 channel_dashboard.html 保持一致：
# 今天之前用 actual，今天及未来用 combined_forecast（fallback 经营/预算目标）
DATA = {}
min_date = None
max_date = None
for ch, byday in raw.items():
    DATA[ch] = {}
    for d, rec in byday.items():
        a = rec.get("actual") or 0
        b = rec.get("budget_target") or 0
        o = rec.get("operating_target") or 0
        fc = rec.get("combined_forecast") or 0
        af = a if d < TODAY else (fc or o or b)
        DATA[ch][d] = [a, b, o, fc, af]
        if min_date is None or d < min_date:
            min_date = d
        if max_date is None or d > max_date:
            max_date = d

palette = ["#c9a962", "#b8923f", "#d9bd7e", "#a8873f", "#e3cda0",
           "#8c6d2f", "#c2a663", "#bda06a", "#d4b878", "#9c7c3a"]

PAYLOAD = {
    "generated": D["meta"].get("generated_at", ""),
    "today": TODAY,
    "min_date": min_date,
    "max_date": max_date,
    "channels": channels,
    "groups": groups,
    "palette": palette,
    "data": DATA,
}

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ITO 电商渠道业绩 · 高级看板 Demo</title>
<style>
:root{
  --gold:#c9a962; --gold-deep:#a8873f; --gold-soft:#e3cda0;
  --ink:#1d1b16; --ink-2:#5b554a; --ink-3:#9a9183;
  --bg:#fbf9f4; --card:#ffffff; --line:rgba(201,169,98,.18);
  --shadow:0 10px 40px rgba(60,45,20,.06);
}
*{box-sizing:border-box;margin:0;padding:0}
body{
  font-family:'Inter','PingFang SC','Microsoft YaHei',-apple-system,sans-serif;
  background:
    radial-gradient(1200px 600px at 80% -10%, rgba(201,169,98,.10), transparent 60%),
    radial-gradient(900px 500px at -10% 10%, rgba(201,169,98,.06), transparent 55%),
    var(--bg);
  color:var(--ink); -webkit-font-smoothing:antialiased; letter-spacing:.01em;
}
.tnum{font-variant-numeric:tabular-nums}
#jsError{display:none;position:fixed;top:0;left:0;right:0;z-index:9999;
  background:#b3261e;color:#fff;padding:10px 16px;font-size:13px;font-weight:600}
.wrap{max-width:1280px;margin:0 auto;padding:40px 32px 72px}
/* header */
header{display:flex;justify-content:space-between;align-items:flex-end;
  padding-bottom:26px;margin-bottom:22px;border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:16px}
.brand .logo{width:54px;height:54px;border-radius:14px;
  background:linear-gradient(135deg,var(--gold),var(--gold-deep));
  display:flex;align-items:center;justify-content:center;color:#fff;
  font-weight:800;font-size:22px;letter-spacing:.04em;box-shadow:var(--shadow)}
.brand h1{font-size:26px;font-weight:800;letter-spacing:.06em}
.brand .sub{font-size:12.5px;color:var(--ink-3);letter-spacing:.18em;
  text-transform:uppercase;margin-top:3px}
.meta{text-align:right;font-size:13px;color:var(--ink-2)}
.meta .range{font-weight:700;color:var(--ink);font-size:15px}
.meta .ver{display:inline-block;margin-top:8px;padding:3px 10px;border-radius:20px;
  background:rgba(201,169,98,.12);color:var(--gold-deep);font-size:11px;
  font-weight:700;letter-spacing:.06em}
/* filter bar */
.filter-bar{display:flex;flex-wrap:wrap;gap:14px;align-items:center;
  background:var(--card);border:1px solid var(--line);border-radius:18px;
  padding:15px 20px;box-shadow:var(--shadow);margin-bottom:30px;animation:rise .6s both}
.filter-bar .grp{display:flex;align-items:center;gap:9px}
.filter-bar .lbl{font-size:12px;color:var(--ink-3);font-weight:600;margin-right:1px}
.seg{display:inline-flex;background:rgba(201,169,98,.10);border-radius:12px;padding:3px}
.seg button{border:none;background:none;padding:7px 18px;border-radius:9px;font-size:13px;
  font-weight:700;color:var(--ink-2);cursor:pointer;transition:.2s;font-family:inherit}
.seg button.active{background:#fff;color:var(--gold-deep);box-shadow:0 2px 8px rgba(60,45,20,.10)}
.quick{display:flex;flex-wrap:wrap;gap:7px}
.quick button{border:1px solid var(--line);background:#fff;padding:7px 13px;border-radius:10px;
  font-size:12.5px;color:var(--ink-2);cursor:pointer;font-family:inherit;transition:.2s}
.quick button:hover{border-color:var(--gold)}
.quick button.active{background:var(--gold);color:#fff;border-color:var(--gold)}
.custom{display:flex;align-items:center;gap:8px;margin-left:auto}
.custom input[type=date]{border:1px solid var(--line);border-radius:8px;padding:6px 10px;
  font-size:12.5px;font-family:inherit;color:var(--ink-2);background:#fff}
.custom span{color:var(--ink-3);font-size:12px}
/* channel filter */
.channel-row{display:none;flex-wrap:wrap;gap:8px;margin:-12px 0 6px;padding:0 4px;
  animation:rise .4s both}
.channel-row.show{display:flex}
.chip{border:1px solid var(--line);background:#fff;padding:6px 14px;border-radius:20px;
  font-size:12.5px;color:var(--ink-2);cursor:pointer;font-family:inherit;transition:.18s;user-select:none}
.chip:hover{border-color:var(--gold)}
.chip.on{background:var(--gold);color:#fff;border-color:var(--gold);font-weight:600}
/* section */
.sec-title{display:flex;align-items:center;gap:10px;margin:38px 0 18px}
.sec-title .bar{width:4px;height:18px;border-radius:3px;
  background:linear-gradient(var(--gold),var(--gold-deep))}
.sec-title h2{font-size:16px;font-weight:700}
.sec-title .en{font-size:11px;color:var(--ink-3);letter-spacing:.18em;
  text-transform:uppercase;margin-left:auto}
/* kpi grid */
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}
.kpi{position:relative;background:var(--card);border:1px solid var(--line);
  border-radius:20px;padding:22px 22px 16px;box-shadow:var(--shadow);
  overflow:hidden;animation:rise .6s both}
.kpi::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,var(--gold),var(--gold-soft),transparent)}
.kpi .ic{width:34px;height:34px;border-radius:10px;background:rgba(201,169,98,.12);
  display:flex;align-items:center;justify-content:center;color:var(--gold-deep);margin-bottom:14px}
.kpi .lab{font-size:12.5px;color:var(--ink-2)}
.kpi .val{font-size:30px;font-weight:800;margin:6px 0 4px;letter-spacing:.01em}
.kpi .val small{font-size:15px;font-weight:700;color:var(--ink-3);margin-left:2px}
.kpi .delta{font-size:12.5px;font-weight:700;display:inline-flex;align-items:center;gap:4px}
.up{color:#2e7d52}.down{color:#c0492f}
.kpi .spark{margin-top:12px;height:38px;opacity:.85}
/* charts */
.charts{display:grid;grid-template-columns:1.55fr 1fr;gap:20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:20px;
  padding:24px;box-shadow:var(--shadow);animation:rise .6s both}
.card h3{font-size:14.5px;font-weight:700;margin-bottom:4px}
.card .hint{font-size:12px;color:var(--ink-3);margin-bottom:16px}
/* channel rank */
.rank{display:flex;flex-direction:column;gap:14px}
.rrow{display:grid;grid-template-columns:190px 1fr 120px;align-items:center;gap:14px}
.rrow .nm{font-size:13.5px;font-weight:600;line-height:1.3}
.rrow .tag{font-size:10.5px;color:var(--ink-3);margin-top:2px}
.track{height:10px;border-radius:6px;background:rgba(201,169,98,.12);overflow:hidden}
.fill{height:100%;border-radius:6px;width:0;
  background:linear-gradient(90deg,var(--gold-soft),var(--gold));
  transition:width 1.1s cubic-bezier(.22,1,.36,1)}
.fill.na{background:rgba(180,180,180,.35)}
.rrow .num{text-align:right}
.rrow .num .rt{font-size:15px;font-weight:800}
.rrow .num .amt{font-size:11.5px;color:var(--ink-3)}
.rrow .num .yoy{font-size:11px;font-weight:700;margin-top:2px}
/* donut legend */
.legend{display:flex;flex-direction:column;gap:9px;margin-top:16px}
.leg{display:flex;align-items:center;gap:9px;font-size:12.5px}
.leg .dot{width:10px;height:10px;border-radius:3px;flex:none}
.leg .ln{flex:1;color:var(--ink-2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.leg .pc{font-weight:700;color:var(--ink)}
/* group cards */
.g-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}
.g-card{background:var(--card);border:1px solid var(--line);border-radius:18px;
  padding:20px;box-shadow:var(--shadow);animation:rise .6s both}
.g-card .gn{font-size:13px;color:var(--ink-2);font-weight:600}
.g-card .grt{font-size:28px;font-weight:800;margin:10px 0 4px}
.g-card .gamt{font-size:12px;color:var(--ink-3)}
footer{margin-top:48px;text-align:center;font-size:12px;color:var(--ink-3)}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@media(max-width:900px){
  .kpi-grid,.g-grid{grid-template-columns:repeat(2,1fr)}
  .charts{grid-template-columns:1fr}
  .rrow{grid-template-columns:140px 1fr 100px}
}
</style>
</head>
<body>
<div id="jsError"></div>
<div class="wrap">
  <header>
    <div class="brand">
      <div class="logo">I</div>
      <div>
        <h1>ITO 电商渠道业绩看板</h1>
        <div class="sub">Channel Performance · 渠道表现</div>
      </div>
    </div>
    <div class="meta">
      <div>当前区间</div>
      <div class="range tnum" id="mRange"></div>
      <div class="range tnum" id="mCh" style="font-size:13px;color:var(--ink-2);font-weight:600"></div>
      <div class="ver" id="mVer"></div>
    </div>
  </header>

  <div class="filter-bar">
    <div class="grp">
      <span class="lbl">周期</span>
      <div class="seg" id="periodSeg">
        <button data-p="day" class="active">日</button>
        <button data-p="week">周</button>
        <button data-p="month">月</button>
      </div>
    </div>
    <div class="grp" style="flex:1;min-width:200px">
      <span class="lbl">范围</span>
      <div class="quick" id="quick"></div>
    </div>
    <div class="grp">
      <span class="lbl">渠道</span>
      <div class="seg" id="chSeg">
        <button data-c="all" class="active">全部</button>
        <button data-c="custom">自定义</button>
      </div>
    </div>
    <div class="grp custom">
      <input type="date" id="dStart"> <span>至</span> <input type="date" id="dEnd">
    </div>
  </div>

  <div class="channel-row" id="chRow"></div>

  <div class="sec-title">
    <span class="bar"></span><h2 id="kpiTitle">核心指标</h2>
    <span class="en" id="kpiEn">Overview</span>
  </div>
  <div class="kpi-grid" id="kpiGrid"></div>

  <div class="sec-title">
    <span class="bar"></span><h2 id="trendTitle">趋势对比</h2>
    <span class="en" id="trendEn">Trend</span>
  </div>
  <div class="charts">
    <div class="card">
      <h3 id="trendCardTitle">实际 GMV vs 经营目标</h3>
      <div class="hint" id="trendHint"></div>
      <div id="trend"></div>
    </div>
    <div class="card">
      <h3>渠道 GMV 结构</h3>
      <div class="hint" id="donutHint">当前区间累计实际 GMV 占比</div>
      <div id="donut"></div>
      <div class="legend" id="legend"></div>
    </div>
  </div>

  <div class="sec-title">
    <span class="bar"></span><h2>渠道达成排行</h2>
    <span class="en">Channel Ranking</span>
  </div>
  <div class="card"><div class="rank" id="rank"></div></div>

  <div class="sec-title">
    <span class="bar"></span><h2>分组汇总</h2>
    <span class="en">Group Summary</span>
  </div>
  <div class="g-grid" id="gGrid"></div>

  <footer id="foot"></footer>
</div>

<script>
const P = __PAYLOAD__;
const $ = (s,el=document)=>el.querySelector(s);
const fmt = n => (n||0).toLocaleString('zh-CN');
const wan = n => (n/10000).toFixed(1);

/* 全局错误条 */
window.onerror = function(msg){const e=$('#jsError');e.style.display='block';e.textContent='⚠ 脚本错误：'+msg;};

/* 基础数据 */
const DATA=P.data, CHANNELS=P.channels, GROUPS=P.groups, PALETTE=P.palette;
const TODAY=P.today, MIND=P.min_date, MAXD=P.max_date;
const groupOf={}; for(const g in GROUPS) for(const c of GROUPS[g]) groupOf[c]=g;

/* 日期工具 */
function parseD(s){const p=s.split('-').map(Number);return new Date(p[0],p[1]-1,p[2]);}
function iso(dt){return dt.getFullYear()+'-'+String(dt.getMonth()+1).padStart(2,'0')+'-'+String(dt.getDate()).padStart(2,'0');}
function addDays(dt,n){const r=new Date(dt);r.setDate(r.getDate()+n);return r;}
function diffDays(a,b){return Math.round((parseD(b)-parseD(a))/86400000);}
function mondayOf(dt){const r=new Date(dt);const w=(r.getDay()+6)%7;r.setDate(r.getDate()-w);return r;}

/* 聚合：区间某指标求和  idx 0=actual 1=budget 2=op 3=fc 4=actual_forecast */
function rec(ch,date){const r=DATA[ch]&&DATA[ch][date];return r?r:[0,0,0,0,0];}
function sumRange(chs,s,e,idx){
  let t=0;let d=parseD(s);const end=parseD(e);
  while(d<=end){const ds=iso(d);for(const ch of chs)t+=rec(ch,ds)[idx];d=addDays(d,1);}
  return t;
}
/* 按周期分桶 */
function aggBucket(chs,s,e,label){
  return {label,start:s,end:e,
    a:sumRange(chs,s,e,0),b:sumRange(chs,s,e,1),
    o:sumRange(chs,s,e,2),f:sumRange(chs,s,e,3),
    af:sumRange(chs,s,e,4)};
}
function labelWeek(ws,we){const a=parseD(ws),b=parseD(we);
  return (a.getMonth()+1)+'/'+a.getDate()+'~'+(b.getMonth()+1)+'/'+b.getDate();}
function buckets(s,e,period,chs){
  const d0=parseD(s),d1=parseD(e);const res=[];
  if(period==='day'){
    let d=d0;while(d<=d1){res.push(aggBucket(chs,iso(d),iso(d),(d.getMonth()+1)+'/'+d.getDate()));d=addDays(d,1);}
  }else if(period==='week'){
    let cur=mondayOf(d0);
    while(cur<=d1){const ws=iso(cur);const capped=addDays(cur,6);const we=iso(capped<d1?capped:d1);
      res.push(aggBucket(chs,ws,we,labelWeek(ws,we)));cur=addDays(cur,7);}
  }else{
    let y=d0.getFullYear(),m=d0.getMonth()+1;
    while(true){const sd=new Date(y,m-1,1);if(sd>d1)break;
      const ld=new Date(y,m-1,1);ld.setMonth(ld.getMonth()+1);ld.setDate(0);
      const ed=ld>d1?d1:ld;
      const lbl=(m)+'月'+((y!==d1.getFullYear())?' '+y:'');
      res.push(aggBucket(chs,iso(sd),iso(ed),lbl));
      if(m===12){m=1;y++;}else m++;}
  }
  return res;
}
/* 去年同期等长区间 / 上一等长区间 */
function lyRange(s,e){return [iso(addDays(parseD(s),-365)),iso(addDays(parseD(e),-365))];}
function prevRange(s,e){const n=diffDays(s,e)+1;const ps=addDays(parseD(s),-n);return [iso(ps),iso(addDays(ps,n-1))];}

/* 图标 */
const ICON = {
  gmv:'<path d="M3 3v18h18"/><path d="M7 14l4-4 3 3 5-6"/>',
  target:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
  rate:'<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  forecast:'<path d="M2 12a10 10 0 0 1 20 0"/><path d="M12 12l6-3"/><circle cx="12" cy="12" r="1.5"/>'
};
function svgIcon(p){return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'+p+'</svg>';}

/* sparkline */
function spark(vals,h=38){
  if(!vals||vals.length<2) return '';
  const w=120, max=Math.max.apply(null,vals), min=Math.min.apply(null,vals);
  const pts=vals.map((v,i)=>`${i*(w/(vals.length-1))},${h-4-((v-min)/((max-min)||1))*(h-8)}`).join(' ');
  return '<svg width="100%" height="'+h+'" viewBox="0 0 '+w+' '+h+'" preserveAspectRatio="none">'+
    '<defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c9a962" stop-opacity=".25"/>'+
    '<stop offset="1" stop-color="#c9a962" stop-opacity="0"/></linearGradient></defs>'+
    '<polyline points="'+pts+' '+w+','+h+' 0,'+h+'" fill="url(#sg)" stroke="none"/>'+
    '<polyline points="'+pts+'" fill="none" stroke="#c9a962" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'+
    '</svg>';
}

/* delta 展示 */
function delta(v,unit){
  if(v==null||isNaN(v)) return '<span class="delta">—</span>';
  const cls=v>=0?'up':'down'; const ar=v>=0?'▲':'▼';
  return '<span class="delta '+cls+'">'+ar+' '+Math.abs(v).toFixed(1)+unit+'</span>';
}

/* ============ 状态 ============ */
const QUICK = {
  day:[{t:'近7天',a:'last',n:7},{t:'近30天',a:'last',n:30},{t:'本月',a:'month'},{t:'本年',a:'year'},{t:'全部',a:'all'}],
  week:[{t:'近8周',a:'lastw',n:8},{t:'近12周',a:'lastw',n:12},{t:'本季',a:'quarter'},{t:'本年',a:'year'},{t:'全部',a:'all'}],
  month:[{t:'近6月',a:'lastm',n:6},{t:'近12月',a:'lastm',n:12},{t:'本年',a:'year'},{t:'全部',a:'all'}]
};
const DEF_QUICK = {day:1, week:1, month:1};  // 默认选中第几个快捷
const state = {period:'day', start:null, end:null, quickIdx:1, channels:CHANNELS.slice(), chMode:'all'};

function computeRange(q){
  const t=parseD(TODAY);
  if(q.a==='last'){return [iso(addDays(t,-(q.n-1))),TODAY];}
  if(q.a==='lastw'){return [iso(addDays(t,-(q.n*7-1))),TODAY];}
  if(q.a==='lastm'){let y=t.getFullYear(),m=t.getMonth()+1;m=m-q.n+1;while(m<=0){m+=12;y--;}
    return [iso(new Date(y,m-1,1)),TODAY];}
  if(q.a==='month'){return [iso(new Date(t.getFullYear(),t.getMonth(),1)),TODAY];}
  if(q.a==='quarter'){const qm=Math.floor(t.getMonth()/3)*3;return [iso(new Date(t.getFullYear(),qm,1)),TODAY];}
  if(q.a==='year'){return [iso(new Date(t.getFullYear(),0,1)),TODAY];}
  if(q.a==='all'){return [MIND,MAXD];}
  return [MIND,TODAY];
}

/* 构建快捷按钮 */
function buildQuick(){
  const box=$('#quick'); box.innerHTML='';
  QUICK[state.period].forEach((q,i)=>{
    const b=document.createElement('button');
    b.textContent=q.t; if(i===state.quickIdx) b.className='active';
    b.onclick=()=>{ state.quickIdx=i; const [s,e]=computeRange(q);
      state.start=s; state.end=e; syncDateInputs(); renderAll(); };
    box.appendChild(b);
  });
}
function syncDateInputs(){
  $('#dStart').value=state.start; $('#dEnd').value=state.end;
}

/* 构建渠道多选 chips */
function buildChannels(){
  const row=$('#chRow'); row.innerHTML='';
  CHANNELS.forEach(ch=>{
    const c=document.createElement('button');
    c.className='chip'+(state.channels.indexOf(ch)>=0?' on':'');
    c.textContent=ch;
    c.onclick=()=>{
      const i=state.channels.indexOf(ch);
      if(i>=0){
        if(state.channels.length===1) return;   // 至少保留 1 个渠道
        state.channels.splice(i,1);
      }else{
        state.channels.push(ch);
      }
      c.classList.toggle('on');
      renderAll();
    };
    row.appendChild(c);
  });
}

/* ============ 渲染 ============ */
function renderKPI(){
  const s=state.start,e=state.end,p=state.period, chs=state.channels;
  const a=sumRange(chs,s,e,0),b=sumRange(chs,s,e,1),
        o=sumRange(chs,s,e,2),f=sumRange(chs,s,e,3),
        af=sumRange(chs,s,e,4);
  // 与现有 channel_dashboard.html 口径一致：达成率用 actual+forecast
  const br=b?af/b*100:null, opr=o?af/o*100:null, fr=o?f/o*100:null;
  const [lys,lye]=lyRange(s,e); const la=sumRange(chs,lys,lye,0);
  const yoy=la>0?(a/la-1)*100:null;
  const [ps,pe]=prevRange(s,e); const pa=sumRange(chs,ps,pe,0);
  const mom=pa>0?(a/pa-1)*100:null;
  const fc_vs_actual=a?((f-a)/a*100):null;

  const periodName={day:'日',week:'周',month:'月'}[p];
  $('#kpiTitle').textContent='核心指标 · '+periodName+'度区间';
  $('#kpiEn').textContent=periodName+'-period Overview';

  const spVals = buckets(s,e,p,chs).map(x=>x.a);
  const kpis=[
    {ic:ICON.gmv, lab:periodName+'度实际 GMV', val:wan(a), unit:'万',
     d:(yoy!=null?delta(yoy,'%'):'<span class="delta">—</span>')+' <span style="color:var(--ink-3);font-weight:500">|</span> 环比 '+delta(mom,'%'),
     sp:spVals, sub:''},
    {ic:ICON.target, lab:'预算达成率', val:br==null?'—':br.toFixed(1), unit:br==null?'':'%',
     d:delta(null), sp:null, sub:br==null?'区间内无预算目标':'缺口 '+wan(b-af)+'万'},
    {ic:ICON.rate, lab:'经营达成率', val:opr==null?'—':opr.toFixed(1), unit:opr==null?'':'%',
     d:delta(null), sp:null, sub:opr==null?'区间内无经营目标':'缺口 '+wan(o-af)+'万'},
    {ic:ICON.forecast, lab:'实际+预估 GMV', val:wan(af), unit:'万', d:delta(fc_vs_actual,'%'),
     sp:null, sub:'预测/经营 '+(fr==null?'—':fr.toFixed(1)+'%')+'  ·  较实际 '+wan(f-a)+'万'}
  ];
  $('#kpiGrid').innerHTML = kpis.map((x,i)=>`
    <div class="kpi" style="animation-delay:${i*0.07}s">
      <div class="ic">${svgIcon(x.ic)}</div>
      <div class="lab">${x.lab}</div>
      <div class="val tnum">${x.val}<small>${x.unit}</small></div>
      <div>${x.d}</div>
      <div class="spark tnum" style="font-size:11px;color:var(--ink-3)">${x.sp?spark(x.sp):''}</div>
      ${x.sub?`<div style="margin-top:3px;font-size:11px;color:var(--ink-3)">${x.sub}</div>`:''}
    </div>`).join('');
}

function renderTrend(){
  const bks=buckets(state.start,state.end,state.period,state.channels);
  const periodName={day:'日',week:'周',month:'月'}[state.period];
  $('#trendCardTitle').textContent=periodName+'度实际 GMV vs 经营目标';
  const span=diffDays(state.start,state.end)+1;
  $('#trendHint').textContent='区间 '+state.start+' ~ '+state.end+'（'+span+' 天，'+bks.length+' 个'+periodName+'度桶）';

  const W=620,H=240,pl=46,pr=14,pt=18,pb=34;
  const iw=W-pl-pr, ih=H-pt-pb;
  const A=bks.map(b=>b.a), T=bks.map(b=>b.o), L=bks.map(b=>b.label);
  const maxv=Math.max.apply(null,A.concat(T).concat([1]))*1.12;
  const n=A.length, bw=Math.min(iw/n*0.6,40), gap=iw/n;
  const y=v=>pt+ih-(v/maxv)*ih;
  const xc=i=>pl+gap*i+gap/2;
  let bars='', line='', dots='', xl='';
  const step=Math.max(1,Math.ceil(n/16));
  A.forEach((v,i)=>{
    const bx=xc(i)-bw/2;
    bars+=`<rect x="${bx}" y="${y(v)}" width="${bw}" height="${pt+ih-y(v)}" rx="5" fill="url(#bg)"><title>${L[i]} 实际 ${fmt(v)}</title></rect>`;
    line+=`${i?'L':'M'}${xc(i)},${y(T[i])} `;
    dots+=`<circle cx="${xc(i)}" cy="${y(T[i])}" r="3.5" fill="#fff" stroke="#5b554a" stroke-width="2"><title>${L[i]} 目标 ${fmt(T[i])}</title></circle>`;
    if(i%step===0 || i===n-1) xl+=`<text x="${xc(i)}" y="${H-12}" text-anchor="middle" font-size="11" fill="#9a9183">${L[i]}</text>`;
  });
  let grid='';
  for(let g=0;g<=4;g++){const gv=maxv*g/4; const gy=y(gv);
    grid+=`<line x1="${pl}" y1="${gy}" x2="${W-pr}" y2="${gy}" stroke="rgba(201,169,98,.12)"/>`+
          `<text x="${pl-8}" y="${gy+4}" text-anchor="end" font-size="10" fill="#9a9183">${Math.round(gv/10000)}万</text>`;}
  $('#trend').innerHTML=`<svg viewBox="0 0 ${W} ${H}" width="100%">
    <defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#d9bd7e"/><stop offset="1" stop-color="#c9a962"/></linearGradient></defs>
    ${grid}${bars}
    <path d="${line}" fill="none" stroke="#5b554a" stroke-width="2.2" stroke-dasharray="5 4"/>
    ${dots}${xl}</svg>`;
}

function channelStats(s,e,chs){
  return chs.map((ch,i)=>{
    const a=sumRange([ch],s,e,0),b=sumRange([ch],s,e,1),o=sumRange([ch],s,e,2),af=sumRange([ch],s,e,4);
    const [lys,lye]=lyRange(s,e); const ly=sumRange([ch],lys,lye,0);
    // 与现有看板一致：目标达成率 = actual_forecast / operating_target
    const rate=o>0?af/o*100:null;
    const yoy=ly>0?(a/ly-1)*100:null;
    return {name:ch,actual:a,op:o,af:af,
      rate:rate==null?null:+rate.toFixed(1),
      yoy:yoy==null?null:+yoy.toFixed(1),
      group:groupOf[ch],color:PALETTE[i%PALETTE.length]};
  }).sort((x,y)=>y.actual-x.actual);
}

function renderRank(){
  const s=state.start,e=state.end;
  const st=channelStats(s,e,state.channels);
  $('#rank').innerHTML = st.map((c,i)=>{
    const na=c.rate==null;
    const width=na?0:Math.min(c.rate,120);
    const color=na?'':(c.rate>=100?'#2e7d52':(c.rate>=80?'#a8873f':'#c0492f'));
    const amt=na?(wan(c.actual)+'万 / 无目标'):(wan(c.af)+'万 / '+wan(c.op)+'万');
    return `<div class="rrow">
      <div><div class="nm">${i+1}. ${c.name}</div><div class="tag">${c.group}</div></div>
      <div class="track"><div class="fill ${na?'na':''}" data-w="${width}"></div></div>
      <div class="num"><div class="rt tnum" style="color:${color||'#9a9183'}">${na?'—':c.rate+'%'}</div>
        <div class="amt tnum">${amt}</div>
        ${c.yoy!=null?`<div class="yoy ${c.yoy>=0?'up':'down'}">同比 ${c.yoy>=0?'▲':'▼'} ${Math.abs(c.yoy).toFixed(1)}%</div>`:''}
      </div>
    </div>`;
  }).join('');
  requestAnimationFrame(()=>{document.querySelectorAll('.fill').forEach(f=>{f.style.width=f.dataset.w+'%';});});
}

function renderDonut(){
  const s=state.start,e=state.end;
  const st=channelStats(s,e,state.channels).sort((a,b)=>b.actual-a.actual);
  const total=st.reduce((s2,x)=>s2+x.actual,0);
  const R=78, C=2*Math.PI*R, cx=100, cy=100;
  let off=0, arcs='';
  st.forEach(it=>{
    const frac=total?it.actual/total:0; const len=frac*C;
    arcs+=`<circle cx="${cx}" cy="${cy}" r="${R}" fill="none" stroke="${it.color}" stroke-width="22"
      stroke-dasharray="${len} ${C-len}" stroke-dashoffset="${-off}" transform="rotate(-90 ${cx} ${cy})">
      <title>${it.name} ${wan(it.actual)}万 (${(frac*100).toFixed(1)}%)</title></circle>`;
    off+=len;
  });
  $('#donut').innerHTML=`<svg viewBox="0 0 200 200" width="100%" style="max-width:240px;display:block;margin:0 auto">
    ${arcs}<text x="${cx}" y="${cy-4}" text-anchor="middle" font-size="13" fill="#9a9183">区间GMV</text>
    <text x="${cx}" y="${cy+18}" text-anchor="middle" font-size="20" font-weight="800" fill="#1d1b16">${wan(total)}万</text></svg>`;
  $('#legend').innerHTML=st.map(it=>`<div class="leg">
    <span class="dot" style="background:${it.color}"></span>
    <span class="ln">${it.name}</span>
    <span class="pc tnum">${total?(it.actual/total*100).toFixed(1):'0.0'}%</span></div>`).join('');
}

function renderGroups(){
  const s=state.start,e=state.end, chs=state.channels;
  if(!chs.length){$('#gGrid').innerHTML='<div style="color:var(--ink-3);font-size:13px;grid-column:1/-1;padding:10px 0">未选择渠道</div>';return;}
  const sel=new Set(chs);
  const order=["货架电商汇总","兴趣电商-自营","兴趣电商-达播","兴趣电商汇总"];
  $('#gGrid').innerHTML = order.filter(g=>GROUPS[g].some(c=>sel.has(c))).map((gname,i)=>{
    const cs=GROUPS[gname].filter(c=>sel.has(c));
    const a=sumRange(cs,s,e,0),o=sumRange(cs,s,e,2),b=sumRange(cs,s,e,1),af=sumRange(cs,s,e,4);
    const rate=o>0?af/o*100:0;
    return `<div class="g-card" style="animation-delay:${i*0.06}s">
      <div class="gn">${gname}</div>
      <div class="grt tnum" style="color:${rate>=100?'#2e7d52':'#1d1b16'}">${rate.toFixed(1)}%</div>
      <div class="gamt tnum">实际+预估 ${wan(af)}万 · 目标 ${wan(o)}万</div>
    </div>`;
  }).join('');
}

function renderAll(){
  $('#mRange').textContent = state.start + ' ~ ' + state.end;
  let chTxt;
  if(state.chMode==='all') chTxt='全部渠道 ('+CHANNELS.length+')';
  else if(state.channels.length>4) chTxt='已选 '+state.channels.length+' 个渠道';
  else chTxt=state.channels.join('、');
  $('#mCh').textContent='渠道：'+chTxt;
  renderKPI(); renderTrend(); renderRank(); renderDonut(); renderGroups();
}

/* ============ 初始化 & 事件 ============ */
function init(){
  document.getElementById('mVer').textContent = 'v1.0 渠道表现';
  // 默认：周期 day + 默认快捷
  const q=QUICK[state.period][state.quickIdx];
  const [s,e]=computeRange(q); state.start=s; state.end=e;
  buildQuick(); syncDateInputs(); buildChannels();
  // 渠道切换
  $('#chSeg').addEventListener('click',ev=>{
    const btn=ev.target.closest('button'); if(!btn) return;
    document.querySelectorAll('#chSeg button').forEach(x=>x.classList.remove('active'));
    btn.classList.add('active');
    const mode=btn.dataset.c;
    state.chMode=mode;
    if(mode==='all'){ state.channels=CHANNELS.slice(); $('#chRow').classList.remove('show'); }
    else { $('#chRow').classList.add('show'); }
    buildChannels(); renderAll();
  });
  // 周期切换
  $('#periodSeg').addEventListener('click',ev=>{
    const btn=ev.target.closest('button'); if(!btn) return;
    document.querySelectorAll('#periodSeg button').forEach(x=>x.classList.remove('active'));
    btn.classList.add('active');
    state.period=btn.dataset.p; state.quickIdx=DEF_QUICK[state.period];
    buildQuick();
    const qq=QUICK[state.period][state.quickIdx]; const [s2,e2]=computeRange(qq);
    state.start=s2; state.end=e2; syncDateInputs(); renderAll();
  });
  // 自定义日期
  $('#dStart').addEventListener('change',()=>{ state.start=$('#dStart').value||MIND;
    document.querySelectorAll('#quick button').forEach(x=>x.classList.remove('active')); renderAll(); });
  $('#dEnd').addEventListener('change',()=>{ state.end=$('#dEnd').value||MAXD;
    document.querySelectorAll('#quick button').forEach(x=>x.classList.remove('active')); renderAll(); });
  renderAll();
  document.getElementById('foot').textContent =
    'ITO 电商渠道业绩看板 · 渠道表现（数据基于 dashboard_data.json 实时聚合，支持日/周/月筛选 + 渠道筛选） · 数据刷新时间：'+P.generated;
}
init();
</script>
</body>
</html>"""

html = html.replace("__PAYLOAD__", json.dumps(PAYLOAD, ensure_ascii=False))
out = BASE + "channel_dashboard.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("OK ->", out, "size=", len(html))
print("min_date=", min_date, "max_date=", max_date)
print("embedded channels=", len(channels), "data entries=", sum(len(v) for v in DATA.values()))
