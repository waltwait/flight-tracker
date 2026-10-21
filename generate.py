#!/usr/bin/env python3
"""Flight-tracker site generator (journal style, multi-destination).

Reads destinations.json manifest; for each destination reads its
watch + history JSON and generates <id>/index.html; also generates
the hub index.html.

Usage: python3 generate.py   (run from the repo directory)
"""
import json
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")

FONTS = ("https://fonts.googleapis.com/css2?family=Young+Serif"
         "&family=Noto+Serif+TC:wght@600;900&family=LXGW+WenKai+TC"
         "&family=Courier+Prime:wght@400;700&display=swap")

PWA_HEAD = """<link rel="manifest" href="/flight-tracker/manifest.json">
<meta name="theme-color" content="#B3301F">
<link rel="apple-touch-icon" href="/flight-tracker/icons/apple-touch-icon.png">
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/flight-tracker/sw.js', {scope: '/flight-tracker/'});
  });
}
/* one-tap install button: shown only when the browser actually offers install */
let deferredInstallPrompt = null;
function wireInstallBtn() {
  document.querySelectorAll('.install-btn').forEach(function(b) {
    b.addEventListener('click', function() {
      if (deferredInstallPrompt) {
        deferredInstallPrompt.prompt();
        deferredInstallPrompt = null;
      }
    });
  });
}
window.addEventListener('beforeinstallprompt', function(e) {
  e.preventDefault();
  deferredInstallPrompt = e;
  document.querySelectorAll('.install-btn').forEach(function(b) { b.hidden = false; });
});
window.addEventListener('appinstalled', function() {
  deferredInstallPrompt = null;
  document.querySelectorAll('.install-btn').forEach(function(b) { b.hidden = true; });
});
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', wireInstallBtn);
} else {
  wireInstallBtn();
}
</script>"""

BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
--bg:#F3ECDC;--surface:#FBF7EC;--kraft:#B98F63;
--ink:#3B2F25;--ink2:#66564A;--ink3:#8F7E6B;
--rule:#DCCFB8;--rule2:#E9E0CD;--dot:rgba(59,47,37,.14);
--red:#B3301F;--red-soft:#F1DDD2;
--blue:#2B4A86;--blue-soft:#E0E2E8;
--green:#2F6B4F;--plum:#6E3B6E;
--now:#F2DC5D;--now-ink:#4A3A00;
--cover-ink:#2b2119;
--tape-clip:polygon(0 4%,4% 0,96% 3%,100% 0,97% 26%,100% 50%,97% 74%,100% 100%,95% 97%,4% 100%,0 96%,3% 72%,0 50%,3% 26%);
--f-display:'Young Serif','Noto Serif TC',serif;
--f-body:'LXGW WenKai TC','Kaiti TC','PingFang TC','Microsoft JhengHei',serif;
--f-mono:'Courier Prime',monospace;
}
body{font-family:var(--f-body);color:var(--ink);line-height:1.65;font-size:15.5px;
background-color:var(--bg);
background-image:radial-gradient(var(--dot) 1.1px,transparent 1.1px);
background-size:22px 22px;padding:0 0 48px;-webkit-text-size-adjust:100%}
.wrap{max-width:760px;margin:0 auto;padding:0 16px}
@media(min-width:640px){.wrap{padding:0 28px}}
/* nav */
.nav{position:sticky;top:0;z-index:10;background:rgba(243,236,220,.88);
backdrop-filter:blur(8px);border-bottom:1px solid var(--rule)}
.nav .wrap{display:flex;align-items:center;gap:10px;padding-top:10px;padding-bottom:10px}
.nav a.brand{font-family:var(--f-display);font-weight:900;color:var(--ink);text-decoration:none;font-size:17px}
.nav a.brand .stamp-sm{display:inline-block;color:var(--red);border:2px solid var(--red);
border-radius:4px;font-size:12px;padding:0 6px;margin-right:8px;transform:rotate(-4deg);font-family:var(--f-display)}
.nav .crumb{color:var(--ink3);font-size:13px}
.install-btn{margin-left:auto;background:rgba(179,48,31,.06);border:2px solid var(--red);color:var(--red);
border-radius:4px;font-family:var(--f-body);font-weight:700;font-size:13.5px;padding:7px 14px;cursor:pointer;white-space:nowrap}
.install-btn[hidden]{display:none}
.install-btn:active{transform:scale(.96)}
/* hero */
.hero{padding:34px 0 10px;text-align:center}
.stamp{display:inline-block;color:var(--red);border:4px double var(--red);border-radius:8px;
font-family:var(--f-display);font-weight:900;font-size:clamp(48px,14vw,84px);
padding:2px 18px;transform:rotate(-4deg);letter-spacing:4px;opacity:.92}
.hero h1{font-family:var(--f-display);font-weight:900;font-size:clamp(26px,6vw,36px);margin:14px 0 6px}
.hero .sub{color:var(--ink2);font-size:14px}
.hl{background:linear-gradient(100deg,transparent 2%,var(--now) 4%,var(--now) 96%,transparent 98%);
padding:0 4px;font-weight:700}
/* section */
.sec{margin-top:30px}
.sec-h{display:flex;align-items:baseline;gap:10px;border-bottom:1.5px dashed var(--rule);padding-bottom:8px;margin-bottom:14px}
.sec-h h2{font-family:var(--f-display);font-size:22px;font-weight:900}
.sec-h .en{font-family:var(--f-mono);font-size:12px;color:var(--ink3)}
/* ticket card */
.ticket{position:relative;background:var(--surface);border:1px solid var(--rule);
border-radius:4px;margin-bottom:18px;box-shadow:0 1px 0 var(--rule)}
.tape{position:absolute;top:-11px;left:28px;width:92px;height:24px;opacity:.85;transform:rotate(-3deg);
clip-path:var(--tape-clip)}
.ticket:nth-child(even) .tape{left:auto;right:28px;transform:rotate(3deg)}
.t-in{padding:16px 16px 12px}
.t-route{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.t-combo{font-family:var(--f-display);font-weight:900;font-size:17px}
.t-id{font-family:var(--f-mono);font-size:12px;color:var(--ink3)}
.t-price{font-family:var(--f-mono);font-weight:700;font-size:30px;margin:6px 0 2px}
.t-delta{font-size:13px;margin-bottom:8px}
.down{color:var(--green)}.up{color:var(--red)}
.t-meta{font-size:13.5px;color:var(--ink2)}
.t-meta div{margin:2px 0}
.t-meta .k{display:inline-block;min-width:70px;color:var(--ink3);font-size:12.5px}
.t-perf{border-top:2px dashed var(--rule);margin:10px 0 0;position:relative}
.t-foot{display:flex;justify-content:space-between;align-items:center;padding:10px 16px 12px}
.src{font-family:var(--f-mono);font-size:12px;color:var(--ink3)}
.btn{display:inline-block;background:var(--blue-soft);color:var(--blue);font-weight:700;font-size:14px;
border-radius:999px;padding:9px 26px;text-decoration:none;min-height:44px;line-height:26px}
.btn:hover{filter:brightness(.96)}
.badge{display:inline-block;font-size:11.5px;border:1.5px solid var(--red);color:var(--red);
border-radius:3px;padding:0 7px;margin-left:8px;transform:rotate(-3deg);font-weight:700;background:var(--red-soft)}
.badge.ok{border-color:var(--green);color:var(--green);transform:rotate(2deg);background:rgba(47,107,79,.08)}
/* chart */
.chart-card{background:var(--surface);border:1px solid var(--rule);border-radius:4px;padding:16px 12px 8px;position:relative}
.chart-wrap{position:relative;height:290px}
.note{font-size:13px;color:var(--ink3);margin-top:8px}
/* table */
table{width:100%;border-collapse:collapse;font-size:13.5px;background:var(--surface);
border:1px solid var(--rule);border-radius:4px;overflow:hidden}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--rule2)}
th{font-size:12.5px;color:var(--ink2);background:rgba(220,207,184,.25);font-family:var(--f-mono)}
td.num{font-family:var(--f-mono)}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
/* nav drawer menu */
.drawer-btn{background:none;border:none;font-size:21px;color:var(--ink);cursor:pointer;
padding:6px 10px;min-width:44px;min-height:44px;line-height:1;margin-left:-12px}
.drawer-btn:active{color:var(--red)}
.scrim{position:fixed;inset:0;background:rgba(30,20,10,.45);z-index:40;display:none}
.scrim.open{display:block}
.drawer{position:fixed;top:0;left:0;bottom:0;width:272px;max-width:82vw;background:var(--surface);
z-index:50;transform:translateX(-106%);transition:transform .25s ease;
box-shadow:4px 0 18px rgba(0,0,0,.18);padding:20px 18px 28px;overflow-y:auto}
.drawer.open{transform:none}
.drawer .d-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:4px}
.drawer .d-brand{font-family:var(--f-display);font-weight:900;font-size:16px}
.drawer .d-close{background:none;border:none;font-size:20px;color:var(--ink3);cursor:pointer;
min-width:44px;min-height:44px}
.drawer h4{font-family:var(--f-mono);font-size:11.5px;letter-spacing:2px;color:var(--ink3);
margin:20px 0 4px}
.drawer .row{display:flex;align-items:center;width:100%;text-align:left;background:none;border:none;
font-family:var(--f-body);font-size:16px;color:var(--ink);padding:13px 8px;cursor:pointer;
text-decoration:none;border-bottom:1px solid var(--rule2);min-height:44px}
.drawer .row.active{color:var(--red);font-weight:700}
.drawer .row .arr{margin-left:auto;color:var(--ink3)}
.tabpane{display:none}
.tabpane.active{display:block;animation:fadein .25s}
@keyframes fadein{from{opacity:0}to{opacity:1}}
/* hub */
.dest-card{display:block;background:var(--surface);border:1px solid var(--rule);border-radius:4px;
padding:18px;margin-bottom:18px;text-decoration:none;color:var(--ink);position:relative;box-shadow:0 1px 0 var(--rule)}
.dest-card .go{position:absolute;right:16px;top:50%;transform:translateY(-50%);color:var(--blue);font-size:22px}
.dest-card h3{font-family:var(--f-display);font-size:20px;font-weight:900}
.dest-card .route{font-family:var(--f-mono);font-size:13px;color:var(--ink2);margin:4px 0}
.dest-card .best{font-family:var(--f-mono);font-size:15px;margin-top:8px}
.dest-card .best b{font-size:20px}
.soon{border:1.5px dashed var(--rule);border-radius:4px;padding:18px;text-align:center;color:var(--ink3);font-size:14px}
.foot{margin-top:36px;font-size:12.5px;color:var(--ink3);border-top:1px solid var(--rule);padding-top:12px}
@media(prefers-color-scheme:dark){
:root{--bg:#231D17;--surface:#2D261F;--kraft:#120E0B;
--ink:#EDE3CF;--ink2:#BDAF99;--ink3:#8C7E6A;
--rule:#43392E;--rule2:#352C24;--dot:rgba(237,227,207,.08);
--red:#EE8672;--red-soft:#45261F;
--blue:#A2B9EA;--blue-soft:#2A2F40;
--green:#86C3A2;--plum:#D29BD0;
--now:#6A5812;--now-ink:#FBE58A;
--cover-ink:#EDE3CF;color-scheme:dark}
body{background-image:radial-gradient(var(--dot) 1.1px,transparent 1.1px)}
.nav{background:rgba(35,29,23,.88)}
.btn{background:var(--blue-soft);color:var(--blue)}.btn:hover{filter:brightness(1.12)}
.badge.ok{background:rgba(134,195,162,.1)}
.hl{color:var(--now-ink)}
}
"""

COMBO_SHORT = {"return_20270302": "R"}
COMBO_LABELS = {"return_20270302": "3/2 回程單程"}
ACTIVE_SHORTS = ["R"]
SERIES_COLORS = {"A": "#2B4A86", "B": "#B3301F", "C": "#2F6B4F", "D": "#B98F63",
                 "R": "#2B4A86"}
TAPE_COLORS = ["rgba(224,178,74,.62)", "rgba(219,154,149,.62)",
               "rgba(157,181,146,.62)", "rgba(162,185,234,.55)"]


def fmt(n):
    return f"{n:,}"


def load_dest(d):
    watch = json.load(open(os.path.join(HOME, d["watch"])))
    hist = json.load(open(os.path.join(HOME, d["history"])))
    return watch, hist["history"]


def ticket_card(combo_key, v, delta, pct, link, tape_color, badge_html, rows_html,
                 first_run=False):
    if first_run:
        delta_html = '<div class="t-delta">新規格首日・首次記錄</div>'
    else:
        cls = "down" if delta < 0 else ("up" if delta > 0 else "")
        arrow = "▼" if delta < 0 else ("▲" if delta > 0 else "－")
        delta_html = (f'<div class="t-delta {cls}">{arrow} {fmt(abs(delta))}'
                      f'（{pct:+.1f}%）vs 昨日</div>')
    return f"""
<div class="ticket">
  <div class="tape" style="background:{tape_color}"></div>
  <div class="t-in">
    <div class="t-route"><span class="t-combo">{COMBO_LABELS[combo_key]}</span>
    <span class="t-id">{COMBO_SHORT[combo_key]}</span></div>
    <div class="t-price">NT$ {fmt(v['twd'])}{badge_html}</div>
    {delta_html}
    {rows_html}
  </div>
  <div class="t-perf"></div>
  <div class="t-foot"><span class="src">{v.get('source', '')}</span>
  <a class="btn" href="{link}" target="_blank" rel="noopener">訂票 ✈</a></div>
</div>"""


def dest_page(d, dests):
    watch, history = load_dest(d)
    fx = watch.get("fx_usd_twd", 0)
    checked = watch.get("checked_at", "")
    try:
        dt = datetime.fromisoformat(checked)
        date_str = f"{dt.year} 年 {dt.month} 月 {dt.day} 日"
    except Exception:
        date_str = checked
    prev = watch.get("previous_baselines_twd", {})
    links = watch.get("booking_links", {})
    part2 = watch.get("part2_true_totals_twd", {})

    focus_items = []
    for k, v in watch["baselines"].items():
        p = prev.get(k)
        if not p:
            continue
        dd = v["twd"] - p
        pct = dd / p * 100
        if dd < 0 and (pct <= -5 or dd <= -50 * fx):
            focus_items.append(
                f"<strong>{COMBO_LABELS[k]} {v['airline']} NT$ {fmt(v['twd'])}</strong>"
                f"，下跌 NT$ {fmt(-dd)}（{pct:.1f}%）")
    if focus_items:
        focus_html = "；".join(focus_items) + "。"
    else:
        ck, cv = min(watch["baselines"].items(), key=lambda kv: kv[1]["twd"])
        if prev:
            focus_html = (f"今日回程單程含行李最低價整體持平，無值得注意的降價。"
                          f"目前最低為 <span class='hl'>{COMBO_LABELS[ck]} {cv['airline']} NT$ {fmt(cv['twd'])}</span>。")
        else:
            focus_html = (f"今日起改為只追蹤 3/2 回程單程（NRT → TPE），新規格首日。"
                          f"含行李直飛最低價為 <span class='hl'>{COMBO_LABELS[ck]} {cv['airline']} NT$ {fmt(cv['twd'])}</span>。")

    def flight_line(v):
        fl = v.get("flight") or v.get("out", "")
        ret = v.get("ret", "")
        return f"{fl} / {ret}" if ret else fl

    cards1 = []
    sk_blocked = watch.get("skyscanner_blocked", False)
    for i, k in enumerate(COMBO_LABELS):
        v = watch["baselines"][k]
        p = prev.get(k, v["twd"])
        dd = v["twd"] - p
        pct = dd / p * 100 if p else 0
        badge = ""
        if dd < 0 and (pct <= -5 or dd <= -50 * fx):
            badge = '<span class="badge">值得注意</span>'
        rows = (f"<div class='t-meta'><div><span class='k'>航空</span>{v['airline']}</div>"
                f"<div><span class='k'>航班</span>{flight_line(v)}</div>"
                f"<div><span class='k'>托運行李</span>{v.get('bags', '')}</div></div>")
        lk = links.get(k, {})
        book_link = lk.get("google_flights_A", "#") if sk_blocked and lk.get("google_flights_A") else lk.get("skyscanner_search", "#")
        cards1.append(ticket_card(k, v, dd, pct, book_link,
                                 TAPE_COLORS[i % 4], badge, rows, first_run=not prev.get(k)))

    cards2 = []
    for i, k in enumerate(COMBO_LABELS):
        v = part2.get(k, {})
        total = v.get("true_total_twd")
        total_txt = f"NT$ {fmt(total)}" if total else (v.get("true_total_note") or "無法完整計算")
        vv = {"twd": v.get("fare_twd", 0), "source": v.get("source", "")}
        rows = (f"<div class='t-meta'><div><span class='k'>組合</span>{v.get('airline', '')}</div>"
                f"<div><span class='k'>航班</span>{flight_line(v)}</div>"
                f"<div><span class='k'>加購行李</span>{v.get('bag_fee_note', '')}</div>"
                f"<div><span class='k'>真實總價</span><strong>{total_txt}</strong></div></div>")
        cards2.append(ticket_card(k, vv, 0, 0, links.get(k, {}).get("google_flights_B", "#"),
                                 TAPE_COLORS[(i + 2) % 4], "", rows))

    labels = [h["date"][5:].replace("-", "/") for h in history]
    datasets = [{"label": f"{key} {COMBO_LABELS[[kk for kk, vv in COMBO_SHORT.items() if vv == key][0]]}",
                 "data": [h.get(key) for h in history],
                 "borderColor": SERIES_COLORS[key], "backgroundColor": SERIES_COLORS[key],
                 "tension": 0.25, "pointRadius": 3} for key in ACTIVE_SHORTS]
    airlines_map = {h["date"]: h.get("airlines", {}) for h in history}

    arows = []
    for key in ACTIVE_SHORTS:
        prices = [h[key] for h in history if key in h]
        if not prices:
            arows.append(
                f"<tr><td><span class='dot' style='background:{SERIES_COLORS[key]}'></span>{key}</td>"
                f"<td class='num'>—</td><td class='num'>—</td><td>尚無資料</td></tr>")
            continue
        low = min(prices)
        low_date = next(h["date"] for h in history if h.get(key) == low)
        chg = (prices[-1] - prices[0]) / prices[0] * 100
        trend = "上漲" if chg > 1 else ("下跌" if chg < -1 else "持平")
        cls = "up" if chg > 1 else ("down" if chg < -1 else "")
        arows.append(
            f"<tr><td><span class='dot' style='background:{SERIES_COLORS[key]}'></span>{key}</td>"
            f"<td class='num'>NT$ {fmt(prices[-1])}</td>"
            f"<td class='num'>NT$ {fmt(low)}（{low_date[5:].replace('-', '/')}）</td>"
            f"<td class='{cls}'>{trend} {chg:+.1f}%</td></tr>")

    chart_json = json.dumps({"labels": labels, "datasets": datasets}, ensure_ascii=False)
    airlines_json = json.dumps(airlines_map, ensure_ascii=False)
    dates_json = json.dumps([h["date"] for h in history], ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{d['name']}機票追蹤｜{d['route']}</title>
<link rel="stylesheet" href="{FONTS}">
{PWA_HEAD}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>{BASE_CSS}</style>
</head>
<body>
<nav class="nav"><div class="wrap">
<button class="drawer-btn" id="drawerBtn" aria-label="選單">☰</button>
<a class="brand" href="../"><span class="stamp-sm">TRACK</span>機票追蹤手帳</a>
<span class="crumb">/ {d['name']}</span>
<button class="install-btn" hidden>安裝 App</button>
</div></nav>
<div class="scrim" id="scrim"></div>
<aside class="drawer" id="drawer">
<div class="d-head"><span class="d-brand">機票追蹤手帳</span>
<button class="d-close" id="drawerClose" aria-label="關閉">✕</button></div>
<h4>檢視 VIEW</h4>
<button class="row active" data-tab="prices">今日比價</button>
<button class="row" data-tab="trend">走勢分析</button>
</aside>
<div class="wrap">
<div class="hero">
<div class="stamp">{d['code']}</div>
<h1>{d['name']}機票追蹤</h1>
<div class="sub">{d['route']}・1 位成人・經濟艙・直飛・{date_str}更新</div>
<div class="sub">{d.get('desc', '')}</div>
</div>

<div class="tabpane active" id="tab-prices">
<div class="sec"><div class="sec-h"><h2>今日焦點</h2><span class="en">FOCUS</span></div>
<div class="ticket"><div class="tape" style="background:rgba(242,220,93,.7)"></div>
<div class="t-in" style="font-size:14px">{focus_html}</div></div></div>

<div class="sec"><div class="sec-h"><h2>含行李直飛最低價</h2><span class="en">WITH BAGGAGE</span></div>
{''.join(cards1)}</div>

<div class="sec"><div class="sec-h"><h2>無行李＋官網加購</h2><span class="en">NO BAG + ADD-ON</span></div>
{''.join(cards2)}</div>
<div class="note">部分航空公司線上預購行李費官方未公開，真實總價無法完整計算，詳見各票根說明。</div>
</div>

<div class="tabpane" id="tab-trend">
<div class="sec"><div class="sec-h"><h2>價格走勢</h2><span class="en">TREND</span></div>
<div class="chart-card"><div class="chart-wrap"><canvas id="trend"></canvas></div></div>
<div class="note">點擊圖例可篩選日期組合。每日含行李直飛最低價（NT$）。</div></div>

<div class="sec"><div class="sec-h"><h2>漲跌分析</h2><span class="en">ANALYSIS</span></div>
<table><tr><th>組合</th><th>今日</th><th>歷史低點</th><th>期間走勢</th></tr>
{''.join(arows)}</table></div>
</div>

<div class="foot">資料來源：Google Flights、Skyscanner 台灣（瀏覽器實際查詢）・價格為選定航班後的實際總價・僅供參考，實際以訂票頁面為準・每日自動更新</div>
</div>
<script>
const chartData = {chart_json};
const airlines = {airlines_json};
const dates = {dates_json};
let trendChart = null;
function initTrend() {{
trendChart = new Chart(document.getElementById('trend'), {{
  type: 'line',
  data: chartData,
  options: {{
    responsive: true, maintainAspectRatio: false,
    interaction: {{mode: 'index', intersect: false}},
    plugins: {{
      legend: {{position: 'bottom', labels: {{font: {{family: "'Courier Prime', monospace"}}}},
        onClick: (e, li, leg) => {{
          const m = leg.chart.getDatasetMeta(li.datasetIndex);
          m.hidden = !m.hidden; leg.chart.update();
        }}}},
      tooltip: {{callbacks: {{
        label: (c) => ` ${{c.dataset.label}}: NT$ ${{c.parsed.y.toLocaleString()}}`,
        afterBody: (items) => {{
          const al = airlines[dates[items[0].dataIndex]] || {{}};
          return Object.entries(al).map(([k, v]) => ` ${{k}}: ${{v}}`);
        }}
      }}}}
    }},
    scales: {{
      x: {{ticks: {{font: {{family: "'Courier Prime', monospace", size: 11}}}}}},
      y: {{ticks: {{callback: v => 'NT$' + (v/1000).toFixed(0) + 'k',
        font: {{family: "'Courier Prime', monospace", size: 11}}}}}}
    }}
  }}
}});
}}
const drawer = document.getElementById('drawer');
const scrim = document.getElementById('scrim');
function closeDrawer() {{
  drawer.classList.remove('open');
  scrim.classList.remove('open');
}}
document.getElementById('drawerBtn').addEventListener('click', function() {{
  drawer.classList.add('open');
  scrim.classList.add('open');
}});
document.getElementById('drawerClose').addEventListener('click', closeDrawer);
scrim.addEventListener('click', closeDrawer);
drawer.querySelectorAll('[data-tab]').forEach(function(btn) {{
  btn.addEventListener('click', function() {{
    drawer.querySelectorAll('[data-tab]').forEach(function(b) {{ b.classList.remove('active'); }});
    document.querySelectorAll('.tabpane').forEach(function(p) {{ p.classList.remove('active'); }});
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'trend') {{
      if (!trendChart) initTrend(); else trendChart.resize();
    }}
    closeDrawer();
    window.scrollTo({{top: 0, behavior: 'smooth'}});
  }});
}});
</script>
</body>
</html>"""


def hub_page(dests):
    cards = []
    for d in dests:
        watch, history = load_dest(d)
        ck, cv = min(watch["baselines"].items(), key=lambda kv: kv[1]["twd"])
        all_prices = [h[s] for h in history for s in ACTIVE_SHORTS if s in h]
        low_txt = f"歷史低點 NT$ {fmt(min(all_prices))}" if all_prices else "新規格首日・尚無歷史低點"
        cards.append(f"""
<a class="dest-card" href="./{d['id']}/">
  <div class="tape" style="background:{d.get('theme_tape', 'rgba(224,178,74,.62)')}"></div>
  <h3>{d['name']}</h3>
  <div class="route">{d['route']}・{d.get('desc', '')}</div>
  <div class="best">今日最低 <b>NT$ {fmt(cv['twd'])}</b>（{COMBO_LABELS[ck]}）</div>
  <div class="route">{low_txt}・追蹤 {len(history)} 天</div>
  <span class="go">→</span>
</a>""")
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>機票追蹤手帳</title>
<link rel="stylesheet" href="{FONTS}">
{PWA_HEAD}
<style>{BASE_CSS}
.cover{{background:var(--kraft);border-radius:8px;padding:34px 24px;text-align:center;color:var(--cover-ink);
position:relative;overflow:hidden;margin:26px 0 8px;box-shadow:0 2px 6px rgba(0,0,0,.15)}}
.cover::after{{content:'';position:absolute;top:0;bottom:0;right:34px;width:14px;background:#1c1c1e;opacity:.85}}
.cover h1{{font-family:var(--f-display);font-weight:900;font-size:clamp(30px,8vw,44px);letter-spacing:6px}}
.cover p{{font-size:14px;margin-top:8px;opacity:.8}}
</style>
</head>
<body>
<nav class="nav"><div class="wrap">
<a class="brand" href="./"><span class="stamp-sm">TRACK</span>機票追蹤手帳</a>
<button class="install-btn" hidden>安裝 App</button>
</div></nav>
<div class="wrap">
<div class="cover"><h1>機票追蹤手帳</h1><p>FLIGHT PRICE JOURNAL・每日比價・漲跌全紀錄</p></div>

<div class="sec"><div class="sec-h"><h2>追蹤中的航線</h2><span class="en">ROUTES</span></div>
{''.join(cards)}
<div class="soon">更多航線即將加入…</div>
</div>

<div class="foot">每天自動更新・價格為瀏覽器實際查詢的選定航班總價（NT$）・僅供參考</div>
</div>
</body>
</html>"""


SW_TEMPLATE = """/* flight-tracker service worker (generated {stamp}) */
const CACHE = 'flight-tracker-{stamp}';
const ASSETS = [
  '/flight-tracker/',
  '/flight-tracker/tokyo/',
  '/flight-tracker/manifest.json',
  '/flight-tracker/icons/icon-192.png',
  '/flight-tracker/icons/icon-512.png',
];

self.addEventListener('install', (e) => {{
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
}});

self.addEventListener('activate', (e) => {{
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
}});

self.addEventListener('fetch', (e) => {{
  if (e.request.method !== 'GET') return;
  // Page navigations: network-first so the installed app always opens fresh prices.
  if (e.request.mode === 'navigate' || e.request.destination === 'document') {{
    e.respondWith(
      fetch(e.request).then((res) => {{
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      }}).catch(() => caches.match(e.request))
    );
    return;
  }}
  // Static assets: cache-first with background refresh.
  e.respondWith(
    caches.match(e.request).then((hit) => {{
      const net = fetch(e.request).then((res) => {{
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      }}).catch(() => hit);
      return hit || net;
    }})
  );
}});
"""


def main():
    dests = json.load(open(os.path.join(HERE, "destinations.json")))
    for d in dests:
        # resolve ~ in paths
        d["watch"] = os.path.expanduser(d["watch"])
        d["history"] = os.path.expanduser(d["history"])
        outdir = os.path.join(HERE, d["id"])
        os.makedirs(outdir, exist_ok=True)
        html = dest_page(d, dests)
        with open(os.path.join(outdir, "index.html"), "w") as f:
            f.write(html)
        print(f"wrote {d['id']}/index.html ({len(html)} bytes)")
    with open(os.path.join(HERE, "index.html"), "w") as f:
        hub = hub_page(dests)
        f.write(hub)
    print(f"wrote index.html ({len(hub)} bytes)")
    stamp = datetime.now().strftime("%Y%m%d")
    with open(os.path.join(HERE, "sw.js"), "w") as f:
        f.write(SW_TEMPLATE.format(stamp=stamp))
    print(f"wrote sw.js (cache {stamp})")


if __name__ == "__main__":
    main()
