#!/usr/bin/env python3
"""生成纯浏览器版报告系统 - 完整报告渲染匹配服务器版"""
import json

with open('data_template.json') as f:
    TEMPLATE = json.load(f)
TEMPLATE_JS = json.dumps(TEMPLATE, ensure_ascii=False)

# 读取完整渲染JS
with open('render_report.js', 'r') as f:
    RENDER_JS = f.read()

html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>营养与健康检测报告系统</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root { --accent: #2c5f2d; --danger: #c0392b; --warn: #d4a017; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'PingFang SC','Microsoft YaHei',sans-serif; background: #f5f0e8; color: #333; }
.header { background: #1a1a2e; color: #fff; padding: 14px 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
.header h1 { font-size: 18px; }
.container { max-width: 960px; margin: 0 auto; padding: 20px; }
.card { background: #fff; border-radius: 12px; padding: 20px 24px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.05); }
.card h2 { font-size: 16px; color: var(--accent); margin-bottom: 12px; }
.upload-zone { border: 2px dashed #ccc; border-radius: 12px; padding: 30px; text-align: center; cursor: pointer; transition: .3s; }
.upload-zone:hover, .upload-zone.drag { border-color: var(--accent); background: #f0f7f0; }
.upload-zone input { display: none; }
.upload-zone .icon { font-size: 40px; }
.btn { padding: 10px 24px; background: var(--accent); color: #fff; border: none; border-radius: 8px; font-size: 14px; cursor: pointer; }
.btn:hover { opacity: .85; }
.btn-warn { background: #e67e22; }
.customer-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px,1fr)); gap: 10px; }
.customer-card { border: 1px solid #ddd; border-radius: 10px; padding: 14px; display: flex; justify-content: space-between; align-items: center; }
.customer-card:hover { border-color: var(--accent); }
.customer-card strong { font-size: 15px; display: block; }
.customer-card span { font-size: 12px; color: #999; }
.btn-sm { padding: 5px 10px; border-radius: 5px; border: none; cursor: pointer; font-size: 12px; text-decoration: none; }
.btn-view { background: var(--accent); color: #fff; }
.btn-dl { background: #e8e8e8; color: #333; }
.btn-del { background: #fee; color: var(--danger); }
.msg { padding: 8px 14px; border-radius: 6px; margin-bottom: 10px; display: none; }
.msg.show { display: block; }
.msg.success { background: #e8f5e9; color: #2e7d32; }
.msg.error { background: #ffe0e0; color: #c0392b; }
.msg.info { background: #e3f2fd; color: #1565c0; }
.progress { display: none; height: 6px; background: #e0e0e0; border-radius: 3px; margin: 12px 0; overflow: hidden; }
.progress.active { display: block; }
.progress-bar { height: 100%; background: var(--accent); width: 0%; transition: width .3s; }
@media (max-width: 600px) { .header { padding: 10px 14px; } .container { padding: 10px; } }
</style>
</head>
<body>
<div class="header">
  <h1>📋 营养与健康检测报告系统</h1>
  <span style="font-size:12px;opacity:.7;">纯浏览器版 · 无需服务器 · 不限量</span>
</div>
<div class="container">
  <div id="msgBox"></div>
  <div class="progress" id="progress"><div class="progress-bar" id="progressBar"></div></div>

  <div id="uploadSection">
  <div class="card">
    <h2>📤 上传 PDF 生成报告</h2>
    <div class="upload-zone" id="uploadZone">
      <div class="icon">📄</div>
      <p>拖拽 PDF 到此处，或点击选择</p>
      <p style="font-size:12px;color:#aaa;">支持 QX WORLD 生物反馈检测报告 | 纯浏览器处理，数据不上传</p>
      <input type="file" id="fileInput" accept=".pdf" multiple>
      <button class="btn" onclick="document.getElementById('fileInput').click()">📁 选择文件</button>
      <button class="btn btn-warn" onclick="processAll()" style="margin-top:10px;display:block;width:100%;">🚀 批量生成报告</button>
      <div id="fileList" style="margin-top:8px;font-size:13px;color:var(--accent);"></div>
    </div>
  </div>
  </div>

  <div id="listSection">
  <div class="card">
    <h2>👥 已有报告（浏览器本地存储，最多3份）</h2>
    <div class="customer-list" id="customerList"><p style="color:#999;">暂无报告</p></div>
  </div>
  </div>

  <div id="reportView" style="display:none;"></div>
</div>

<script>
// ============ EMBEDDED DATA ============
const TEMPLATE = ''' + TEMPLATE_JS + ''';
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
window._charts = {};

// ============ RENDER ENGINE (from render_report.js) ============
___RENDER_JS___

// ============ APP STATE ============
let pendingFiles = [];
const MAX_REPORTS = 3;

// ============ UI HELPERS ============
function msg(text, type) {
  const el = document.getElementById('msgBox');
  el.innerHTML = '<div class="msg '+type+' show">'+text+'</div>';
  setTimeout(function(){ el.innerHTML = ''; }, 5000);
}

function setProgress(pct) {
  const bar = document.getElementById('progressBar');
  document.getElementById('progress').classList.add('active');
  bar.style.width = pct + '%';
  if (pct >= 100) setTimeout(function(){ document.getElementById('progress').classList.remove('active'); }, 1000);
}

// ============ FILE HANDLING ============
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');

uploadZone.addEventListener('dragover', function(e){ e.preventDefault(); uploadZone.classList.add('drag'); });
uploadZone.addEventListener('dragleave', function(){ uploadZone.classList.remove('drag'); });
uploadZone.addEventListener('drop', function(e){
  e.preventDefault(); uploadZone.classList.remove('drag');
  addFiles(Array.from(e.dataTransfer.files));
});
fileInput.addEventListener('change', function(e){ addFiles(Array.from(e.target.files)); });
uploadZone.addEventListener('click', function(e){
  if (e.target === uploadZone || e.target.classList.contains('icon') || e.target.tagName === 'P') fileInput.click();
});

function addFiles(files) {
  const pdfs = files.filter(function(f){ return f.name.endsWith('.pdf'); });
  pendingFiles = pendingFiles.concat(pdfs);
  document.getElementById('fileList').innerHTML = pendingFiles.map(function(f){
    return '<div>📄 '+f.name+' ('+(f.size/1024/1024).toFixed(1)+'MB)</div>';
  }).join('');
  if (pendingFiles.length) msg('已选择 '+pendingFiles.length+' 个文件，点击「批量生成报告」开始', 'info');
}

// ============ PDF PROCESSING ============
async function extractTextFromPDF(file) {
  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
  let fullText = '';
  let pageTexts = [];
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const text = content.items.map(function(it){ return it.str; }).join(' ');
    pageTexts.push(text);
    fullText += text + '\\n';
  }
  return { fullText: fullText, pageTexts: pageTexts, numPages: pdf.numPages };
}

function extractValues(fullText) {
  const valueMap = {};

  // VARHOP patterns
  const patterns = {
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
  };
  for (const [k, pat] of Object.entries(patterns)) {
    const m = fullText.match(pat);
    if (m) {
      const v = m[1].replace('%','');
      valueMap[k] = parseInt(v) || v;
    }
  }

  // Extract all label-value pairs
  const lines = fullText.split('\\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.length > 200) continue;
    if (/^\\d+\\s*\\/\\s*\\d+$/.test(trimmed)) continue;
    if (/^(\\u00a9|QX WORLD|\\u4fdd\\u7559\\u6240\\u6709)/.test(trimmed)) continue;

    const m = trimmed.match(/^(.+?)\\s+(\\d{1,4})\\b/);
    if (m) {
      const name = m[1].trim().toLowerCase();
      const val = parseInt(m[2]);
      if (val >= 0 && val <= 2000 && name.length >= 2) {
        valueMap[name] = val;
      }
    }
  }
  return valueMap;
}

function lookupValue(valueMap) {
  const names = Array.prototype.slice.call(arguments, 1);
  for (const name of names) {
    if (!name) continue;
    const key = name.toLowerCase().trim();
    if (valueMap[key] !== undefined) return valueMap[key];

    // Key without parentheses
    const cleanKey = key.replace(/\\s*\\(.*/, '').trim();
    for (const [k, v] of Object.entries(valueMap)) {
      if (k.replace(/\\s*\\(.*/, '').trim() === cleanKey) return v;
    }
    // Contains match
    for (const [k, v] of Object.entries(valueMap)) {
      if (k.indexOf(key) >= 0) return v;
      if (key.length >= 3 && key.indexOf(k) >= 0) return v;
    }
  }
  return null;
}

function extractMeta(pageTexts) {
  const meta = {name:'', gender:'', birthDate:'', testDate:'', visitNumber:'', soc:'',
    practitioner:'', clinic:'', address:'', phone:'', country:'中国', reportDate:''};

  // PDF.js loses quotes, meta ends with: 姓名 日期 Female 出生日 SOC 编号 国家
  let combined = '';
  for (let i = 0; i < Math.min(4, pageTexts.length); i++) {
    combined += (pageTexts[i] || '') + ' ';
  }
  const t = combined.replace(/\\s+/g, ' ');
  console.log('Meta text:', t.substring(0, 400));

  // Format: ...报告创建对象： ... 刘惠 2026/6/25 Female 1972/3/30 1 62 中国
  // Or:    ...报告创建对象： Lily 会话日期 2026/6/22 Female ...
  // Find the tail section after "报告创建对象"
  const tail = t.split(/报告创建对象[：:\\s]+/)[1] || t;

  // Find name + date + Female/Male cluster
  // Pattern: WordWord  dddd/d/d  Female/Male  dddd/d/d  number  number
  const clusterM = tail.match(/(\\S{2,15})\\s+(\\d{4}\\/\\d{1,2}\\/\\d{1,2})\\s+(Female|Male)\\s+(\\d{4}\\/\\d{1,2}\\/\\d{1,2})\\s+(\\d{1,4})\\s+(\\d{1,4})/i);
  if (clusterM) {
    meta.name = clusterM[1];
    meta.testDate = clusterM[2];
    meta.gender = clusterM[3].toLowerCase() === 'female' ? '女' : '男';
    meta.birthDate = clusterM[4];
    meta.soc = clusterM[5];
    meta.visitNumber = clusterM[6];
    console.log('Cluster match:', clusterM[1], clusterM[2], clusterM[3], clusterM[4], clusterM[5], clusterM[6]);
  } else {
    console.log('Cluster NOT matched, trying fallbacks...');
    // Fallbacks
    const allDates = tail.match(/\\d{4}\\/\\d{1,2}\\/\\d{1,2}/g) || [];
    meta.testDate = allDates[0] || '';
    meta.birthDate = allDates[1] || '';
    meta.gender = /Female/i.test(tail) ? '女' : (/Male/i.test(tail) ? '男' : '');
    const viM = tail.match(/(\\d+)\\s*(?:中国|CHINA)/);
    if (viM) meta.visitNumber = viM[1];
    const nameAfterObj = tail.match(/(\\S{2,15})\\s+\\d{4}\\/\\d{1,2}/);
    if (nameAfterObj && !/^\\d/.test(nameAfterObj[1])) meta.name = nameAfterObj[1];
    const socM = tail.match(/(\\d+)\\s+(?:\\d+)\\s+(?:中国|CHINA)/);
  }

  // Practitioner: search all pages for quoted names near "检测师"
  for (let i = 0; i < Math.min(5, pageTexts.length); i++) {
    const pg = (pageTexts[i] || '');
    const pm = pg.match(/Jasmine|Shen|[A-Z][a-z]+\\s+[A-Z][a-z]+/g);
    if (pm && /检测师|从业者/.test(pg)) {
      meta.practitioner = pm.filter(n => n.length > 3 && !/^(Female|Male|CHINA|SOC)$/i.test(n)).join(' ');
      if (meta.practitioner) break;
    }
  }

  meta.reportDate = meta.testDate;
  console.log('Meta result:', JSON.stringify(meta));
  return meta;
}

function processTemplate(valueMap, meta) {
  const data = JSON.parse(JSON.stringify(TEMPLATE));
  data.meta = Object.assign(data.meta, meta);

  let updated = 0;
  for (const [sectionKey, items] of Object.entries(data.sections)) {
    if (!Array.isArray(items)) continue;
    for (const item of items) {
      const cn = item.cn || '';
      const name = item.name || '';
      const oldVal = item.value;
      const v = lookupValue(valueMap, cn, name);
      if (v !== null && v !== oldVal) {
        item.value = v;
        updated++;
      }
    }
  }

  // risk_profile
  const risk = data.sections.risk_profile || {};
  for (const [key, val] of Object.entries(risk)) {
    const v = lookupValue(valueMap, key.replace(/_/g, ' '));
    if (v !== null) { risk[key] = v; updated++; }
  }

  // varhop
  const vh = data.sections.varhop || {};
  for (const [key, val] of Object.entries(vh)) {
    if (valueMap[key] !== undefined) { vh[key] = valueMap[key]; updated++; }
  }

  return { data: data, updated: updated };
}

// ============ PROCESS ALL ============
async function processAll() {
  if (!pendingFiles.length) { msg('请先选择PDF文件', 'error'); return; }

  const total = pendingFiles.length;
  for (let i = 0; i < pendingFiles.length; i++) {
    const file = pendingFiles[i];
    setProgress(i / total * 100);
    msg('正在处理 ' + (i+1) + '/' + total + ': ' + file.name + '...', 'info');

    try {
      console.log('处理:', file.name);
      const result = await extractTextFromPDF(file);
      console.log('PDF页数:', result.numPages, '文本长度:', result.fullText.length);
      const valueMap = extractValues(result.fullText);
      console.log('提取值:', Object.keys(valueMap).length, '个映射');
      const meta = extractMeta(result.pageTexts);
      console.log('Meta:', meta.name, meta.testDate);
      const name = file.name.replace(/\\.pdf$/i, '');
      meta.name = name;

      const processed = processTemplate(valueMap, meta);
      console.log('更新了', processed.updated, '个数值');
      saveCustomer(name, processed.data, file.name);
      msg('✅ ' + name + ' 处理完成 (' + Object.keys(valueMap).length + '值, ' + processed.updated + '更新)', 'success');
    } catch(e) {
      msg('❌ ' + file.name + ' 失败: ' + e.message, 'error');
      console.error('处理错误:', e);
    }
  }

  setProgress(100);
  pendingFiles = [];
  document.getElementById('fileList').innerHTML = '';
  fileInput.value = '';
  msg('✅ 全部完成！共处理 ' + total + ' 份报告', 'success');
  refreshList();
}

// ============ STORAGE ============
function getCustomers() {
  try { return JSON.parse(localStorage.getItem('health_reports') || '{}'); }
  catch(e) { return {}; }
}

function saveCustomer(name, data, filename) {
  const customers = getCustomers();
  customers[name] = {
    name: name, filename: filename,
    date: data.meta.testDate || '',
    data: data,
    savedAt: new Date().toISOString()
  };

  // Keep only latest MAX_REPORTS
  const sorted = Object.entries(customers).sort(function(a,b){ return b[1].savedAt.localeCompare(a[1].savedAt); });
  const trimmed = {};
  for (let i = 0; i < Math.min(sorted.length, MAX_REPORTS); i++) {
    trimmed[sorted[i][0]] = sorted[i][1];
  }
  localStorage.setItem('health_reports', JSON.stringify(trimmed));
}

function deleteCustomer(name) {
  if (!confirm('删除 ' + name + ' 的报告？')) return;
  const customers = getCustomers();
  delete customers[name];
  localStorage.setItem('health_reports', JSON.stringify(customers));
  refreshList();
}

// ============ VIEW / DOWNLOAD ============
function viewReport(name) {
  const customers = getCustomers();
  const c = customers[name];
  if (!c) return;

  // Destroy old charts
  Object.values(window._charts).forEach(function(ch){ ch.destroy(); });
  window._charts = {};

  document.getElementById('uploadSection').style.display = 'none';
  document.getElementById('listSection').style.display = 'none';
  const rv = document.getElementById('reportView');
  rv.style.display = 'block';
  rv.innerHTML = '<div class="report-body">' +
    '<div style="margin-bottom:12px;margin-left:250px;"><button class="btn" onclick="closeReport()">← 返回列表</button></div>' +
    renderFullReport(c.data) +
    '</div>';
  window.scrollTo(0,0);
}

function closeReport() {
  Object.values(window._charts).forEach(function(ch){ ch.destroy(); });
  window._charts = {};
  document.getElementById('uploadSection').style.display = 'block';
  document.getElementById('listSection').style.display = 'block';
  document.getElementById('reportView').style.display = 'none';
  window.scrollTo(0,0);
}

function downloadReport(name) {
  const customers = getCustomers();
  const c = customers[name];
  if (!c) return;
  const reportHTML = renderFullReport(c.data);
  const fullHTML = '<!DOCTYPE html>\\n<html lang="zh-CN">\\n<head>\\n<meta charset="UTF-8">\\n<title>'+name+' - 健康报告</title>\\n' +
    '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"><\\/script>\\n' +
    '<style>body{font-family:PingFang SC,Microsoft YaHei,sans-serif;background:#f5f0e8;}</style>\\n</head>\\n<body class="report-body">\\n' +
    reportHTML + '\\n</body>\\n</html>';
  const blob = new Blob([fullHTML], {type:'text/html;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name + '_健康检测报告.html';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(function(){ URL.revokeObjectURL(a.href); }, 1000);
}

function refreshList() {
  const customers = getCustomers();
  const names = Object.keys(customers).sort(function(a,b){ return customers[b].savedAt.localeCompare(customers[a].savedAt); });
  const list = document.getElementById('customerList');
  if (!names.length) { list.innerHTML = '<p style="color:#999;">暂无报告，上传PDF开始</p>'; return; }
  list.innerHTML = names.map(function(n){
    const c = customers[n];
    return '<div class="customer-card"><div class="info"><strong>'+n+'</strong><span>'+(c.date||'')+' · '+(c.filename||'')+'</span></div>' +
      '<div class="actions"><button class="btn-sm btn-view" onclick="viewReport(\\''+n+'\\')">👁 查看</button>' +
      '<button class="btn-sm btn-dl" onclick="downloadReport(\\''+n+'\\')">⬇ 下载</button>' +
      '<button class="btn-sm btn-del" onclick="deleteCustomer(\\''+n+'\\')">🗑</button></div></div>';
  }).join('');
}

// Init
refreshList();
</script>
</body>
</html>'''

html = html.replace('___RENDER_JS___', RENDER_JS)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

import os
print(f'✅ Generated index.html ({os.path.getsize("index.html"):,} bytes)')
