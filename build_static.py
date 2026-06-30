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
  <span style="font-size:12px;opacity:.7;">v2.2 · 纯浏览器版 · 不限量</span>
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
    <h2>👥 已有报告（浏览器本地存储）</h2>
    <div class="customer-list" id="customerList"><p style="color:#999;">暂无报告</p></div>
    <div id="pager"></div>
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
  let pageRawItems = [];
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const items = content.items;
    const text = items.map(function(it){ return it.str; }).join(' ');
    pageTexts.push(text);
    fullText += text + '\\n';
    // Save raw items from page 3-4 for practitioner extraction
    if (i === 3 || i === 4) {
      pageRawItems.push({page: i, items: items});
      console.log('Page ' + i + ' has ' + items.length + ' raw text items');
      for (let j = 0; j < Math.min(items.length, 80); j++) {
        const it = items[j];
        if (it.str && it.str.trim()) {
          console.log('  [' + j + '] str="' + it.str + '"');
        }
      }
    }
  }
  return { fullText: fullText, pageTexts: pageTexts, numPages: pdf.numPages, rawItems: pageRawItems };
}

function extractValues(fullText) {
  const valueMap = {};

  // VARHOP patterns (page-level, unchanged)
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

  // PDF.js text: "Name (desc) VALUE 0 % NextName (desc) VALUE2 0 %"
  // Match VALUE skipping the "0 %" improvement percentage
  const pairRegex = /([A-Za-z][A-Za-z\\s,().&+\\-]{2,80}?)\\s+(\\d{2,4})\\s+\\d+\\s*%/g;
  let m;
  while ((m = pairRegex.exec(fullText)) !== null) {
    const name = m[1].trim().toLowerCase();
    const val = parseInt(m[2]);
    if (val >= 10 && val <= 2000 && name.length >= 2) {
      valueMap[name] = val;
    }
  }
  // Also match values without trailing "0 %" (risk scores, etc)
  const simpleRegex = /([A-Z][A-Z\\s]{1,30})\\s+(\\d{1,3})\\b/g;
  while ((m = simpleRegex.exec(fullText)) !== null) {
    const name = m[1].trim().toLowerCase();
    const val = parseInt(m[2]);
    if (val >= 10 && val <= 200 && !(name in valueMap)) {
      valueMap[name] = val;
    }
  }
  console.log('Extracted values:', Object.keys(valueMap).length);

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

function extractMeta(pageTexts, rawItems) {
  const meta = {name:'', gender:'', birthDate:'', testDate:'', visitNumber:'', soc:'',
    practitioner:'', clinic:'', address:'', phone:'', country:'中国', reportDate:''};

  // PDF.js loses quotes, meta ends with: 姓名 日期 Female 出生日 SOC 编号 国家
  let combined = '';
  for (let i = 0; i < Math.min(4, pageTexts.length); i++) {
    combined += (pageTexts[i] || '') + ' ';
  }
  const t = combined.replace(/\\s+/g, ' ');
  console.log('Meta text:', t.substring(0, 400));

  // Two possible PDF formats:
  // Format A: labels then values: "...刘惠 2026/6/25 Female 1972/3/30 1 62 中国"
  // Format B: labels mixed: "...Lily 会话日期 2026/6/22 Female 就诊编号 382 出生日 1976/2/26 SOC 1"
  const tail = t.split(/报告创建对象[：:\\s]+/)[1] || t;

  // Try Format A: value cluster at end
  const clusterM = tail.match(/(\\S{2,15})\\s+(\\d{4}\\/\\d{1,2}\\/\\d{1,2})\\s+(Female|Male)\\s+(\\d{4}\\/\\d{1,2}\\/\\d{1,2})\\s+(\\d{1,4})\\s+(\\d{1,4})/i);
  if (clusterM) {
    meta.name = clusterM[1];
    meta.testDate = clusterM[2];
    meta.gender = clusterM[3].toLowerCase() === 'female' ? '女' : '男';
    meta.birthDate = clusterM[4];
    meta.soc = clusterM[5];
    meta.visitNumber = clusterM[6];
    console.log('Format A (cluster):', clusterM[1], clusterM[2], clusterM[4]);
  }

  // Format B: labeled fields
  if (!meta.testDate) {
    const dtM = tail.match(/会话日期\\s*(\\d{4}\\/\\d{1,2}\\/\\d{1,2})/);
    if (dtM) meta.testDate = dtM[1];
  }
  if (!meta.birthDate) {
    const bdM = tail.match(/出生日[期]?\\s*(\\d{4}\\/\\d{1,2}\\/\\d{1,2})/);
    if (bdM) meta.birthDate = bdM[1];
  }
  if (!meta.visitNumber) {
    const viM = tail.match(/就诊编号\\s*(\\d+)/) || tail.match(/(\\d+)\\s*(?:中国|CHINA)/);
    if (viM) meta.visitNumber = viM[1];
  }
  if (!meta.name) {
    const nmM = tail.match(/(\\S{2,15})\\s+(?:会话日期|\\d{4}\\/)/);
    if (nmM && !/^\\d/.test(nmM[1])) meta.name = nmM[1];
  }
  if (!meta.gender) {
    meta.gender = /Female/i.test(tail) ? '女' : (/Male/i.test(tail) ? '男' : '');
  }
  if (!meta.soc) {
    const socM = tail.match(/SOC\\s+(\\d+)/i) || tail.match(/(\\d+)\\s+(?:中国|CHINA)/);
    // Don't override cluster-found soc
  }

  // Practitioner: check joined text first (Lily format: '检测师' 'Jasmine' 'Shen')
  const pracMatch = t.match(/'检测师'\\s*'([^']+)'\\s*'([^']+)'/);
  if (pracMatch) {
    meta.practitioner = pracMatch[1] + ' ' + pracMatch[2];
    console.log('Practitioner from joined text:', meta.practitioner);
  }
  // Fallback: search raw items
  if (!meta.practitioner && rawItems) {
    for (const pg of rawItems) {
      let foundNames = [];
      let nearPrac = false;
      for (const item of pg.items) {
        const s = (item.str || '').trim();
        if (!s) continue;
        if (/检测师|从业者/.test(s)) { nearPrac = true; continue; }
        if (nearPrac && /^[A-Z][a-z]{2,20}$/.test(s) &&
            !/^(Female|Male|CHINA|SOC|Varhop|Volt|Amper|QX|WORLD|Ltd)$/i.test(s)) {
          foundNames.push(s);
        }
        if (foundNames.length >= 2) break;
      }
      if (foundNames.length >= 2) {
        meta.practitioner = foundNames.join(' ');
        console.log('Practitioner from raw items:', foundNames);
        break;
      }
    }
  }

  meta.reportDate = meta.testDate;
  console.log('Meta result:', JSON.stringify(meta));
  // Return only non-empty fields so template defaults survive for missing ones
  const clean = {};
  for (const k of Object.keys(meta)) {
    if (meta[k] !== '' && meta[k] !== undefined && meta[k] !== null) {
      clean[k] = meta[k];
    }
  }
  return clean;
}

function processTemplate(valueMap, meta) {
  const data = JSON.parse(JSON.stringify(TEMPLATE));
  // Always override practitioner: use extracted value or empty
  if (!meta.practitioner) meta.practitioner = '';
  console.log('Merging meta. Template practitioner:', data.meta.practitioner, '| Extracted:', JSON.stringify(meta));
  data.meta = Object.assign(data.meta, meta);
  console.log('After merge practitioner:', data.meta.practitioner);

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
      const meta = extractMeta(result.pageTexts, result.rawItems);
      console.log('Meta:', meta.name, meta.testDate, '| practitioner:', meta.practitioner);
      const name = meta.name || file.name.replace(/\\.pdf$/i, '');
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

  localStorage.setItem('health_reports', JSON.stringify(customers));
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
  window._chartConfigs = [];

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
  window._chartConfigs = [];
  document.getElementById('uploadSection').style.display = 'block';
  document.getElementById('listSection').style.display = 'block';
  document.getElementById('reportView').style.display = 'none';
  window.scrollTo(0,0);
}

function downloadReport(name) {
  const customers = getCustomers();
  const c = customers[name];
  if (!c) return;
  window._chartConfigs = [];
  const reportHTML = renderFullReport(c.data);
  // Use collected chart configs for download script
  const configs = window._chartConfigs || [];
  let chartInitJS = '<script>\\n';
  chartInitJS += 'var _cfgs=' + JSON.stringify(configs) + ';\\n';
  chartInitJS += `_cfgs.forEach(function(cfg){
    var cv=document.getElementById(cfg.chartId);
    if(!cv) return;
    var colors=cfg.colors, borders=cfg.borders, values=cfg.values;
    new Chart(cv,{type:"bar",data:{labels:cfg.labels,datasets:[{data:values,backgroundColor:colors,borderColor:borders,borderWidth:1}]},
    options:{responsive:true,maintainAspectRatio:true,plugins:{legend:{display:false}},
    scales:{y:{min:0,max:160,grid:{color:"#e0e0e0"}},x:{ticks:{maxRotation:60,font:{size:9}}}}},
    plugins:[{id:"bl_"+cfg.chartId,afterDraw:function(ch){
      var ctx=ch.ctx,m=ch.getDatasetMeta(0);ctx.save();
      ctx.font="bold 11px PingFang SC,Microsoft YaHei,sans-serif";ctx.textAlign="center";ctx.textBaseline="bottom";
      m.data.forEach(function(b,i){var v=values[i],x=b.x,y=b.y-4;
      ctx.fillStyle=v<=50?"#c0392b":v>=100?"#d4a017":"#2c5f2d";ctx.fillText(v,x,y);});
      ctx.restore();
    }}]})});\\n`;
  chartInitJS += '<\\/script>';
  window._chartConfigs = [];

  const fullHTML = '<!DOCTYPE html>\\n<html lang="zh-CN">\\n<head>\\n<meta charset="UTF-8">\\n<title>'+name+' - 健康报告</title>\\n' +
    '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"><\\/script>\\n' +
    '<style>body{font-family:PingFang SC,Microsoft YaHei,sans-serif;background:#f5f0e8;}</style>\\n</head>\\n<body class="report-body">\\n' +
    reportHTML + '\\n' + chartInitJS + '\\n</body>\\n</html>';
  const blob = new Blob([fullHTML], {type:'text/html;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name + '_健康检测报告.html';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(function(){ URL.revokeObjectURL(a.href); }, 1000);
}

let currentPage = 1;
const PAGE_SIZE = 6;

function refreshList(page) {
  const customers = getCustomers();
  const names = Object.keys(customers).sort(function(a,b){ return customers[b].savedAt.localeCompare(customers[a].savedAt); });
  const list = document.getElementById('customerList');
  const pager = document.getElementById('pager');
  if (!names.length) { list.innerHTML = '<p style="color:#999;">暂无报告，上传PDF开始</p>'; pager.innerHTML = ''; return; }

  if (page) currentPage = page;
  const totalPages = Math.ceil(names.length / PAGE_SIZE);
  if (currentPage > totalPages) currentPage = totalPages;
  if (currentPage < 1) currentPage = 1;

  const start = (currentPage - 1) * PAGE_SIZE;
  const pageNames = names.slice(start, start + PAGE_SIZE);

  list.innerHTML = pageNames.map(function(n){
    const c = customers[n];
    return '<div class="customer-card"><div class="info"><strong>'+n+'</strong><span>'+(c.date||'')+' · '+(c.filename||'')+'</span></div>' +
      '<div class="actions"><button class="btn-sm btn-view" onclick="viewReport(\\''+n+'\\')">👁 查看</button>' +
      '<button class="btn-sm btn-dl" onclick="downloadReport(\\''+n+'\\')">⬇ 下载</button>' +
      '<button class="btn-sm btn-del" onclick="deleteCustomer(\\''+n+'\\')">🗑</button></div></div>';
  }).join('');

  // Pagination controls
  pager.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;gap:8px;margin-top:12px;flex-wrap:wrap;">' +
    '<button class="btn-sm" style="background:#e0e0e0;" onclick="refreshList(1)" '+(currentPage===1?'disabled':'')+'>⏮ 首页</button>' +
    '<button class="btn-sm" style="background:#e0e0e0;" onclick="refreshList('+(currentPage-1)+')" '+(currentPage===1?'disabled':'')+'>◀ 上一页</button>' +
    '<span style="font-size:13px;">第 <input type="number" id="pageInput" value="'+currentPage+'" min="1" max="'+totalPages+'" style="width:50px;text-align:center;padding:4px;border:1px solid #ccc;border-radius:4px;" onchange="goToPage()"> / '+totalPages+' 页（共 '+names.length+' 份）</span>' +
    '<button class="btn-sm" style="background:#e0e0e0;" onclick="refreshList('+(currentPage+1)+')" '+(currentPage===totalPages?'disabled':'')+'>下一页 ▶</button>' +
    '<button class="btn-sm" style="background:#e0e0e0;" onclick="refreshList('+totalPages+')" '+(currentPage===totalPages?'disabled':'')+'>末页 ⏭</button>' +
    '</div>';
}

function goToPage() {
  const p = parseInt(document.getElementById('pageInput').value);
  if (p >= 1) refreshList(p);
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
