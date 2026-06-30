// render_report.js - 完整报告渲染（匹配服务器版build_html.py的所有板块和样式）
// 由 build_static.py 嵌入到 index.html 中

const PALETTE = [
    'rgba(65,105,225,0.85)','rgba(220,20,60,0.85)','rgba(46,139,87,0.85)',
    'rgba(255,140,0,0.85)','rgba(138,43,226,0.85)','rgba(0,139,139,0.85)',
    'rgba(255,69,0,0.85)','rgba(70,130,180,0.85)','rgba(218,165,32,0.85)',
    'rgba(199,21,133,0.85)','rgba(34,139,34,0.85)','rgba(255,99,71,0.85)',
    'rgba(100,149,237,0.85)','rgba(178,34,34,0.85)','rgba(0,128,128,0.85)',
    'rgba(210,105,30,0.85)','rgba(123,104,238,0.85)','rgba(205,92,92,0.85)',
    'rgba(60,179,113,0.85)','rgba(255,160,122,0.85)','rgba(72,61,139,0.85)',
    'rgba(188,143,143,0.85)','rgba(95,158,160,0.85)','rgba(240,128,128,0.85)',
    'rgba(106,90,205,0.85)','rgba(184,134,11,0.85)','rgba(30,144,255,0.85)',
    'rgba(255,127,80,0.85)','rgba(50,205,50,0.85)','rgba(186,85,211,0.85)',
];

function statSummary(items) {
    const vals = items.map(i => i.value).filter(v => v !== null && v !== undefined);
    if (!vals.length) return '';
    const avg = (vals.reduce((a,b)=>a+b,0) / vals.length).toFixed(1);
    const high = items.filter(i => i.value !== null && i.value !== undefined && i.value >= 100).length;
    const low = items.filter(i => i.value !== null && i.value !== undefined && i.value <= 50).length;
    return `共 ${vals.length} 项 | 平均值: ${avg} | 高反应(≥100): ${high} 项 | 低反应(≤50): ${low} 项`;
}

function valClass(v) {
    if (v === null || v === undefined) return '';
    if (v <= 50) return 'low';
    if (v >= 100) return 'high';
    return 'normal';
}

function valBg(v) {
    if (v === null || v === undefined) return '';
    if (v <= 50) return 'background:#ffe0e0;';
    if (v >= 100) return 'background:#fff8e1;';
    return '';
}

function makeDataTable(items, cols) {
    const colLabels = {name:'检测项目',value:'反应值',desc:'说明解释',food:'食物来源',cn:'英文名'};
    let html = '<div style="overflow-x:auto;"><table><thead><tr>';
    for (const c of cols) html += `<th>${colLabels[c]||c}</th>`;
    html += '</tr></thead><tbody>';
    for (const it of items) {
        html += '<tr>';
        for (const c of cols) {
            if (c === 'value') {
                const v = it.value;
                html += `<td class="${valClass(v)}" style="${valBg(v)}">${v !== null && v !== undefined ? v : '-'}</td>`;
            } else {
                html += `<td>${it[c] || ''}</td>`;
            }
        }
        html += '</tr>';
    }
    html += '</tbody></table></div>';
    return html;
}

