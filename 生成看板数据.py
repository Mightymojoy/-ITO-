import pandas as pd
import json
import os

BASE = r'E:\电商渠道业绩看板'
TARGET_FILE = os.path.join(BASE, '各渠道月度目标数据.xlsx')

# ===== 读取所有sheet =====
xls = pd.ExcelFile(TARGET_FILE)
sheet_names = xls.sheet_names
print(f'Sheets: {sheet_names}')

sheet_data = {}
for s in sheet_names:
    sheet_data[s] = pd.read_excel(TARGET_FILE, sheet_name=s)

# ===== 读取达播sheet（特殊处理） =====
dbo_raw = pd.read_excel(TARGET_FILE, sheet_name='达播', header=None)
dbo = dbo_raw.iloc[2:].copy()
dbo.columns = ['日期', 'dabo_luggage_actual', 'dabo_bag_actual', 'xhs_actual',
               'year', 'month',
               'dabo_luggage_forecast', 'dabo_luggage_target', 'dabo_luggage_ft',
               'dabo_bag_forecast', 'dabo_bag_target', 'dabo_bag_ft',
               'xhs_forecast', 'xhs_target', 'xhs_ft']
dbo['日期'] = pd.to_datetime(dbo['日期'])
for c in ['dabo_luggage_actual', 'dabo_bag_actual', 'xhs_actual',
          'dabo_luggage_forecast', 'dabo_luggage_target',
          'dabo_bag_forecast', 'dabo_bag_target',
          'xhs_forecast', 'xhs_target',
          'dabo_luggage_ft', 'dabo_bag_ft', 'xhs_ft']:
    dbo[c] = pd.to_numeric(dbo[c], errors='coerce').fillna(0)

# ===== 标准读取：单sheet =====
def read_single_sheet(df_in):
    df = df_in.copy()
    df['日期'] = pd.to_datetime(df['日期'])
    # 列名映射 - 注意排除"预估+目标"这类计算列
    col_map = {}
    for c in df.columns:
        cn = str(c).strip()
        if cn == '日期':
            continue  # 保留日期列名不变
        elif '实际销售' in cn:
            col_map[c] = 'actual'
        elif '预估+目标' in cn:
            col_map[c] = 'combined_forecast'
        elif '目标（年初预算）' in cn or '目标（预算）' in cn:
            col_map[c] = 'target_budget'
        elif '目标-经营计划' in cn:
            col_map[c] = 'target_plan'
        elif cn == '目标' or cn.strip() == '目标':
            col_map[c] = 'target'
        elif cn == '预估':
            col_map[c] = '_skip'  # 不需要预估列
        else:
            col_map[c] = '_skip'
    df.rename(columns=col_map, inplace=True)
    
    result = {}
    for _, row in df.iterrows():
        date_str = row['日期'].strftime('%Y-%m-%d')
        actual = float(row['actual']) if pd.notna(row.get('actual', 0)) else 0
        entry = {'actual': actual}
        
        tb = row.get('target_budget')
        if pd.notna(tb) and tb != 0 and tb != actual:
            entry['budget_target'] = float(tb)
        
        tp = row.get('target_plan')
        if pd.notna(tp) and tp != 0 and tp != actual:
            entry['operating_target'] = float(tp)
        
        t = row.get('target')
        if pd.notna(t) and t != 0 and t != actual:
            entry['target'] = float(t)
            # 对于没有独立预算目标的渠道(如抖音3店/小红书)，用"目标"作为预算
            tb_orig = row.get('target_budget')
            if pd.notna(tb_orig) and tb_orig != 0 and tb_orig != actual:
                pass  # 有独立预算目标，跳过
            else:
                if 'budget_target' not in entry:
                    entry['budget_target'] = float(t)
        
        cf = row.get('combined_forecast')
        if pd.notna(cf):
            try:
                cf_val = float(cf)
                if cf_val != 0:
                    entry['combined_forecast'] = cf_val
            except (ValueError, TypeError):
                pass
        
        result[date_str] = entry
    return result

# ===== 处理达播sheet的特定子渠道 =====
def read_dabo_channel(col_actual, col_budget, col_operating, col_combined=None):
    result = {}
    for _, row in dbo.iterrows():
        date_str = row['日期'].strftime('%Y-%m-%d')
        entry = {'actual': float(row[col_actual])}
        if col_budget and row.get(col_budget, 0) != 0:
            entry['budget_target'] = float(row[col_budget])
        if col_operating and row.get(col_operating, 0) != 0:
            entry['operating_target'] = float(row[col_operating])
        if col_combined and row.get(col_combined, 0) != 0:
            entry['combined_forecast'] = float(row[col_combined])
        result[date_str] = entry
    return result

