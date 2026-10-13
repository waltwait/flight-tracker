#!/usr/bin/env python3
"""Generate the flight-tracker dashboard index.html from the daily watch state.

Reads:
  ~/workspace/goals/goal-2/hidden_files/travel/flight-watch.json
  ~/workspace/goals/goal-2/hidden_files/travel/price-history.json
Writes:
  index.html (in this repo directory)
"""
import json
import os
from datetime import datetime

HOME = os.path.expanduser("~")
WATCH = os.path.join(HOME, "workspace/goals/goal-2/hidden_files/travel/flight-watch.json")
HIST = os.path.join(HOME, "workspace/goals/goal-2/hidden_files/travel/price-history.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

COMBO_LABELS = {
    "20270225_20270302": "2/25 → 3/2",
    "20270225_20270303": "2/25 → 3/3",
    "20270226_20270302": "2/26 → 3/2",
    "20270226_20270303": "2/26 → 3/3",
}
COMBO_SHORT = {"20270225_20270302": "A", "20270225_20270303": "B",
               "20270226_20270302": "C", "20270226_20270303": "D"}
COLORS = {"A": "#0b5fff", "B": "#e8a100", "C": "#0a7d3b", "D": "#c0392b"}


def fmt(n):
    return f"{n:,}"


def main():
    watch = json.load(open(WATCH))
    hist = json.load(open(HIST))
    history = hist["history"]
    fx = watch.get("fx_usd_twd", 0)
    checked = watch.get("checked_at", "")
    try:
        dt = datetime.fromisoformat(checked)
        date_str = f"{dt.year} 年 {dt.month} 月 {dt.day} 日"
        date_iso = dt.strftime("%Y-%m-%d")
    except Exception:
        date_str, date_iso = checked, checked
    prev = watch.get("previous_baselines_twd", {})
    links = watch.get("booking_links", {})
    part2 = watch.get("part2_true_totals_twd", {})

    # ---- focus: noteworthy drops ----
    focus_items = []
    for k, v in watch["baselines"].items():
        p = prev.get(k)
        if not p:
            continue
        d = v["twd"] - p
        pct = d / p * 100
        if d < 0 and (pct <= -5 or d <= -50 * fx):
            focus_items.append(
                f"<strong>{COMBO_LABELS[k]} {v['airline']} NT${fmt(v['twd'])}</strong>"
                f"，下跌 NT${fmt(-d)}（{pct:.1f}%）⚠️值得注意"
            )
    if focus_items:
        focus_html = "；".join(focus_items) + "。"
    else:
        # fallback: highlight cheapest combo
        cheapest = min(watch["baselines"].items(), key=lambda kv: kv[1]["twd"])
        ck, cv = cheapest
        focus_html = (
            f"今日四組含行李最低價皆小漲，無值得注意的降價。"
            f"整體最低為 <strong>{COMBO_LABELS[ck]} {cv['airline']} NT${fmt(cv['twd'])}</strong>。"
        )

    # ---- part 1 cards ----
    p1_cards = []
    for k in COMBO_LABELS:
        v = watch["baselines"][k]
        p = prev.get(k, v["twd"])
        d = v["twd"] - p
        cls = "down" if d < 0 else ("up" if d > 0 else "")
        arrow = "▼" if d < 0 else ("▲" if d > 0 else "－")
        pct = d / p * 100 if p else 0
        badge = ""
        if d < 0 and (pct <= -5 or d <= -50 * fx):
            badge = '<span class="badge low">值得注意</span>'
        link = links.get(k, {}).get("skyscanner_search", "#")
        p1_cards.append(f"""
      <div class="card">
        <div class="card-head">{COMBO_LABELS[k]}<span class="combo-id">{COMBO_SHORT[k]}</span></div>
        <div class="price">NT${fmt(v['twd'])}{badge}</div>
        <div class="delta {cls}">{arrow} {fmt(abs(d))}（{pct:+.1f}%）vs 昨日</div>
        <div class="detail"><span>航空</span>{v['airline']}</div>
        <div class="detail"><span>航班</span>{v.get('out', '')} / {v.get('ret', '')}</div>
        <div class="detail"><span>托運行李</span>{v.get('bags', '')}</div>
        <div class="detail"><span>來源</span>{v.get('source', '')}</div>
        <a class="book" href="{link}" target="_blank" rel="noopener">訂票</a>
      </div>""")

    # ---- part 2 cards ----
    p2_cards = []
    for k in COMBO_LABELS:
        v = part2.get(k, {})
        total = v.get("true_total_twd")
        total_txt = f"NT${fmt(total)}" if total else (v.get("true_total_note") or "無法完整計算")
        link = links.get(k, {}).get("google_flights_B", "#")
        p2_cards.append(f"""
      <div class="card">
        <div class="card-head">{COMBO_LABELS[k]}<span class="combo-id">{COMBO_SHORT[k]}</span></div>
        <div class="price">NT${fmt(v.get('fare_twd', 0))}</div>
        <div class="detail"><span>組合</span>{v.get('airline', '')}</div>
        <div class="detail"><span>航班</span>{v.get('out', '')} / {v.get('ret', '')}</div>
        <div class="detail"><span>加購行李</span>{v.get('bag_fee_note', '')}</div>
        <div class="detail"><span>真實總價</span><strong>{total_txt}</strong></div>
        <a class="book" href="{link}" target="_blank" rel="noopener">訂票</a>
      </div>""")

    # ---- chart data ----
    labels = [h["date"][5:].replace("-", "/") for h in history]
    datasets = []
    for key in ["A", "B", "C", "D"]:
        datasets.append({
            "label": f"{key} {COMBO_LABELS[[kk for kk, vv in COMBO_SHORT.items() if vv == key][0]]}",
            "data": [h[key] for h in history],
            "borderColor": COLORS[key],
            "backgroundColor": COLORS[key],
            "tension": 0.25,
            "pointRadius": 3,
        })
    # airlines per point for tooltip
    airlines_map = {h["date"]: h.get("airlines", {}) for h in history}

    # ---- analysis ----
    analysis_rows = []
    for key in ["A", "B", "C", "D"]:
        prices = [h[key] for h in history]
        low = min(prices)
        low_i = prices.index(low)
        chg = (prices[-1] - prices[0]) / prices[0] * 100
        trend = "上漲" if chg > 1 else ("下跌" if chg < -1 else "持平")
        analysis_rows.append(f"""
        <tr><td><span class="dot" style="background:{COLORS[key]}"></span>{key}</td>
        <td>NT${fmt(prices[-1])}</td><td>NT${fmt(low)}（{history[low_i]['date'][5:].replace('-', '/')}）</td>
        <td class="{'up' if chg > 1 else ('down' if chg < -1 else '')}">{trend} {chg:+.1f}%</td></tr>""")

    chart_json = json.dumps({"labels": labels, "datasets": datasets}, ensure_ascii=False)
    airlines_json = json.dumps(airlines_map, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>機票追蹤｜東京 TPE⇄NRT 每日比價</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;color:#1a1a1a;background:#f7f7f5;padding:12px 8px;line-height:1.6;font-size:15px;-webkit-text-size-adjust:100%}}
.page{{max-width:900px;margin:0 auto;background:#fff;border-radius:10px;padding:20px 16px;box-shadow:0 2px 12px rgba(0,0,0,.06)}}
h1{{font-size:20px;margin-bottom:4px}}
.meta{{color:#666;font-size:12.5px;margin-bottom:16px}}
.alert{{background:#fff8e6;border:1px solid #f0d77b;border-radius:8px;padding:14px 16px;margin-bottom:18px;font-size:13.5px}}
.alert .tag{{display:inline-block;background:#e8a100;color:#fff;font-size:12px;border-radius:4px;padding:1px 8px;margin-right:6px}}
h2{{font-size:16px;margin:22px 0 10px;padding-bottom:6px;border-bottom:2px solid #1a1a1a}}
.cards{{display:grid;grid-template-columns:1fr;gap:12px}}
.card{{border:1px solid #e8e8e8;border-radius:10px;padding:14px;box-shadow:0 1px 4px rgba(0,0,0,.04)}}
.card-head{{font-weight:700;font-size:15px;margin-bottom:6px}}
.combo-id{{display:inline-block;background:#eee;border-radius:4px;font-size:11px;padding:0 6px;margin-left:6px;color:#555}}
.price{{font-weight:700;font-size:22px;margin:2px 0}}
.delta{{font-size:13px;margin-bottom:8px}}
.down{{color:#0a7d3b}}.up{{color:#c0392b}}
.detail{{font-size:13px;color:#444;margin:3px 0}}
.detail span{{display:inline-block;min-width:64px;color:#999;font-size:12px}}
.book{{display:inline-block;background:#0b5fff;color:#fff!important;border-radius:8px;padding:10px 28px;font-size:15px;font-weight:600;margin-top:8px;text-decoration:none}}
.badge{{display:inline-block;font-size:11px;border-radius:4px;padding:1px 7px;margin-left:6px;background:#e7f6ec;color:#0a7d3b;border:1px solid #bfe6cc}}
.chart-wrap{{position:relative;height:300px;margin-top:6px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{text-align:left;padding:8px 6px;border-bottom:1px solid #eee}}
th{{color:#666;font-size:12px}}
.dot{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}}
.note{{font-size:12px;color:#888;margin-top:8px}}
.foot{{margin-top:22px;font-size:12px;color:#999;border-top:1px solid #eee;padding-top:12px}}
@media(min-width:720px){{.cards{{grid-template-columns:1fr 1fr}}body{{padding:24px 16px}}.page{{padding:28px 32px}}h1{{font-size:24px}}}}
</style>
</head>
<body>
<div class="page">
<h1>✈️ 東京機票每日比價</h1>
<div class="meta">{date_str}・台北桃園 (TPE) ⇄ 東京成田 (NRT)・1 位成人・經濟艙・直飛・查詢時間 {checked[11:16] if len(checked) > 16 else ''}・匯率 USD/TWD {fx}</div>
<div class="alert"><span class="tag">今日焦點</span>{focus_html}</div>

<h2>一、含行李直飛最低價</h2>
<div class="cards">{''.join(p1_cards)}</div>

<h2>二、無行李票價＋官網加購行李</h2>
<div class="cards">{''.join(p2_cards)}</div>
<div class="note">註：部分航空公司線上預購行李費官方未公開，真實總價無法完整計算，詳見各卡說明。</div>

<h2>三、價格走勢（{history[0]['date']} 起）</h2>
<div class="chart-wrap"><canvas id="trend"></canvas></div>
<div class="note">點擊圖例可篩選日期組合。價格為每日含行李直飛最低價（NT$）。</div>

<h2>四、漲跌分析</h2>
<table>
<tr><th>組合</th><th>今日</th><th>歷史低點</th><th>期間走勢</th></tr>
{''.join(analysis_rows)}
</table>

<div class="foot">資料來源：Google Flights、Skyscanner 台灣（瀏覽器實際查詢）・價格為選定去回程後的實際總價・僅供參考，實際以訂票頁面為準・每日自動更新</div>
</div>
<script>
const chartData = {chart_json};
const airlines = {airlines_json};
const dates = {json.dumps([h["date"] for h in history], ensure_ascii=False)};
new Chart(document.getElementById('trend'), {{
  type: 'line',
  data: chartData,
  options: {{
    responsive: true, maintainAspectRatio: false,
    interaction: {{mode: 'index', intersect: false}},
    plugins: {{
      legend: {{position: 'bottom', onClick: (e, li, leg) => {{
        const i = li.datasetIndex;
        const meta = leg.chart.getDatasetMeta(i);
        meta.hidden = !meta.hidden;
        leg.chart.update();
      }}}},
      tooltip: {{callbacks: {{
        label: (c) => ` ${{c.dataset.label}}: NT$${{c.parsed.y.toLocaleString()}}`,
        afterBody: (items) => {{
          const d = dates[items[0].dataIndex];
          const al = airlines[d] || {{}};
          return Object.entries(al).map(([k, v]) => ` ${{k}}: ${{v}}`);
        }}
      }}}}
    }},
    scales: {{y: {{ticks: {{callback: v => 'NT$' + (v/1000) + 'k'}}}}}}
  }}
}});
</script>
</body>
</html>"""
    open(OUT, "w").write(html)
    print(f"wrote {OUT} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
