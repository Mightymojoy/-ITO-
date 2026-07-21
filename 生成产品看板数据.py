import pandas as pd
import json, os, re
from collections import defaultdict

BASE = r'E:\电商渠道业绩看板'
DATA_SRC = os.path.join(BASE, '各渠道销售数据源')
TARGET_FILE = os.path.join(BASE, '各渠道月度目标数据.xlsx')
TIMESTAMP_FILE = os.path.join(BASE, '_cached_data', 'data_built.txt')

# ===== 渠道映射 =====
KEY_STORES = [
    '直销_伊稻_电商_天猫ITO旗舰店', '直销_乐绘_电商_京东ITO京东自营旗舰店',
    '直销_伊稻_电商_抖音ITO旗舰店', '直销_乐绘_电商_抖音ITO官方旗舰店',
    '直销_伊远_电商_抖音ITO行李箱旗舰店', '直销_伊稻_电商_小红书ITO旗舰店',
    '直销_伊稻_电商_视频号ITO旗舰店',
]
CHANNEL_NAMES = {
    '直销_伊稻_电商_天猫ITO旗舰店': '天猫',
    '直销_乐绘_电商_京东ITO京东自营旗舰店': '京东自营',
    '直销_伊稻_电商_抖音ITO旗舰店': '抖音ITO旗舰店（摩登新贵女）',
    '直销_乐绘_电商_抖音ITO官方旗舰店': '抖音ITO官方旗舰店（轻熟质享客）',
    '直销_伊远_电商_抖音ITO行李箱旗舰店': '抖音ito箱包旗舰店（云端商务家）',
    '直销_伊稻_电商_小红书ITO旗舰店': '小红书自营',
    '直销_伊稻_电商_视频号ITO旗舰店': '视频号',
}

# ===== 1. 系列匹配表 =====
print('读取系列产品匹配表...')
match_raw = pd.read_excel(TARGET_FILE, sheet_name='系列产品匹配')
# 兼容源表结构变化：旧表存在重复列名(pandas 自动加 .1 后缀)，新表已去重无后缀。
# 优先取 .1 后缀列，不存在则回退到无后缀列，避免源 Excel 表头一改动脚本就崩。
_cols = list(match_raw.columns)
def _pick_col(base):
    return base + '.1' if (base + '.1') in _cols else base
_sel = ['货品名称', _pick_col('系列'), _pick_col('颜色'), _pick_col('尺寸'), _pick_col('品类'), '箱型', '简称-商品', '人群']
_missing = [c for c in _sel if c not in _cols]
if _missing:
    raise KeyError(f'系列产品匹配表缺少必要列: {_missing}；当前列: {_cols}')
match = match_raw[_sel].copy()
match.columns = ['货品名称', '系列', '颜色', '尺寸', '品类', '箱型', '简称', '人群']

product_attrs = {}
series_to_short = {}
for _, row in match.iterrows():
    name = str(row.get('货品名称', '')).strip()
    series = str(row.get('系列', '')).strip()
    short = str(row.get('简称', '')).strip()
    color = str(row.get('颜色', '')).strip()
    size = str(row.get('尺寸', '')).strip()
    cat = str(row.get('品类', '')).strip()
    trunk = str(row.get('箱型', '')).strip()
    audience = str(row.get('人群', '')).strip()
    display = short if short and short != 'nan' and short else series
    attrs = {'series': series, 'display': display, 'color': color, 'size': size, 'cat': cat, 'trunk': trunk, 'audience': audience}
    if name:
        product_attrs[name] = attrs
    if series and series not in series_to_short:
        series_to_short[series] = display

all_series = sorted(set(s for s in match['系列'].dropna() if str(s).strip()))
all_audiences = match['人群'].dropna().unique()
print(f'  系列: {len(all_series)}个, 人群: {len(all_audiences)}个')

