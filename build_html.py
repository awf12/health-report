#!/usr/bin/env python3
"""
Generate complete report HTML from data.json.
Creates a self-contained HTML file with all sections, tables, and charts.
"""
import json

with open('data.json', 'r', encoding='utf-8') as f:
    D = json.load(f)

M = D['meta']
S = D['sections']

def val_class(v):
    if v is None: return ''
    if v <= 50: return 'low'
    if v >= 100: return 'high'
    return 'normal'

def val_bg(v):
    if v is None: return ''
    if v <= 50: return 'background:#ffe0e0;'
    if v >= 100: return 'background:#fff8e1;'
    return ''

def stat_summary(items):
    vals = [it['value'] for it in items if it.get('value') is not None]
    if not vals: return ''
    avg = sum(vals) / len(vals)
    high = len([it for it in items if it.get('value') is not None and it['value'] >= 100])
    low = len([it for it in items if it.get('value') is not None and it['value'] <= 50])
    return f'共 {len(vals)} 项 | 平均值: {avg:.1f} | 高反应(≥100): {high} 项 | 低反应(≤50): {low} 项'

def data_table(items, cols='name,value,desc,food', chart_id=None):
    """Render a data table with optional chart."""
    cols = cols.split(',')
    html = ''
    if chart_id:
        html += f'<div class="chart-wrap"><canvas id="{chart_id}"></canvas></div>'
    html += '<div style="overflow-x:auto;"><table><thead><tr>'
    col_labels = {'name': '检测项目', 'value': '反应值', 'desc': '说明解释', 'food': '食物来源', 'cn': '英文名'}
    for c in cols:
        html += f'<th>{col_labels.get(c, c)}</th>'
    html += '</tr></thead><tbody>'
    for it in items:
        html += '<tr>'
        for c in cols:
            if c == 'value':
                v = it.get('value')
                html += f'<td class="{val_class(v)}" style="{val_bg(v)}">{v if v is not None else "-"}</td>'
            else:
                html += f'<td>{it.get(c, "")}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    return html

# Vibrant distinct color palette
PALETTE = [
    "'rgba(65,105,225,0.85)'",   # Royal Blue
    "'rgba(220,20,60,0.85)'",    # Crimson
    "'rgba(46,139,87,0.85)'",    # Sea Green
    "'rgba(255,140,0,0.85)'",    # Dark Orange
    "'rgba(138,43,226,0.85)'",   # Blue Violet
    "'rgba(0,139,139,0.85)'",    # Dark Cyan
    "'rgba(255,69,0,0.85)'",     # Orange Red
    "'rgba(70,130,180,0.85)'",   # Steel Blue
    "'rgba(218,165,32,0.85)'",   # Goldenrod
    "'rgba(199,21,133,0.85)'",   # Medium Violet Red
    "'rgba(34,139,34,0.85)'",    # Forest Green
    "'rgba(255,99,71,0.85)'",    # Tomato
    "'rgba(100,149,237,0.85)'",  # Cornflower Blue
    "'rgba(178,34,34,0.85)'",    # Firebrick
    "'rgba(0,128,128,0.85)'",    # Teal
    "'rgba(210,105,30,0.85)'",   # Chocolate
    "'rgba(123,104,238,0.85)'",  # Medium Slate Blue
    "'rgba(205,92,92,0.85)'",    # Indian Red
    "'rgba(60,179,113,0.85)'",   # Medium Sea Green
    "'rgba(255,160,122,0.85)'",  # Light Salmon
    "'rgba(72,61,139,0.85)'",    # Dark Slate Blue
    "'rgba(188,143,143,0.85)'",  # Rosy Brown
    "'rgba(95,158,160,0.85)'",   # Cadet Blue
    "'rgba(240,128,128,0.85)'",  # Light Coral
    "'rgba(106,90,205,0.85)'",   # Slate Blue
    "'rgba(184,134,11,0.85)'",   # Dark Goldenrod
    "'rgba(30,144,255,0.85)'",   # Dodger Blue
    "'rgba(255,127,80,0.85)'",   # Coral
    "'rgba(50,205,50,0.85)'",    # Lime Green
    "'rgba(186,85,211,0.85)'",   # Medium Orchid
]