function makeBarChart(chartId, items, labelKey='name') {
    const labels = items.map(i => i[labelKey] || '');
    const values = items.map(i => i.value || 0);
    const n = values.length;
    const colors = values.map((_, i) => PALETTE[i % PALETTE.length]);
    const borders = colors.map(c => c.replace('0.85','1'));

    setTimeout(() => {
        const canvas = document.getElementById(chartId);
        if (!canvas) return;
        if (window._charts && window._charts[chartId]) window._charts[chartId].destroy();
        if (!window._charts) window._charts = {};

        window._charts[chartId] = new Chart(canvas, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderColor: borders,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: false, min: 0, max: 160,
                        grid: { color: '#e0e0e0' }
                    },
                    x: { ticks: { maxRotation: 60, font: { size: 10 } } }
                }
            },
            plugins: [{
                id: 'barLabels_'+chartId,
                afterDraw: function(chart) {
                    const ctx = chart.ctx;
                    const meta = chart.getDatasetMeta(0);
                    ctx.save();
                    ctx.font = 'bold 11px "PingFang SC","Microsoft YaHei",sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'bottom';
                    meta.data.forEach(function(bar, i) {
                        const val = values[i];
                        const x = bar.x;
                        const y = bar.y - 4;
                        if (val <= 50) ctx.fillStyle = '#c0392b';
                        else if (val >= 100) ctx.fillStyle = '#d4a017';
                        else ctx.fillStyle = '#2c5f2d';
                        ctx.fillText(val, x, y);
                    });
                    ctx.restore();
                }
            }]
        });
    }, 150);
}

function makeSection(id, title, items, chartId, cols='name,value,desc,food') {
    if (!items || !items.length) return '';
    const colsArr = cols.split(',');
    const summary = statSummary(items);
    let html = `<div class="report-card" id="${id}"><h3>${title}</h3>`;
    if (summary) html += `<div class="summary-box">${summary}</div>`;
    html += '<div class="legend"><span class="r-low">■ ≤50 长期压力</span><span class="r-normal">■ 50-100 平衡</span><span class="r-high">■ ≥100 近期压力</span></div>';
    html += `<div class="chart-wrap"><canvas id="${chartId}"></canvas></div>`;
    html += makeDataTable(items, colsArr);
    html += '</div>';
    if (chartId) makeBarChart(chartId, items);
    return html;
}