# ===== 2. 读取文件 =====
files = sorted([f for f in os.listdir(DATA_SRC) if re.match(r'\d{2}-\d+\.xlsx', f) and not f.startswith('_')])
print(f'  月度文件: {len(files)}个')

# 数据结构
# 数据结构：all_data[date][channel][series_key] = {qty, amt}
# series_key='$total'表示该渠道当日汇总
M = lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'qty': 0, 'amt': 0})))
C = lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'qty': 0, 'amt': 0}))))

all_data = M()
luggage_data = M()
bag_data = M()
audience_data = M()
lug_audience_data = M()
bag_audience_data = M()
cross_data = C()
lug_cross_data = C()
bag_cross_data = C()
color_data = M()
size_data = M()
lug_color_data = M()
lug_size_data = M()
bag_color_data = M()
bag_size_data = M()
sku_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'qty': 0, 'amt': 0})))
sku_by_date = defaultdict(lambda: defaultdict(lambda: {'qty': 0, 'amt': 0}))
sku_meta = {}

total_read = 0
total_matched = 0
total_audience = 0

for fname in files:
    fp = os.path.join(DATA_SRC, fname)
    df = pd.read_excel(fp)
    for row in df.to_dict('records'):
        total_read += 1
        date_str = str(row.get('日期', '')).strip()[:10]
        ch_raw = str(row.get('渠道', str(row.get('店铺', '')))).strip()
        if ch_raw not in CHANNEL_NAMES:
            continue
        ch = CHANNEL_NAMES[ch_raw]
        name = str(row.get('货品名称', '')).strip()
        qty_raw = row.get('实际销售量', row.get('数量', 0))
        qty = int(qty_raw) if qty_raw and not pd.isna(qty_raw) else 0
        amt_raw = row.get('实际销售额', 0)
        amt = int(amt_raw) if amt_raw and not pd.isna(amt_raw) else 0
        if qty == 0 and amt == 0:
            continue
        if not date_str or not name:
            continue

        attrs = product_attrs.get(name)
        if attrs is None:
            fb = None
            m = re.search(r'ITO\s+(.+?)(?:系列|$)', name)
            if m:
                s = m.group(1).strip()
                for sn in all_series:
                    if sn in s or s in sn:
                        short = series_to_short.get(sn, sn)
                        fb = {'series': sn, 'display': short, 'cat': '', 'audience': '', 'color': '', 'size': ''}
                        break
            if fb is None:
                for key, val in product_attrs.items():
                    if key and name and (key in name or name in key):
                        product_attrs[name] = val.copy()  # 缓存到精确匹配字典，后续 O(1)
                        fb = val.copy()
                        break
            attrs = fb
        if attrs is None:
            continue
        total_matched += 1
        display = attrs['display']
        series = attrs['series']
        cat = attrs['cat']
        audience = attrs['audience']
        color = attrs['color']
        size = attrs['size']

        # 品类判别
        is_luggage = (cat == '行李箱') or ('TRUNK' in series.upper() and '箱套' not in display and '保护' not in display and '收纳' not in display)
        is_bag = (cat == '包袋')

        # 全量
        all_data[date_str][ch]['$total']['qty'] += qty
        all_data[date_str][ch]['$total']['amt'] += amt
        all_data[date_str][ch][display]['qty'] += qty
        all_data[date_str][ch][display]['amt'] += amt

        if is_luggage:
            luggage_data[date_str][ch]['$total']['qty'] += qty
            luggage_data[date_str][ch]['$total']['amt'] += amt
            luggage_data[date_str][ch][display]['qty'] += qty
            luggage_data[date_str][ch][display]['amt'] += amt

        if is_bag:
            bag_data[date_str][ch]['$total']['qty'] += qty
            bag_data[date_str][ch]['$total']['amt'] += amt
            bag_data[date_str][ch][display]['qty'] += qty
            bag_data[date_str][ch][display]['amt'] += amt

        # 人群
        if audience and audience != 'nan' and audience:
            audience_data[date_str][ch]['$total']['qty'] += qty
            audience_data[date_str][ch]['$total']['amt'] += amt
            audience_data[date_str][ch][audience]['qty'] += qty
            audience_data[date_str][ch][audience]['amt'] += amt
            total_audience += 1
            if is_luggage:
                lug_audience_data[date_str][ch]['$total']['qty'] += qty
                lug_audience_data[date_str][ch]['$total']['amt'] += amt
                lug_audience_data[date_str][ch][audience]['qty'] += qty
                lug_audience_data[date_str][ch][audience]['amt'] += amt
                lug_cross_data[date_str][ch][audience][display]['qty'] += qty
                lug_cross_data[date_str][ch][audience][display]['amt'] += amt
            if is_bag:
                bag_audience_data[date_str][ch]['$total']['qty'] += qty
                bag_audience_data[date_str][ch]['$total']['amt'] += amt
                bag_audience_data[date_str][ch][audience]['qty'] += qty
                bag_audience_data[date_str][ch][audience]['amt'] += amt
                bag_cross_data[date_str][ch][audience][display]['qty'] += qty
                bag_cross_data[date_str][ch][audience][display]['amt'] += amt

        # 颜色/尺寸
        if color and color != 'nan' and color:
            color_data[date_str][ch]['$total']['qty'] += qty
            color_data[date_str][ch]['$total']['amt'] += amt
            color_data[date_str][ch][color]['qty'] += qty
            color_data[date_str][ch][color]['amt'] += amt
            if is_luggage:
                lug_color_data[date_str][ch]['$total']['qty'] += qty
                lug_color_data[date_str][ch]['$total']['amt'] += amt
                lug_color_data[date_str][ch][color]['qty'] += qty
                lug_color_data[date_str][ch][color]['amt'] += amt
            if is_bag:
                bag_color_data[date_str][ch]['$total']['qty'] += qty
                bag_color_data[date_str][ch]['$total']['amt'] += amt
                bag_color_data[date_str][ch][color]['qty'] += qty
                bag_color_data[date_str][ch][color]['amt'] += amt

        if size and size != 'nan' and size:
            size_data[date_str][ch]['$total']['qty'] += qty
            size_data[date_str][ch]['$total']['amt'] += amt
            size_data[date_str][ch][size]['qty'] += qty
            size_data[date_str][ch][size]['amt'] += amt
            if is_luggage:
                lug_size_data[date_str][ch]['$total']['qty'] += qty
                lug_size_data[date_str][ch]['$total']['amt'] += amt
                lug_size_data[date_str][ch][size]['qty'] += qty
                lug_size_data[date_str][ch][size]['amt'] += amt
            if is_bag:
                bag_size_data[date_str][ch]['$total']['qty'] += qty
                bag_size_data[date_str][ch]['$total']['amt'] += amt
                bag_size_data[date_str][ch][size]['qty'] += qty
                bag_size_data[date_str][ch][size]['amt'] += amt

        # SKU
        sku_color = color if color and color != 'nan' else ''
        sku_size = size if size and size != 'nan' else ''
        if sku_color and sku_size:
            sku_key = display + '|' + sku_color + '|' + sku_size
            sku_data[date_str][ch][sku_key]['qty'] += qty
            sku_data[date_str][ch][sku_key]['amt'] += amt
            sku_by_date[date_str][sku_key]['qty'] += qty
            sku_by_date[date_str][sku_key]['amt'] += amt
            if sku_key not in sku_meta:
                cat_name = '行李箱' if is_luggage else ('包袋' if is_bag else '其他')
                sku_meta[sku_key] = {'series': display, 'color': sku_color, 'size': sku_size, 'category': cat_name}