def bar_chart_js(chart_id, items, label_key='name'):
    """Generate Chart.js bar chart with data labels and diverse colors."""
    labels = [it[label_key] for it in items]
    values = [it.get('value', 0) or 0 for it in items]
    n = len(values)
    # Assign each bar a different color from the palette
    colors = [PALETTE[i % len(PALETTE)] for i in range(n)]
    borders = [c.replace('0.85', '1') for c in colors]
    data_json = json.dumps(values)
    return f"""
new Chart(document.getElementById('{chart_id}'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(labels, ensure_ascii=False)},
    datasets: [{{
      data: {data_json},
      backgroundColor: [{', '.join(colors)}],
      borderColor: [{', '.join(borders)}],
      borderWidth: 1
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: true,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      y: {{ beginAtZero: false, min: 0, max: 160,
        ticks: {{ callback: v => v }},
        grid: {{ color: v => v === 50 ? '#c0392b' : '#e0e0e0', lineWidth: v => v === 50 ? 2 : 1 }}
      }},
      x: {{ ticks: {{ maxRotation: 60, font: {{ size: 10 }} }} }}
    }}
  }},
  plugins: [{{
    id: 'barLabels_{chart_id}',
    afterDraw: function(chart) {{
      var ctx = chart.ctx;
      var meta = chart.getDatasetMeta(0);
      ctx.save();
      ctx.font = 'bold 11px \"PingFang SC\",\"Microsoft YaHei\",sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      meta.data.forEach(function(bar, i) {{
        var val = {data_json}[i];
        var x = bar.x;
        var y = bar.y - 4;
        // Color based on value thresholds
        if (val <= 50) ctx.fillStyle = '#c0392b';
        else if (val >= 100) ctx.fillStyle = '#d4a017';
        else ctx.fillStyle = '#2c5f2d';
        ctx.fillText(val, x, y);
      }});
      ctx.restore();
    }}
  }}]
}});
"""

def make_section(id, title, items, item_type='table', cols='name,value,desc,food', chart_id=None, summary=None):
    """Generate a complete section HTML + JS."""
    if summary is None and isinstance(items, list) and items:
        summary = stat_summary(items)
    html = f'<div class="card" id="{id}"><h3>{title}</h3>'
    if summary:
        html += f'<div class="summary-box">{summary}</div>'
    html += '<div class="legend"><span class="low">■ ≤50 长期压力</span><span class="normal">■ 50-100 平衡</span><span class="high">■ ≥100 近期压力</span></div>'
    if item_type == 'table':
        html += data_table(items, cols, chart_id)
    elif item_type == 'spine':
        html += '<div class="spine-grid">'
        for it in items:
            s = it.get('status', '')
            html += f'<div class="spine-item"><strong>{it["vertebra"]} · {it["region"]}</strong>'
            html += f'<span class="status status-{s}">{s}</span>'
            html += f'<div style="margin-top:4px;font-size:12px;color:#666;">{it.get("body","")}</div></div>'
        html += '</div>'
    html += '</div>'
    js = ''
    if chart_id and isinstance(items, list):
        js = bar_chart_js(chart_id, items)
    return html, js

# ============ BUILD HTML ============
sections_html = []
charts_js = []

# Cover
sections_html.append(f'''
<div class="cover card" id="cover">
  <h1>营养与健康检测报告</h1>
  <h3>Nutrition and Wellness Assessment Report</h3>
  <div class="meta-grid">
    <div class="meta-item"><label>姓名</label><span>{M['name']}</span></div>
    <div class="meta-item"><label>性别</label><span>{M['gender']}</span></div>
    <div class="meta-item"><label>出生日期</label><span>{M['birthDate']}</span></div>
    <div class="meta-item"><label>检测日期</label><span>{M['testDate']}</span></div>
    <div class="meta-item"><label>就诊编号</label><span>{M['visitNumber']}</span></div>
    <div class="meta-item"><label>检测师</label><span>{M['practitioner']}</span></div>
    <div class="meta-item"><label>诊所</label><span>{M['clinic']}</span></div>
    <div class="meta-item"><label>地址</label><span>{M['address']}</span></div>
  </div>
  <p style="color:#999;font-size:13px;">本报告基于生物反馈检测数据，反应值仅供参考，不作为医学诊断依据。</p>
  <div style="margin-top:24px;font-size:14px;" class="toc" id="toc"></div>
</div>
''')