# ===== 渠道映射 =====
# 叶子渠道名称 → sheet名
LEAF_SHEETS = {
    '天猫': '直销_伊稻_电商_天猫ITO旗舰店',
    '京东自营': '直销_乐绘_电商_京东ITO京东自营旗舰店',
    '抖音ITO旗舰店（摩登新贵女）_含达播': ' 抖音ITO旗舰店（摩登新贵女）',
    '抖音ITO官方旗舰店（轻熟质享客）': ' 抖音ITO官方旗舰店（轻熟质享客）',
    '抖音ito箱包旗舰店（云端商务家）': ' 抖音ito箱包旗舰店（云端商务家）',
    '小红书自营': '小红书自营',
}

all_data = {}
for ch_name, sheet_n in LEAF_SHEETS.items():
    df = sheet_data[sheet_n]
    all_data[ch_name] = read_single_sheet(df)

# ===== 获取所有日期的完整集合 =====
all_dates = set()
for ch_data in all_data.values():
    all_dates.update(ch_data.keys())
all_dates = sorted(all_dates)

# ===== 补零函数 =====
def get_val(ch_data, date_str, key):
    if date_str in ch_data:
        return ch_data[date_str].get(key, 0)
    return 0

# ===== STEP 1: 拆分摩登新贵女中的达播部分 =====
# 达播-行李箱：预算=H, 目标=G, 实际+预估=I
dabo_luggage = read_dabo_channel('dabo_luggage_actual', 'dabo_luggage_target', 'dabo_luggage_forecast', 'dabo_luggage_ft')
# 达播-包袋：预算=K, 目标=J, 实际+预估=L
dabo_bag = read_dabo_channel('dabo_bag_actual', 'dabo_bag_target', 'dabo_bag_forecast', 'dabo_bag_ft')
# 小红书达播：预算=N, 目标=M, 实际+预估=O
xhs_dabo = read_dabo_channel('xhs_actual', 'xhs_target', 'xhs_forecast', 'xhs_ft')

all_data['抖音达播-行李箱'] = dabo_luggage
all_data['抖音达播-包袋'] = dabo_bag
all_data['小红书达播'] = xhs_dabo

# ===== 读取达播历史数据sheet（2024/2025年历史实际销售，按月均摊到天） =====
DB_SHEET = '达播历史数据'
if DB_SHEET in sheet_names:
    dbh_raw = pd.read_excel(TARGET_FILE, sheet_name=DB_SHEET, header=None)
    # 列配置：(年, 月份列index, 行李箱列index, 包袋列index, 小红书列index)
    year_configs = [
        (2024, 11, 12, 13, 14),  # L=月份, M=行李箱, N=包袋, O=小红书  (0-indexed)
        (2025, 6, 7, 8, 9),      # G=月份, H=行李箱, I=包袋, J=小红书
        (2026, 1, 2, 3, 4),      # B=月份, C=行李箱, D=包袋, E=小红书
    ]
    days_in_month = [31,28,31,30,31,30,31,31,30,31,30,31]
    ch_names = ['抖音达播-行李箱', '抖音达播-包袋', '小红书达播']
    ch_cols = [1, 2, 3]  # 在config中对应的列偏移
    
    for year, month_col, lug_col, bag_col, xhs_col in year_configs:
        for r in range(5, 16):  # pandas 0-indexed rows 5-15 = openpyxl rows 6-16
            month_val = dbh_raw.iloc[r, month_col]
            if pd.isna(month_val) or month_val == 0:
                continue
            month = int(month_val)
            if month < 1 or month > 12:
                continue
            # 月天数
            dim = days_in_month[month - 1]
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                if month == 2:
                    dim = 29
            # 各渠道月总计
            monthly_totals = []
            for col_idx in [lug_col, bag_col, xhs_col]:
                v = dbh_raw.iloc[r, col_idx]
                monthly_totals.append(float(v) if pd.notna(v) and float(v) != 0 else 0)
            # 每日均摊
            for day in range(1, dim + 1):
                date_str = '%d-%02d-%02d' % (year, month, day)
                for ci, ch_name in enumerate(ch_names):
                    daily_val = round(monthly_totals[ci] / dim)
                    if date_str not in all_data.get(ch_name, {}):
                        # 该日期尚未存在（2024/2025），新建
                        if ch_name not in all_data:
                            all_data[ch_name] = {}
                        all_data[ch_name][date_str] = {'actual': daily_val}
                    else:
                        # 2026年已有数据，不覆盖（达播sheet优先）
                        pass

