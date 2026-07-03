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

function makeDataTable(items, cols, labels) {
    const defaultLabels = {name:'检测项目',value:'反应值',desc:'详解',food:'食物来源',cn:'英文名'};
    const L = Object.assign({}, defaultLabels, labels || {});
    let html = '<div style="overflow-x:auto;"><table><thead><tr>';
    for (const c of cols) html += `<th>${L[c]||c}</th>`;
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

    // Collect chart config for download
    if (!window._chartConfigs) window._chartConfigs = [];
    window._chartConfigs.push({ chartId, labels, values, colors, borders });

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

function makeSection(id, title, items, chartId, cols, labels) {
    if (!items || !items.length) return '';
    const colsArr = (cols || 'name,value,desc,food').split(',');
    const summary = statSummary(items);
    let html = `<div class="report-card" id="${id}"><h3>${title}</h3>`;
    if (summary) html += `<div class="summary-box">${summary}</div>`;
    html += '<div class="legend"><span class="r-low">■ ≤50 长期压力</span><span class="r-normal">■ 50-100 平衡</span><span class="r-high">■ ≥100 近期压力</span></div>';
    html += `<div class="chart-wrap"><canvas id="${chartId}"></canvas></div>`;
    html += makeDataTable(items, colsArr, labels);
    html += '</div>';
    if (chartId) makeBarChart(chartId, items);
    return html;
}

function getOptimalCols(items) {
    const hasFood = items.some(function(i){ return i.food && i.food.length > 3; });
    const hasDesc = items.some(function(i){ return i.desc && i.desc.length > 3; });
    if (hasDesc && hasFood) return 'name,value,desc,food';
    if (hasDesc) return 'name,value,desc';
    if (hasFood) return 'name,value,food';
    return 'name,value';
}

function renderFullReport(data) {
    const M = data.meta;
    const S = data.sections;

    // Build sidebar nav
    const navItems = [
        ['cover','📄 封面'],
        ['s1','1. 基本体质'],['s2','2. 氨基酸'],['s3','3. 矿物质'],
        ['s4','4. 芳香疗法'],['s5','5. 脊柱反应性'],
        ['s6','6. 水溶性维生素'],['s7','7. 脂溶性维生素'],
        ['s8','8. 一般消化系统'],['s9','9. 碳水化合物代谢'],
        ['s10','10. 蛋白质和脂类代谢'],['s11','11. 外源性物质'],
        ['s12','12. 外源性物质额外因素'],
        ['s13','13. 导致健康风险和健康恶化的原因'],
        ['s14','14. 74项情绪'],['s15','15. 压力指数和来源'],
        ['s16','16. 神经递质'],
    ];
    const sidebar = navItems.map(([id,label]) => `<a href="#${id}">${label}</a>`).join('');

    let html = `
<div style="text-align:center;margin-bottom:20px;" id="cover">
  <img src="covers/cover1.png" style="width:100%;max-width:100%;display:block;margin:0 auto;" alt="封面1">
  <img src="covers/cover2.png" style="width:100%;max-width:100%;display:block;margin:0 auto;" alt="封面2">
  <div style="text-align:center;padding:20px;">
    <p style="color:#666;font-size:14px;">姓名: ${M.name||''} &nbsp;|&nbsp; 性别: ${M.gender||''} &nbsp;|&nbsp; 检测日期: ${M.testDate||''}</p>
    <p style="color:#999;font-size:12px;">本报告基于生物反馈检测数据，反应值仅供参考，不作为医学诊断依据。</p>
  </div>
</div>
<style>
.report-body { font-family: 'PingFang SC','Microsoft YaHei',sans-serif; background: #f5f0e8; color: #333; line-height: 1.7; }
.r-sidebar { position: fixed; left: 0; top: 0; width: 200px; height: 100vh; background: #1a1a2e; color: #ccc; overflow-y: auto; z-index: 100; font-size: 12px; }
.r-sidebar h2 { color: #fff; padding: 14px 16px; font-size: 14px; border-bottom: 1px solid #333; margin: 0; position: sticky; top: 0; background: #1a1a2e; }
.r-sidebar a { display: block; padding: 4px 18px; color: #aaa; text-decoration: none; border-left: 3px solid transparent; }
.r-sidebar a:hover, .r-sidebar a.active { color: #fff; background: #16213e; border-left-color: #4caf50; }
.r-main { margin-left: 200px; padding: 0; max-width: none; }
.r-main .report-card { margin: 0 20px 20px 20px; }
.r-main .report-cover, .r-main .report-back-cover { margin: 0; }
.report-cover { text-align: center; padding: 0; background: #fff; border-radius: 12px; margin-bottom: 0; }
.report-cover h1 { font-size: 30px; color: #1a3a1a; margin-bottom: 6px; }
.report-cover h3 { font-weight: 400; color: #666; margin-bottom: 24px; font-size: 16px; }
.meta-item-cover { background:rgba(255,255,255,.15); padding:10px 14px; border-radius:8px; }
.meta-item-cover label { font-size:11px; opacity:.7; display:block; }
.meta-item-cover span { font-size:15px; font-weight:600; }
.meta-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px,1fr)); gap: 10px; max-width: 700px; margin: 0 auto 24px; text-align: left; }
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
.chart-wrap { margin: 12px 0; width: 100%; max-height: 450px; }
.chart-wrap canvas { max-height: 450px; }
table { width: 100%; border-collapse: collapse; font-size: 12px; margin: 8px 0; }
thead th { background: #f0f0f0; padding: 7px 8px; text-align: left; font-weight: 600; font-size: 12px; }
tbody td { padding: 6px 8px; border-bottom: 1px solid #eee; }
tbody tr:hover { background: #fafafa; }
td.low { background: #ffe0e0; font-weight: 700; color: #c0392b; }
td.high { background: #fff8e1; font-weight: 700; color: #b8860b; }
td.normal { color: #2e7d32; }
.r-scroll-top { position: fixed; bottom: 30px; right: 30px; width: 40px; height: 40px; background: #2c5f2d; color: #fff; border: none; border-radius: 50%; font-size: 20px; cursor: pointer; z-index: 200; display: none; box-shadow: 0 2px 8px rgba(0,0,0,.2); }
@media (max-width: 768px) { .r-sidebar { display: none; } .r-main { margin-left: 0; padding: 10px; } }
@media print { .r-sidebar,.r-scroll-top { display: none !important; } .r-main { margin-left: 0; } .report-card { break-inside: avoid; } }
</style>

<nav class="r-sidebar"><h2>📋 报告目录</h2>${sidebar}</nav>
<button class="r-scroll-top" onclick="window.scrollTo({top:0,behavior:'smooth'})">↑</button>
<div class="r-main">
`;


    // Section configs matching new template (改5)
    const sectionKeys = [
        '1.基本体质','2.氨基酸','3.矿物质','4.芳香疗法','5.脊柱反应性',
        '6.水溶性维生素','7.脂溶性维生素','8.一般消化系统','9.碳水化合物代谢',
        '10.蛋白质和脂类代谢','11.外源性物质','12.外源性物质额外因素',
        '13.导致健康风险和健康恶化的原因','14.74项情绪','15.压力指数和来源','16.神经递质'
    ];

    for (let i = 0; i < sectionKeys.length; i++) {
        const key = sectionKeys[i];
        const sections = S[key];
        if (!sections || !Array.isArray(sections) || !sections.length) continue;

        // Handle sheets with sub-sections (e.g., 3.矿物质 has 2)
        for (let si = 0; si < sections.length; si++) {
            const sec = sections[si];
            const items = sec.indicators || sec;
            if (!items || !Array.isArray(items) || !items.length) continue;

            const id = 's' + (i + 1) + (sections.length > 1 ? '_' + (si + 1) : '');
            const title = sections.length > 1 ? sec.title || key : key;
            const chartId = 'chart_' + id;

            if (key.includes('脊柱')) {
                html += `<div class="report-card" id="${id}"><h3>${title}</h3>`;
                html += '<div style="overflow-x:auto;"><table><thead><tr><th>脊柱名称</th><th>区域</th><th>压力状态</th><th>对应身体部位</th></tr></thead><tbody>';
                // Body part mapping from template
                const bodyMap = {
                    'C1':'头部血液供应，脑垂体，头皮，脸部骨骼，大脑，内耳及中耳，交感神经系统',
                    'C2':'双耳，视神经，听觉神经，额窦，乳突，舌，前额',
                    'C3':'脸颊，外耳，面部骨骼，牙，三叉神经',
                    'C4':'鼻，唇，嘴，耳咽',
                    'C5':'声带，腺体，咽',
                    'C6':'颈部肌肉，肩，扁桃体',
                    'C7':'甲状腺，肩关节，肘关节',
                    'T1':'前臂，包括手、腕及手指，食管，气管',
                    'T2':'心，包括瓣膜及心包，冠状动脉',
                    'T3':'肺，支气管，胸膜，胸廓，乳房',
                    'T4':'胆囊，胆总管',
                    'T5':'肝，腹腔神经丛，总循环系统',
                    'T6':'胃','T7':'胰腺，十二指肠','T8':'脾','T9':'肾上腺',
                    'T10':'肾脏','T11':'输尿管','T12':'小肠，输卵管',
                    'L1':'大肠，腹股沟','L2':'阑尾，腹部，大腿',
                    'L3':'生殖器官，膀胱，膝','L4':'坐骨神经，腰部','L5':'小腿，脚踝，脚'
                };
                for (const it of items) {
                    const st = it.desc || '';
                    let stColor = '#2e7d32', stBg = '#e8f5e9';
                    if (/神经压迫|退化|重度/.test(st)) { stColor = '#c0392b'; stBg = '#ffe0e0'; }
                    else if (/炎症|中度|暂时/.test(st)) { stColor = '#f57f17'; stBg = '#fff8e1'; }
                    else if (/未校正|困难|半脱位|轻度/.test(st)) { stColor = '#e65100'; stBg = '#fff3e0'; }
                    const body = bodyMap[it.name] || it.desc || '';
                    html += `<tr>
                      <td><strong>${it.name||''}</strong></td>
                      <td>${it.cn||''}</td>
                      <td><span style="background:${stBg};color:${stColor};padding:2px 8px;border-radius:4px;font-weight:600;">${st}</span></td>
                      <td style="font-size:11px;color:#666;">${body}</td></tr>`;
                }
                html += '</tbody></table></div></div>';
            } else if (key.includes('神经递质')) {
                // Neuro: two-column paired layout, no English, no chart
                html += `<div class="report-card" id="${id}"><h3>${title}</h3>`;
                html += '<div style="overflow-x:auto;"><table><thead><tr><th>检测项目</th><th>反应值</th><th>检测项目</th><th>反应值</th></tr></thead><tbody>';
                for (let ni = 0; ni < items.length; ni += 2) {
                    const a = items[ni] || {};
                    const b = items[ni + 1] || {};
                    html += `<tr>
                      <td>${a.name||''}</td><td class="${valClass(a.value)}" style="${valBg(a.value)}">${a.value!=null?a.value:'-'}</td>
                      <td>${b.name||''}</td><td class="${valClass(b.value)}" style="${valBg(b.value)}">${b.value!=null?b.value:'-'}</td>
                    </tr>`;
                }
                html += '</tbody></table></div></div>';
            } else if (key.includes('情绪')) {
                // Emotions: split into 3 groups, no chart for groups
                const half = Math.floor(items.length / 2);
                const low10 = items.slice(0, 10);
                const high10 = items.slice(10, 20);
                const rest = items.slice(20);
                html += `<div class="report-card" id="${id}"><h3>${title}</h3>`;
                const emoLabels = {name:'检测项目',value:'反应值'};
                if (low10.length) {
                    html += '<h4 style="margin-top:10px;">📉 反应值最低的10项</h4>';
                    html += makeDataTable(low10, ['name','value'], emoLabels);
                }
                if (high10.length) {
                    html += '<h4 style="margin-top:10px;">📈 反应值最高的10项</h4>';
                    html += makeDataTable(high10, ['name','value'], emoLabels);
                }
                if (rest.length) {
                    html += '<h4 style="margin-top:10px;">📊 全部情绪特征</h4>';
                    html += makeDataTable(rest, ['name','value'], emoLabels);
                }
                html += '</div>';
            } else {
                // 列配置完全按模板
                let cols = 'name,value,desc,food';
                const labels = {};
                if (key.includes('基本体质') || key.includes('压力指数')) {
                    cols = 'name,value,desc,food'; labels.desc = '数值说明'; labels.food = '身体反应与症状'; }
                else if (key.includes('氨基酸') || key.includes('矿物质') || key.includes('水溶性') || key.includes('脂溶性')) {
                    cols = 'name,value,desc,food'; labels.desc = '详解'; labels.food = '食物来源'; }
                else if (key.includes('芳香') || key.includes('消化') || key.includes('碳水') || key.includes('蛋白质') || key.includes('外源性') || key.includes('额外因素') || key.includes('导致健康')) {
                    cols = 'name,value,desc'; labels.desc = '详解'; }
                else if (key.includes('脊柱')) { /* special rendering */ }
                html += makeSection(id, title, items, chartId, cols, labels);
            }
        }
    }

    html += `<div style="text-align:center;padding:32px;color:#999;font-size:12px;">
      <p>营养与健康检测报告 · ${M.name||''} · 检测日期: ${M.testDate||''}</p>
      <p>仅供健康管理参考，不作为医学诊断依据</p></div>
<div style="page-break-before:always;"></div>
<div style="text-align:center;margin-top:20px;">
  <img src="covers/back0.png" style="width:100%;max-width:100%;display:block;margin:0 auto;" alt="封底">
  <img src="covers/back1.png" style="width:100%;max-width:100%;display:block;margin:0 auto;" alt="封底1">
  <img src="covers/back2.png" style="width:100%;max-width:100%;display:block;margin:0 auto;" alt="封底2">
  <img src="covers/back3.png" style="width:100%;max-width:100%;display:block;margin:0 auto;" alt="封底3">
  <img src="covers/back4.png" style="width:100%;max-width:100%;display:block;margin:0 auto;" alt="封底4">
</div></div>`;

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