print(f'总行数: {total_read}, 已匹配: {total_matched}, 匹配人群: {total_audience}')

# ===== 输出JSON =====
out_dir = BASE
os.makedirs(out_dir, exist_ok=True)

def dict_to_native(d):
    return {k: dict_to_native(v) if isinstance(v, (dict, defaultdict)) else v for k, v in d.items()}

def make_meta(data_dict, extra_keys=None):
    dates = sorted(data_dict.keys())
    series_set = set()
    for d in data_dict.values():
        for ch_data in d.values():
            for k in ch_data:
                if k != '$total':
                    series_set.add(k)
    meta = {
        'generated_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date_range': {'min': dates[0], 'max': dates[-1]} if dates else None,
        'total_days': len(dates),
        'channels': list(CHANNEL_NAMES.values()),
        'series': sorted(series_set),
    }
    if extra_keys:
        meta.update(extra_keys)
    return dates, meta

# 全量
all_dates, all_meta = make_meta(all_data)
all_json = {'meta': all_meta, 'daily': {d: dict_to_native(all_data[d]) for d in all_dates}}
with open(os.path.join(out_dir, 'all_series_daily.json'), 'w', encoding='utf-8') as f:
    json.dump(all_json, f, ensure_ascii=False)
print(f'全量JSON: {os.path.getsize(os.path.join(out_dir,"all_series_daily.json"))/1024:.0f} KB, {len(all_dates)}天')