# VARHOP
h, j = make_section('varhop', 'VARHOP 数值 — 身体基本体质评估', [
    {'name': '电压指数(Volt)', 'value': S['varhop']['volt'], 'desc': '体力指数，100-80正常', 'food': ''},
    {'name': '电流强度(Amper)', 'value': S['varhop']['amper'], 'desc': '脑力指数，100-80正常', 'food': ''},
    {'name': '电阻(Resistance)', 'value': S['varhop']['resistance'], 'desc': '免疫力指数', 'food': ''},
    {'name': '水合指数(Hydration)', 'value': S['varhop']['hydration'], 'desc': '细胞水分', 'food': ''},
    {'name': '氧化指数(Oxidation)', 'value': S['varhop']['oxidation'], 'desc': '血液携氧能力', 'food': ''},
    {'name': '质子压力', 'value': S['varhop']['proton_pressure'], 'desc': '能量代谢/ATP生产', 'food': ''},
    {'name': '电子压力', 'value': S['varhop']['electron_pressure'], 'desc': '能量转换/ATP合成', 'food': ''},
    {'name': '相角指数', 'value': S['varhop']['phase_angle'], 'desc': '细胞再生/老化指标', 'food': ''},
    {'name': '相反应指数', 'value': S['varhop']['phase_response'], 'desc': '各系统协同能力', 'food': ''},
    {'name': '阻抗指数', 'value': S['varhop']['impedance'], 'desc': '能量流通指标', 'food': ''},
    {'name': '反应速度', 'value': S['varhop']['reaction_speed'], 'desc': '＜19正常，100重度迟钝', 'food': ''},
    {'name': '体脂率', 'value': 18, 'desc': S['varhop']['body_fat'], 'food': ''},
    {'name': '细胞活力指数', 'value': S['varhop']['cellular_vitality'], 'desc': '≥6正常', 'food': ''},
], chart_id='chart_varhop')
sections_html.append(h); charts_js.append(j)

# Risk Profile
h, j = make_section('risk', '风险概况', [{'name': k.replace('_',' ').title(), 'value': v} for k,v in S['risk_profile'].items()],
                   chart_id='chart_risk')
sections_html.append(h); charts_js.append(j)

# Vitamin Families
h, j = make_section('vitamins', '维生素家族反应值', S['vitamin_families'], chart_id='chart_vitamins')
sections_html.append(h); charts_js.append(j)

# Vitamin A detail
h, j = make_section('vita', '维生素A族详细', S['vitamin_a_detail'], chart_id='chart_vita')
sections_html.append(h); charts_js.append(j)

# Vitamin B detail
h, j = make_section('vitb', '维生素B族详细', S['vitamin_b_detail'], chart_id='chart_vitb')
sections_html.append(h); charts_js.append(j)

# Vitamin C detail
h, j = make_section('vitc', '维生素C族详细', S['vitamin_c_detail'], chart_id='chart_vitc')
sections_html.append(h); charts_js.append(j)

# Vitamin D detail
h, j = make_section('vitd', '维生素D族详细', S['vitamin_d_detail'], chart_id='chart_vitd')
sections_html.append(h); charts_js.append(j)

# Vitamin E detail
h, j = make_section('vite', '维生素E族详细', S['vitamin_e_detail'], chart_id='chart_vite')
sections_html.append(h); charts_js.append(j)

# Vitamin F detail
h, j = make_section('vitf', '维生素F（脂肪酸）详细', S['vitamin_f_detail'], chart_id='chart_vitf')
sections_html.append(h); charts_js.append(j)

# Vitamin K detail
h, j = make_section('vitk', '维生素K族详细', S['vitamin_k_detail'], chart_id='chart_vitk')
sections_html.append(h); charts_js.append(j)

# Vitamin U detail
h, j = make_section('vitu', '维生素U族（辅酶Q）详细', S['vitamin_u_detail'], chart_id='chart_vitu')
sections_html.append(h); charts_js.append(j)

