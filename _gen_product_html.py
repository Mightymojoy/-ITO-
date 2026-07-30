# -*- coding: utf-8 -*-
import json
import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r'E:\电商渠道业绩看板'

# 加载JSON数据
with open(os.path.join(BASE, 'luggage_daily.json'), 'r', encoding='utf-8') as f:
    luggage = json.load(f)
with open(os.path.join(BASE, 'bag_daily.json'), 'r', encoding='utf-8') as f:
    bag = json.load(f)
with open(os.path.join(BASE, 'all_series_daily.json'), 'r', encoding='utf-8') as f:
    all_series_data = json.load(f)
with open(os.path.join(BASE, 'audience_daily.json'), 'r', encoding='utf-8') as f:
    audience_data = json.load(f)
with open(os.path.join(BASE, 'luggage_audience_x_series.json'), 'r', encoding='utf-8') as f:
    cross_data = json.load(f)
with open(os.path.join(BASE, 'luggage_audience_daily.json'), 'r', encoding='utf-8') as f:
    lug_audience_data = json.load(f)
with open(os.path.join(BASE, 'bag_audience_daily.json'), 'r', encoding='utf-8') as f:
    bag_audience_data = json.load(f)
with open(os.path.join(BASE, 'bag_audience_x_series.json'), 'r', encoding='utf-8') as f:
    bag_cross_data = json.load(f)
with open(os.path.join(BASE, 'color_daily.json'), 'r', encoding='utf-8') as f:
    color_data = json.load(f)
with open(os.path.join(BASE, 'size_daily.json'), 'r', encoding='utf-8') as f:
    size_data = json.load(f)
with open(os.path.join(BASE, 'luggage_color_daily.json'), 'r', encoding='utf-8') as f:
    lug_color_data = json.load(f)
with open(os.path.join(BASE, 'luggage_size_daily.json'), 'r', encoding='utf-8') as f:
    lug_size_data = json.load(f)
with open(os.path.join(BASE, 'bag_color_daily.json'), 'r', encoding='utf-8') as f:
    bag_color_data = json.load(f)
with open(os.path.join(BASE, 'bag_size_daily.json'), 'r', encoding='utf-8') as f:
    bag_size_data = json.load(f)
# ===== 退货数据（2026-07-30 新增） =====
with open(os.path.join(BASE, 'return_daily.json'), 'r', encoding='utf-8') as f:
    ret_all_data = json.load(f)
with open(os.path.join(BASE, 'luggage_return_daily.json'), 'r', encoding='utf-8') as f:
    ret_lug_data = json.load(f)
with open(os.path.join(BASE, 'bag_return_daily.json'), 'r', encoding='utf-8') as f:
    ret_bag_data = json.load(f)

# ===== SKU数据：从sku_daily.json压缩为紧凑格式 =====
print('  处理SKU数据...')
with open(os.path.join(BASE, 'sku_daily.json'), 'r', encoding='utf-8') as f:
    raw_sku = json.load(f)
# 全渠道SKU汇总（不区分渠道）
sku_summary = {}
sku_compact = {}
# 按渠道SKU汇总（渠道维度）
sku_ch_summary = {}  # [series][channel][sku_key] = {amt, qty}
sku_ch_daily = {}    # [date][channel][sku_key] = {amt, qty}
CHANNEL_LIST = raw_sku['meta'].get('channels', [])

for date_str, day_data in raw_sku['daily'].items():
    comp_day = {}
    ch_day = {}
    for ch_name, ch_data in day_data.items():
        if ch_name in ('$total',):
            continue
        if ch_name not in ch_day:
            ch_day[ch_name] = {}
        for sku_key, vals in ch_data.items():
            if sku_key in ('$total','amt','qty'):
                continue
            a = vals.get('amt', 0) or 0
            q = vals.get('qty', 0) or 0
            if a == 0 and q == 0:
                continue
            # 全渠道汇总
            if sku_key not in sku_summary:
                sku_summary[sku_key] = {'amt': 0, 'qty': 0}
            sku_summary[sku_key]['amt'] += a
            sku_summary[sku_key]['qty'] += q
            if sku_key not in comp_day:
                comp_day[sku_key] = {'amt': 0, 'qty': 0}
            comp_day[sku_key]['amt'] += a
            comp_day[sku_key]['qty'] += q
            # 按渠道汇总
            ch_day[ch_name][sku_key] = {'amt': a, 'qty': q}
            # 渠道级长期汇总
            parts = sku_key.split('|', 2)
            series = parts[0] if len(parts) > 0 else ''
            if series not in sku_ch_summary:
                sku_ch_summary[series] = {}
            if ch_name not in sku_ch_summary[series]:
                sku_ch_summary[series][ch_name] = {}
            if sku_key not in sku_ch_summary[series][ch_name]:
                sku_ch_summary[series][ch_name][sku_key] = {'amt': 0, 'qty': 0}
            sku_ch_summary[series][ch_name][sku_key]['amt'] += a
            sku_ch_summary[series][ch_name][sku_key]['qty'] += q
    if comp_day:
        sku_compact[date_str] = comp_day
    if ch_day:
        sku_ch_daily[date_str] = ch_day

sku_by_series = {}
for sku_key, vals in sku_summary.items():
    parts = sku_key.split('|', 2)
    series = parts[0] if len(parts) > 0 else ''
    if series not in sku_by_series:
        sku_by_series[series] = {'skus': {}, 'total_amt': 0, 'total_qty': 0, 'is_luggage': False, 'is_bag': False}
    sku_by_series[series]['skus'][sku_key] = vals
    sku_by_series[series]['total_amt'] += vals['amt']
    sku_by_series[series]['total_qty'] += vals['qty']
# 标记品类
lug_series_set = set(luggage['meta'].get('series', []))
bag_series_set = set(bag['meta'].get('series', []))
for series_name in sku_by_series:
    if series_name in lug_series_set:
        sku_by_series[series_name]['is_luggage'] = True
    if series_name in bag_series_set:
        sku_by_series[series_name]['is_bag'] = True
# 确保每个系列有所有渠道
for series in sku_ch_summary:
    for ch in CHANNEL_LIST:
        if ch not in sku_ch_summary[series]:
            sku_ch_summary[series][ch] = {}

compressed_sku = {
    'meta': raw_sku['meta'],
    'summary': sku_summary,
    'daily': sku_compact,
    'ch_daily': sku_ch_daily,
    'ch_summary': sku_ch_summary,
    'by_series': sku_by_series
}
print(f'  SKU压缩: summary={len(sku_summary)}个, daily={len(sku_compact)}天, ch_daily={len(sku_ch_daily)}天, series_group={len(sku_by_series)}个')

luggage_json_str = json.dumps(luggage['daily'], ensure_ascii=False)
bag_json_str = json.dumps(bag['daily'], ensure_ascii=False)
all_json_str = json.dumps(all_series_data['daily'], ensure_ascii=False)
audience_json_str = json.dumps(audience_data['daily'], ensure_ascii=False)
cross_json_str = json.dumps(cross_data['daily'], ensure_ascii=False)
lug_aud_json_str = json.dumps(lug_audience_data['daily'], ensure_ascii=False)
bag_aud_json_str = json.dumps(bag_audience_data['daily'], ensure_ascii=False)
bag_cross_json_str = json.dumps(bag_cross_data['daily'], ensure_ascii=False)
color_json_str = json.dumps(color_data['daily'], ensure_ascii=False)
size_json_str = json.dumps(size_data['daily'], ensure_ascii=False)
lug_color_json_str = json.dumps(lug_color_data['daily'], ensure_ascii=False)
lug_size_json_str = json.dumps(lug_size_data['daily'], ensure_ascii=False)
bag_color_json_str = json.dumps(bag_color_data['daily'], ensure_ascii=False)
bag_size_json_str = json.dumps(bag_size_data['daily'], ensure_ascii=False)
# === 退货JSON（2026-07-30 新增） ===
ret_all_json_str = json.dumps(ret_all_data['daily'], ensure_ascii=False)
ret_lug_json_str = json.dumps(ret_lug_data['daily'], ensure_ascii=False)
ret_bag_json_str = json.dumps(ret_bag_data['daily'], ensure_ascii=False)

LUG_META = json.dumps(luggage['meta'], ensure_ascii=False)
BAG_META = json.dumps(bag['meta'], ensure_ascii=False)
ALL_META = json.dumps(all_series_data['meta'], ensure_ascii=False)
AUD_META = json.dumps(audience_data['meta'], ensure_ascii=False)
LUG_AUD_META = json.dumps(lug_audience_data['meta'], ensure_ascii=False)
BAG_AUD_META = json.dumps(bag_audience_data['meta'], ensure_ascii=False)

SERIES_LIST = all_series_data['meta']['series']
ALL_SERIES_LIST = all_series_data['meta']['series']
AUDIENCE_LIST = audience_data['meta'].get('audience', [])

# 系列品类映射
LUG_SERIES_SET = set(luggage['meta'].get('series', []))
BAG_SERIES_SET = set(bag['meta'].get('series', []))

html = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ITO产品分析看板</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://unpkg.com/lucide@latest"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
html,body{height:100vh;overflow:hidden;background:#f3f4f6;color:#1f2937}
.main-content{height:calc(100vh - 52px);overflow-y:auto}
/* 导航 */
.nav{background:#fff;border-bottom:1px solid #e5e7eb;display:flex;align-items:center;padding:0 20px;position:sticky;top:0;z-index:100;overflow-x:auto}
.nav .brand{font-weight:700;font-size:16px;color:#111827;padding:14px 12px 14px 0;margin-right:8px;white-space:nowrap;border-right:1px solid #e5e7eb}
.nav a{display:flex;align-items:center;gap:6px;padding:14px 16px;text-decoration:none;color:#6b7280;font-size:13px;white-space:nowrap;border-bottom:3px solid transparent;transition:all 0.2s}
.nav a:hover{color:#374151;background:#f9fafb}
.nav a.active{color:#2563eb;border-bottom-color:#2563eb;background:#eff6ff}
.nav a .icon{width:18px;height:18px}
/* 主内容 */
.container{max-width:1400px;margin:0 auto;padding:16px}
/* 筛选栏 */
.filters{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:16px;background:#fff;padding:12px 16px;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.filters label{font-size:12px;color:#6b7280;font-weight:500}
.filters input[type=date]{border:1px solid #d1d5db;border-radius:6px;padding:5px 10px;font-size:13px}
.filters select{border:1px solid #d1d5db;border-radius:6px;padding:5px 10px;font-size:13px;background:#fff}
.filters .metric-toggle{display:flex;background:#f3f4f6;border-radius:6px;overflow:hidden}
.filters .metric-toggle button{padding:5px 14px;border:none;background:transparent;font-size:12px;cursor:pointer;color:#6b7280}
.filters .metric-toggle button.active{background:#2563eb;color:#fff;border-radius:5px}
.channel-tags{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.channel-tags button{padding:4px 12px;border:1px solid #d1d5db;border-radius:14px;background:#fff;font-size:12px;cursor:pointer;color:#4b5563;transition:all .15s}
.channel-tags button.active{background:#2563eb;color:#fff;border-color:#2563eb}
.tab-content{display:none}
.tab-content.active{display:block}
/* KPI */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:16px}
.kpi-card{background:#fff;border-radius:10px;padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.kpi-card .label{font-size:11px;color:#6b7280;margin-bottom:4px}
.kpi-card .value{font-size:22px;font-weight:700;color:#111827}
.kpi-card .sub{font-size:11px;margin-top:4px}
.kpi-card .up{color:#059669}
.kpi-card .down{color:#dc2626}
/* 图表 */
.chart-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.chart-box{background:#fff;border-radius:10px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.chart-box canvas{max-height:360px;width:100%!important}
.chart-box.full{grid-column:1/-1}
.chart-box h3{font-size:13px;color:#374151;margin-bottom:10px;font-weight:600}
/* 可折叠表格 */
.collapse-wrap{background:#fff;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:14px;overflow:hidden}
.collapse-header{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;cursor:pointer;user-select:none;background:#f9fafb;transition:background .15s}
.collapse-header:hover{background:#f3f4f6}
.collapse-header h3{font-size:13px;color:#374151;font-weight:600;display:flex;align-items:center;gap:8px}
.collapse-header .arrow{font-size:14px;color:#9ca3af;transition:transform .2s;display:inline-block}
.collapse-header .arrow.open{transform:rotate(180deg)}
.collapse-body{overflow:hidden;max-height:0;transition:max-height .35s ease}
.collapse-body.open{max-height:10000px}
.collapse-body .table-wrap{overflow-x:auto;border-top:1px solid #e5e7eb}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:#fff;padding:10px 12px;text-align:right;font-weight:600;color:#374151;border-bottom:2px solid #e5e7eb;position:sticky;top:0}
th:first-child{text-align:left}
td{padding:9px 12px;text-align:right;border-bottom:1px solid #f3f4f6}
td:first-child{text-align:left;font-weight:500}
tr:hover{background:#f9fafb}
tr.section td{font-weight:600;background:#f3f4f6;color:#374151}
tr.summary td{font-weight:700;background:#eff6ff;border-top:2px solid #2563eb}
.collapse-ctrls{display:flex;gap:8px;align-items:center}
.collapse-ctrls button{padding:4px 10px;border:1px solid #d1d5db;border-radius:5px;background:#fff;font-size:11px;cursor:pointer;color:#4b5563}
.collapse-ctrls button:hover{background:#f3f4f6}
/* 占位 */
.placeholder{display:flex;align-items:center;justify-content:center;height:300px;background:#fff;border-radius:10px;color:#9ca3af;font-size:14px}
/* 数值高亮 */
.val-amt{color:#059669}
.val-qty{color:#2563eb}
</style>
</head>
<body>
<div class="main-content">
<!-- 导航 -->
<nav class="nav" id="nav"></nav>

<div class="container">

<!-- 筛选栏 -->
<div class="filters" id="filterBar"></div>
<div class="channel-tags" id="channelTags"></div>

<!-- ===== 行李箱总览 ===== -->
<div class="tab-content active" id="tab-luggage">
  <div class="kpi-grid" id="lugKpi"></div>
  <div class="chart-row">
    <div class="chart-box full"><h3>销售趋势 <small id="lugTrendLabel"></small></h3><canvas id="lugTrend"></canvas></div>
  </div>
  <div class="chart-row">
    <div class="chart-box"><h3>系列销售TOP <small id="lugSeriesLabel"></small></h3><canvas id="lugSeriesChart"></canvas></div>
    <div class="chart-box"><h3>各渠道销售额占比</h3><canvas id="lugPieChart"></canvas></div>
  </div>
  <!-- 可折叠系列明细 -->
  <div class="collapse-wrap" id="lugDetailCollapse">
    <div class="collapse-header" onclick="toggleCollapse('lugDetailBody')">
      <h3>📋 系列销售明细 <small id="lugDetailCount"></small></h3>
      <span class="arrow" id="lugDetailBodyArrow">▼</span>
    </div>
    <div class="collapse-body" id="lugDetailBody">
      <div class="table-wrap"><table><thead><tr id="lugDetailHead"><th>系列</th><th>销售额</th><th>销量</th><th>占比</th></tr></thead><tbody id="lugDetailBodyInner"></tbody></table></div>
    </div>
  </div>
</div>

<!-- ===== 包袋总览 ===== -->
<div class="tab-content" id="tab-bag">
  <div class="kpi-grid" id="bagKpi"></div>
  <div class="chart-row">
    <div class="chart-box full"><h3>销售趋势 <small id="bagTrendLabel"></small></h3><canvas id="bagTrend"></canvas></div>
  </div>
  <div class="chart-row">
    <div class="chart-box"><h3>系列销售TOP <small id="bagSeriesLabel"></small></h3><canvas id="bagSeriesChart"></canvas></div>
    <div class="chart-box"><h3>各渠道销售额占比</h3><canvas id="bagPieChart"></canvas></div>
  </div>
  <!-- 可折叠系列明细 -->
  <div class="collapse-wrap" id="bagDetailCollapse">
    <div class="collapse-header" onclick="toggleCollapse('bagDetailBody')">
      <h3>📋 系列销售明细 <small id="bagDetailCount"></small></h3>
      <span class="arrow" id="bagDetailBodyArrow">▼</span>
    </div>
    <div class="collapse-body" id="bagDetailBody">
      <div class="table-wrap"><table><thead><tr id="bagDetailHead"><th>系列</th><th>销售额</th><th>销量</th><th>占比</th></tr></thead><tbody id="bagDetailBodyInner"></tbody></table></div>
    </div>
  </div>
</div>

<!-- ===== 系列看板 ===== -->
<div class="tab-content" id="tab-series-detail">
  <div style="margin-bottom:12px;display:flex;gap:10px;align-items:center;background:#fff;padding:8px 16px;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.08)">
    <label style="font-size:12px;color:#6b7280;font-weight:500">品类</label>
    <select id="seriesCat" onchange="renderSeriesTab()" style="border:1px solid #d1d5db;border-radius:6px;padding:5px 10px;font-size:13px;background:#fff">
      <option value="all">全部</option><option value="luggage">行李箱</option><option value="bag">包袋</option>
    </select>
  </div>
  <div class="kpi-grid" id="seriesKpi"></div>
  <div id="seriesCardsContainer" style="display:flex;flex-direction:column;gap:10px;margin-bottom:14px"></div>
</div>

<!-- ===== 人群看板 ===== -->
<div class="tab-content" id="tab-audience">
  <div style="margin-bottom:12px;display:flex;gap:10px;align-items:center;background:#fff;padding:8px 16px;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.08)">
    <label style="font-size:12px;color:#6b7280;font-weight:500">品类</label>
    <select id="audCat" onchange="setAudCategory(this.value)" style="border:1px solid #d1d5db;border-radius:6px;padding:5px 10px;font-size:13px;background:#fff">
      <option value="all">全部</option><option value="luggage">行李箱</option><option value="bag">包袋</option>
    </select>
    <button onclick="renderAudience()" style="padding:5px 16px;background:#2563eb;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:12px">刷新</button>
  </div>
  <div class="kpi-grid" id="audKpi"></div>
  <div class="chart-row">
    <div class="chart-box full"><h3>各人群销售趋势 <small id="audTrendLabel"></small></h3><canvas id="audTrend"></canvas></div>
  </div>
  <div class="chart-row">
    <div class="chart-box"><h3>人群销售额占比</h3><canvas id="audPieChart"></canvas></div>
    <div class="chart-box"><h3>人群×系列 TOP</h3><canvas id="audSeriesChart"></canvas></div>
  </div>
</div>

<!-- ===== 尺寸看板 ===== -->
<div class="tab-content" id="tab-size">
  <div style="margin-bottom:12px;display:flex;gap:10px;align-items:center;background:#fff;padding:8px 16px;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.08)">
    <label style="font-size:12px;color:#6b7280;font-weight:500">品类</label>
    <select id="sizeCat" onchange="renderSize()" style="border:1px solid #d1d5db;border-radius:6px;padding:5px 10px;font-size:13px;background:#fff">
      <option value="all">全部</option><option value="luggage">行李箱</option><option value="bag">包袋</option>
    </select>
  </div>
  <div class="kpi-grid" id="sizeKpi"></div>
  <div class="chart-row">
    <div class="chart-box"><h3>尺寸销售额排行 <small>（带同比箭头）</small></h3><canvas id="sizeRankChart"></canvas></div>
    <div class="chart-box"><h3>尺寸占比</h3><canvas id="sizePieChart"></canvas></div>
  </div>
  <div class="chart-row">
    <div class="chart-box full"><h3>尺寸销售趋势 <small id="sizeTrendLabel"></small> <button onclick="resetSizes()" style="font-size:10px;padding:1px 8px;background:#c9a962;color:#fff;border:none;border-radius:8px;cursor:pointer;vertical-align:middle;margin-left:4px;">重置</button></h3><canvas id="sizeTrendChart"></canvas></div>
  </div>
</div>

<!-- ===== 颜色看板 ===== -->
<div class="tab-content" id="tab-sku">
  <div class="chart-row"><div class="chart-box full" id="skuContent" style="min-height:500px"><h3>请选择一个系列开始分析</h3></div></div>
</div>

<div class="tab-content" id="tab-color">
  <div style="margin-bottom:12px;display:flex;gap:10px;align-items:center;background:#fff;padding:8px 16px;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.08)">
    <label style="font-size:12px;color:#6b7280;font-weight:500">品类</label>
    <select id="colorCat" onchange="renderColor()" style="border:1px solid #d1d5db;border-radius:6px;padding:5px 10px;font-size:13px;background:#fff">
      <option value="all">全部</option><option value="luggage">行李箱</option><option value="bag">包袋</option>
    </select>
  </div>
  <div class="kpi-grid" id="colorKpi"></div>
  <div class="chart-row">
    <div class="chart-box"><h3>颜色销售额排行 <small>（带同比箭头）</small></h3><canvas id="colorRankChart"></canvas></div>
    <div class="chart-box"><h3>颜色占比</h3><canvas id="colorPieChart"></canvas></div>
  </div>
  <div class="chart-row">
    <div class="chart-box full"><h3>颜色销售趋势 <small id="colorTrendLabel"></small></h3><canvas id="colorTrendChart"></canvas></div>
  </div>
  </div>
</div>

<!-- 退货分析 Tab（2026-07-30 新增） -->
<div class="tab-content" id="tab-return">
  <div style="margin-bottom:12px;display:flex;gap:10px;align-items:center;background:#fff;padding:8px 16px;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.08)">
    <label style="font-size:12px;color:#6b7280;font-weight:500">品类</label>
    <select id="returnCat" onchange="renderReturn()" style="border:1px solid #d1d5db;border-radius:6px;padding:5px 10px;font-size:13px;background:#fff">
      <option value="all">全部</option><option value="luggage">行李箱</option><option value="bag">包袋</option>
    </select>
  </div>
  <div class="kpi-grid" id="returnKpi"></div>
  <div class="chart-row">
    <div class="chart-box"><h3>系列退货金额排行</h3><canvas id="returnRankChart"></canvas></div>
    <div class="chart-box"><h3>渠道退货占比</h3><canvas id="returnPieChart"></canvas></div>
  </div>
  <div class="chart-row">
    <div class="chart-box full"><h3>退货金额趋势 <small id="returnTrendLabel"></small></h3><canvas id="returnTrendChart"></canvas></div>
  </div>
</div>

</div>

<script>
const CHANNELS = ''' + json.dumps(all_series_data['meta']['channels'], ensure_ascii=False) + r''';
const ALL_SERIES = ''' + json.dumps(ALL_SERIES_LIST, ensure_ascii=False) + r''';
const AUDIENCES = ''' + json.dumps(AUDIENCE_LIST, ensure_ascii=False) + r''';
// === 退货数据（2026-07-30 新增） ===
const RET_ALL_DAILY = ''' + ret_all_json_str + r''';
const RET_LUG_DAILY = ''' + ret_lug_json_str + r''';
const RET_BAG_DAILY = ''' + ret_bag_json_str + r''';
const LUG_DAILY = ''' + luggage_json_str + r''';
const BAG_DAILY = ''' + bag_json_str + r''';
const ALL_DAILY = ''' + all_json_str + r''';
const AUD_DAILY = ''' + audience_json_str + r''';
const CROSS_DAILY = ''' + cross_json_str + r''';
const LUG_AUD_DAILY = ''' + lug_aud_json_str + r''';
const BAG_AUD_DAILY = ''' + bag_aud_json_str + r''';
const BAG_CROSS_DAILY = ''' + bag_cross_json_str + r''';
const COLOR_DAILY = ''' + color_json_str + r''';
const SIZE_DAILY = ''' + size_json_str + r''';
const LUG_COLOR_DAILY = ''' + lug_color_json_str + r''';
const LUG_SIZE_DAILY = ''' + lug_size_json_str + r''';
const BAG_COLOR_DAILY = ''' + bag_color_json_str + r''';
const BAG_SIZE_DAILY = ''' + bag_size_json_str + r''';
const LUG_SERIES = ''' + json.dumps(sorted(LUG_SERIES_SET), ensure_ascii=False) + r''';
const BAG_SERIES = ''' + json.dumps(sorted(BAG_SERIES_SET), ensure_ascii=False) + r''';
const SKU_SUMMARY = JSON.parse(''' + json.dumps(json.dumps(compressed_sku['summary']), ensure_ascii=False) + r''');
const SKU_DAILY = JSON.parse(''' + json.dumps(json.dumps(compressed_sku['daily']), ensure_ascii=False) + r''');
const SKU_CH_DAILY = JSON.parse(''' + json.dumps(json.dumps(compressed_sku['ch_daily']), ensure_ascii=False) + r''');
const SKU_CH_SUMMARY = ''' + json.dumps(compressed_sku['ch_summary'], ensure_ascii=False) + r''';
const SKU_META = JSON.parse(''' + json.dumps(json.dumps(compressed_sku['meta']), ensure_ascii=False) + r''');
const SKU_BY_SERIES = ''' + json.dumps(compressed_sku['by_series'], ensure_ascii=False) + r''';


// ===== 导航 =====
const tabs=[
  {id:'luggage',icon:'luggage',label:'行李箱总览'},
  {id:'bag',icon:'shopping-bag',label:'包袋总览'},
  {id:'series-detail',icon:'layers',label:'系列看板'},
  {id:'sku',icon:'search',label:'SKU分析'},
  {id:'audience',icon:'users',label:'人群看板'},
  {id:'size',icon:'ruler',label:'尺寸看板'},
  {id:'color',icon:'palette',label:'颜色看板'},
  {id:'return',icon:'rotate-ccw',label:'退货分析'},
];
const navEl=document.getElementById('nav');
navEl.innerHTML='<span class="brand">ITO 产品分析</span>';
tabs.forEach(t=>{
  const a=document.createElement('a');
  a.href='#';a.dataset.tab=t.id;
  a.innerHTML='<i data-lucide="'+t.icon+'" class="icon"></i>'+t.label;
  a.onclick=e=>{e.preventDefault();switchTab(t.id)};
  navEl.appendChild(a);
});
if(document.querySelector('[data-lucide]')) lucide.createIcons();

function switchTab(id){
  document.querySelectorAll('.tab-content').forEach(el=>el.classList.remove('active'));
  document.querySelectorAll('.nav a').forEach(el=>el.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  document.querySelector('.nav a[data-tab="'+id+'"]').classList.add('active');
  if(id==='luggage')renderLuggage();
  if(id==='bag')renderBag();
  if(id==='audience')renderAudience();
  if(id==='size')renderSize();
  if(id==='color')renderColor();
  if(id==='return')renderReturn();
  if(id==='series-detail')renderSeriesTab();
  if(id==='sku')renderSKU();
}

// ===== 过滤器状态 =====
let selChannels=new Set();
let metric='amt';
let audCategory='all';
let startDate,endDate;
let showYoy=false;
const TODAY=function(){const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');}();

function parseDate(s){const p=s.split('-');return new Date(+p[0],+p[1]-1,+p[2])}
function fmt(d){const p=d.split('-');return p[0]+'-'+p[1]+'-'+p[2]}
function formatLocalDate(d){const y=d.getFullYear();const m=String(d.getMonth()+1).padStart(2,'0');const dd=String(d.getDate()).padStart(2,'0');return y+'-'+m+'-'+dd}
function fmtD(v){return Math.round(v/10000)+'万'}
function pct(a,b){if(!b||b===0)return'-';return ((a/b)*100).toFixed(1)+'%'}
function diffPct(a,b){if(!b||b===0)return'-';return ((a-b)/b*100).toFixed(1)+'%'}

function getDatesInRange(s,e){
  const r=[];let d=new Date(parseDate(s));
  while(d<=parseDate(e)){r.push(formatLocalDate(d));d.setDate(d.getDate()+1)}
  return r;
}
function getPrevPeriod(s,e){
  const sd=parseDate(s),ed=parseDate(e);
  const dc=Math.round((ed-sd)/86400000)+1;
  const ps=new Date(sd.getTime()-dc*86400000),pe=new Date(sd.getTime()-86400000);
  return {start:formatLocalDate(ps),end:formatLocalDate(pe)};
}
function getYoYPeriod(s,e){
  const s2=new Date(parseDate(s));s2.setFullYear(s2.getFullYear()-1);
  const e2=new Date(parseDate(e));e2.setFullYear(e2.getFullYear()-1);
  return {start:formatLocalDate(s2),end:formatLocalDate(e2)};
}

// ===== 数据聚合工具 =====
function sumDaily(data,channels,start,end,subKey,metric,onlySub){
  let total=0;
  const dates=getDatesInRange(start,end);
  dates.forEach(d=>{
    if(!data[d])return;
    (channels.length?channels:Object.keys(data[d])).forEach(ch=>{
      if(!data[d][ch])return;
      if(subKey){
        if(data[d][ch][subKey])total+=data[d][ch][subKey][metric]||0;
      }else if(onlySub){
        Object.keys(data[d][ch]).forEach(sk=>{
          if(sk!=='$total')total+=data[d][ch][sk][metric]||0;
        });
      }else{
        total+=data[d][ch].$total?.[metric]||0;
      }
    });
  });
  return total;
}

function sumDailyBoth(data,channels,start,end,subKey){
  /* 同时返回销售额和销量 */
  let amt=0,qty=0;
  const dates=getDatesInRange(start,end);
  dates.forEach(d=>{
    if(!data[d])return;
    (channels.length?channels:Object.keys(data[d])).forEach(ch=>{
      if(!data[d][ch])return;
      if(subKey){
        if(data[d][ch][subKey]){amt+=data[d][ch][subKey].amt||0;qty+=data[d][ch][subKey].qty||0}
      }else if(data[d][ch].$total){
        amt+=data[d][ch].$total.amt||0;qty+=data[d][ch].$total.qty||0;
      }
    });
  });
  return {amt,qty};
}

function getSeriesRank(data,channels,start,end,metric,topN){
  const map={};
  const dates=getDatesInRange(start,end);
  dates.forEach(d=>{
    if(!data[d])return;
    (channels.length?channels:Object.keys(data[d])).forEach(ch=>{
      if(!data[d][ch])return;
      Object.keys(data[d][ch]).forEach(sk=>{
        if(sk==='$total')return;
        map[sk]=(map[sk]||0)+(data[d][ch][sk][metric]||0);
      });
    });
  });
  const sorted=Object.entries(map).sort((a,b)=>b[1]-a[1]);
  return topN?sorted.slice(0,topN):sorted;
}

function getAllSeriesSorted(data,channels,start,end,metric){
  return getSeriesRank(data,channels,start,end,metric,0);
}

function getDailyTrend(data,channels,start,end,metric){
  const dates=getDatesInRange(start,end);
  return dates.map(d=>{
    let v=0;
    if(!data[d])return 0;
    (channels.length?channels:Object.keys(data[d])).forEach(ch=>{
      if(data[d][ch]?.$total)v+=data[d][ch].$total[metric]||0;
    });
    return v;
  });
}

// ===== 可折叠控制 =====
function toggleCollapse(id){
  const body=document.getElementById(id);
  const arrow=document.getElementById(id+'Arrow');
  if(!body)return;
  body.classList.toggle('open');
  if(arrow)arrow.classList.toggle('open');
}

// ===== 初始化筛选器 =====
function initFilters(){
  const today=new Date();
  const endStr=formatLocalDate(today);
  const sd=new Date(today);sd.setDate(1);
  const startStr=formatLocalDate(sd);
  startDate=startStr;endDate=endStr;

  document.getElementById('filterBar').innerHTML=
    `<label>日期</label><input type="date" id="fdStart" value="${startStr}"><input type="date" id="fdEnd" value="${endStr}">`+
    `<label>指标</label><div class="metric-toggle"><button data-m="amt" class="active" onclick="setMetric('amt')">销售额</button><button data-m="qty" onclick="setMetric('qty')">销量</button></div>`+
    `<label style="margin-left:6px"><input type="checkbox" id="chkYoy" onchange="toggleYoy()" style="vertical-align:middle;margin-right:3px">显示去年同期</label>`+
    `<button onclick="applyFilters()" style="padding:5px 16px;background:#2563eb;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:12px">刷新</button>`;

  document.getElementById('channelTags').innerHTML=
    `<button class="active" onclick="toggleAllChannels()">全部渠道</button>`+
    CHANNELS.map(ch=>`<button data-ch="${ch}" onclick="toggleCh('${ch}')">${ch}</button>`).join('');
}
function setMetric(m){
  console.log('setMetric called: '+m);
  metric=m;
  document.querySelectorAll('.metric-toggle button').forEach(b=>b.classList.toggle('active',b.dataset.m===m));
  renderCurrentTab();
}
function toggleYoy(){
  showYoy=document.getElementById('chkYoy').checked;
  renderCurrentTab();
}
function setAudCategory(v){audCategory=v}
function getAudData(){
  /* 返回当前品类对应的人群数据和交叉数据 */
  if(audCategory==='luggage')return {daily:LUG_AUD_DAILY,cross:CROSS_DAILY};
  if(audCategory==='bag')return {daily:BAG_AUD_DAILY,cross:BAG_CROSS_DAILY};
  return {daily:AUD_DAILY,cross:CROSS_DAILY};
}
function getAudMeta(){
  if(audCategory==='luggage')return ''' + LUG_AUD_META + r''';
  if(audCategory==='bag')return ''' + BAG_AUD_META + r''';
  return ''' + AUD_META + r''';
}
function toggleAllChannels(){
  selChannels=new Set();
  document.querySelectorAll('.channel-tags button').forEach(b=>b.classList.toggle('active',b.dataset.ch==null));
  renderCurrentTab();
}
function toggleCh(ch){
  console.log('toggleCh called: '+ch);
  selChannels=new Set([ch]);
  document.querySelectorAll('.channel-tags button').forEach(b=>b.classList.toggle('active',b.dataset.ch===ch));
  renderCurrentTab();
}
function renderCurrentTab(){
  console.log('renderCurrentTab called, active tab='+(document.querySelector('.tab-content.active')?.id||'none'));
  const active=document.querySelector('.tab-content.active');
  if(active&&active.id==='tab-luggage')renderLuggage();
  if(active&&active.id==='tab-bag')renderBag();
  if(active&&active.id==='tab-audience')renderAudience();
  if(active&&active.id==='tab-size')renderSize();
  if(active&&active.id==='tab-color')renderColor();
  if(active&&active.id==='tab-return')renderReturn();
  if(active&&active.id==='tab-series-detail')renderSeriesTab();
  if(active&&active.id==='tab-sku')renderSKUData();
}
function getVisChannels(){return selChannels.size?[...selChannels]:CHANNELS}
function applyFilters(){
  startDate=document.getElementById('fdStart').value;
  endDate=document.getElementById('fdEnd').value;
  document.querySelectorAll('.tab-content.active').forEach(el=>{
    if(el.id==='tab-luggage')renderLuggage();
    if(el.id==='tab-bag')renderBag();
    if(el.id==='tab-audience')renderAudience();
    if(el.id==='tab-size')renderSize();
    if(el.id==='tab-color')renderColor();
    if(el.id==='tab-return')renderReturn();
    if(el.id==='tab-series-detail')renderSeriesTab();
    if(el.id==='tab-sku')renderSKU();
  });
}

// ===== 行李箱总览 =====
let lugTrendChart,lugSeriesChart,lugPieChart;
function renderLuggage(){
  const ch=getVisChannels();
  const dates=getDatesInRange(startDate,endDate);
  const dayCount=dates.length;
  if(!dayCount)return;

  const total=sumDaily(LUG_DAILY,ch,startDate,endDate,'',metric,false);
  const prev=getPrevPeriod(startDate,endDate);
  const yoy=getYoYPeriod(startDate,endDate);
  const totalPrev=sumDaily(LUG_DAILY,ch,prev.start,prev.end,'',metric,false);
  const totalYoy=sumDaily(LUG_DAILY,ch,yoy.start,yoy.end,'',metric,false);

  document.getElementById('lugKpi').innerHTML=
    `<div class="kpi-card"><div class="label">${metric==='amt'?'销售额':'销量'} <small>${dayCount}天</small></div><div class="value">${metric==='amt'?fmtD(total):total.toLocaleString()}</div><div class="sub">环比 <span class="${total>=totalPrev?'up':'down'}">${diffPct(total,totalPrev)}</span> | 同比 <span class="${total>=totalYoy?'up':'down'}">${diffPct(total,totalYoy)}</span></div></div>`+
    `<div class="kpi-card"><div class="label">系列数 <small>有销售</small></div><div class="value">${getSeriesRank(LUG_DAILY,ch,startDate,endDate,metric,999).length}</div></div>`+
    `<div class="kpi-card"><div class="label">渠道数</div><div class="value">${ch.length}</div></div>`;

  // 趋势图（当期+去年同期）
  const trendData=getDailyTrend(LUG_DAILY,ch,startDate,endDate,metric);
  const yoyDates=dates.map(d=>{const p=d.split('-');const yd=new Date(+p[0]-1,+p[1]-1,+p[2]);return yd.getFullYear()+'-'+String(yd.getMonth()+1).padStart(2,'0')+'-'+String(yd.getDate()).padStart(2,'0');});
  const yoyData=yoyDates.map(d=>{let v=0;if(!LUG_DAILY[d])return null;(ch.length?ch:Object.keys(LUG_DAILY[d])).forEach(c=>{if(LUG_DAILY[d][c]?.$total)v+=LUG_DAILY[d][c].$total[metric]||0;});return v;});
  document.getElementById('lugTrendLabel').textContent=startDate+' ~ '+endDate;
  var lugDs=[{label:'今年',data:trendData,borderColor:'#2563eb',backgroundColor:'rgba(37,99,235,0.1)',fill:true,tension:0.3,pointRadius:2,pointHitRadius:20,borderWidth:2}];
  if(showYoy)lugDs.push({label:'去年同期',data:yoyData,borderColor:'#9ca3af',backgroundColor:'transparent',fill:false,tension:0.3,pointRadius:2,pointHitRadius:20,borderWidth:2,borderDash:[5,5]});
  if(lugTrendChart)lugTrendChart.destroy();
  lugTrendChart=new Chart(document.getElementById('lugTrend'),{
    type:'line',
    data:{labels:dates,datasets:lugDs},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'top',labels:{usePointStyle:true,boxWidth:8}},tooltip:{enabled:true,mode:'index',intersect:false,callbacks:{title:function(items){return items[0].label},label:function(ctx){var p=Math.round(ctx.parsed.y);return ctx.dataset.label+': '+(metric==='amt'?'¥'+p.toLocaleString()+'元':p.toLocaleString()+'件')}}}},hover:{mode:'index',intersect:false},scales:{y:{beginAtZero:true,ticks:{callback:v=>Math.round(metric==='amt'?v/10000:v)+''}}}}
  });

  // 系列TOP
  const topSeries=getSeriesRank(LUG_DAILY,ch,startDate,endDate,metric,10);
  document.getElementById('lugSeriesLabel').textContent=startDate+' ~ '+endDate;
  if(lugSeriesChart)lugSeriesChart.destroy();
  lugSeriesChart=new Chart(document.getElementById('lugSeriesChart'),{
    type:'bar',
    data:{
      labels:topSeries.map(s=>s[0].length>15?s[0].slice(0,15)+'...':s[0]),
      datasets:[{label:metric==='amt'?'销售额':'销量',data:topSeries.map(s=>Math.round(s[1])),backgroundColor:['#2563eb','#3b82f6','#60a5fa','#93c5fd','#bfdbfe','#6366f1','#8b5cf6','#a78bfa','#c4b5fd','#ddd6fe']}]
    },
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{callback:v=>metric==='amt'?fmtD(v):v.toLocaleString()}}}}
  });

  // 饼图（金额+百分比）
  const chAmts=CHANNELS.map(ch=>sumDaily(LUG_DAILY,[ch],startDate,endDate,'',metric,false));
  const chTotal=chAmts.reduce((a,b)=>a+b,0)||1;
  if(lugPieChart)lugPieChart.destroy();
  lugPieChart=new Chart(document.getElementById('lugPieChart'),{
    type:'pie',
    data:{
      labels:CHANNELS.filter((_,i)=>chAmts[i]>0),
      datasets:[{data:chAmts.filter(v=>v>0),backgroundColor:['#2563eb','#3b82f6','#60a5fa','#93c5fd','#bfdbfe','#6366f1']}]
    },
    options:{responsive:true,plugins:{
      legend:{position:'bottom',labels:{font:{size:10},generateLabels:function(c){
        const ds=c.data.datasets[0];const meta=c.getDatasetMeta(0);
        return ds.data.map((v,i)=>({text:(c.data.labels[i]||'渠道')+': '+Math.round(v).toLocaleString()+' ('+Math.round(v/chTotal*100)+'%)',fillStyle:ds.backgroundColor[i],strokeStyle:'#fff',lineWidth:0,hidden:false,index:i}));
      }},title:{display:true,text:'渠道占比 ('+(metric==='amt'?'销售额':'销量')+')'}},
      tooltip:{callbacks:{label:function(ctx){const v=ctx.parsed;return ctx.label+': '+Math.round(v).toLocaleString()+' ('+Math.round(v/chTotal*100)+'%)'}}}
    }}
  });

  // ===== 系列销售明细（ALL系列，可折叠）=====
  renderSeriesDetail();
}

function renderSeriesDetail(){
  const ch=getVisChannels();
  // 使用LUG_DAILY展示行李箱系列
  const allRanked=getAllSeriesSorted(LUG_DAILY,ch,startDate,endDate,metric);
  const countEl=document.getElementById('lugDetailCount');
  if(countEl)countEl.textContent='（共 '+allRanked.length+' 个系列）';

  // 计算总金额/总销量
  let grandTotal={amt:0,qty:0};
  allRanked.forEach(([seriesName])=>{
    const both=sumDailyBoth(LUG_DAILY,ch,startDate,endDate,seriesName);
    grandTotal.amt+=both.amt;
    grandTotal.qty+=both.qty;
  });

  // 构建表头（含渠道列）
  const showChs=getVisChannels();
  const headRow=document.getElementById('lugDetailHead');
  if(headRow){
    headRow.innerHTML='<th>系列</th><th>销售额</th><th>占比</th><th>销量</th>';
    showChs.forEach(c=>{
      headRow.innerHTML+='<th style="font-size:11px;color:#6b7280">'+c.slice(0,6)+'</th>';
    });
  }

  // 构建表体
  let tbody='';
  const totalForPct=grandTotal[metric]||1;
  allRanked.forEach(([seriesName,val],i)=>{
    const both=sumDailyBoth(LUG_DAILY,ch,startDate,endDate,seriesName);
    const pctStr=metric==='amt'?pct(both.amt,totalForPct):pct(both.qty,totalForPct);
    tbody+='<tr>';
    tbody+='<td>'+(seriesName.length>22?seriesName.slice(0,22)+'...':seriesName)+'</td>';
    tbody+='<td class="val-amt">'+fmtD(both.amt)+'</td>';
    tbody+='<td>'+pctStr+'</td>';
    tbody+='<td class="val-qty">'+Math.round(both.qty).toLocaleString()+'</td>';
    // 每个渠道的贡献
    showChs.forEach(c=>{
      const chBoth=sumDailyBoth(LUG_DAILY,[c],startDate,endDate,seriesName);
      tbody+='<td style="font-size:11px;color:#9ca3af">'+(metric==='amt'?fmtD(chBoth.amt):Math.round(chBoth.qty).toLocaleString())+'</td>';
    });
    tbody+='</tr>';
  });

  // 汇总行
  tbody='<tr class="summary"><td>合计</td><td class="val-amt">'+fmtD(grandTotal.amt)+'</td><td>100%</td><td class="val-qty">'+Math.round(grandTotal.qty).toLocaleString()+'</td>'+showChs.map(c=>{
    const chBoth=sumDailyBoth(LUG_DAILY,[c],startDate,endDate,'');
    return '<td style="font-size:11px">'+(metric==='amt'?fmtD(chBoth.amt):Math.round(chBoth.qty).toLocaleString())+'</td>';
  }).join('')+'</tr>'+tbody;

  document.getElementById('lugDetailBodyInner').innerHTML=tbody;
}

// ===== 包袋总览 =====
let bagTrendChart,bagSeriesChart,bagPieChart;
function renderBag(){
  const ch=getVisChannels();
  const dates=getDatesInRange(startDate,endDate);
  const dayCount=dates.length;
  if(!dayCount)return;

  const total=sumDaily(BAG_DAILY,ch,startDate,endDate,'',metric,false);
  const prev=getPrevPeriod(startDate,endDate);
  const yoy=getYoYPeriod(startDate,endDate);
  const totalPrev=sumDaily(BAG_DAILY,ch,prev.start,prev.end,'',metric,false);
  const totalYoy=sumDaily(BAG_DAILY,ch,yoy.start,yoy.end,'',metric,false);

  document.getElementById('bagKpi').innerHTML=
    `<div class="kpi-card"><div class="label">${metric==='amt'?'销售额':'销量'} <small>${dayCount}天</small></div><div class="value">${metric==='amt'?fmtD(total):total.toLocaleString()}</div><div class="sub">环比 <span class="${total>=totalPrev?'up':'down'}">${diffPct(total,totalPrev)}</span> | 同比 <span class="${total>=totalYoy?'up':'down'}">${diffPct(total,totalYoy)}</span></div></div>`+
    `<div class="kpi-card"><div class="label">系列数 <small>有销售</small></div><div class="value">${getSeriesRank(BAG_DAILY,ch,startDate,endDate,metric,999).length}</div></div>`+
    `<div class="kpi-card"><div class="label">渠道数</div><div class="value">${ch.length}</div></div>`;

  // 趋势图（当期+去年同期）
  const trendData=getDailyTrend(BAG_DAILY,ch,startDate,endDate,metric);
  const yoyDates=dates.map(d=>{const p=d.split('-');const yd=new Date(+p[0]-1,+p[1]-1,+p[2]);return yd.getFullYear()+'-'+String(yd.getMonth()+1).padStart(2,'0')+'-'+String(yd.getDate()).padStart(2,'0');});
  const yoyData=yoyDates.map(d=>{let v=0;if(!BAG_DAILY[d])return null;(ch.length?ch:Object.keys(BAG_DAILY[d])).forEach(c=>{if(BAG_DAILY[d][c]?.$total)v+=BAG_DAILY[d][c].$total[metric]||0;});return v;});
  document.getElementById('bagTrendLabel').textContent=startDate+' ~ '+endDate;
  var bagDs=[{label:'今年',data:trendData,borderColor:'#8b5cf6',backgroundColor:'rgba(139,92,246,0.1)',fill:true,tension:0.3,pointRadius:2,pointHitRadius:20,borderWidth:2}];
  if(showYoy)bagDs.push({label:'去年同期',data:yoyData,borderColor:'#9ca3af',backgroundColor:'transparent',fill:false,tension:0.3,pointRadius:2,pointHitRadius:20,borderWidth:2,borderDash:[5,5]});
  if(bagTrendChart)bagTrendChart.destroy();
  bagTrendChart=new Chart(document.getElementById('bagTrend'),{
    type:'line',
    data:{labels:dates,datasets:bagDs},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'top',labels:{usePointStyle:true,boxWidth:8}},tooltip:{enabled:true,mode:'index',intersect:false,callbacks:{title:function(items){return items[0].label},label:function(ctx){var p=Math.round(ctx.parsed.y);return ctx.dataset.label+': '+(metric==='amt'?'¥'+p.toLocaleString()+'元':p.toLocaleString()+'件')}}}},hover:{mode:'index',intersect:false},scales:{y:{beginAtZero:true,ticks:{callback:v=>Math.round(metric==='amt'?v/10000:v)+''}}}}
  });

  // 系列TOP
  const topSeries=getSeriesRank(BAG_DAILY,ch,startDate,endDate,metric,10);
  document.getElementById('bagSeriesLabel').textContent=startDate+' ~ '+endDate;
  if(bagSeriesChart)bagSeriesChart.destroy();
  bagSeriesChart=new Chart(document.getElementById('bagSeriesChart'),{
    type:'bar',
    data:{
      labels:topSeries.map(s=>s[0].length>15?s[0].slice(0,15)+'...':s[0]),
      datasets:[{label:metric==='amt'?'销售额':'销量',data:topSeries.map(s=>Math.round(s[1])),backgroundColor:['#8b5cf6','#a78bfa','#c4b5fd','#ec4899','#f472b6','#f9a8d4','#f59e0b','#fbbf24','#fcd34d','#10b981']}]
    },
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{callback:v=>metric==='amt'?fmtD(v):v.toLocaleString()}}}}
  });

  // 饼图
  const chAmts=CHANNELS.map(ch=>sumDaily(BAG_DAILY,[ch],startDate,endDate,'',metric,false));
  const chTotal=chAmts.reduce((a,b)=>a+b,0)||1;
  if(bagPieChart)bagPieChart.destroy();
  bagPieChart=new Chart(document.getElementById('bagPieChart'),{
    type:'pie',
    data:{
      labels:CHANNELS.filter((_,i)=>chAmts[i]>0),
      datasets:[{data:chAmts.filter(v=>v>0),backgroundColor:['#8b5cf6','#a78bfa','#c4b5fd','#ec4899','#f472b6','#f9a8d4']}]
    },
    options:{responsive:true,plugins:{
      legend:{position:'bottom',labels:{font:{size:10},generateLabels:function(c){
        const ds=c.data.datasets[0];const meta=c.getDatasetMeta(0);
        return ds.data.map((v,i)=>({text:(c.data.labels[i]||'渠道')+': '+Math.round(v).toLocaleString()+' ('+Math.round(v/chTotal*100)+'%)',fillStyle:ds.backgroundColor[i],strokeStyle:'#fff',lineWidth:0,hidden:false,index:i}));
      }},title:{display:true,text:'渠道占比 ('+(metric==='amt'?'销售额':'销量')+')'}},
      tooltip:{callbacks:{label:function(ctx){const v=ctx.parsed;return ctx.label+': '+Math.round(v).toLocaleString()+' ('+Math.round(v/chTotal*100)+'%)'}}}
    }}
  });

  // 系列销售明细
  renderBagDetail();
}

function renderBagDetail(){
  const ch=getVisChannels();
  const allRanked=getAllSeriesSorted(BAG_DAILY,ch,startDate,endDate,metric);
  const countEl=document.getElementById('bagDetailCount');
  if(countEl)countEl.textContent='（共 '+allRanked.length+' 个系列）';

  let grandTotal={amt:0,qty:0};
  allRanked.forEach(([seriesName])=>{
    const both=sumDailyBoth(BAG_DAILY,ch,startDate,endDate,seriesName);
    grandTotal.amt+=both.amt;
    grandTotal.qty+=both.qty;
  });

  const showChs=getVisChannels();
  const headRow=document.getElementById('bagDetailHead');
  if(headRow){
    headRow.innerHTML='<th>系列</th><th>销售额</th><th>占比</th><th>销量</th>';
    showChs.forEach(c=>{
      headRow.innerHTML+='<th style="font-size:11px;color:#6b7280">'+c.slice(0,6)+'</th>';
    });
  }

  let tbody='';
  const totalForPct=grandTotal[metric]||1;
  allRanked.forEach(([seriesName,val])=>{
    const both=sumDailyBoth(BAG_DAILY,ch,startDate,endDate,seriesName);
    const pctStr=metric==='amt'?pct(both.amt,totalForPct):pct(both.qty,totalForPct);
    tbody+='<tr>';
    tbody+='<td>'+(seriesName.length>22?seriesName.slice(0,22)+'...':seriesName)+'</td>';
    tbody+='<td class="val-amt">'+fmtD(both.amt)+'</td>';
    tbody+='<td>'+pctStr+'</td>';
    tbody+='<td class="val-qty">'+Math.round(both.qty).toLocaleString()+'</td>';
    showChs.forEach(c=>{
      const chBoth=sumDailyBoth(BAG_DAILY,[c],startDate,endDate,seriesName);
      tbody+='<td style="font-size:11px;color:#9ca3af">'+(metric==='amt'?fmtD(chBoth.amt):Math.round(chBoth.qty).toLocaleString())+'</td>';
    });
    tbody+='</tr>';
  });

  tbody='<tr class="summary"><td>合计</td><td class="val-amt">'+fmtD(grandTotal.amt)+'</td><td>100%</td><td class="val-qty">'+Math.round(grandTotal.qty).toLocaleString()+'</td>'+showChs.map(c=>{
    const chBoth=sumDailyBoth(BAG_DAILY,[c],startDate,endDate,'');
    return '<td style="font-size:11px">'+(metric==='amt'?fmtD(chBoth.amt):Math.round(chBoth.qty).toLocaleString())+'</td>';
  }).join('')+'</tr>'+tbody;

  document.getElementById('bagDetailBodyInner').innerHTML=tbody;
}

// ===== 系列看板 =====
let seriesCards={};
function renderSeriesTab(){
  const ch=getVisChannels();
  const dates=getDatesInRange(startDate,endDate);
  const dayCount=dates.length;
  if(!dayCount)return;

  // 聚合所有系列数据
  const seriesMap={};
  dates.forEach(d=>{
    if(!ALL_DAILY[d])return;
    (ch.length?ch:Object.keys(ALL_DAILY[d])).forEach(c=>{
      if(!ALL_DAILY[d][c])return;
      Object.keys(ALL_DAILY[d][c]).forEach(sk=>{
        if(sk==='$total')return;
        if(!seriesMap[sk])seriesMap[sk]={amt:0,qty:0};
        seriesMap[sk].amt+=ALL_DAILY[d][c][sk].amt||0;
        seriesMap[sk].qty+=ALL_DAILY[d][c][sk].qty||0;
      });
    });
  });
  const sorted=Object.entries(seriesMap).sort((a,b)=>b[1].amt-a[1].amt);

  // 品类筛选
  const seriesCat=document.getElementById('seriesCat')?.value||'all';
  const filteredSorted=sorted.filter(function(s){
    if(seriesCat==='all')return true;
    if(seriesCat==='luggage')return LUG_SERIES.indexOf(s[0])!==-1;
    if(seriesCat==='bag')return BAG_SERIES.indexOf(s[0])!==-1;
    return true;
  });

  // KPI显示当前品类系列数
  const totalAmt=filteredSorted.reduce(function(t,s){return t+s[1].amt;},0);
  const totalQty=filteredSorted.reduce(function(t,s){return t+s[1].qty;},0);
  const grandAmt=totalAmt;
  const grandQty=totalQty;

  // 同比+环比计算
  const yoyPeriod=getYoYPeriod(startDate,endDate);
  const yoyDates=yoyPeriod.start?getDatesInRange(yoyPeriod.start,yoyPeriod.end):[];
  const prevPeriod=getPrevPeriod(startDate,endDate);
  const prevDates=prevPeriod.start?getDatesInRange(prevPeriod.start,prevPeriod.end):[];
  const seriesYoy={};
  const seriesPrev={};
  yoyDates.forEach(d=>{
    if(!ALL_DAILY[d])return;
    (ch.length?ch:Object.keys(ALL_DAILY[d])).forEach(c=>{
      if(!ALL_DAILY[d][c])return;
      Object.keys(ALL_DAILY[d][c]).forEach(sk=>{
        if(sk==='$total')return;
        if(!seriesYoy[sk])seriesYoy[sk]={amt:0,qty:0};
        seriesYoy[sk].amt+=ALL_DAILY[d][c][sk].amt||0;
        seriesYoy[sk].qty+=ALL_DAILY[d][c][sk].qty||0;
      });
    });
  });
  prevDates.forEach(d=>{
    if(!ALL_DAILY[d])return;
    (ch.length?ch:Object.keys(ALL_DAILY[d])).forEach(c=>{
      if(!ALL_DAILY[d][c])return;
      Object.keys(ALL_DAILY[d][c]).forEach(sk=>{
        if(sk==='$total')return;
        if(!seriesPrev[sk])seriesPrev[sk]={amt:0,qty:0};
        seriesPrev[sk].amt+=ALL_DAILY[d][c][sk].amt||0;
        seriesPrev[sk].qty+=ALL_DAILY[d][c][sk].qty||0;
      });
    });
  });

  // KPI（使用筛选后的数据）
  document.getElementById('seriesKpi').innerHTML=
    `<div class="kpi-card"><div class="label">系列数 <small>有销售</small></div><div class="value">${filteredSorted.length}</div></div>`+
    `<div class="kpi-card"><div class="label">${metric==='amt'?'销售额':'销量'} <small>${dayCount}天</small></div><div class="value">${metric==='amt'?fmtD(totalAmt):Math.round(totalQty).toLocaleString()}</div></div>`;

  // 渲染卡片（使用筛选后的数据）
  const container=document.getElementById('seriesCardsContainer');
  container.innerHTML='';
  filteredSorted.forEach(([name,val],idx)=>{
    const yv=seriesYoy[name]||{amt:0,qty:0};
    const yoyDiff=metric==='amt'?val.amt-yv.amt:val.qty-yv.qty;
    const yoyStr=yv[metric]?(yoyDiff>0?'<span class="up">▲ +'+Math.round(Math.abs(yoyDiff)/yv[metric]*100)+'%</span>':yoyDiff<0?'<span class="down">▼ -'+Math.round(Math.abs(yoyDiff)/yv[metric]*100)+'%</span>':'<span style="color:#9ca3af">—</span>'):'<span style="color:#9ca3af">新</span>';
    const pv=seriesPrev[name]||{amt:0,qty:0};
    const prevDiff=metric==='amt'?val.amt-pv.amt:val.qty-pv.qty;
    const prevStr=pv[metric]?(prevDiff>0?'<span class="up">▲ +'+Math.round(Math.abs(prevDiff)/pv[metric]*100)+'%</span>':prevDiff<0?'<span class="down">▼ -'+Math.round(Math.abs(prevDiff)/pv[metric]*100)+'%</span>':'<span style="color:#9ca3af">—</span>'):'<span style="color:#9ca3af">新</span>';
    const pctStr=metric==='amt'?Math.round(val.amt/grandAmt*100)+'%':Math.round(val.qty/grandQty*100)+'%';

    container.innerHTML+=
      '<div class="collapse-wrap" id="series-card-'+idx+'">'+
      '<div class="collapse-header" onclick="toggleSeriesCard('+idx+')">'+
      '<h3>#'+(idx+1)+' '+escapeHtml(name)+' <small>'+(metric==='amt'?fmtD(val.amt):Math.round(val.qty).toLocaleString())+' | 占比'+pctStr+' | 环比'+prevStr.replace(/<[^>]+>/g,'')+' | 同比'+yoyStr.replace(/<[^>]+>/g,'')+'</small></h3>'+
      '<span class="arrow" id="series-arrow-'+idx+'">▼</span></div>'+
      '<div class="collapse-body" id="series-body-'+idx+'"><div class="table-wrap" style="padding:12px"><div style="display:grid;grid-template-columns:1fr 1fr;gap:12px" id="series-grid-'+idx+'">'+
      '<div><canvas id="series-trend-'+idx+'" style="max-height:260px"></canvas></div>'+
      '<div><canvas id="series-pie-'+idx+'" style="max-height:260px"></canvas></div>'+
      '<div id="series-pie-yoy-wrap-'+idx+'" style="display:none"><canvas id="series-pie-yoy-'+idx+'" style="max-height:260px"></canvas></div>'+
      '</div></div></div></div>';
  });
  seriesCards=filteredSorted;
}

function escapeHtml(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;}

function toggleSeriesCard(idx){
  const body=document.getElementById('series-body-'+idx);
  const arrow=document.getElementById('series-arrow-'+idx);
  if(!body)return;
  if(!body.classList.contains('open')){
    // 首次打开时生成图表
    if(!body.dataset.loaded){
      body.dataset.loaded='1';
      const [name,val]=seriesCards[idx]||[];
      if(!name)return;
      const ch=getVisChannels();
      let dates=getDatesInRange(startDate,endDate);
      const yoyDates=dates.map(d=>{const p=d.split('-');return (+p[0]-1)+'-'+p[1]+'-'+p[2];});
      let trendNow=dates.map(dt=>{let v=0;if(!ALL_DAILY[dt])return 0;(ch.length?ch:Object.keys(ALL_DAILY[dt])).forEach(c=>{if(ALL_DAILY[dt][c]?.[name])v+=ALL_DAILY[dt][c][name][metric]||0;});return Math.round(v);});
      let trendYoy=yoyDates.map(dt=>{let v=0;if(!ALL_DAILY[dt])return null;(ch.length?ch:Object.keys(ALL_DAILY[dt])).forEach(c=>{if(ALL_DAILY[dt][c]?.[name])v+=ALL_DAILY[dt][c][name][metric]||0;});return v?Math.round(v):null;});
      // 硬性防护：全新系列（无同期数据）不显示去年同期线
      const hasYoyData=trendYoy.some(function(x){return x!==null && x!==undefined;});
      // 如新系列无同期数据→隐藏去年同期线；如新系列当期无数据→裁剪至首个有销日期
      var firstIdx=trendNow.findIndex(function(x){return x>0;});
      if(firstIdx>0){dates=dates.slice(firstIdx);trendNow=trendNow.slice(firstIdx);trendYoy=trendYoy.slice(firstIdx);}
      const chData=CHANNELS.map(c=>sumDaily(ALL_DAILY,[c],startDate,endDate,name,metric,true));
      const chTotal=chData.reduce((a,b)=>a+b,0)||1;

      setTimeout(function(){
        const trendCtx=document.getElementById('series-trend-'+idx);
        if(trendCtx)new Chart(trendCtx,{type:'line',data:{labels:dates,datasets:[
          {label:'今年',data:trendNow,borderColor:'#2563eb',backgroundColor:'rgba(37,99,235,0.1)',fill:true,tension:.3,pointRadius:0,pointHitRadius:20,borderWidth:2},
          {label:'去年同期',data:showYoy&&hasYoyData?trendYoy:[],borderColor:'#9ca3af',backgroundColor:'transparent',fill:false,tension:.3,pointRadius:0,pointHitRadius:20,borderWidth:2,borderDash:[5,5]}
        ].filter(function(ds){return ds.data.length>0})},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,ticks:{callback:function(v){return Math.round(metric==='amt'?v/10000:v)+''}}}}}});

        const pieCtx=document.getElementById('series-pie-'+idx);
        const chTotal2=chData.reduce((a,b)=>a+b,0)||1;
        var pieData=chData.filter(v=>v>0);
        var pieLbl=CHANNELS.filter((_,i)=>chData[i]>0);
        var pieColors=['#2563eb','#3b82f6','#60a5fa','#93c5fd','#bfdbfe','#6366f1','#8b5cf6','#a78bfa','#c4b5fd','#ddd6fe'];
        if(pieCtx)new Chart(pieCtx,{type:'pie',data:{labels:pieLbl,datasets:[{data:pieData,backgroundColor:pieColors.slice(0,pieLbl.length)}]},options:{responsive:true,plugins:{legend:{position:'bottom',labels:{font:{size:10},generateLabels:function(cc){var ds=cc.data.datasets[0];return ds.data.map((v,i)=>({text:(cc.data.labels[i]||'')+': '+Math.round(v).toLocaleString()+' ('+Math.round(v/chTotal2*100)+'%)',fillStyle:ds.backgroundColor[i],strokeStyle:'#fff',lineWidth:0,hidden:false,index:i}));}}},tooltip:{callbacks:{label:function(ctx){var p=Math.round(ctx.parsed);return ctx.label+': '+p.toLocaleString()+' ('+Math.round(p/chTotal2*100)+'%)';}}}}}});

        // 去年同期饼图
        const yoyPieWrap=document.getElementById('series-pie-yoy-wrap-'+idx);
        if(showYoy && yoyPieWrap){
          yoyPieWrap.style.display='block';
          document.getElementById('series-grid-'+idx).style.gridTemplateColumns='1fr 1fr 1fr';
          var yoyP=getYoYPeriod(startDate,endDate);
          if(yoyP.start){
            var yoyD=getDatesInRange(yoyP.start,yoyP.end);
            var yoyCh=CHANNELS.map(function(ccc){var a=0,q=0;yoyD.forEach(function(dt){if(!ALL_DAILY[dt]||!ALL_DAILY[dt][ccc]||!ALL_DAILY[dt][ccc][name])return;a+=ALL_DAILY[dt][ccc][name].amt||0;q+=ALL_DAILY[dt][ccc][name].qty||0;});return metric==='amt'?a:q;});
            var yoyTot=yoyCh.reduce((a,b)=>a+b,0)||1;
            var yoyPieCtx=document.getElementById('series-pie-yoy-'+idx);
            if(yoyPieCtx)new Chart(yoyPieCtx,{type:'pie',data:{labels:CHANNELS.filter((_,i)=>yoyCh[i]>0),datasets:[{data:yoyCh.filter(v=>v>0),backgroundColor:pieColors.slice(0,CHANNELS.filter((_,i)=>yoyCh[i]>0).length)}]},options:{responsive:true,plugins:{legend:{position:'bottom',labels:{font:{size:9},generateLabels:function(cc2){var ds2=cc2.data.datasets[0];return ds2.data.map((v,i)=>({text:(cc2.data.labels[i]||'')+': '+Math.round(v).toLocaleString()+' ('+Math.round(v/yoyTot*100)+'%)',fillStyle:ds2.backgroundColor[i],strokeStyle:'#fff',lineWidth:0,hidden:false,index:i}));}}}}}});
          }
        }else if(yoyPieWrap){
          yoyPieWrap.style.display='none';
          document.getElementById('series-grid-'+idx).style.gridTemplateColumns='1fr 1fr';
          try{var oldC=document.getElementById('series-pie-yoy-'+idx);if(oldC)Chart.getChart(oldC)?.destroy();}catch(e){}
        }
      }, 100);
    }
  }
  body.classList.toggle('open');
  if(arrow)arrow.classList.toggle('open');
}

// ===== 人群看板 =====
let audTrendChart,audPieChart,audSeriesChart;
function renderAudience(){
  const ch=getVisChannels();
  const dates=getDatesInRange(startDate,endDate);
  const dayCount=dates.length;
  if(!dayCount)return;
  const ad=getAudData();
  const audMeta=getAudMeta();
  const audList=audMeta.audience||AUDIENCES;

  const total=sumDaily(ad.daily,ch,startDate,endDate,'',metric,false);
  const prev=getPrevPeriod(startDate,endDate);
  const yoy=getYoYPeriod(startDate,endDate);
  const totalPrev=sumDaily(ad.daily,ch,prev.start,prev.end,'',metric,false);
  const totalYoy=sumDaily(ad.daily,ch,yoy.start,yoy.end,'',metric,false);

  const audTotals=audList.filter(a=>a).map(a=>{
    const val=sumDaily(ad.daily,ch,startDate,endDate,a,metric,true);
    if(val===0)return null;
    const prevVal=sumDaily(ad.daily,ch,prev.start,prev.end,a,metric,true);
    const yoyVal=sumDaily(ad.daily,ch,yoy.start,yoy.end,a,metric,true);
    return {aud:a,val,prevVal,yoyVal};
  }).filter(x=>x!==null);

  document.getElementById('audKpi').innerHTML=
    `<div class="kpi-card"><div class="label">${metric==='amt'?'销售额':'销量'} <small>${dayCount}天</small></div><div class="value">${metric==='amt'?fmtD(total):total.toLocaleString()}</div><div class="sub">环比 <span class="${total>=totalPrev?'up':'down'}">${diffPct(total,totalPrev)}</span> | 同比 <span class="${total>=totalYoy?'up':'down'}">${diffPct(total,totalYoy)}</span></div></div>`+
    audTotals.map(a=>`<div class="kpi-card"><div class="label">${a.aud}</div><div class="value">${metric==='amt'?fmtD(a.val):a.val.toLocaleString()}</div><div class="sub">占比 ${pct(a.val,total)} | 环比 <span class="${a.val>=a.prevVal?'up':'down'}">${diffPct(a.val,a.prevVal)}</span> | 同比 <span class="${a.val>=a.yoyVal?'up':'down'}">${diffPct(a.val,a.yoyVal)}</span></div></div>`).join('');

  document.getElementById('audTrendLabel').textContent=startDate+' ~ '+endDate;
  const trendData=getDailyTrend(ad.daily,ch,startDate,endDate,metric);
  const yoyDates=dates.map(d=>{const p=d.split('-');const yd=new Date(+p[0]-1,+p[1]-1,+p[2]);return yd.getFullYear()+'-'+String(yd.getMonth()+1).padStart(2,'0')+'-'+String(yd.getDate()).padStart(2,'0');});
  const yoyData=yoyDates.map(d=>{let v=0;if(!ad.daily[d])return null;(ch.length?ch:Object.keys(ad.daily[d])).forEach(c=>{if(ad.daily[d][c]?.$total)v+=ad.daily[d][c].$total[metric]||0;});return v;});
  if(audTrendChart)audTrendChart.destroy();
  var audDs=[{label:'今年',data:trendData,borderColor:'#2563eb',backgroundColor:'rgba(37,99,235,0.1)',fill:true,tension:.3,pointRadius:2,pointHitRadius:20,borderWidth:2}];
  if(showYoy)audDs.push({label:'去年同期',data:yoyData,borderColor:'#9ca3af',backgroundColor:'transparent',fill:false,tension:.3,pointRadius:2,pointHitRadius:20,borderWidth:2,borderDash:[5,5]});
  audTrendChart=new Chart(document.getElementById('audTrend'),{
    type:'line',
    data:{labels:dates,datasets:audDs},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'top',labels:{usePointStyle:true,boxWidth:8}},tooltip:{enabled:true,mode:'index',intersect:false,callbacks:{title:function(items){return items[0].label},label:function(ctx){var p=Math.round(ctx.parsed.y);return ctx.dataset.label+': '+(metric==='amt'?'¥'+p.toLocaleString()+'元':p.toLocaleString()+'件')}}}},hover:{mode:'index',intersect:false},scales:{y:{beginAtZero:true,ticks:{callback:v=>Math.round(metric==='amt'?v/10000:v)+''}}}}
  });

  if(audPieChart)audPieChart.destroy();
  const audColors=['#8b5cf6','#ec4899','#f59e0b','#10b981','#6366f1','#f97316'];
  const audTotal=audTotals.reduce((a,b)=>a+b.val,0)||1;
  audPieChart=new Chart(document.getElementById('audPieChart'),{
    type:'pie',
    data:{
      labels:audTotals.map(a=>a.aud),
      datasets:[{data:audTotals.map(a=>Math.round(a.val)),backgroundColor:audColors.slice(0,audTotals.length)}]
    },
    options:{responsive:true,plugins:{
      legend:{position:'bottom',labels:{font:{size:10},generateLabels:function(c){
        const ds=c.data.datasets[0];
        return ds.data.map((v,i)=>({text:(c.data.labels[i]||'人群')+': '+v.toLocaleString()+' ('+Math.round(v/audTotal*100)+'%)',fillStyle:ds.backgroundColor[i],strokeStyle:'#fff',lineWidth:0,hidden:false,index:i}));
      }},title:{display:true,text:'人群占比 ('+(metric==='amt'?'销售额':'销量')+')'}},
      tooltip:{callbacks:{label:function(ctx){const v=ctx.parsed;return ctx.label+': '+Math.round(v).toLocaleString()+' ('+Math.round(v/audTotal*100)+'%)'}}}
    }}
  });

  // 人群×系列
  if(audSeriesChart)audSeriesChart.destroy();
  const crossTotals={};
  dates.forEach(d=>{
    if(!ad.cross[d])return;
    (ch.length?ch:Object.keys(ad.cross[d])).forEach(c=>{
      if(!ad.cross[d][c])return;
      Object.keys(ad.cross[d][c]).forEach(a=>{
        if(!crossTotals[a])crossTotals[a]={};
        Object.keys(ad.cross[d][c][a]).forEach(s=>{
          crossTotals[a][s]=(crossTotals[a][s]||0)+(ad.cross[d][c][a][s][metric]||0);
        });
      });
    });
  });
  const crossLabels=[],crossData=[];
  Object.keys(crossTotals).sort((a,b)=>{
    const va=Object.values(crossTotals[a]).reduce((x,y)=>x+y,0);
    const vb=Object.values(crossTotals[b]).reduce((x,y)=>x+y,0);
    return vb-va;
  }).forEach(a=>{
    const tops=Object.entries(crossTotals[a]).sort((x,y)=>y[1]-x[1]).slice(0,3);
    tops.forEach(([s,v])=>{
      crossLabels.push(a+': '+s.slice(0,15));
      crossData.push(Math.round(v));
    });
  });
  audSeriesChart=new Chart(document.getElementById('audSeriesChart'),{
    type:'bar',
    data:{
      labels:crossLabels.slice(0,15),
      datasets:[{label:metric==='amt'?'销售额':'销量',data:crossData.slice(0,15),backgroundColor:['#8b5cf6','#a78bfa','#c4b5fd','#ec4899','#f472b6','#f9a8d4','#f59e0b','#fbbf24','#fcd34d','#10b981','#34d399','#6ee7b7','#6366f1','#818cf8','#a5b4fc']}]
    },
    options:{indexAxis:'y',responsive:true,plugins:{legend:{display:false}},scales:{x:{ticks:{callback:v=>Math.round(v/10000)+'万'}}}}
  });
}

function getSizeColorData(isColor){
  /* 在size/color看板中按品类获取数据 */
  const catEl=document.getElementById(isColor?'colorCat':'sizeCat');
  const cat=catEl?catEl.value:'all';
  if(isColor){
    if(cat==='luggage')return LUG_COLOR_DAILY;
    if(cat==='bag')return BAG_COLOR_DAILY;
    return COLOR_DAILY;
  }else{
    if(cat==='luggage')return LUG_SIZE_DAILY;
    if(cat==='bag')return BAG_SIZE_DAILY;
    return SIZE_DAILY;
  }
}

// ===== 尺寸看板 =====
let sizeRankChart,sizeTrendChart,sizePieChart;
let hiddenSizes=[];
function renderSize(){
  const ch=getVisChannels();
  const dates=getDatesInRange(startDate,endDate);
  if(!dates.length)return;
  const daily=getSizeColorData(false);
  const ranked=getSeriesRank(daily,ch,startDate,endDate,metric,0);
  const total=ranked.reduce((a,b)=>a+b[1],0);
  // 同比+环比计算
  const prev=getPrevPeriod(startDate,endDate);
  const yoy=getYoYPeriod(startDate,endDate);
  const rankYoy=ranked.map(([sz,v])=>{
    const yv=sumDaily(daily,ch,yoy.start,yoy.end,sz,metric,true);
    const pv=sumDaily(daily,ch,prev.start,prev.end,sz,metric,true);
    const gpct=yv?Math.round((v-yv)/yv*100):0;
    const mpct=pv?Math.round((v-pv)/pv*100):0;
    return {name:sz,val:Math.round(v),yoy:gpct,mom:mpct};
  });
  if(hiddenSizes.length)rankYoy=rankYoy.filter(s=>!hiddenSizes.includes(s.name));
  // KPI（含同环比）
  const totalYoy2=sumDaily(daily,ch,yoy.start,yoy.end,'',metric,false);
  const totalPrev2=sumDaily(daily,ch,prev.start,prev.end,'',metric,false);
  document.getElementById('sizeKpi').innerHTML=
    `<div class="kpi-card"><div class="label">尺寸数 <small>含同比</small></div><div class="value">${rankYoy.length}</div><div class="sub">同比 <span class="${rankYoy.length>=rankYoy.length?'up':'down'}">—</span></div></div>`+
    `<div class="kpi-card"><div class="label">${metric==='amt'?'销售额':'销量'} <small>${dates.length}天</small></div><div class="value">${metric==='amt'?fmtD(total):Math.round(total).toLocaleString()}</div><div class="sub">环比 <span class="${total>=totalPrev2?'up':'down'}">${diffPct(total,totalPrev2)}</span> | 同比 <span class="${total>=totalYoy2?'up':'down'}">${diffPct(total,totalYoy2)}</span></div></div>`+
    (rankYoy.length?`<div class="kpi-card"><div class="label">TOP1 ${rankYoy[0].name}</div><div class="value">${metric==='amt'?fmtD(rankYoy[0].val):rankYoy[0].val.toLocaleString()}</div><div class="sub">环比 <span class="${rankYoy[0].mom>=0?'up':'down'}">${rankYoy[0].mom>=0?'+':''}${rankYoy[0].mom}%</span> | 同比 <span class="${rankYoy[0].yoy>=0?'up':'down'}">${rankYoy[0].yoy>=0?'+':''}${rankYoy[0].yoy}%</span></div></div>`:'');
  // 排行柱状图（标注仅尺寸名，同环比放在tooltip中）
  const topN=rankYoy.slice(0,12);
  document.getElementById('sizeTrendLabel').textContent=startDate+' ~ '+endDate;
  if(sizeRankChart)sizeRankChart.destroy();
  const barLabels=topN.map(s=>s.name);
  sizeRankChart=new Chart(document.getElementById('sizeRankChart'),{
    type:'bar',
    data:{labels:barLabels,datasets:[{label:metric==='amt'?'销售额':'销量',data:topN.map(s=>s.val),backgroundColor:['#2563eb','#3b82f6','#60a5fa','#93c5fd','#bfdbfe','#6366f1','#8b5cf6','#a78bfa','#c4b5fd','#ddd6fe','#059669','#34d399']}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:function(ctx){const i=ctx.dataIndex;const d=topN[i];return' 价值: '+ctx.parsed.x.toLocaleString()+', 同比: '+(d.yoy>=0?'+':'')+d.yoy+'%, 环比: '+(d.mom>=0?'+':'')+d.mom+'%'}}}},scales:{x:{ticks:{callback:v=>Math.round(v/10000)+'万'}}}}
  });
  // 饼图
  if(sizePieChart)sizePieChart.destroy();
  const szTotal=rankYoy.reduce((a,b)=>a+b.val,0)||1;
  sizePieChart=new Chart(document.getElementById('sizePieChart'),{
    type:'pie',data:{labels:rankYoy.filter(s=>s.val/szTotal>=0.01).map(s=>s.name),datasets:[{data:rankYoy.filter(s=>s.val/szTotal>=0.01).map(s=>s.val),backgroundColor:['#2563eb','#3b82f6','#60a5fa','#93c5fd','#bfdbfe','#6366f1','#8b5cf6','#a78bfa','#c4b5fd','#ddd6fe','#059669','#34d399','#ec4899','#d97706','#7c3aed']}]},
    options:{responsive:true,plugins:{legend:{position:'bottom',labels:{font:{size:10},generateLabels:function(c){const ds=c.data.datasets[0];return ds.data.map((v,i)=>({text:(c.data.labels[i]||'')+': '+Math.round(v).toLocaleString()+' ('+Math.round(v/szTotal*100)+'%)',fillStyle:ds.backgroundColor[i],strokeStyle:'#fff',lineWidth:0,hidden:false,index:i}));}},title:{display:true,text:'尺寸占比 ('+(metric==='amt'?'销售额':'销量')+')'}},tooltip:{callbacks:{label:function(ctx){const v=ctx.parsed;return ctx.label+': '+Math.round(v).toLocaleString()+' ('+Math.round(v/szTotal*100)+'%)'}}}}}
  });
  // 趋势：各尺寸分线，每条带今年(实线)+去年(虚线)
  const yoyDates2=dates.map(d=>{const p=d.split('-');return (+p[0]-1)+'-'+p[1]+'-'+p[2];});
  const sizeColors=['#2563eb','#dc2626','#059669','#d97706','#7c3aed','#ec4899','#f59e0b','#6366f1','#14b8a6','#f97316','#8b5cf6','#e11d48'];
  const sizeDatasets=[];
  rankYoy.forEach((sz,i)=>{
    const sd=dates.map(dt=>{let v=sumDaily(daily,ch,dt,dt,sz.name,metric,true);return Math.round(v);});
    sizeDatasets.push({label:sz.name+(showYoy?' (今年)':''),data:sd,borderColor:sizeColors[i%sizeColors.length],backgroundColor:'transparent',fill:false,tension:.3,pointRadius:1,pointHitRadius:20,borderWidth:2});
    if(showYoy){
      const yd=yoyDates2.map(dt=>{let v=sumDaily(daily,ch,dt,dt,sz.name,metric,true);return v?Math.round(v):null;});
      sizeDatasets.push({label:sz.name+' (去年)',data:yd,borderColor:sizeColors[i%sizeColors.length],backgroundColor:'transparent',fill:false,tension:.3,pointRadius:1,pointHitRadius:20,borderWidth:1.5,borderDash:[4,4]});
    }
  });
  if(sizeTrendChart)sizeTrendChart.destroy();
  sizeTrendChart=new Chart(document.getElementById('sizeTrendChart'),{
    type:'line',
    data:{labels:dates,datasets:sizeDatasets},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'top',labels:{usePointStyle:true,boxWidth:8},onClick:function(e,legItem){const nm=legItem.text.replace(' (今年)','').replace(' (去年)','');const idx=hiddenSizes.indexOf(nm);if(idx>=0)hiddenSizes.splice(idx,1);else hiddenSizes.push(nm);renderSize()}},tooltip:{enabled:true,mode:'index',intersect:false,callbacks:{title:function(items){return items[0].label},label:function(ctx){var p=Math.round(ctx.parsed.y);return ctx.dataset.label+': '+(metric==='amt'?'¥'+p.toLocaleString()+'元':p.toLocaleString()+'件')}}}},hover:{mode:'index',intersect:false},scales:{y:{beginAtZero:true,ticks:{callback:v=>Math.round(metric==='amt'?v/10000:v)+''}}}}
  });
}
function resetSizes(){hiddenSizes=[];renderSize();}

// ===== 颜色看板 =====
let colorRankChart,colorTrendChart,colorPieChart;
function renderColor(){
  const ch=getVisChannels();
  const dates=getDatesInRange(startDate,endDate);
  if(!dates.length)return;
  const daily=getSizeColorData(true);
  const ranked=getSeriesRank(daily,ch,startDate,endDate,metric,0);
  const total=ranked.reduce((a,b)=>a+b[1],0);
  // 同比+环比计算
  const prev=getPrevPeriod(startDate,endDate);
  const yoy=getYoYPeriod(startDate,endDate);
  const rankYoy=ranked.map(([cl,v])=>{
    const yv=sumDaily(daily,ch,yoy.start,yoy.end,cl,metric,true);
    const pv=sumDaily(daily,ch,prev.start,prev.end,cl,metric,true);
    const gpct=yv?Math.round((v-yv)/yv*100):0;
    const mpct=pv?Math.round((v-pv)/pv*100):0;
    return {name:cl,val:Math.round(v),yoy:gpct,mom:mpct};
  });
  const yoyTotal2=sumDaily(daily,ch,yoy.start,yoy.end,'',metric,false);
  const prevTotal2=sumDaily(daily,ch,prev.start,prev.end,'',metric,false);
  document.getElementById('colorKpi').innerHTML=
    `<div class="kpi-card"><div class="label">颜色数</div><div class="value">${rankYoy.length}</div></div>`+
    `<div class="kpi-card"><div class="label">${metric==='amt'?'销售额':'销量'} <small>${dates.length}天</small></div><div class="value">${metric==='amt'?fmtD(total):Math.round(total).toLocaleString()}</div><div class="sub">环比 <span class="${total>=prevTotal2?'up':'down'}">${diffPct(total,prevTotal2)}</span> | 同比 <span class="${total>=yoyTotal2?'up':'down'}">${diffPct(total,yoyTotal2)}</span></div></div>`+
    (rankYoy.length?`<div class="kpi-card"><div class="label">TOP1 ${rankYoy[0].name}</div><div class="value">${metric==='amt'?fmtD(rankYoy[0].val):rankYoy[0].val.toLocaleString()}</div><div class="sub">环比 <span class="${rankYoy[0].mom>=0?'up':'down'}">${rankYoy[0].mom>=0?'+':''}${rankYoy[0].mom}%</span> | 同比 <span class="${rankYoy[0].yoy>=0?'up':'down'}">${rankYoy[0].yoy>=0?'+':''}${rankYoy[0].yoy}%</span></div></div>`:'');
  const topN=rankYoy.slice(0,12);
  document.getElementById('colorTrendLabel').textContent=startDate+' ~ '+endDate;
  if(colorRankChart)colorRankChart.destroy();
  const barLabels=topN.map(s=>s.name);
  colorRankChart=new Chart(document.getElementById('colorRankChart'),{
    type:'bar',
    data:{labels:barLabels,datasets:[{label:metric==='amt'?'销售额':'销量',data:topN.map(s=>s.val),backgroundColor:['#dc2626','#2563eb','#059669','#d97706','#7c3aed','#ec4899','#f59e0b','#6366f1','#14b8a6','#f97316','#8b5cf6','#e11d48']}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:function(ctx){const i=ctx.dataIndex;const d=topN[i];return' 价值: '+ctx.parsed.x.toLocaleString()+', 同比: '+(d.yoy>=0?'+':'')+d.yoy+'%, 环比: '+(d.mom>=0?'+':'')+d.mom+'%'}}}},scales:{x:{ticks:{callback:v=>Math.round(v/10000)+'万'}}}}
  });
  // 饼图
  if(colorPieChart)colorPieChart.destroy();
  const clTotal=rankYoy.reduce((a,b)=>a+b.val,0)||1;
  colorPieChart=new Chart(document.getElementById('colorPieChart'),{
    type:'pie',data:{labels:rankYoy.filter(s=>s.val/clTotal>=0.01).map(s=>s.name),datasets:[{data:rankYoy.filter(s=>s.val/clTotal>=0.01).map(s=>s.val),backgroundColor:['#dc2626','#2563eb','#059669','#d97706','#7c3aed','#ec4899','#f59e0b','#6366f1','#14b8a6','#f97316','#8b5cf6','#e11d48','#3b82f6','#10b981','#a855f7']}]},
    options:{responsive:true,plugins:{legend:{position:'bottom',labels:{font:{size:10},generateLabels:function(c){const ds=c.data.datasets[0];return ds.data.map((v,i)=>({text:(c.data.labels[i]||'')+': '+Math.round(v).toLocaleString()+' ('+Math.round(v/clTotal*100)+'%)',fillStyle:ds.backgroundColor[i],strokeStyle:'#fff',lineWidth:0,hidden:false,index:i}));}},title:{display:true,text:'颜色占比 ('+(metric==='amt'?'销售额':'销量')+')'}},tooltip:{callbacks:{label:function(ctx){const v=ctx.parsed;return ctx.label+': '+Math.round(v).toLocaleString()+' ('+Math.round(v/clTotal*100)+'%)'}}}}}
  });
  // 趋势：各颜色分线，每条带今年(实线)+去年(虚线)
  const yoyDates3=dates.map(d=>{const p=d.split('-');return (+p[0]-1)+'-'+p[1]+'-'+p[2];});
  const colorColors=['#dc2626','#2563eb','#059669','#d97706','#7c3aed','#ec4899','#f59e0b','#6366f1','#14b8a6','#f97316','#8b5cf6','#e11d48','#3b82f6','#10b981','#a855f7'];
  const clDatasets=[];
  rankYoy.slice(0,15).forEach((cl,i)=>{
    const cd=dates.map(dt=>{let v=sumDaily(daily,ch,dt,dt,cl.name,metric,true);return Math.round(v);});
    clDatasets.push({label:cl.name+(showYoy?' (今年)':''),data:cd,borderColor:colorColors[i%colorColors.length],backgroundColor:'transparent',fill:false,tension:.3,pointRadius:1,pointHitRadius:20,borderWidth:2});
    if(showYoy){
      const yd=yoyDates3.map(dt=>{let v=sumDaily(daily,ch,dt,dt,cl.name,metric,true);return v?Math.round(v):null;});
      clDatasets.push({label:cl.name+' (去年)',data:yd,borderColor:colorColors[i%colorColors.length],backgroundColor:'transparent',fill:false,tension:.3,pointRadius:1,pointHitRadius:20,borderWidth:1.5,borderDash:[4,4]});
    }
  });
  if(colorTrendChart)colorTrendChart.destroy();
  colorTrendChart=new Chart(document.getElementById('colorTrendChart'),{
    type:'line',
    data:{labels:dates,datasets:clDatasets},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'top',labels:{usePointStyle:true,boxWidth:8}},tooltip:{enabled:true,mode:'index',intersect:false,callbacks:{title:function(items){return items[0].label},label:function(ctx){var p=Math.round(ctx.parsed.y);return ctx.dataset.label+': '+(metric==='amt'?'¥'+p.toLocaleString()+'元':p.toLocaleString()+'件')}}}},hover:{mode:'index',intersect:false},scales:{y:{beginAtZero:true,ticks:{callback:v=>Math.round(metric==='amt'?v/10000:v)+''}}}}
  });
}

// ===== SKU分析 =====
var _skuFilterBuilt=false;
function renderSKU(keepFilters){
  // keepFilters=true时（渠道切换、指标切换）不重建筛选控件
  var ch=getVisChannels();
  var dates=getDatesInRange(startDate,endDate);
  var dayCount=dates.length;
  if(!dayCount){document.getElementById('skuContent').innerHTML='<h3>请选择日期范围</h3>';return;}
  console.log('renderSKU called, keepFilters='+keepFilters+', metric='+metric+', channels='+ch.join(','));

  var cat='all';
  var prevSelected='';
  var filterEl=document.getElementById('skuFilterBar');
  if(filterEl&&keepFilters){
    // 保持现有筛选控件
    cat=document.getElementById('skuCat')?document.getElementById('skuCat').value:'all';
    prevSelected=document.getElementById('skuSeries')?document.getElementById('skuSeries').value:'';
  }else{
    // 首次渲染或品类变化，重建筛选控件
    cat=document.getElementById('skuCat')?document.getElementById('skuCat').value:'all';
    prevSelected=document.getElementById('skuSeries')?document.getElementById('skuSeries').value:'';
  }
  console.log('renderSKU cat='+cat+' prevSelected='+prevSelected);

  var seriesList=(SKU_META.series||[]).filter(function(s){
    if(cat==='all')return true;
    if(cat==='luggage')return SKU_BY_SERIES[s]&&SKU_BY_SERIES[s].is_luggage;
    if(cat==='bag')return SKU_BY_SERIES[s]&&SKU_BY_SERIES[s].is_bag;
    return true;
  });

  var html='';
  if(!filterEl||!keepFilters){
    // 只有首次加载或品类变化时才重建筛选栏
    html='<div class="filters" id="skuFilterBar" style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:16px;background:#fff;padding:12px 16px;border-radius:10px">';
    html+='<label style="font-size:12px;color:#6b7280;font-weight:500">品类</label>';
    html+='<select id="skuCat" onchange="renderSKU()" style="border:1px solid #d1d5db;border-radius:6px;padding:5px 10px;font-size:13px;background:#fff"><option value="all"'+(cat==='all'?' selected':'')+'>全部</option><option value="luggage"'+(cat==='luggage'?' selected':'')+'>行李箱</option><option value="bag"'+(cat==='bag'?' selected':'')+'>包袋</option></select>';
    html+='<label style="font-size:12px;color:#6b7280">系列</label>';
    html+='<select id="skuSeries" onchange="renderSKU()" style="border:1px solid #d1d5db;border-radius:6px;padding:5px 10px;font-size:13px;background:#fff"><option value="">请选择系列</option>';
    seriesList.sort().forEach(function(s){
      if(SKU_BY_SERIES[s])html+='<option value="'+s+'"'+(s===prevSelected?' selected':'')+'>'+s+'</option>';
    });
    html+='</select>';
    html+='</div>';
  }

  var selSeries=prevSelected;
  if(!selSeries){html+='<div class="placeholder" style="height:200px">选择一个系列以查看SKU分析</div>';document.getElementById('skuContent').innerHTML=html;return;}

  var seriesData=SKU_BY_SERIES[selSeries];
  if(!seriesData||!seriesData.skus){html+='<div class="placeholder">该系列暂无SKU数据</div>';document.getElementById('skuContent').innerHTML=html;return;}

  // 计算该系列在筛选日期范围内、按渠道过滤的总量
  var seriesTotal={amt:0,qty:0};
  var seriesDaily={};
  var visCh=getVisChannels();
  dates.forEach(function(dt){
    if(!SKU_CH_DAILY[dt])return;
    visCh.forEach(function(c){
      if(!SKU_CH_DAILY[dt][c])return;
      Object.keys(SKU_CH_DAILY[dt][c]).forEach(function(sk){
        if(!sk.startsWith(selSeries+'|'))return;
        seriesTotal.amt+=SKU_CH_DAILY[dt][c][sk].amt||0;
        seriesTotal.qty+=SKU_CH_DAILY[dt][c][sk].qty||0;
        if(!seriesDaily[sk])seriesDaily[sk]={amt:0,qty:0};
        seriesDaily[sk].amt+=SKU_CH_DAILY[dt][c][sk].amt||0;
        seriesDaily[sk].qty+=SKU_CH_DAILY[dt][c][sk].qty||0;
      });
    });
  });

  // 如果切换渠道后该系列无数据，显示提示
  var skuCount=Object.keys(seriesDaily).length;
  if(skuCount===0){
    if(!filterEl||!keepFilters){
      html+='<div class="placeholder" style="height:200px">该渠道无此品类数据</div>';
      document.getElementById('skuContent').innerHTML=html;
    }else{
      document.getElementById('skuDataArea').innerHTML='<div class="placeholder" style="height:200px">该渠道无此品类数据</div>';
    }
    return;
  }

  // KPI
  var topSKU=Object.entries(seriesDaily).sort(function(a,b){return b[1][metric]-a[1][metric]})[0];
  html+='<div class="kpi-grid"><div class="kpi-card"><div class="label">SKU数</div><div class="value">'+skuCount+'</div></div>';
  html+='<div class="kpi-card"><div class="label">'+selSeries+' '+(metric==='amt'?'销售额':'销量')+'</div><div class="value">'+(metric==='amt'?fmtD(seriesTotal.amt):Math.round(seriesTotal.qty).toLocaleString())+'</div></div>';
  if(topSKU)html+='<div class="kpi-card"><div class="label">TOP1 SKU</div><div class="value" style="font-size:14px">'+topSKU[0].split('|').slice(1).join(' / ')+'</div><div class="sub">'+(metric==='amt'?fmtD(topSKU[1][metric]):topSKU[1][metric].toLocaleString())+'</div></div>';
  html+='</div>';

  // 提炼颜色和尺寸
  var colorMap={},sizeMap={};
  Object.keys(seriesDaily).forEach(function(sk){
    var parts=sk.split('|');
    if(parts.length>=3){var col=parts[1]||'未知',sz=parts[2]||'均码';
      if(!colorMap[col])colorMap[col]={};
      if(!colorMap[col][sz])colorMap[col][sz]={amt:0,qty:0};
      colorMap[col][sz].amt+=seriesDaily[sk].amt||0;
      colorMap[col][sz].qty+=seriesDaily[sk].qty||0;
      if(!sizeMap[sz])sizeMap[sz]={};
      if(!sizeMap[sz][col])sizeMap[sz][col]={amt:0,qty:0};
      sizeMap[sz][col].amt+=seriesDaily[sk].amt||0;
      sizeMap[sz][col].qty+=seriesDaily[sk].qty||0;
    }
  });
  var colorsSorted=Object.keys(colorMap).sort(function(a,b){var ta=0;Object.values(colorMap[a]).forEach(function(v){ta+=v[metric]||0;});var tb=0;Object.values(colorMap[b]).forEach(function(v){tb+=v[metric]||0;});return tb-ta;});
  var sizesSorted=Object.keys(sizeMap).sort(function(a,b){var ta=0;Object.values(sizeMap[a]).forEach(function(v){ta+=v[metric]||0;});var tb=0;Object.values(sizeMap[b]).forEach(function(v){tb+=v[metric]||0;});return tb-ta;});

  var totalForPct=seriesTotal[metric]||1;
  html+='<h3 style="font-size:13px;margin:12px 0 8px;color:#374151">颜色×尺寸销售矩阵</h3><div class="table-wrap" style="margin-bottom:14px"><table><thead><tr><th>颜色 \\ 尺寸</th>';
  sizesSorted.forEach(function(sz){html+='<th style="font-size:11px;text-align:center">'+sz+'</th>';});
  html+='<th style="font-size:11px;text-align:center;background:#f3f4f6">小计</th></tr></thead><tbody>';
  colorsSorted.forEach(function(col){
    html+='<tr><td style="font-weight:500;white-space:nowrap">'+col+'</td>';
    var colAmt=0;
    sizesSorted.forEach(function(sz){
      var v=colorMap[col]&&colorMap[col][sz]?colorMap[col][sz][metric]||0:0;
      colAmt+=v;
      if(v>0){
        var pct=Math.round(v/totalForPct*100);
        html+='<td onclick="showSKUDetail(\''+selSeries+'|'+col+'|'+sz+'\')" style="cursor:pointer;background:rgba(37,99,235,'+(v/totalForPct*5+0.1).toFixed(2)+');text-align:center;font-weight:600">'+(metric==='amt'?fmtD(v):Math.round(v).toLocaleString())+'<br><span style="font-size:12px;font-weight:600;color:'+(v/totalForPct>0.1?'#fff':'#374151')+'">'+pct+'%</span></td>';
      }else{
        html+='<td style="text-align:center;color:#d1d5db">—</td>';
      }
    });
    html+='<td style="text-align:center;font-weight:600;background:#f3f4f6">'+(metric==='amt'?fmtD(colAmt):Math.round(colAmt).toLocaleString())+'</td></tr>';
  });
  html+='<tr class="summary"><td>合计</td>';
  sizesSorted.forEach(function(sz){
    var szAmt=0;
    colorsSorted.forEach(function(col){if(colorMap[col]&&colorMap[col][sz])szAmt+=colorMap[col][sz][metric]||0;});
    html+='<td style="text-align:center">'+(metric==='amt'?fmtD(szAmt):Math.round(szAmt).toLocaleString())+'</td>';
  });
  html+='<td style="text-align:center;font-weight:700">'+(metric==='amt'?fmtD(seriesTotal[metric]):Math.round(seriesTotal[metric]).toLocaleString())+'</td></tr>';
  html+='</tbody></table></div>';

  // 帕累托
  var sortedSKU=Object.entries(seriesDaily).sort(function(a,b){return b[1][metric]-a[1][metric];});
  var cumul=0;
  html+='<div class="chart-box full" style="margin-bottom:14px"><h3>帕累托分析 (ABC)</h3><div class="table-wrap"><table><thead><tr><th>#</th><th>SKU</th><th>'+(metric==='amt'?'销售额':'销量')+'</th><th>占比</th><th>累计</th><th>等级</th></tr></thead><tbody>';
  sortedSKU.forEach(function(sk,i){
    cumul+=sk[1][metric];
    var pct=Math.round(sk[1][metric]/totalForPct*100);
    var cumPct=Math.round(cumul/totalForPct*100);
    var grade=cumPct<=70?'<span style="color:#dc2626;font-weight:700">A</span>':cumPct<=90?'<span style="color:#d97706;font-weight:700">B</span>':'<span style="color:#6b7280">C</span>';
    html+='<tr><td>'+(i+1)+'</td><td>'+sk[0].split('|').slice(1).join(' / ')+'</td><td>'+(metric==='amt'?fmtD(sk[1][metric]):Math.round(sk[1][metric]).toLocaleString())+'</td><td>'+pct+'%</td><td>'+cumPct+'%</td><td>'+grade+'</td></tr>';
  });
  html+='</tbody></table></div></div>';
  html+='<div style="padding:8px 14px;background:#f9fafb;border-radius:0 0 10px 10px;font-size:11px;color:#6b7280;border-top:1px solid #e5e7eb">';
  html+='<b>说明：</b>SKU按销售额/销量从高到低排序，"累计"表示前N个SKU的总占比。';
  html+='A类(0-70%)核心款、B类(70-90%)中坚款、C类(90-100%)长尾款。<br>';
  html+='<b>策略建议：</b>A类重点保障库存和投放；B类维持观察；C类考虑清仓或淘汰。</div>';

  // 生命周期卡片
  html+='<div class="chart-box full" style="margin-bottom:14px"><h3>生命周期状态</h3><div class="kpi-grid" style="grid-template-columns:1fr 1fr">';
  var totalMonths=Math.round(Object.keys(SKU_DAILY).length/30);
  var slugCount=seriesList.length;
  var avgPrice=seriesTotal.qty>0?Math.round(seriesTotal.amt/seriesTotal.qty):0;
  // 简单生命周期判断
  var lifecycle='';
  if(seriesTotal.amt<=0)lifecycle='<span style="color:#9ca3af">No Data</span>';
  else if(Object.keys(seriesDaily).length<3)lifecycle='<span style="background:#dbeafe;color:#2563eb;padding:2px 10px;border-radius:10px">导入期</span>';
  else{
    // 检测最近3个月趋势
    var recent3=dates.slice(-90);
    if(recent3.length<30)recent3=dates;
    var recentAmt=0;var visCh=getVisChannels();recent3.forEach(function(dt){if(!SKU_CH_DAILY[dt])return;visCh.forEach(function(c){if(!SKU_CH_DAILY[dt][c])return;Object.keys(SKU_CH_DAILY[dt][c]).forEach(function(sk){if(sk.startsWith(selSeries+'|'))recentAmt+=SKU_CH_DAILY[dt][c][sk][metric]||0;});});});
    if(recentAmt>seriesTotal.amt*0.6)lifecycle='<span style="background:#dcfce7;color:#059669;padding:2px 10px;border-radius:10px">🟢 导入期</span>';
    else if(Object.keys(seriesDaily).length>6)lifecycle='<span style="background:#fef3c7;color:#d97706;padding:2px 10px;border-radius:10px">🟡 成熟期</span>';
    else lifecycle='<span style="background:#dbeafe;color:#2563eb;padding:2px 10px;border-radius:10px">🔵 成长期</span>';
  }
  html+='<div class="kpi-card"><div class="label">生命周期</div><div class="value" style="font-size:16px">'+lifecycle+'</div></div>';
  html+='<div class="kpi-card"><div class="label">均价</div><div class="value" style="font-size:16px">¥'+avgPrice.toLocaleString()+'</div></div>';
  html+='<div class="kpi-card"><div class="label">系列数</div><div class="value" style="font-size:16px">'+slugCount+'</div></div>';
  html+='<div class="kpi-card"><div class="label">数据天数</div><div class="value" style="font-size:16px">'+Object.keys(SKU_DAILY).length+'天</div></div>';
  html+='</div></div>';

  // 集中度风险
  var top1=0,top3=0,top5=0;
  sortedSKU.forEach(function(sk,i){
    if(i===0)top1=sk[1][metric]/totalForPct*100;
    if(i<3)top3+=sk[1][metric];
    if(i<5)top5+=sk[1][metric];
  });
  top3=Math.round(top3/totalForPct*100);
  top5=Math.round(top5/totalForPct*100);
  var riskColor1=top1>30?'#dc2626':top1>20?'#d97706':'#059669';
  var riskColor3=top3>60?'#dc2626':top3>45?'#d97706':'#059669';
  var riskColor5=top5>80?'#dc2626':top5>65?'#d97706':'#059669';
  html+='<div class="chart-box full" style="margin-bottom:14px"><h3>集中度风险仪表</h3><div class="kpi-grid" style="grid-template-columns:repeat(3,1fr)">';
  html+='<div class="kpi-card" style="text-align:center"><div class="label">TOP1 SKU占比</div><div style="font-size:36px;font-weight:700;color:'+riskColor1+'">'+Math.round(top1)+'%</div><div class="sub">'+(top1>30?'⚠️ 风险偏高':top1>20?'⚠️ 需关注':'✅ 健康')+'</div></div>';
  html+='<div class="kpi-card" style="text-align:center"><div class="label">TOP3 SKU占比</div><div style="font-size:36px;font-weight:700;color:'+riskColor3+'">'+top3+'%</div><div class="sub">'+(top3>60?'⚠️ 风险偏高':top3>45?'⚠️ 需关注':'✅ 健康')+'</div></div>';
  html+='<div class="kpi-card" style="text-align:center"><div class="label">TOP5 SKU占比</div><div style="font-size:36px;font-weight:700;color:'+riskColor5+'">'+top5+'%</div><div class="sub">'+(top5>80?'⚠️ 风险偏高':top5>65?'⚠️ 需关注':'✅ 健康')+'</div></div>';
  // 自动生成解读文本
  var analysisParts=[];
  if(top1>20)analysisParts.push('TOP1 SKU占比'+Math.round(top1)+'%，'+(top1>30?'单一SKU依赖过高，若该SKU出现库存或渠道问题将显著影响整体业绩':'集中度偏高，建议关注TOP1 SKU的库存深度'));
  if(top3>45)analysisParts.push('TOP3 SKU合计占比'+top3+'%，产品矩阵偏集中，'+(top3>60?'建议通过新品培育或中腰部SKU投放来分散风险':'可评估TOP3之外的SKU增长潜力'));
  if(top5>65)analysisParts.push('TOP5 SKU合计占比'+top5+'%，长尾SKU贡献不足，建议定期评估淘汰低效SKU并扶持新潜力款');
  if(analysisParts.length===0)analysisParts.push('SKU分布较为分散，产品矩阵健康');
  html+='</div>';
  html+='<div style="background:#f8fafc;border-radius:8px;padding:12px 16px;margin-top:8px;border-left:3px solid '+(top3>60?'#dc2626':top3>45?'#d97706':'#059669')+'">';
  html+='<div style="font-size:12px;color:#374151;line-height:1.8">📊 <strong>数据解读：</strong>'+analysisParts.join('；')+'</div>';
  html+='</div></div>';

  // SKU详情区（占位，点击矩阵格子后填充）
  html+='<div id="skuDetailArea"></div>';

  if(filterEl&&keepFilters){
    // 渠道/指标切换：只刷新数据区
    console.log('SKU: keepFilters mode, updating skuDataArea');
    var dataArea=document.getElementById('skuDataArea');
    if(!dataArea){
      // 首次keepFilters但无skuDataArea，回退全量刷新
      console.log('SKU: skuDataArea not found, full refresh');
      document.getElementById('skuContent').innerHTML=html;
    }else{
      dataArea.innerHTML=html;
    }
  }else{
    // 首次加载或品类变化：全量刷新
    console.log('SKU: full refresh mode');
    document.getElementById('skuContent').innerHTML=html+'<div id="skuDataArea"></div>';
  }
}

function renderSKUData(){
  console.log('renderSKUData called');
  // 只刷新SKU数据区域（不重建筛选控件），供渠道/指标切换时调用
  renderSKU(true);
}

// SKU详情展示
function showSKUDetail(skuKey){
  var dates=getDatesInRange(startDate,endDate);
  var total={amt:0,qty:0};
  var visCh=getVisChannels();
  var trendNow=dates.map(function(dt){
    var v=0;if(!SKU_CH_DAILY[dt])return 0;visCh.forEach(function(c){if(SKU_CH_DAILY[dt][c]&&SKU_CH_DAILY[dt][c][skuKey]){v+=SKU_CH_DAILY[dt][c][skuKey][metric]||0;total.amt+=SKU_CH_DAILY[dt][c][skuKey].amt||0;total.qty+=SKU_CH_DAILY[dt][c][skuKey].qty||0;}});
    return Math.round(v);
  });

  // 同期对比值计算（用于KPI卡片展示）
  var yoyD=dates.map(function(d){var p=d.split('-');return (+p[0]-1)+'-'+p[1]+'-'+p[2];});
  var yoyTotal=0;
  if(showYoy){
    yoyD.forEach(function(dt){
      var v=0;if(!SKU_CH_DAILY[dt])return;visCh.forEach(function(c){if(SKU_CH_DAILY[dt][c]&&SKU_CH_DAILY[dt][c][skuKey])v+=SKU_CH_DAILY[dt][c][skuKey][metric]||0;});
      yoyTotal+=Math.round(v);
    });
  }
  var hasYoyNum=yoyTotal>0;
  var yoyPct=hasYoyNum?Math.round((total[metric]-yoyTotal)/yoyTotal*100):null;

  var parts=skuKey.split('|');
  var series=parts[0]||'',color=parts[1]||'',size=parts[2]||'';

  var html='<div class="chart-box full"><h3>SKU详情: '+color+' / '+size+'</h3>';
  html+='<div class="kpi-grid" style="grid-template-columns:repeat(3,1fr);margin-bottom:8px">';
  html+='<div class="kpi-card"><div class="label">'+(metric==='amt'?'销售额':'销量')+'</div><div class="value" style="font-size:18px">'+(metric==='amt'?fmtD(total.amt):Math.round(total.qty).toLocaleString())+'</div><div class="sub" style="font-size:10px;color:#2563eb">筛选期内</div></div>';
  html+='<div class="kpi-card"><div class="label">均价</div><div class="value" style="font-size:18px">¥'+(total.qty?Math.round(total.amt/total.qty).toLocaleString():'—')+'</div></div>';
  html+='<div class="kpi-card"><div class="label">趋势方向</div><div class="value" style="font-size:18px">'+(trendNow.length>1?(trendNow[trendNow.length-1]>=trendNow[0]?'<span class="up">▲ 上升</span>':'<span class="down">▼ 下降</span>'):'—')+'</div><div class="sub" style="font-size:10px;color:#9ca3af">首尾对比</div></div>';
  html+='</div>';
  if(hasYoyNum){
    html+='<div style="display:flex;gap:12px;margin-bottom:10px">';
    html+='<div style="flex:1;padding:8px 10px;background:#f0f5ff;border-radius:6px;text-align:center;border:1px solid #dbeafe"><div style="font-size:10px;color:#6b7280;margin-bottom:2px">去年同期</div><div style="font-size:16px;font-weight:600;color:#2563eb">'+(metric==='amt'?fmtD(yoyTotal):Math.round(yoyTotal).toLocaleString())+'</div><div style="font-size:9px;color:#9ca3af">'+dates[0]+' ~ '+dates[dates.length-1]+'</div></div>';
    html+='<div style="flex:1;padding:8px 10px;background:'+(yoyPct>0?'#f0fdf4':yoyPct<0?'#fef2f2':'#f9fafb')+';border-radius:6px;text-align:center;border:1px solid '+(yoyPct>0?'#bbf7d0':yoyPct<0?'#fecaca':'#e5e7eb')+'"><div style="font-size:10px;color:#6b7280;margin-bottom:2px">同比变化</div><div style="font-size:20px;font-weight:700;color:'+(yoyPct>0?'#059669':yoyPct<0?'#dc2626':'#6b7280')+'">'+(yoyPct>0?'+':'')+yoyPct+'%</div><div style="font-size:11px;color:'+(yoyPct>0?'#059669':yoyPct<0?'#dc2626':'#6b7280')+'">'+(metric==='amt'?(yoyPct>0?'+':'')+fmtD(total.amt-yoyTotal):(Math.round(total.qty-yoyTotal)>0?'+':'')+Math.round(total.qty-yoyTotal).toLocaleString())+'</div></div>';
    html+='</div>';
  }
  html+='<div class="chart-box full"><canvas id="skuDetailTrend"></canvas><div style="margin-top:6px;font-size:11px;color:#9ca3af;text-align:center">▲ 上升 / ▼ 下降：对比时间段首尾日数值，整体呈增长为上升、反之为下降。中间波动不影响趋势判定。</div></div></div>';
  document.getElementById('skuDetailArea').innerHTML=html;

  // 趋势图
  var yoyD=dates.map(function(d){var p=d.split('-');return (+p[0]-1)+'-'+p[1]+'-'+p[2];});
  var yoyTrend=showYoy?yoyD.map(function(dt){
    var v=0;if(!SKU_CH_DAILY[dt])return null;visCh.forEach(function(c){if(SKU_CH_DAILY[dt][c]&&SKU_CH_DAILY[dt][c][skuKey])v+=SKU_CH_DAILY[dt][c][skuKey][metric]||0;});
    return v?Math.round(v):null;
  }):[];
  var hasSkuYoy=yoyTrend.some(function(x){return x!==null&&x!==undefined;});
  new Chart(document.getElementById('skuDetailTrend'),{type:'line',data:{labels:dates,datasets:[{label:'今年',data:trendNow,borderColor:'#2563eb',backgroundColor:'rgba(37,99,235,0.1)',fill:true,tension:.3,pointRadius:1,pointHitRadius:20,borderWidth:2},{label:'去年同期',data:showYoy&&hasSkuYoy?yoyTrend:[],borderColor:'#9ca3af',backgroundColor:'transparent',fill:false,tension:.3,pointRadius:1,pointHitRadius:20,borderWidth:2,borderDash:[5,5]}].filter(function(ds){return ds.data.length>0})},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{enabled:true,mode:'index',intersect:false,callbacks:{title:function(items){return items[0].label},label:function(ctx){var p=Math.round(ctx.parsed.y);return ctx.dataset.label+': '+(metric==='amt'?'¥'+p.toLocaleString()+'元':p.toLocaleString()+'件')}}}},hover:{mode:'index',intersect:false},scales:{y:{beginAtZero:true,ticks:{callback:function(v){return Math.round(metric==='amt'?v/10000:v)+''}}}}}});
}

// ===== 启动 =====
initFilters();
renderLuggage();
</script>
</div>
</body>
</html>'''

# ===== 注入对比功能代码（f58c8a0 移植） =====
COMPARE_CSS = '''/* 对比功能 */
.compare-btn{display:inline-flex;align-items:center;gap:4px;padding:3px 12px;border:1px dashed #c9a962;border-radius:6px;background:transparent;color:#c9a962;font-size:11px;font-weight:500;cursor:pointer;transition:all .2s;vertical-align:middle;margin:0 4px;font-family:inherit}
.compare-btn:hover{background:rgba(201,169,98,.08);border-style:solid}
.compare-btn.active{background:#c9a962;color:#fff;border-style:solid}
.compare-period{display:none;align-items:center;gap:4px;vertical-align:middle}
.compare-period.visible{display:inline-flex}
.compare-period input[type=date]{border:1px solid #d1d5db;border-radius:6px;padding:3px 8px;font-size:12px;width:115px}
.compare-row{display:none;border-top:2px dashed #c9a962;margin-top:6px;padding-top:10px;margin-bottom:4px;position:relative}
.compare-row.show{display:block}
.compare-row::before{content:'\u5bf9\u6bd4\u5468\u671f';position:absolute;top:-8px;left:0;font-size:10px;color:#c9a962;background:#f3f4f6;padding:0 10px;font-weight:600;z-index:1}
.compare-row .kpi-card{background:rgba(201,169,98,.04);border:1px solid rgba(201,169,98,.2)}
'''

RENDER_COMPARE_ROW_FN = '''
function renderCompareRow(containerId,data,ch,start,end,metric){
  var container=document.getElementById(containerId);
  if(!container)return;
  var compareEl=container.parentElement.querySelector('.compare-row');
  if(!compareEl){
    compareEl=document.createElement('div');
    compareEl.className='compare-row';
    container.parentElement.insertBefore(compareEl,container.nextSibling);
  }
  if(!compareOn||!cStart||!cEnd){compareEl.classList.remove('show');return}
  var cTotal=sumDaily(data,ch,cStart,cEnd,'',metric,false);
  var mTotal=sumDaily(data,ch,start,end,'',metric,false);
  var diffV=mTotal-cTotal;
  var diffP=cTotal>0?(diffV/cTotal*100).toFixed(1):'-';
  var isUp=diffV>=0;
  compareEl.innerHTML='<div class="kpi-card"><div class="label">\u5bf9\u6bd4\u671f '+(metric==='amt'?'\u9500\u552e\u989d':'\u9500\u91cf')+'</div><div class="value">'+(metric==='amt'?fmtD(cTotal):cTotal.toLocaleString())+'</div><div class="sub" style="color:#9ca3af;font-size:10px">'+cStart+' ~ '+cEnd+'</div></div><div class="kpi-card"><div class="label">\u53d8\u5316\u989d</div><div class="value '+(isUp?'up':'down')+'">'+(isUp?'+':'')+(metric==='amt'?fmtD(diffV):diffV.toLocaleString())+'</div><div class="sub" style="color:#9ca3af;font-size:10px">\u53d8\u5316\u7387: '+(diffP==='-'?'-':(isUp?'+':'')+diffP+'%')+'</div></div>';
  compareEl.classList.add('show');
}

// ===== 退货分析（2026-07-30 新增，v3 修复双重累加） =====
// 退货对比行（与 renderCompareRow 解耦，复用 compare-row 样式）；支持渠道数组
function renderReturnCompareRow(containerId,retD,chs,start,end,metric){
  var container=document.getElementById(containerId);
  if(!container)return;
  var compareEl=container.parentElement.querySelector('.compare-row');
  if(!compareEl){
    compareEl=document.createElement('div');
    compareEl.className='compare-row';
    container.parentElement.insertBefore(compareEl,container.nextSibling);
  }
  if(!compareOn||!cStart||!cEnd){compareEl.classList.remove('show');return}
  var key=metric==='amt'?'return_amt':'return_qty';
  var cTotal=0,mTotal=0;
  getDatesInRange(cStart,cEnd).forEach(function(d){
    if(!retD[d])return;
    chs.forEach(function(ch){var t=retD[d][ch]&&retD[d][ch]['$total'];if(t)cTotal+=t[key]||0;});
  });
  getDatesInRange(start,end).forEach(function(d){
    if(!retD[d])return;
    chs.forEach(function(ch){var t=retD[d][ch]&&retD[d][ch]['$total'];if(t)mTotal+=t[key]||0;});
  });
  var diffV=mTotal-cTotal;
  var diffP=cTotal>0?(diffV/cTotal*100).toFixed(1):'-';
  var isUp=diffV>=0;  // 退货增加是负向
  compareEl.innerHTML='<div class="kpi-card"><div class="label">对比期 退货'+(metric==='amt'?'金额':'数量')+'</div><div class="value">'+(metric==='amt'?fmtD(cTotal):cTotal.toLocaleString())+'</div><div class="sub" style="color:#9ca3af;font-size:10px">'+cStart+' ~ '+cEnd+'</div></div><div class="kpi-card"><div class="label">变化额</div><div class="value '+(isUp?'down':'up')+'" style="color:'+(isUp?'#dc2626':'#059669')+'">'+(isUp?'+':'')+(metric==='amt'?fmtD(diffV):diffV.toLocaleString())+'</div><div class="sub" style="color:#9ca3af;font-size:10px">变化率: '+(diffP==='-'?'-':(isUp?'+':'')+diffP+'%')+'</div></div>';
  compareEl.classList.add('show');
}
function renderReturn(){
  var cat=document.getElementById('returnCat').value;
  var daily=cat==='luggage'?LUG_DAILY:cat==='bag'?BAG_DAILY:ALL_DAILY;
  var retD=cat==='luggage'?RET_LUG_DAILY:cat==='bag'?RET_BAG_DAILY:RET_ALL_DAILY;
  var chs=getVisChannels();
  var m=metric||'amt';
  var totalRet=0,totalRetQty=0,totalSales=0,seriesMap={},chMap={};
  var dates=getDatesInRange(startDate,endDate);
  dates.forEach(function(d){
    if(!retD[d])return;
    chs.forEach(function(ch){
      var chData=retD[d][ch];
      if(!chData)return;
      Object.keys(chData).forEach(function(sk){
        if(sk==='$total')return;  // ��过$total避免双重累加
        var v=chData[sk];
        if(!v)return;
        totalRet+=v.return_amt||0;
        totalRetQty+=v.return_qty||0;
        if(daily[d]&&daily[d][ch]){
          var s=daily[d][ch][sk];
          if(s) totalSales+=s.amt||0;
        }
        seriesMap[sk]=seriesMap[sk]||{amt:0,qty:0};
        seriesMap[sk].amt+=v.return_amt||0;
        seriesMap[sk].qty+=v.return_qty||0;
      });
      // 渠道维度用 $total 汇总
      var chTot=chData['$total'];
      if(chTot){
        chMap[ch]=chMap[ch]||{amt:0,qty:0};
        chMap[ch].amt+=chTot.return_amt||0;
        chMap[ch].qty+=chTot.return_qty||0;
      }
    });
  });
  var rate=totalSales>0?(totalRet/totalSales*100):0;
  renderReturnCompareRow('returnKpi',retD,chs,startDate,endDate,m);
  document.getElementById('returnKpi').innerHTML=
    '<div class="kpi-card"><div class="label">退货金额</div><div class="value">'+fmtD(totalRet)+'</div></div>'+
    '<div class="kpi-card"><div class="label">退货数量</div><div class="value">'+totalRetQty.toLocaleString()+'笔</div></div>'+
    '<div class="kpi-card"><div class="label">退货率</div><div class="value" style="color:'+(rate>10?'#dc2626':'#059669')+'">'+rate.toFixed(1)+'%</div><div class="sub">退货/销售</div></div>'+
    '<div class="kpi-card"><div class="label">退货占比<<总销售</div><div class="value" style="color:#8b5cf6">'+(totalSales>0?(totalRet/totalSales*100).toFixed(1):'-')+'%</div></div>'+
    '<div class="kpi-card" style="background:rgba(37,99,235,.04);border-color:rgba(37,99,235,.15)"><div class="label">当前维度</div><div class="value" style="color:#2563eb;font-size:16px">'+(m==='amt'?'按金额':'按数量')+'</div>';
  // 趋势图（联动 metric）
  var labels=[],retData=[],trendLabel=(m==='amt'?'退货金额':'退货数量');
  dates.forEach(function(d){
    var v=0;
    if(retD[d]) chs.forEach(function(ch){
      var t=retD[d][ch]&&retD[d][ch]['$total']; if(t) v+=(m==='amt'?t.return_amt:t.return_qty)||0;
    });
    labels.push(d.slice(5));
    retData.push(v);
  });
  if(window.retTrendChart)window.retTrendChart.destroy();
  window.retTrendChart=new Chart(document.getElementById('returnTrendChart'),{
    type:'bar',data:{labels:labels,datasets:[{label:trendLabel,data:retData,backgroundColor:'rgba(220,38,38,.65)',borderColor:'#dc2626',borderWidth:1,borderRadius:3}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false}},
      scales:{y:{beginAtZero:true,ticks:{callback:function(v){return m==='amt'?(v>=10000?Math.round(v/10000)+'万':v):v}}}}}
  });
  // 系列排行（Top15，联动 metric）
  var sorted=Object.keys(seriesMap).sort(function(a,b){return (m==='amt'?seriesMap[b].amt:seriesMap[b].qty)-(m==='amt'?seriesMap[a].amt:seriesMap[a].qty)}).slice(0,15);
  var rLabels=[],rData=[];
  sorted.forEach(function(sk,i){
    rLabels.push(sk);
    rData.push(m==='amt'?seriesMap[sk].amt:seriesMap[sk].qty);
  });
  if(window.retRankChart)window.retRankChart.destroy();
  window.retRankChart=new Chart(document.getElementById('returnRankChart'),{
    type:'bar',data:{labels:rLabels,datasets:[{label:trendLabel,data:rData,backgroundColor:rData.map(function(v,i){return i===0?'#dc2626':i<3?'#ea580c':'#f97316'}),borderRadius:3}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false}},
      scales:{x:{ticks:{callback:function(v){return m==='amt'?(v>=10000?Math.round(v/10000)+'万':v):v}}}}}
  });
  // 渠道占比（联动 metric，显示百分比）
  var chSorted=chs.filter(function(c){return chMap[c]}).sort(function(a,b){return (m==='amt'?chMap[b].amt:chMap[b].qty)-(m==='amt'?chMap[a].amt:chMap[a].qty)});
  var chTotal=chSorted.reduce(function(s,c){return s+(m==='amt'?chMap[c].amt:chMap[c].qty)},0);
  var pieColors=['#dc2626','#ea580c','#f97316','#fbbf24','#a3e635','#34d399','#06b6d4','#6366f1','#a855f7'];
  if(window.retPieChart)window.retPieChart.destroy();
  window.retPieChart=new Chart(document.getElementById('returnPieChart'),{
    type:'doughnut',
    data:{labels:chSorted,datasets:[{data:chSorted.map(function(c){return m==='amt'?chMap[c].amt:chMap[c].qty}),backgroundColor:pieColors.slice(0,chSorted.length),borderWidth:0}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{position:'right',labels:{boxWidth:12,font:{size:11},generateLabels:function(chart){
          var data=chart.data;return data.labels.map(function(l,i){
            var val=data.datasets[0].data[i],pct=chTotal>0?(val/chTotal*100).toFixed(1):0;
            return {text:l+': '+pct+'%',fillStyle:data.datasets[0].backgroundColor[i],strokeStyle:'transparent',pointStyle:'circle',hidden:false,index:i};
          });
        }}},
        tooltip:{callbacks:{label:function(ctx){
          var val=ctx.parsed||0,pct=chTotal>0?(val/chTotal*100).toFixed(1):0;
          return (m==='amt'?fmtD(val):val.toLocaleString())+' ('+pct+'%)';
        }}}
      }
    }
  });
}
'''

COMPARE_EVENTS = '''
document.getElementById('compareToggle').addEventListener('click',function(){
  compareOn=!compareOn;this.classList.toggle('active');
  document.getElementById('comparePeriod').classList.toggle('visible');
  renderCurrentTab();
});
document.getElementById('compareStart').addEventListener('change',function(){cStart=this.value;if(compareOn)renderCurrentTab();});
document.getElementById('compareEnd').addEventListener('change',function(){cEnd=this.value;if(compareOn)renderCurrentTab();});
'''

html = html.replace('.val-qty{color:#2563eb}', '.val-qty{color:#2563eb}\n' + COMPARE_CSS)
html = html.replace('let showYoy=false;', 'let showYoy=false;\nlet compareOn=false,cStart="2026-06-01",cEnd="2026-06-30";')
compare_btn = '<button class="compare-btn" id="compareToggle"><i data-lucide="git-compare" style="width:14px;height:14px;display:none"></i>\u5bf9\u6bd4</button><div class="compare-period" id="comparePeriod"><span style="font-size:11px;color:#6b7280">\u5bf9\u6bd4</span><input type="date" id="compareStart" value="2026-06-01"><span style="font-size:11px;color:#6b7280">\u81f3</span><input type="date" id="compareEnd" value="2026-06-30"></div>'
html = html.replace('<input type="checkbox" id="chkYoy"', compare_btn + '\n    <input type="checkbox" id="chkYoy"')
html = html.replace('function toggleCh(', RENDER_COMPARE_ROW_FN + '\nfunction toggleCh(')
html = html.replace("document.getElementById('lugKpi').innerHTML=", "  renderCompareRow('lugKpi',LUG_DAILY,ch,startDate,endDate,metric);\n  document.getElementById('lugKpi').innerHTML=")
html = html.replace("document.getElementById('bagKpi').innerHTML=", "  renderCompareRow('bagKpi',BAG_DAILY,ch,startDate,endDate,metric);\n  document.getElementById('bagKpi').innerHTML=")
# seriesKpi 包袋占比注入
html = html.replace(
    "// KPI（使用筛选后的数据）",
    "var _lugV=sumDaily(LUG_DAILY,ch,startDate,endDate,'',metric,false);var _bagV=sumDaily(BAG_DAILY,ch,startDate,endDate,'',metric,false);var _bagPct=(_lugV+_bagV)>0?(_bagV/(_lugV+_bagV)*100):0;\n  // KPI（使用筛选后的数据）"
)
html = html.replace("document.getElementById('seriesKpi').innerHTML=", "  var _seriesCat=document.getElementById('seriesCat')?.value||'all';\n  var _seriesDaily=_seriesCat==='luggage'?LUG_DAILY:_seriesCat==='bag'?BAG_DAILY:ALL_DAILY;\n  renderCompareRow('seriesKpi',_seriesDaily,ch,startDate,endDate,metric);\n  document.getElementById('seriesKpi').innerHTML=")
html = html.replace("fmtD(totalAmt):Math.round(totalQty).toLocaleString()}</div></div>", "fmtD(totalAmt):Math.round(totalQty).toLocaleString()}</div></div>`+\n    `<div class=\"kpi-card\"><div class=\"label\">包袋占比 <small>${metric==='amt'?'销售额':'销量'}</small></div><div class=\"value\" style=\"color:#8b5cf6\">${_bagPct.toFixed(1)}%</div><div class=\"sub\" style=\"color:#9ca3af;font-size:10px\">包袋/(行李箱+包袋)</div></div>")
html = html.replace("document.getElementById('audKpi').innerHTML=", "  renderCompareRow('audKpi',ad.daily,ch,startDate,endDate,metric);\n  document.getElementById('audKpi').innerHTML=")
html = html.replace("document.getElementById('sizeKpi').innerHTML=", "  renderCompareRow('sizeKpi',daily,ch,startDate,endDate,metric);\n  document.getElementById('sizeKpi').innerHTML=")
html = html.replace("document.getElementById('colorKpi').innerHTML=", "  renderCompareRow('colorKpi',daily,ch,startDate,endDate,metric);\n  document.getElementById('colorKpi').innerHTML=")
html = html.replace("renderLuggage();", "renderLuggage();\n" + COMPARE_EVENTS)

# 写文件（使用LF换行，避免Windows CRLF导致Node.js解析JS报错）
with open(os.path.join(BASE, 'product_dashboard.html'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(html)

print('product_dashboard.html 已生成')
fsize = os.path.getsize(os.path.join(BASE, 'product_dashboard.html'))
print('大小: %d KB' % (fsize/1024))