# 行李箱
lug_dates, lug_meta = make_meta(luggage_data)
lug_json = {'meta': lug_meta, 'daily': {d: dict_to_native(luggage_data[d]) for d in lug_dates}}
with open(os.path.join(out_dir, 'luggage_daily.json'), 'w', encoding='utf-8') as f:
    json.dump(lug_json, f, ensure_ascii=False)
print(f'行李箱JSON: {os.path.getsize(os.path.join(out_dir,"luggage_daily.json"))/1024:.0f} KB, {len(lug_dates)}天')

# 包袋
bag_dates, bag_meta = make_meta(bag_data)
bag_json = {'meta': bag_meta, 'daily': {d: dict_to_native(bag_data[d]) for d in bag_dates}}
with open(os.path.join(out_dir, 'bag_daily.json'), 'w', encoding='utf-8') as f:
    json.dump(bag_json, f, ensure_ascii=False)
print(f'包袋JSON: {os.path.getsize(os.path.join(out_dir,"bag_daily.json"))/1024:.0f} KB, {len(bag_dates)}天')

# 人群
aud_dates, aud_meta = make_meta(audience_data, extra_keys={'audience': sorted(set(
    a for d in audience_data.values() for ch_data in d.values() for a in ch_data if a != '$total'))})
aud_json = {'meta': aud_meta, 'daily': {d: dict_to_native(audience_data[d]) for d in aud_dates}}
with open(os.path.join(out_dir, 'audience_daily.json'), 'w', encoding='utf-8') as f:
    json.dump(aud_json, f, ensure_ascii=False)
print(f'人群JSON: {os.path.getsize(os.path.join(out_dir,"audience_daily.json"))/1024:.0f} KB')

# 交叉
cross_out = {d: dict_to_native(lug_cross_data[d]) for d in sorted(lug_cross_data.keys())}
cross_json = {'meta': {'channels': list(CHANNEL_NAMES.values())}, 'daily': cross_out}
with open(os.path.join(out_dir, 'luggage_audience_x_series.json'), 'w', encoding='utf-8') as f:
    json.dump(cross_json, f, ensure_ascii=False)

# 行李箱人群
lug_aud_dates, lug_aud_meta = make_meta(lug_audience_data, extra_keys={'audience': sorted(set(
    a for d in lug_audience_data.values() for ch_data in d.values() for a in ch_data if a != '$total'))})
lug_aud_json = {'meta': lug_aud_meta, 'daily': {d: dict_to_native(lug_audience_data[d]) for d in lug_aud_dates}}
with open(os.path.join(out_dir, 'luggage_audience_daily.json'), 'w', encoding='utf-8') as f:
    json.dump(lug_aud_json, f, ensure_ascii=False)