# Amino Acids
h, j = make_section('amino', '氨基酸平衡性评估', S['amino_acids'], chart_id='chart_amino')
sections_html.append(h); charts_js.append(j)

# Minerals
h, j = make_section('minerals', '矿物质平衡性评估', S['minerals'], chart_id='chart_minerals')
sections_html.append(h); charts_js.append(j)

# Aromatherapy
h, j = make_section('aroma', '芳香疗法反应性评估', S['aromatherapy'], chart_id='chart_aroma')
sections_html.append(h); charts_js.append(j)

# General Digestion
h, j = make_section('digestion', '一般消化系统评估', S['general_digestion'], chart_id='chart_digestion')
sections_html.append(h); charts_js.append(j)

# Carbohydrate Digestion
h, j = make_section('carb', '碳水化合物代谢反应性评估', S['carbohydrate_digestion'], chart_id='chart_carb')
sections_html.append(h); charts_js.append(j)

# Fat Digestion
h, j = make_section('fat', '脂肪消化评估', S['fat_digestion'], chart_id='chart_fat')
sections_html.append(h); charts_js.append(j)

# Protein Digestion
h, j = make_section('protein', '蛋白质消化评估', S['protein_digestion'], chart_id='chart_protein')
sections_html.append(h); charts_js.append(j)

# Spine
h, _ = make_section('spine', '脊柱系统反应性评估', S['spine'], item_type='spine',
                    summary=f'共 {len(S["spine"])} 个椎位。正常: {len([x for x in S["spine"] if x["status"] in ["已校正","Corrected"]])} | 轻度压力/未校正: {len([x for x in S["spine"] if x["status"] in ["未校正","Not Corrected","困难","Difficult","半脱位","subluxation"]])} | 中重度: {len([x for x in S["spine"] if x["status"] in ["炎症","inflammation","神经压迫","NervCompression","退化","Degeneration","暂时性神经压迫","Temp Nerve Comp"]])}')
sections_html.append(h)

# Xenobiotics
h, j = make_section('xeno', '外源性物质反应性评估', S['xenobiotics'], chart_id='chart_xeno')
sections_html.append(h); charts_js.append(j)

# Additional Factors
h, j = make_section('addfactors', '外源性物质额外因素评估', S['additional_factors'], chart_id='chart_addfactors')
sections_html.append(h); charts_js.append(j)

# Disease Causes
h, j = make_section('causes', '导致健康风险和健康恶化的原因', S['disease_causes'], chart_id='chart_causes')
sections_html.append(h); charts_js.append(j)

# Disease Aggravations
h, j = make_section('aggrav', '疾病加重因素', S['disease_aggravations'], chart_id='chart_aggrav')
sections_html.append(h); charts_js.append(j)

# Miasms
h, j = make_section('miasms', '体质特征反应性', S['miasms'], chart_id='chart_miasms')
sections_html.append(h); charts_js.append(j)

# Nosodes
h, j = make_section('nosodes', '病原体特征反应性', S['nosodes'], chart_id='chart_nosodes')
sections_html.append(h); charts_js.append(j)

# Oriental Herbs
h, j = make_section('herbs', '东方草药反应性', S['oriental_herbs'], chart_id='chart_herbs')
sections_html.append(h); charts_js.append(j)

# Emotions
h, j = make_section('emotions', '74项数字化多元情绪压力评估', S['emotions'], chart_id='chart_emotions')
sections_html.append(h); charts_js.append(j)

# Organ Sarcodes
h, j = make_section('organs', '器官拟态剂', S['organ_sarcodes'], chart_id='chart_organs')
sections_html.append(h); charts_js.append(j)

# Neurotransmitters
h, j = make_section('neuro', '神经递质平衡性评估', S['neurotransmitters'], chart_id='chart_neuro')
sections_html.append(h); charts_js.append(j)