# ===== STEP 2: 重新计算摩登新贵女（自营）= 原值 - 达播-行李箱 =====
mgx_raw = all_data['抖音ITO旗舰店（摩登新贵女）_含达播']
mgx_self = {}
for d in all_dates:
    entry = {}
    raw_actual = get_val(mgx_raw, d, 'actual')
    dabo_val = get_val(dabo_luggage, d, 'actual')
    entry['actual'] = raw_actual - dabo_val
    
    # 预算目标：优先用达播目标的补充
    raw_budget = get_val(mgx_raw, d, 'budget_target')
    dabo_budget = get_val(dabo_luggage, d, 'budget_target')
    if raw_budget > 0:
        entry['budget_target'] = raw_budget
    if dabo_budget > 0:
        budget_dabo = dabo_budget
    
    raw_oper = get_val(mgx_raw, d, 'operating_target')
    dabo_oper = get_val(dabo_luggage, d, 'operating_target')
    if raw_oper > 0:
        entry['operating_target'] = raw_oper
    
    raw_target = get_val(mgx_raw, d, 'target')
    if raw_target > 0:
        entry['target'] = raw_target
    
    raw_cf = get_val(mgx_raw, d, 'combined_forecast')
    if raw_cf > 0:
        entry['combined_forecast'] = raw_cf
    
    mgx_self[d] = entry

all_data['抖音ITO旗舰店（摩登新贵女）'] = mgx_self
# 删除含达播的原数据
del all_data['抖音ITO旗舰店（摩登新贵女）_含达播']

# ===== STEP 3: 轻熟质享客 -= 达播-包袋 =====
qsxsk_raw = all_data['抖音ITO官方旗舰店（轻熟质享客）']
qsxsk_self = {}
for d in all_dates:
    entry = {}
    raw_actual = get_val(qsxsk_raw, d, 'actual')
    dabo_actual = get_val(dabo_bag, d, 'actual')
    entry['actual'] = raw_actual - dabo_actual

    raw_budget = get_val(qsxsk_raw, d, 'budget_target')
    if raw_budget > 0:
        entry['budget_target'] = raw_budget
    raw_oper = get_val(qsxsk_raw, d, 'operating_target')
    if raw_oper > 0:
        entry['operating_target'] = raw_oper

    # 实际+预估也减去达播部分
    raw_cf = get_val(qsxsk_raw, d, 'combined_forecast')
    dabo_cf = get_val(dabo_bag, d, 'combined_forecast')
    cf = raw_cf - dabo_cf
    if cf > 0:
        entry['combined_forecast'] = cf
    elif raw_cf > 0:
        entry['combined_forecast'] = raw_cf

    qsxsk_self[d] = entry
all_data['抖音ITO官方旗舰店（轻熟质享客）'] = qsxsk_self

# ===== STEP 4: 小红书自营 -= 小红书达播 =====
xhs_raw = all_data['小红书自营']
xhs_self = {}
for d in all_dates:
    entry = {}
    raw_actual = get_val(xhs_raw, d, 'actual')
    dabo_actual = get_val(xhs_dabo, d, 'actual')
    entry['actual'] = raw_actual - dabo_actual

    raw_budget = get_val(xhs_raw, d, 'budget_target')
    if raw_budget > 0:
        entry['budget_target'] = raw_budget
    raw_oper = get_val(xhs_raw, d, 'operating_target')
    if raw_oper > 0:
        entry['operating_target'] = raw_oper

    # 实际+预估：小红书有独立达播目标，不减达播
    raw_cf = get_val(xhs_raw, d, 'combined_forecast')
    if raw_cf > 0:
        entry['combined_forecast'] = raw_cf

    xhs_self[d] = entry
all_data['小红书自营'] = xhs_self

# ===== 叶渠道列表（排除 抖音ITO旗舰店（摩登新贵女）_含达播） =====
LEAF_CHANNELS = [
    '天猫', '京东自营',
    '抖音ITO旗舰店（摩登新贵女）',
    '抖音ITO官方旗舰店（轻熟质享客）',
    '抖音ito箱包旗舰店（云端商务家）',
    '小红书自营',
    '抖音达播-行李箱',
    '抖音达播-包袋',
    '小红书达播',
]