# 包袋人群
bag_aud_dates, bag_aud_meta = make_meta(bag_audience_data, extra_keys={'audience': sorted(set(
    a for d in bag_audience_data.values() for ch_data in d.values() for a in ch_data if a != '$total'))})
bag_aud_json = {'meta': bag_aud_meta, 'daily': {d: dict_to_native(bag_audience_data[d]) for d in bag_aud_dates}}
with open(os.path.join(out_dir, 'bag_audience_daily.json'), 'w', encoding='utf-8') as f:
    json.dump(bag_aud_json, f, ensure_ascii=False)

# 包袋交叉
bag_cross_out = {d: dict_to_native(bag_cross_data[d]) for d in sorted(bag_cross_data.keys())}
bag_cross_json = {'meta': {'channels': list(CHANNEL_NAMES.values())}, 'daily': bag_cross_out}
with open(os.path.join(out_dir, 'bag_audience_x_series.json'), 'w', encoding='utf-8') as f:
    json.dump(bag_cross_json, f, ensure_ascii=False)

# 颜色
def write_color_json(data, name, out_dir):
    dates, meta = make_meta(data, extra_keys={'colors': sorted(set(
        c for d in data.values() for ch_data in d.values() for c in ch_data if c != '$total'))})
    j = {'meta': meta, 'daily': {d: dict_to_native(data[d]) for d in dates}}
    with open(os.path.join(out_dir, name), 'w', encoding='utf-8') as f:
        json.dump(j, f, ensure_ascii=False)
    sz = os.path.getsize(os.path.join(out_dir, name))
    print(f'{name}: {sz/1024:.0f} KB')

write_color_json(color_data, 'color_daily.json', out_dir)
write_color_json(lug_color_data, 'luggage_color_daily.json', out_dir)
write_color_json(bag_color_data, 'bag_color_daily.json', out_dir)

def write_size_json(data, name, out_dir):
    dates, meta = make_meta(data, extra_keys={'sizes': sorted(set(
        s for d in data.values() for ch_data in d.values() for s in ch_data if s != '$total'))})
    j = {'meta': meta, 'daily': {d: dict_to_native(data[d]) for d in dates}}
    with open(os.path.join(out_dir, name), 'w', encoding='utf-8') as f:
        json.dump(j, f, ensure_ascii=False)
    sz = os.path.getsize(os.path.join(out_dir, name))
    print(f'{name}: {sz/1024:.0f} KB')

write_size_json(size_data, 'size_daily.json', out_dir)
write_size_json(lug_size_data, 'luggage_size_daily.json', out_dir)
write_size_json(bag_size_data, 'bag_size_daily.json', out_dir)

# SKU（包含渠道维度的日级数据 + 无渠道的快速查询数据）
sku_dates = sorted(set(list(sku_data.keys()) + list(sku_by_date.keys())))
sku_series_set = sorted(set(m['series'] for m in sku_meta.values()))
sku_keys_sorted = sorted(sku_meta.keys())
sku_meta_out = {
    'generated_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
    'channels': list(CHANNEL_NAMES.values()),
    'series': sku_series_set,
    'sku_keys': sku_keys_sorted,
}
# sku_daily.json 格式: daily[date][channel][sku_key] = {qty, amt}
sku_daily_out = {'meta': sku_meta_out, 'daily': {d: dict_to_native(sku_data[d]) for d in sorted(sku_data.keys())}}
with open(os.path.join(out_dir, 'sku_daily.json'), 'w', encoding='utf-8') as f:
    json.dump(sku_daily_out, f, ensure_ascii=False)
print(f'SKU JSON: {os.path.getsize(os.path.join(out_dir,"sku_daily.json"))/1024:.0f} KB')

# 更新时间戳
os.makedirs(os.path.join(BASE, '_cached_data'), exist_ok=True)
with open(TIMESTAMP_FILE, 'w') as f:
    f.write(pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'))
print(f'时间戳已保存')

print('\nDone!')