# Build sidebar nav
nav_items = [
    ('cover', '📄 封面'),
    ('varhop', '⚡ 基本体质/VARHOP'),
    ('risk', '⚠️ 风险概况'),
    ('vitamins', '💊 维生素家族'),
    ('vita', '  └ 维生素A族详细'),
    ('vitb', '  └ 维生素B族详细'),
    ('vitc', '  └ 维生素C族详细'),
    ('vitd', '  └ 维生素D族详细'),
    ('vite', '  └ 维生素E族详细'),
    ('vitf', '  └ 维生素F详细'),
    ('vitk', '  └ 维生素K族详细'),
    ('vitu', '  └ 维生素U族详细'),
    ('amino', '🧬 氨基酸'),
    ('minerals', '🪨 矿物质'),
    ('aroma', '🌸 芳香疗法'),
    ('digestion', '🫄 一般消化系统'),
    ('carb', '🍚 碳水化合物代谢'),
    ('fat', '🧈 脂肪消化'),
    ('protein', '🥩 蛋白质消化'),
    ('spine', '🦴 脊柱系统'),
    ('xeno', '🧪 外源性物质'),
    ('addfactors', '➕ 额外因素'),
    ('causes', '🔍 疾病潜在原因'),
    ('aggrav', '📈 疾病加重因素'),
    ('miasms', '🧫 体质特征'),
    ('nosodes', '🦠 病原体特征'),
    ('herbs', '🌿 东方草药'),
    ('emotions', '💭 74项情绪'),
    ('organs', '🫀 器官拟态剂'),
    ('neuro', '🧠 神经递质'),
]

sidebar_html = ''.join([f'<a href="#{id}">{label}</a>' for id, label in nav_items])

