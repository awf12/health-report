#!/usr/bin/env python3
"""生成纯浏览器版报告系统 - 部署到GitHub Pages"""
import json

with open('data_template.json') as f:
    TEMPLATE = json.load(f)

TEMPLATE_JS = json.dumps(TEMPLATE, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>营养与健康检测报告系统</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root {{ --accent: #2c5f2d; --danger: #c0392b; --warn: #d4a017; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'PingFang SC','Microsoft YaHei',sans-serif; background: #f5f0e8; color: #333; }}
.header {{ background: #1a1a2e; color: #fff; padding: 14px 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }}
.header h1 {{ font-size: 18px; }}
.container {{ max-width: 960px; margin: 0 auto; padding: 20px; }}
.card {{ background: #fff; border-radius: 12px; padding: 20px 24px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.05); }}
.card h2 {{ font-size: 16px; color: var(--accent); margin-bottom: 12px; }}
.upload-zone {{ border: 2px dashed #ccc; border-radius: 12px; padding: 30px; text-align: center; cursor: pointer; transition: .3s; }}
.upload-zone:hover, .upload-zone.drag {{ border-color: var(--accent); background: #f0f7f0; }}
.upload-zone input {{ display: none; }}
.upload-zone .icon {{ font-size: 40px; }}
.btn {{ padding: 10px 24px; background: var(--accent); color: #fff; border: none; border-radius: 8px; font-size: 14px; cursor: pointer; }}
.btn:hover {{ opacity: .85; }}
.btn-warn {{ background: #e67e22; }}
.customer-list {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px,1fr)); gap: 10px; }}
.customer-card {{ border: 1px solid #ddd; border-radius: 10px; padding: 14px; display: flex; justify-content: space-between; align-items: center; }}
.customer-card:hover {{ border-color: var(--accent); }}
.customer-card strong {{ font-size: 15px; display: block; }}
.customer-card span {{ font-size: 12px; color: #999; }}
.btn-sm {{ padding: 5px 10px; border-radius: 5px; border: none; cursor: pointer; font-size: 12px; text-decoration: none; }}
.btn-view {{ background: var(--accent); color: #fff; }}
.btn-dl {{ background: #e8e8e8; color: #333; }}
.btn-del {{ background: #fee; color: var(--danger); }}
.msg {{ padding: 8px 14px; border-radius: 6px; margin-bottom: 10px; display: none; }}
.msg.show {{ display: block; }}
.msg.success {{ background: #e8f5e9; color: #2e7d32; }}
.msg.error {{ background: #ffe0e0; color: #c0392b; }}
.msg.info {{ background: #e3f2fd; color: #1565c0; }}
.progress {{ display: none; height: 6px; background: #e0e0e0; border-radius: 3px; margin: 12px 0; overflow: hidden; }}
.progress.active {{ display: block; }}
.progress-bar {{ height: 100%; background: var(--accent); width: 0%; transition: width .3s; }}
@media (max-width: 600px) {{ .header {{ padding: 10px 14px; }} .container {{ padding: 10px; }} }}
</style>
</head>
<body>
<div class="header">
  <h1>📋 营养与健康检测报告系统</h1>
  <span style="font-size:12px;opacity:.7">纯浏览器版 · 无需服务器 · 不限量</span>
</div>
<div class="container">
  <div id="msgBox"></div>
  <div class="progress" id="progress"><div class="progress-bar" id="progressBar"></div></div>

  <div class="card">
    <h2>📤 上传 PDF 生成报告</h2>
    <div class="upload-zone" id="uploadZone">
      <div class="icon">📄</div>
      <p>拖拽 PDF 到此处，或点击选择</p>
      <p style="font-size:12px;color:#aaa;">支持 QX WORLD 生物反馈检测报告 | 纯浏览器处理，不上传服务器</p>
      <input type="file" id="fileInput" accept=".pdf" multiple>
      <button class="btn" onclick="document.getElementById('fileInput').click()">📁 选择文件</button>
      <button class="btn btn-warn" onclick="processAll()" style="margin-top:10px;display:block;width:100%;">🚀 批量生成报告</button>
      <div id="fileList" style="margin-top:8px;font-size:13px;color:var(--accent);"></div>
    </div>
  </div>

  <div class="card">
    <h2>👥 已有报告（浏览器本地存储）</h2>
    <div class="customer-list" id="customerList"><p style="color:#999;">暂无报告</p></div>
  </div>
</div>

<script>
// ============ EMBEDDED TEMPLATE ============
const TEMPLATE = {TEMPLATE_JS};
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

// ============ APP STATE ============
let pendingFiles = [];
let charts = {{}};

// ============ UI HELPERS ============
function msg(text, type) {{
  const el = document.getElementById('msgBox');
  el.innerHTML = '<div class="msg '+type+' show">'+text+'</div>';
  setTimeout(() => el.innerHTML = '', 5000);
}}

function setProgress(pct) {{
  const bar = document.getElementById('progressBar');
  document.getElementById('progress').classList.add('active');
  bar.style.width = pct + '%';
  if (pct >= 100) setTimeout(() => document.getElementById('progress').classList.remove('active'), 1000);
}}

// ============ FILE HANDLING ============
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');

uploadZone.addEventListener('dragover', e => {{ e.preventDefault(); uploadZone.classList.add('drag'); }});
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag'));
uploadZone.addEventListener('drop', e => {{
  e.preventDefault(); uploadZone.classList.remove('drag');
  addFiles(Array.from(e.dataTransfer.files));
}});
fileInput.addEventListener('change', e => addFiles(Array.from(e.target.files)));
uploadZone.addEventListener('click', e => {{ if (e.target === uploadZone || e.target.classList.contains('icon') || e.target.tagName === 'P') fileInput.click(); }});

function addFiles(files) {{
  const pdfs = files.filter(f => f.name.endsWith('.pdf'));
  pendingFiles = [...pendingFiles, ...pdfs];
  document.getElementById('fileList').innerHTML = pendingFiles.map((f,i) =>
    '<div>📄 '+f.name+' ('+(f.size/1024/1024).toFixed(1)+'MB)</div>'
  ).join('');
  if (pendingFiles.length) msg('已选择 '+pendingFiles.length+' 个文件，点击「批量生成报告」开始', 'info');
}}

// ============ PDF PROCESSING ============
async function extractTextFromPDF(file) {{
  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
  let fullText = '';
  let pageTexts = [];
  for (let i = 1; i <= pdf.numPages; i++) {{
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const text = content.items.map(it => it.str).join(' ');
    pageTexts.push(text);
    fullText += text + '\\n';
  }}
  return {{ fullText, pageTexts, numPages: pdf.numPages }};
}}

function extractValues(fullText) {{
  const valueMap = {{}};

  // Extract VARHOP values
  const varhopPatterns = {{
    volt: /Volt\\s+(\\d+)/i, amper: /Amper\\s+(\\d+)/i,
    resistance: /Resistance\\s+(\\d+)/i, hydration: /Hydration\\s+(\\d+)/i,
    oxidation: /Oxidation\\s+(\\d+)/i,
    proton_pressure: /Proton pressure\\s+(\\d+)/i,
    electron_pressure: /Electron pressure\\s+(\\d+)/i,
    resonant_frequency: /Major resonant frequency[^\\d]*(\\d+)/i,
    reactance_speed: /Reactance speed index\\s+(\\d+)/i,
    phase_angle: /Phase angle\\s+(\\d+)/i,
    phase_response: /Phase response react\\s+(\\d+)/i,
    impedance: /Impedance\\s+(\\d+)/i,
    reaction_speed: /Parts per seconds[^\\d]*(\\d+)/i,
    body_fat: /Body fat\\s+(\\d+%?)/i,
    cellular_vitality: /Cellular vitality[^\\d]*(\\d+)/i,
  }};
  for (const [k, pat] of Object.entries(varhopPatterns)) {{
    const m = fullText.match(pat);
    if (m) valueMap[k] = parseInt(m[1]) || m[1];
  }}

  // Extract all label-value pairs from data pages
  const lines = fullText.split('\\n');
  for (const line of lines) {{
    const trimmed = line.trim();
    if (!trimmed || trimmed.length > 200) continue;
    if (/^\\d+\\s*\/\\s*\\d+$/.test(trimmed)) continue;
    if (/^(©|QX WORLD|保留所有)/.test(trimmed)) continue;

    // Match: label (number) at end
    const m = trimmed.match(/^(.+?)\\s+(\\d{{1,4}})\\b/);
    if (m) {{
      const name = m[1].trim().toLowerCase();
      const val = parseInt(m[2]);
      if (val >= 0 && val <= 2000 && name.length >= 2) {{
        valueMap[name] = val;
      }}
    }}
  }}

  return valueMap;
}}

function lookupValue(valueMap, ...names) {{
  for (const name of names) {{
    if (!name) continue;
    const key = name.toLowerCase().trim();
    if (valueMap[key] !== undefined) return valueMap[key];
    // Fuzzy: key without parentheses
    const cleanKey = key.replace(/\\s*\\(.*/, '').trim();
    for (const [k, v] of Object.entries(valueMap)) {{
      const kClean = k.replace(/\\s*\\(.*/, '').trim();
      if (cleanKey === kClean) return v;
    }}
    // Contains match
    for (const [k, v] of Object.entries(valueMap)) {{
      if (k.includes(key) || (key.length >= 3 && key.includes(k))) return v;
    }}
  }}
  return null;
}}

function extractMeta(pageTexts) {{
  const meta = {{name:'', gender:'', birthDate:'', testDate:'', visitNumber:'', soc:'',
    practitioner:'', clinic:'', address:'', phone:'', country:'中国', reportDate:''}};

  const p3 = pageTexts[2] || '';
  const nameM = p3.match(/(\\S{{2,15}})\\s+(?:Female|Male)\\s/);
  if (nameM) meta.name = nameM[1];
  meta.gender = /Female/i.test(p3) ? '女' : (/Male/i.test(p3) ? '男' : '');
  const dtM = p3.match(/(\\d{{4}}\\/\\d{{1,2}}\\/\\d{{1,2}})\\s*(?:就诊|SOC)/);
  meta.testDate = dtM ? dtM[1] : '';
  const bdM = p3.match(/出生日[期]?\\s*[：:]?\\s*(\\d{{4}}\\/\\d{{1,2}}\\/\\d{{1,2}})/);
  meta.birthDate = bdM ? bdM[1] : '';
  const viM = p3.match(/就诊编号[：:\\s]*(\\d+)/);
  meta.visitNumber = viM ? viM[1] : '';
  meta.reportDate = meta.testDate;
  return meta;
}}

function processTemplate(valueMap, meta) {{
  const data = JSON.parse(JSON.stringify(TEMPLATE));
  data.meta = Object.assign(data.meta, meta);

  // Update all section items
  let updated = 0;
  for (const [sectionKey, items] of Object.entries(data.sections)) {{
    if (!Array.isArray(items)) continue;
    for (const item of items) {{
      const cn = item.cn || '';
      const name = item.name || '';
      const oldVal = item.value;
      const v = lookupValue(valueMap, cn, name);
      if (v !== null && v !== oldVal) {{
        item.value = v;
        updated++;
      }}
    }}
  }}

  // Update risk_profile
  const risk = data.sections.risk_profile || {{}};
  for (const [key, val] of Object.entries(risk)) {{
    const v = lookupValue(valueMap, key.replace(/_/g, ' '));
    if (v !== null) {{ risk[key] = v; updated++; }}
  }}

  // Update varhop
  const vh = data.sections.varhop || {{}};
  for (const [key, val] of Object.entries(vh)) {{
    if (valueMap[key] !== undefined) {{ vh[key] = valueMap[key]; updated++; }}
  }}

  return {{ data, updated }};
}}

// ============ PROCESS ALL ============
async function processAll() {{
  if (!pendingFiles.length) {{ msg('请先选择PDF文件', 'error'); return; }}

  const total = pendingFiles.length;
  for (let i = 0; i < pendingFiles.length; i++) {{
    const file = pendingFiles[i];
    setProgress(i / total * 100);
    msg('正在处理 ' + (i+1) + '/' + total + ': ' + file.name + '...', 'info');

    try {{
      const {{ fullText, pageTexts }} = await extractTextFromPDF(file);
      const valueMap = extractValues(fullText);
      const meta = extractMeta(pageTexts);
      const name = file.name.replace(/\\.pdf$/i, '');
      meta.name = name;

      const {{ data }} = processTemplate(valueMap, meta);
      saveCustomer(name, data, file.name);
    }} catch(e) {{
      msg('处理 ' + file.name + ' 失败: ' + e.message, 'error');
      console.error(e);
    }}
  }}

  setProgress(100);
  pendingFiles = [];
  document.getElementById('fileList').innerHTML = '';
  fileInput.value = '';
  msg('✅ 全部完成！共处理 ' + total + ' 份报告', 'success');
  refreshList();
}}

// ============ STORAGE ============
function getCustomers() {{
  try {{ return JSON.parse(localStorage.getItem('health_reports') || '{{}}'); }}
  catch(e) {{ return {{}}; }}
}}

const MAX_REPORTS = 3;

function saveCustomer(name, data, filename) {{
  const customers = getCustomers();
  customers[name] = {{
    name, filename,
    date: data.meta.testDate || '',
    data: data,
    savedAt: new Date().toISOString()
  }};

  // Keep only latest MAX_REPORTS
  const sorted = Object.entries(customers).sort((a,b) => b[1].savedAt.localeCompare(a[1].savedAt));
  const trimmed = {{}};
  for (let i = 0; i < Math.min(sorted.length, MAX_REPORTS); i++) {{
    trimmed[sorted[i][0]] = sorted[i][1];
  }}
  localStorage.setItem('health_reports', JSON.stringify(trimmed));
}}

function deleteCustomer(name) {{
  if (!confirm('删除 ' + name + ' 的报告？')) return;
  const customers = getCustomers();
  delete customers[name];
  localStorage.setItem('health_reports', JSON.stringify(customers));
  refreshList();
}}

// ============ RENDER REPORT ============
function renderReport(data) {{
  const M = data.meta;
  const S = data.sections;

  let html = '<div style="max-width:1100px;margin:0 auto;padding:20px;font-family:PingFang SC,Microsoft YaHei,sans-serif;">';

  // Cover
  html += '<div style="text-align:center;padding:40px 20px;background:#fff;border-radius:12px;margin-bottom:20px;">';
  html += '<h1 style="color:#1a3a1a;">营养与健康检测报告</h1>';
  html += '<h3 style="color:#666;font-weight:400;">Nutrition and Wellness Assessment Report</h3>';
  html += '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;max-width:500px;margin:20px auto;text-align:left;">';
  for (const [label, val] of [['姓名',M.name],['性别',M.gender],['出生日期',M.birthDate],['检测日期',M.testDate],['就诊编号',M.visitNumber]]) {{
    html += '<div style="background:#f9f9f9;padding:6px 12px;border-radius:6px;"><span style="font-size:11px;color:#999;">'+label+'</span><br><strong>'+ (val||'-') +'</strong></div>';
  }}
  html += '</div></div>';

  // VARHOP
  const vh = S.varhop || {{}};
  const varhopItems = [
    {{name:'电压指数',value:vh.volt,desc:'体力'}},{{name:'电流强度',value:vh.amper,desc:'脑力'}},
    {{name:'电阻',value:vh.resistance,desc:'免疫'}},{{name:'水合指数',value:vh.hydration,desc:'细胞水分'}},
    {{name:'氧化指数',value:vh.oxidation,desc:'携氧能力'}},{{name:'质子压力',value:vh.proton_pressure,desc:'ATP'}},
    {{name:'电子压力',value:vh.electron_pressure,desc:'能量转换'}},{{name:'相角指数',value:vh.phase_angle,desc:'细胞老化'}},
    {{name:'阻抗指数',value:vh.impedance,desc:'能量流通'}},
  ];
  html += renderSection('⚡ 基本体质 (VARHOP)', varhopItems, 'chart_varhop');

  // Vitamin families
  html += renderSection('💊 维生素家族', S.vitamin_families, 'chart_vitamins');
  html += renderSection('🧬 氨基酸', S.amino_acids, 'chart_amino');
  html += renderSection('🪨 矿物质', S.minerals, 'chart_minerals');
  html += renderSection('🌸 芳香疗法', S.aromatherapy, 'chart_aroma');
  html += renderSection('🫄 消化系统', S.general_digestion, 'chart_digestion');
  html += renderSection('🍚 碳水化合物代谢', S.carbohydrate_digestion, 'chart_carb');
  html += renderSection('🧈 脂肪消化', S.fat_digestion, 'chart_fat');
  html += renderSection('🥩 蛋白质消化', S.protein_digestion, 'chart_protein');
  html += renderSection('🧪 外源性物质', S.xenobiotics, 'chart_xeno');
  html += renderSection('➕ 额外因素', S.additional_factors, 'chart_addfactors');
  html += renderSection('🔍 疾病潜在原因', S.disease_causes, 'chart_causes');
  html += renderSection('📈 疾病加重因素', S.disease_aggravations, 'chart_aggrav');
  html += renderSection('💭 情绪评估', S.emotions, 'chart_emotions');
  html += renderSection('🧠 神经递质', S.neurotransmitters, 'chart_neuro');

  html += '</div>';
  return html;
}}

function renderSection(title, items, chartId) {{
  if (!items || !items.length) return '';

  const vals = items.map(i => i.value).filter(v => v !== null && v !== undefined);
  const avg = vals.length ? (vals.reduce((a,b)=>a+b,0)/vals.length).toFixed(1) : 0;
  const high = items.filter(i => i.value >= 100).length;
  const low = items.filter(i => i.value !== null && i.value !== undefined && i.value <= 50).length;

  let html = '<div style="background:#fff;border-radius:12px;padding:16px 20px;margin-bottom:14px;box-shadow:0 1px 4px rgba(0,0,0,.05);">';
  html += '<h3 style="color:#2c5f2d;font-size:15px;border-bottom:2px solid #2c5f2d;padding-bottom:6px;margin-bottom:10px;">'+title+'</h3>';
  html += '<div style="background:#f0f7f0;border-left:4px solid #2c5f2d;padding:8px 12px;border-radius:4px;margin-bottom:8px;font-size:12px;">共 '+vals.length+' 项 | 平均 '+avg+' | ⚠高(≥100) '+high+' 项 | 🔴低(≤50) '+low+' 项</div>';
  html += '<div style="max-height:350px;"><canvas id="'+chartId+'"></canvas></div>';
  html += '<table style="width:100%;border-collapse:collapse;font-size:11px;margin-top:8px;"><thead><tr><th style="background:#f0f0f0;padding:5px 8px;text-align:left;">检测项目</th><th style="background:#f0f0f0;padding:5px 8px;">反应值</th><th style="background:#f0f0f0;padding:5px 8px;text-align:left;">说明</th></tr></thead><tbody>';

  for (const item of items) {{
    const v = item.value;
    let bg = '', color = '';
    if (v !== null && v !== undefined) {{
      if (v <= 50) {{ bg = 'background:#ffe0e0;'; color = 'color:#c0392b;font-weight:700;'; }}
      else if (v >= 100) {{ bg = 'background:#fff8e1;'; color = 'color:#b8860b;font-weight:700;'; }}
    }}
    html += '<tr><td style="padding:4px 8px;border-bottom:1px solid #eee;">'+ (item.name||'') +'</td><td style="padding:4px 8px;text-align:center;border-bottom:1px solid #eee;'+bg+color+'">'+ (v!=null?v:'-') +'</td><td style="padding:4px 8px;border-bottom:1px solid #eee;font-size:11px;color:#666;">'+ (item.desc||'') +'</td></tr>';
  }}
  html += '</tbody></table></div>';

  // Schedule chart rendering
  setTimeout(() => {{
    const canvas = document.getElementById(chartId);
    if (!canvas) return;
    if (charts[chartId]) charts[chartId].destroy();

    const labels = items.map(i => i.name || '');
    const values = items.map(i => i.value || 0);
    const colors = values.map(v => v <= 50 ? 'rgba(192,57,43,0.8)' : v >= 100 ? 'rgba(212,160,23,0.8)' : 'rgba(44,95,45,0.8)');

    charts[chartId] = new Chart(canvas, {{
      type: 'bar',
      data: {{ labels, datasets: [{{ data: values, backgroundColor: colors, borderWidth: 1 }}] }},
      options: {{
        responsive: true, maintainAspectRatio: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          y: {{ min: 0, max: 160,
            grid: {{ color: ctx => ctx.tick.value === 50 ? '#c0392b' : ctx.tick.value === 100 ? '#d4a017' : '#e0e0e0' }}
          }},
          x: {{ ticks: {{ maxRotation: 60, font: {{ size: 9 }} }} }}
        }}
      }}
    }});
  }}, 100);

  return html;
}}

// ============ VIEW / DOWNLOAD ============
function viewReport(name) {{
  const customers = getCustomers();
  const c = customers[name];
  if (!c) return;
  const html = renderReport(c.data);
  const w = window.open('', '_blank');
  w.document.write('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>'+name+' - 健康报告</title><script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"><\\/script></head><body>'+html+'</body></html>');
  w.document.close();
}}

function downloadReport(name) {{
  const customers = getCustomers();
  const c = customers[name];
  if (!c) return;
  const html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>'+name+' - 健康报告</title><script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"><\\/script></head><body>'+renderReport(c.data)+'</body></html>';
  const blob = new Blob([html], {{type:'text/html;charset=utf-8'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = name + '_健康检测报告.html';
  a.click(); URL.revokeObjectURL(url);
}}

function refreshList() {{
  const customers = getCustomers();
  const names = Object.keys(customers).sort((a,b) => customers[b].savedAt.localeCompare(customers[a].savedAt));
  const list = document.getElementById('customerList');
  if (!names.length) {{ list.innerHTML = '<p style="color:#999;">暂无报告，上传PDF开始</p>'; return; }}
  list.innerHTML = names.map(n => {{
    const c = customers[n];
    return '<div class="customer-card"><div class="info"><strong>'+n+'</strong><span>'+ (c.date||'') +' · '+ (c.filename||'') +'</span></div><div class="actions"><button class="btn-sm btn-view" onclick="viewReport(\\''+n+'\\')">👁 查看</button><button class="btn-sm btn-dl" onclick="downloadReport(\\''+n+'\\')">⬇ 下载</button><button class="btn-sm btn-del" onclick="deleteCustomer(\\''+n+'\\')">🗑</button></div></div>';
  }}).join('');
}}

// Init
refreshList();
</script>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

import os
print(f'✅ Generated index.html ({os.path.getsize("index.html"):,} bytes)')