# ===== 汇总组 =====
GROUP_CHANNELS = {
    '货架电商汇总': ['天猫', '京东自营'],
    '兴趣电商-自营': [
        '抖音ITO旗舰店（摩登新贵女）',
        '抖音ITO官方旗舰店（轻熟质享客）',
        '抖音ito箱包旗舰店（云端商务家）',
        '小红书自营',
    ],
    '兴趣电商-达播': ['抖音达播-行李箱', '抖音达播-包袋', '小红书达播'],
    '兴趣电商汇总': [
        '抖音ITO旗舰店（摩登新贵女）',
        '抖音ITO官方旗舰店（轻熟质享客）',
        '抖音ito箱包旗舰店（云端商务家）',
        '小红书自营',
        '抖音达播-行李箱',
        '抖音达播-包袋',
        '小红书达播',
    ],
}

# ===== 汇总计算 =====
def sum_channels(ch_names, date_str):
    result = {'actual': 0, 'target': 0, 'budget_target': 0, 'operating_target': 0, 'combined_forecast': 0}
    has_any = False
    for ch in ch_names:
        if ch in all_data and date_str in all_data[ch]:
            has_any = True
            entry = all_data[ch][date_str]
            result['actual'] += entry.get('actual', 0)
            t = entry.get('target', entry.get('operating_target', entry.get('budget_target', 0)))
            result['target'] += t
            result['budget_target'] += entry.get('budget_target', 0)
            result['operating_target'] += entry.get('operating_target', 0)
            result['combined_forecast'] += entry.get('combined_forecast', 0)
    return result if has_any else None

for group_name, children in GROUP_CHANNELS.items():
    group_data = {}
    for d in all_dates:
        s = sum_channels(children, d)
        if s:
            group_data[d] = s
    all_data[group_name] = group_data

# ===== 构建JSON =====
output = {
    'meta': {
        'generated_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date_range': {'min': all_dates[0], 'max': all_dates[-1]},
        'total_dates': len(all_dates),
    },
    'channels': sorted(LEAF_CHANNELS),
    'groups': [
        {'name': '货架电商汇总', 'children': GROUP_CHANNELS['货架电商汇总']},
        {'name': '兴趣电商-自营', 'children': GROUP_CHANNELS['兴趣电商-自营']},
        {'name': '兴趣电商-达播', 'children': GROUP_CHANNELS['兴趣电商-达播']},
        {'name': '兴趣电商汇总', 'children': GROUP_CHANNELS['兴趣电商汇总']},
    ],
    'data': {ch: all_data[ch] for ch in all_data if ch in LEAF_CHANNELS or ch in GROUP_CHANNELS},
}

out_path = os.path.join(BASE, 'dashboard_data.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False)

# ===== 验证 =====
print('=== 验证 ===')
print(f'日期范围: {all_dates[0]} ~ {all_dates[-1]}')
print(f'总天数: {len(all_dates)}')
print(f'\n=== 2026年1-5月 各渠道累计实际销售额 ===')
for ch in LEAF_CHANNELS:
    total = sum(get_val(all_data[ch], d, 'actual') for d in all_dates if d >= '2026-01-01' and d <= '2026-05-25')
    print(f'  {ch:20s}: {total:>10,.0f}')

print(f'\n=== 汇总组验证 ===')
for gn in GROUP_CHANNELS:
    total = sum(get_val(all_data[gn], d, 'actual') for d in all_dates if d >= '2026-01-01' and d <= '2026-05-25')
    print(f'  {gn:20s}: {total:>10,.0f}')

# 验证摩登新贵女自营 = 原 - 达播-行李箱
mgx_self_total = sum(get_val(all_data['抖音ITO旗舰店（摩登新贵女）'], d, 'actual') for d in all_dates if d >= '2026-01-01' and d <= '2026-05-25')
dabo_l_total = sum(get_val(all_data['抖音达播-行李箱'], d, 'actual') for d in all_dates if d >= '2026-01-01' and d <= '2026-05-25')
print(f'\n=== 拆分验证（2026年1-5月） ===')
print(f'  摩登新贵女(自营): {mgx_self_total:>10,.0f}')
print(f'  达播-行李箱:      {dabo_l_total:>10,.0f}')
print(f'  合计:             {mgx_self_total + dabo_l_total:>10,.0f}')

# 输出文件大小
import os
fsize = os.path.getsize(out_path)
print(f'\nJSON文件大小: {fsize/1024:.0f} KB')
print('\n[OK] 数据生成完成!')