function renderFullReport(data) {
    const M = data.meta;
    const S = data.sections;

    // Build sidebar nav with collapsible groups
    const navGroups = [
        {id:'cover', label:'📄 封面'},
        {id:'varhop', label:'⚡ 基本体质'},
        {id:'risk', label:'⚠️ 风险概况'},
        {label:'💊 维生素家族', children:[
            'vitamins','vita','vitb','vitc','vitd','vite','vitf','vitk','vitu'
        ], childLabels:['总览','A族','B族','C族','D族','E族','F族','K族','U族']},
        {label:'🧬 消化代谢', children:[
            'amino','minerals','digestion','carb','fat','protein','aroma'
        ], childLabels:['氨基酸','矿物质','消化系统','碳水代谢','脂肪消化','蛋白质消化','芳香疗法']},
        {id:'spine', label:'🦴 脊柱'},
        {label:'🛡️ 外源与疾病', children:[
            'xeno','addfactors','causes','aggrav','miasms','nosodes','herbs'
        ], childLabels:['外源物质','额外因素','疾病原因','加重因素','体质','病原体','草药']},
        {id:'emotions', label:'💭 情绪'},
        {id:'organs', label:'🫀 器官'},
        {id:'neuro', label:'🧠 神经递质'},
    ];
    let sidebar = '';
    for (const g of navGroups) {
        if (g.children) {
            sidebar += `<a href="javascript:void(0)" class="nav-group" onclick="this.classList.toggle('open')">▸ ${g.label}</a>`;
            sidebar += '<div class="nav-sub">';
            for (let i = 0; i < g.children.length; i++) {
                sidebar += `<a href="#${g.children[i]}">  ${g.childLabels[i]}</a>`;
            }
            sidebar += '</div>';
        } else {
            sidebar += `<a href="#${g.id}">${g.label}</a>`;
        }
    }

    let html = `
<style>
.report-body { font-family: 'PingFang SC','Microsoft YaHei',sans-serif; background: #f5f0e8; color: #333; line-height: 1.7; }
.r-sidebar { position: fixed; left: 0; top: 0; width: 240px; height: 100vh; background: #1a1a2e; color: #ccc; overflow-y: auto; z-index: 100; font-size: 12px; }
.r-sidebar h2 { color: #fff; padding: 16px 18px; font-size: 15px; border-bottom: 1px solid #333; margin: 0; position: sticky; top: 0; background: #1a1a2e; }
.r-sidebar a { display: block; padding: 5px 20px; color: #aaa; text-decoration: none; border-left: 3px solid transparent; cursor: pointer; }
.r-sidebar a:hover, .r-sidebar a.active { color: #fff; background: #16213e; border-left-color: #4caf50; }
.r-sidebar .nav-group { color: #ddd; font-weight: 600; padding: 6px 16px; }
.r-sidebar .nav-group.open { color: #4caf50; }
.r-sidebar .nav-group.open::before { content: '▾ '; }
.r-sidebar .nav-group::before { content: '▸ '; }
.r-sidebar .nav-sub { display: none; padding-left: 12px; }
.r-sidebar .nav-group.open + .nav-sub { display: block; }
.r-sidebar .nav-sub a { font-size: 11px; padding: 3px 20px; }
.r-main { margin-left: 240px; padding: 24px 32px; max-width: 1100px; }
.report-cover { text-align: center; padding: 50px 20px; background: #fff; border-radius: 12px; margin-bottom: 20px; }
.report-cover h1 { font-size: 30px; color: #1a3a1a; margin-bottom: 6px; }
.report-cover h3 { font-weight: 400; color: #666; margin-bottom: 24px; font-size: 16px; }
.meta-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px,1fr)); gap: 10px; max-width: 580px; margin: 0 auto 24px; text-align: left; }
.meta-item { background: #fff; padding: 8px 14px; border-radius: 8px; border: 1px solid #ddd; }
.meta-item label { font-size: 11px; color: #999; display: block; }
.meta-item span { font-size: 14px; font-weight: 600; }
.report-card { background: #fff; border-radius: 12px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.05); border: 1px solid #ddd; }
.report-card h3 { font-size: 17px; color: #2c5f2d; margin-bottom: 10px; border-bottom: 2px solid #2c5f2d; padding-bottom: 8px; }
.summary-box { background: #f0f7f0; border-left: 4px solid #2c5f2d; padding: 10px 14px; border-radius: 6px; margin-bottom: 14px; font-size: 13px; }
.legend { display: flex; gap: 14px; margin-bottom: 10px; font-size: 12px; flex-wrap: wrap; }
.r-low { background: #ffe0e0; color: #c0392b; padding: 2px 8px; border-radius: 4px; }
.r-high { background: #fff8e1; color: #b8860b; padding: 2px 8px; border-radius: 4px; }
.r-normal { background: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 4px; }
.chart-wrap { margin: 12px 0; width: 100%; max-height: 380px; }
.chart-wrap canvas { max-height: 380px; }
table { width: 100%; border-collapse: collapse; font-size: 12px; margin: 8px 0; }
thead th { background: #f0f0f0; padding: 7px 8px; text-align: left; font-weight: 600; font-size: 12px; }
tbody td { padding: 6px 8px; border-bottom: 1px solid #eee; }
tbody tr:hover { background: #fafafa; }
td.low { background: #ffe0e0; font-weight: 700; color: #c0392b; }
td.high { background: #fff8e1; font-weight: 700; color: #b8860b; }
td.normal { color: #2e7d32; }
.r-scroll-top { position: fixed; bottom: 30px; right: 30px; width: 40px; height: 40px; background: #2c5f2d; color: #fff; border: none; border-radius: 50%; font-size: 20px; cursor: pointer; z-index: 200; display: none; box-shadow: 0 2px 8px rgba(0,0,0,.2); }
@media (max-width: 768px) { .r-sidebar { display: none; } .r-main { margin-left: 0; padding: 12px; } }
@media print { .r-sidebar,.r-scroll-top { display: none !important; } .r-main { margin-left: 0; } .report-card { break-inside: avoid; } }
</style>

<nav class="r-sidebar"><h2>📋 报告目录</h2>${sidebar}</nav>
<button class="r-scroll-top" onclick="window.scrollTo({top:0,behavior:'smooth'})">↑</button>
<div class="r-main">

<div class="report-cover" id="cover">
  <h1>营养与健康检测报告</h1>
  <h3>Nutrition and Wellness Assessment Report</h3>
  <div class="meta-grid">
    <div class="meta-item"><label>姓名</label><span>${M.name||''}</span></div>
    <div class="meta-item"><label>性别</label><span>${M.gender||''}</span></div>
    <div class="meta-item"><label>出生日期</label><span>${M.birthDate||''}</span></div>
    <div class="meta-item"><label>检测日期</label><span>${M.testDate||''}</span></div>
    <div class="meta-item"><label>就诊编号</label><span>${M.visitNumber||''}</span></div>
    <div class="meta-item"><label>检测师</label><span>${M.practitioner||'<span style="color:#999;">（未提取到）</span>'}</span></div>
  </div>
  <p style="color:#999;font-size:13px;">本报告基于生物反馈检测数据，反应值仅供参考，不作为医学诊断依据。</p>
</div>
`;

    // VARHOP
    const vh = S.varhop || {};
    const varhopItems = [
        {name:'电压指数(Volt)',value:vh.volt,desc:'体力指数，100-80正常',food:''},
        {name:'电流强度(Amper)',value:vh.amper,desc:'脑力指数，100-80正常',food:''},
        {name:'电阻(Resistance)',value:vh.resistance,desc:'免疫力指数',food:''},
        {name:'水合指数(Hydration)',value:vh.hydration,desc:'细胞水分',food:''},
        {name:'氧化指数(Oxidation)',value:vh.oxidation,desc:'血液携氧能力',food:''},
        {name:'质子压力',value:vh.proton_pressure,desc:'能量代谢/ATP生产',food:''},
        {name:'电子压力',value:vh.electron_pressure,desc:'能量转换/ATP合成',food:''},
        {name:'相角指数',value:vh.phase_angle,desc:'细胞再生/老化指标',food:''},
        {name:'相反应指数',value:vh.phase_response,desc:'各系统协同能力',food:''},
        {name:'阻抗指数',value:vh.impedance,desc:'能量流通指标',food:''},
        {name:'反应速度',value:vh.reaction_speed,desc:'<19正常，100重度迟钝',food:''},
        {name:'细胞活力指数',value:vh.cellular_vitality,desc:'≥6正常',food:''},
    ];
    html += makeSection('varhop', '⚡ VARHOP 数值 — 身体基本体质评估', varhopItems, 'chart_varhop');

    // Risk profile
    const risk = S.risk_profile || {};
    const riskItems = Object.entries(risk).map(([k,v]) => ({name: k.replace(/_/g,' '), value: v, desc:'', food:''}));
    html += makeSection('risk', '⚠️ 风险概况', riskItems, 'chart_risk');

    // Sections config - matching build_html.py
    const sectionConfigs = [
        ['vitamins','vitamin_families','💊 维生素家族反应值','chart_vitamins'],
        ['vita','vitamin_a_detail','维生素A族详细','chart_vita'],
        ['vitb','vitamin_b_detail','维生素B族详细','chart_vitb'],
        ['vitc','vitamin_c_detail','维生素C族详细','chart_vitc'],
        ['vitd','vitamin_d_detail','维生素D族详细','chart_vitd'],
        ['vite','vitamin_e_detail','维生素E族详细','chart_vite'],
        ['vitf','vitamin_f_detail','维生素F（脂肪酸）详细','chart_vitf'],
        ['vitk','vitamin_k_detail','维生素K族详细','chart_vitk'],
        ['vitu','vitamin_u_detail','维生素U族（辅酶Q）详细','chart_vitu'],
        ['amino','amino_acids','🧬 氨基酸平衡性评估','chart_amino'],
        ['minerals','minerals','🪨 矿物质平衡性评估','chart_minerals'],
        ['aroma','aromatherapy','🌸 芳香疗法反应性评估','chart_aroma'],
        ['digestion','general_digestion','🫄 一般消化系统评估','chart_digestion'],
        ['carb','carbohydrate_digestion','🍚 碳水化合物代谢反应性评估','chart_carb'],
        ['fat','fat_digestion','🧈 脂肪消化评估','chart_fat'],
        ['protein','protein_digestion','🥩 蛋白质消化评估','chart_protein'],
        ['xeno','xenobiotics','🧪 外源性物质反应性评估','chart_xeno'],
        ['addfactors','additional_factors','➕ 外源性物质额外因素评估','chart_addfactors'],
        ['causes','disease_causes','🔍 导致健康风险和健康恶化的原因','chart_causes'],
        ['aggrav','disease_aggravations','📈 疾病加重因素','chart_aggrav'],
        ['miasms','miasms','🧫 体质特征反应性','chart_miasms'],
        ['nosodes','nosodes','🦠 病原体特征反应性','chart_nosodes'],
        ['herbs','oriental_herbs','🌿 东方草药反应性','chart_herbs'],
        ['emotions','emotions','💭 74项数字化多元情绪压力评估','chart_emotions'],
        ['organs','organ_sarcodes','🫀 器官拟态剂','chart_organs'],
        ['neuro','neurotransmitters','🧠 神经递质平衡性评估','chart_neuro'],
    ];

    for (const [id, key, title, chartId] of sectionConfigs) {
        const items = S[key];
        if (items && Array.isArray(items) && items.length > 0) {
            if (key === 'spine') {
                // Special spine rendering
                html += `<div class="report-card" id="${id}"><h3>${title}</h3><div class="summary-box">共 ${items.length} 个椎位</div>`;
                html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;">';
                for (const it of items) {
                    const st = it.status || '';
                    let stCls = '';
                    if (['已校正','Corrected','正常'].includes(st)) stCls = 'status-green';
                    else if (['未校正','Not Corrected','困难','Difficult'].includes(st)) stCls = 'status-orange';
                    else if (['炎症','inflammation','暂时性神经压迫','Temp Nerve Comp'].includes(st)) stCls = 'status-yellow';
                    else if (['神经压迫','NervCompression','退化','Degeneration','半脱位','subluxation'].includes(st)) stCls = 'status-red';
                    html += `<div style="padding:8px 12px;border-radius:8px;border:1px solid #ddd;font-size:12px;">
                      <strong style="font-size:14px;">${it.vertebra||''} · ${it.region||''}</strong>
                      <span class="${stCls}" style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;margin-left:4px;">${st}</span>
                      <div style="margin-top:4px;font-size:11px;color:#666;">${it.body||''}</div></div>`;
                }
                html += '</div></div>';
            } else {
                html += makeSection(id, title, items, chartId);
            }
        }
    }

    html += `<div style="text-align:center;padding:32px;color:#999;font-size:12px;">
      <p>营养与健康检测报告 · ${M.name||''} · 检测日期: ${M.testDate||''}</p>
      <p>仅供健康管理参考，不作为医学诊断依据</p></div></div>`;

    // Add scroll behavior for sidebar
    html += `<script>
(function(){
  var sections = document.querySelectorAll('.report-card[id]');
  var links = document.querySelectorAll('.r-sidebar a');
  var btn = document.querySelector('.r-scroll-top');
  window.addEventListener('scroll', function(){
    if (btn) btn.style.display = window.scrollY > 300 ? 'block' : 'none';
    var current = '';
    sections.forEach(function(s){ if(window.scrollY >= s.offsetTop - 100) current = s.id; });
    links.forEach(function(l){ l.classList.toggle('active', l.getAttribute('href')==='#'+current); });
  });
})();
<\/script>`;

    return html;
}

// Export for use in build_static.py
if (typeof module !== 'undefined') { module.exports = { renderFullReport, PALETTE }; }