# Build the complete HTML
data_json = json.dumps(D, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>营养与健康检测报告 - {M["name"]}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
// Embedded data - no external files needed
var REPORT_DATA = {data_json};
</script>
<style>
:root {{ --bg: #f5f0e8; --card: #fff; --text: #333; --border: #ddd; --accent: #2c5f2d; --warn: #d4a017; --danger: #c0392b; --sidebar-w: 250px; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif; background: var(--bg); color: var(--text); line-height: 1.7; }}
.sidebar {{ position: fixed; left: 0; top: 0; width: var(--sidebar-w); height: 100vh; background: #1a1a2e; color: #ccc; overflow-y: auto; z-index: 100; padding: 0; font-size: 12px; }}
.sidebar h2 {{ color: #fff; padding: 16px 18px; font-size: 15px; border-bottom: 1px solid #333; margin: 0; position: sticky; top: 0; background: #1a1a2e; }}
.sidebar a {{ display: block; padding: 5px 20px; color: #aaa; text-decoration: none; transition: .15s; border-left: 3px solid transparent; }}
.sidebar a:hover, .sidebar a.active {{ color: #fff; background: #16213e; border-left-color: #4caf50; }}
.main {{ margin-left: var(--sidebar-w); padding: 24px 32px; max-width: 1100px; }}
.cover {{ text-align: center; padding: 50px 20px; }}
.cover h1 {{ font-size: 30px; color: #1a3a1a; margin-bottom: 6px; }}
.cover h3 {{ font-weight: 400; color: #666; margin-bottom: 24px; font-size: 16px; }}
.meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px,1fr)); gap: 10px; max-width: 580px; margin: 0 auto 24px; text-align: left; }}
.meta-item {{ background: #fff; padding: 8px 14px; border-radius: 8px; border: 1px solid var(--border); }}
.meta-item label {{ font-size: 11px; color: #999; display: block; }}
.meta-item span {{ font-size: 14px; font-weight: 600; }}
.card {{ background: var(--card); border-radius: 12px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.05); border: 1px solid var(--border); }}
.card h3 {{ font-size: 17px; color: var(--accent); margin-bottom: 10px; border-bottom: 2px solid var(--accent); padding-bottom: 8px; }}
.summary-box {{ background: #f0f7f0; border-left: 4px solid var(--accent); padding: 10px 14px; border-radius: 6px; margin-bottom: 14px; font-size: 13px; }}
.legend {{ display: flex; gap: 14px; margin-bottom: 10px; font-size: 12px; flex-wrap: wrap; }}
.legend span {{ padding: 2px 8px; border-radius: 4px; }}
.legend .low {{ background: #ffe0e0; color: var(--danger); }}
.legend .high {{ background: #fff8e1; color: #b8860b; }}
.legend .normal {{ background: #e8f5e9; color: #2e7d32; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin: 8px 0; }}
thead th {{ background: #f0f0f0; padding: 7px 8px; text-align: left; font-weight: 600; position: sticky; top: 0; font-size: 12px; }}
tbody td {{ padding: 6px 8px; border-bottom: 1px solid #eee; }}
tbody tr:hover {{ background: #fafafa; }}
td.low {{ background: #ffe0e0; font-weight: 700; color: var(--danger); }}
td.high {{ background: #fff8e1; font-weight: 700; color: #b8860b; }}
td.normal {{ color: #2e7d32; }}
.chart-wrap {{ margin: 12px 0; position: relative; width: 100%; max-height: 380px; }}
.chart-wrap canvas {{ max-height: 380px; }}
@media (max-width: 768px) {{ .sidebar {{ display: none; }} .main {{ margin-left: 0; padding: 12px; }} }}
.spine-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px; }}
.spine-item {{ padding: 8px 12px; border-radius: 8px; border: 1px solid #ddd; font-size: 12px; }}
.spine-item strong {{ display: block; font-size: 14px; margin-bottom: 3px; }}
.spine-item .status {{ display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 11px; }}
.status-正常,.status-已校正,.status-Corrected {{ background: #e8f5e9; color: #2e7d32; }}
.status-未校正,.status-Not.Corrected,.status-困难,.status-Difficult {{ background: #fff3e0; color: #e65100; }}
.status-炎症,.status-inflammation,.status-暂时性神经压迫,.status-Temp.Nerve.Comp {{ background: #fff8e1; color: #f57f17; }}
.status-神经压迫,.status-NervCompression,.status-退化,.status-Degeneration {{ background: #ffe0e0; color: #c0392b; }}
.status-半脱位,.status-subluxation {{ background: #fce4ec; color: #c62828; }}
.scroll-top {{ position: fixed; bottom: 30px; right: 30px; width: 40px; height: 40px; background: var(--accent); color: #fff; border: none; border-radius: 50%; font-size: 20px; cursor: pointer; z-index: 200; display: none; box-shadow: 0 2px 8px rgba(0,0,0,.2); }}
.digest-summary {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; margin-bottom: 14px; }}
.digest-item {{ background: #f9f9f9; padding: 8px 12px; border-radius: 8px; text-align: center; }}
.digest-item .val {{ font-size: 22px; font-weight: 700; }}
.footer {{ text-align: center; padding: 32px; color: #999; font-size: 12px; }}
@media print {{ .sidebar,.scroll-top {{ display: none !important; }} .main {{ margin-left: 0; }} .card {{ break-inside: avoid; }} }}
</style>
</head>
<body>
<nav class="sidebar" id="sidebar"><h2>📋 报告目录</h2>{sidebar_html}</nav>
<button class="scroll-top" id="scrollTop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})" title="返回顶部">↑</button>
<div class="main" id="main">
{''.join(sections_html)}
<div class="footer">
  <p>营养与健康检测报告 · {M['name']} · 检测日期: {M['testDate']}</p>
  <p>本报告基于生物反馈检测数据，反应值仅供参考，不作为医学诊断依据。</p>
</div>
</div>
<script>
(function() {{
  // Charts
  {' '.join(charts_js)}

  // Scroll to top button
  window.addEventListener('scroll', function() {{
    document.getElementById('scrollTop').style.display = window.scrollY > 300 ? 'block' : 'none';
  }});

  // Active sidebar link
  var sections = document.querySelectorAll('.card[id]');
  var links = document.querySelectorAll('.sidebar a');
  window.addEventListener('scroll', function() {{
    var current = '';
    sections.forEach(function(s) {{
      if (window.scrollY >= s.offsetTop - 100) current = s.id;
    }});
    links.forEach(function(l) {{
      l.classList.toggle('active', l.getAttribute('href') === '#' + current);
    }});
  }});
}})();
</script>
</body>
</html>
'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Generated index.html ({len(html):,} bytes)')
print(f'Sections: {len(sections_html)}')
