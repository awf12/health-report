#!/usr/bin/env python3
"""
报告系统 Web 服务器
功能: 上传PDF → 自动生成报告 → 在线查看 → 下载
"""
import json
import os
import re
import shutil
import subprocess
import pdfplumber
from datetime import datetime
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)
UPLOAD_DIR = 'customers'
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================================
HOME_PAGE = r'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>营养与健康检测报告系统</title>
<style>
:root { --accent: #2c5f2d; --danger: #c0392b; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'PingFang SC','Microsoft YaHei',sans-serif; background: #f5f0e8; color: #333; min-height: 100vh; }
.header { background: linear-gradient(135deg, #1a1a2e, #16213e); color: #fff; padding: 20px 32px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.header h1 { font-size: 20px; }
.container { max-width: 900px; margin: 0 auto; padding: 24px; }
.card { background: #fff; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.05); }
.card h2 { font-size: 18px; color: var(--accent); margin-bottom: 16px; }
.upload-zone { border: 2px dashed #ccc; border-radius: 12px; padding: 40px 20px; text-align: center; transition: .3s; }
.upload-zone:hover, .upload-zone.drag { border-color: var(--accent); background: #f0f7f0; }
.upload-zone input { display: none; }
.upload-zone .icon { font-size: 48px; margin-bottom: 12px; }
.upload-zone p { color: #999; font-size: 14px; margin: 4px 0; }
.btn { display: inline-block; padding: 12px 32px; background: var(--accent); color: #fff; border: none; border-radius: 8px; font-size: 15px; cursor: pointer; transition: .2s; }
.btn:hover { opacity: .9; transform: translateY(-1px); }
.btn-block { width: 100%; margin-top: 16px; }
.customer-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.customer-card { border: 1px solid #ddd; border-radius: 10px; padding: 16px; display: flex; justify-content: space-between; align-items: center; transition: .2s; }
.customer-card:hover { border-color: var(--accent); box-shadow: 0 2px 8px rgba(0,0,0,.08); }
.customer-card .info strong { display: block; font-size: 16px; }
.customer-card .info span { font-size: 12px; color: #999; }
.customer-card .actions { display: flex; gap: 6px; flex-wrap: wrap; }
.btn-sm { padding: 6px 12px; border-radius: 6px; border: none; cursor: pointer; font-size: 12px; text-decoration: none; display: inline-block; }
.btn-view { background: var(--accent); color: #fff; }
.btn-dl { background: #e8e8e8; color: #333; }
.btn-del { background: #fee; color: var(--danger); }
.msg { padding: 10px 16px; border-radius: 8px; margin-bottom: 12px; display: none; }
.msg.success { background: #e8f5e9; color: #2e7d32; display: block; }
.msg.error { background: #ffe0e0; color: #c0392b; display: block; }
.msg.info { background: #e3f2fd; color: #1565c0; display: block; }
.loading { display: none; text-align: center; padding: 20px; }
.loading.active { display: block; }
.spinner { width: 40px; height: 40px; border: 4px solid #e0e0e0; border-top-color: var(--accent); border-radius: 50%; animation: spin .8s linear infinite; margin: 0 auto 12px; }
@keyframes spin { to { transform: rotate(360deg); } }
.footer { text-align: center; padding: 24px; color: #999; font-size: 12px; }
@media (max-width: 600px) { .header { padding: 12px 16px; } .container { padding: 12px; } }
</style>
</head>
<body>
<div class="header">
  <h1>📋 营养与健康检测报告系统</h1>
  <span style="font-size:13px;opacity:.7;">上传 PDF → 查看报告 → 下载</span>
</div>
<div class="container">
  <div id="msgBox"></div>
  <div class="card">
    <h2>📤 上传新顾客 PDF</h2>
    <div class="upload-zone" id="uploadZone">
      <div class="icon">📄</div>
      <p>拖拽 PDF 到此处，或点击按钮选择文件</p>
      <p style="font-size:12px;color:#bbb;">支持 QX WORLD 生物反馈检测报告 PDF</p>
      <input type="file" id="fileInput" accept=".pdf">
      <button class="btn" onclick="document.getElementById('fileInput').click()">📁 选择 PDF 文件</button>
      <p id="fileName" style="margin-top:8px;color:var(--accent);font-weight:600;"></p>
      <button class="btn btn-block" onclick="uploadPDF()" style="background:#e67e22;">🚀 上传并生成报告</button>
    </div>
    <div class="loading" id="loading"><div class="spinner"></div><p>正在解析 PDF 并生成报告，请稍候...</p></div>
  </div>
  <div class="card">
    <h2>👥 已有顾客报告</h2>
    <div class="customer-list" id="customerList"><p style="color:#999;">加载中...</p></div>
  </div>
</div>
<div class="footer">QX WORLD 生物反馈检测报告 · 仅供健康管理参考，不作为医学诊断依据</div>
<script>
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const msgBox = document.getElementById('msgBox');
const loading = document.getElementById('loading');

function showMsg(text, type) {
  msgBox.innerHTML = '<div class="msg '+type+'">'+text+'</div>';
  setTimeout(function(){ msgBox.innerHTML = ''; }, 6000);
}

uploadZone.addEventListener('dragover', function(e){ e.preventDefault(); uploadZone.classList.add('drag'); });
uploadZone.addEventListener('dragleave', function(){ uploadZone.classList.remove('drag'); });
uploadZone.addEventListener('drop', function(e){
  e.preventDefault(); uploadZone.classList.remove('drag');
  if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', function(e){
  if (e.target.files[0]) handleFile(e.target.files[0]);
});

function handleFile(file) {
  if (!file.name.endsWith('.pdf')) { showMsg('请上传 PDF 文件', 'error'); return; }
  document.getElementById('fileName').textContent = '✅ 已选择: ' + file.name + ' (' + (file.size/1024/1024).toFixed(1) + 'MB)';
}

async function uploadPDF() {
  var file = fileInput.files[0];
  if (!file) { showMsg('请先选择 PDF 文件', 'error'); return; }
  loading.classList.add('active');
  var fd = new FormData();
  fd.append('pdf', file);
  try {
    var resp = await fetch('/upload', { method: 'POST', body: fd });
    var data = await resp.json();
    loading.classList.remove('active');
    if (data.success) {
      showMsg('✅ ' + data.message, 'success');
      fileInput.value = '';
      document.getElementById('fileName').textContent = '';
      loadCustomers();
      window.open('/report/' + data.customer_id, '_blank');
    } else {
      showMsg('❌ ' + data.message, 'error');
    }
  } catch(e) {
    loading.classList.remove('active');
    showMsg('上传失败: ' + e.message, 'error');
  }
}

async function loadCustomers() {
  try {
    var resp = await fetch('/customers');
    var data = await resp.json();
    var list = document.getElementById('customerList');
    if (!data.customers.length) {
      list.innerHTML = '<p style="color:#999;">暂无顾客报告，上传第一个 PDF 开始使用</p>';
      return;
    }
    list.innerHTML = data.customers.map(function(c){
      return '<div class="customer-card"><div class="info"><strong>'+c.name+'</strong><span>'+c.date+' · '+c.size+'</span></div><div class="actions"><a href="/report/'+c.id+'" target="_blank" class="btn-sm btn-view">👁 查看</a><a href="/download/'+c.id+'" class="btn-sm btn-dl">⬇ 下载</a><button onclick="delCustomer(\''+c.id+'\')" class="btn-sm btn-del">🗑 删除</button></div></div>';
    }).join('');
  } catch(e) {
    document.getElementById('customerList').innerHTML = '<p style="color:#c0392b;">加载失败</p>';
  }
}

async function delCustomer(id) {
  if (!confirm('确定删除该顾客报告？此操作不可撤销。')) return;
  await fetch('/delete/' + id, { method: 'POST' });
  loadCustomers();
}

loadCustomers();
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return HOME_PAGE

@app.route('/upload', methods=['POST'])
def upload():
    if 'pdf' not in request.files:
        return jsonify({'success': False, 'message': '未收到文件'})
    file = request.files['pdf']
    if not file.filename.endswith('.pdf'):
        return jsonify({'success': False, 'message': '只支持 PDF 文件'})

    try:
        customer_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_path = os.path.join(UPLOAD_DIR, f'{customer_id}.pdf')
        file.save(pdf_path)

        # 用上传的 PDF 文件名作为顾客名称（去掉 .pdf 后缀）
        name = file.filename.replace('.pdf', '').strip()[:50]

        # 1) Run dynamic PDF extractor
        result = subprocess.run(
            ['python3', 'extract.py', pdf_path],
            check=True, capture_output=True, text=True
        )
        print(result.stdout)

        # 2) Overwrite meta name in data.json with PDF filename
        with open('data.json', 'r', encoding='utf-8') as f:
            jdata = json.load(f)
        jdata['meta']['name'] = name
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(jdata, f, ensure_ascii=False, indent=2)

        # 3) Run build_html.py (now reads the filename-based name)
        subprocess.run(['python3', 'build_html.py'], check=True, capture_output=True)

        # 4) Copy the generated files to customers dir
        if os.path.exists('index.html'):
            shutil.copy('index.html', os.path.join(UPLOAD_DIR, f'{customer_id}.html'))
        if os.path.exists('data.json'):
            shutil.copy('data.json', os.path.join(UPLOAD_DIR, f'{customer_id}.json'))

        return jsonify({
            'success': True,
            'message': f'报告已生成: {name}',
            'customer_id': customer_id,
            'name': name
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {str(e)}'})

@app.route('/customers')
def list_customers():
    customers = []
    for f in sorted(os.listdir(UPLOAD_DIR), reverse=True):
        if f.endswith('.json') and not f.startswith('_'):
            cid = f.replace('.json', '')
            try:
                with open(os.path.join(UPLOAD_DIR, f), 'r') as fp:
                    data = json.load(fp)
                name = data['meta'].get('name', cid)
                date = data['meta'].get('testDate', '')
                pdf_file = os.path.join(UPLOAD_DIR, f'{cid}.pdf')
                size = f'{os.path.getsize(pdf_file)/1024/1024:.1f}MB' if os.path.exists(pdf_file) else ''
                customers.append({'id': cid, 'name': name, 'date': date, 'size': size})
            except:
                pass
    return jsonify({'customers': customers})

@app.route('/report/<customer_id>')
def view_report(customer_id):
    html_path = os.path.join(UPLOAD_DIR, f'{customer_id}.html')
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()
    return '<h2 style="text-align:center;padding:40px;">报告不存在或已被删除</h2>', 404

@app.route('/download/<customer_id>')
def download_report(customer_id):
    html_path = os.path.join(UPLOAD_DIR, f'{customer_id}.html')
    if os.path.exists(html_path):
        name = customer_id
        try:
            with open(os.path.join(UPLOAD_DIR, f'{customer_id}.json'), 'r') as f:
                name = json.load(f)['meta'].get('name', customer_id)
        except:
            pass
        return send_file(html_path, as_attachment=True, download_name=f'健康检测报告_{name}.html')
    return '报告不存在', 404

@app.route('/delete/<customer_id>', methods=['POST'])
def delete_customer(customer_id):
    for ext in ['.pdf', '.json', '.html']:
        p = os.path.join(UPLOAD_DIR, f'{customer_id}{ext}')
        if os.path.exists(p):
            os.remove(p)
    return jsonify({'success': True})

if __name__ == '__main__':
    import os as _os
    # Auto-generate template if missing
    if not _os.path.exists('data_template.json'):
        print('📦 生成数据模板...')
        import subprocess as _sp
        _sp.run(['python3', 'generate_data.py'], check=True, capture_output=True)
        __import__('shutil').copy('data.json', 'data_template.json')
        print('✅ 模板就绪')

    port = int(_os.environ.get('PORT', 5100))
    print(f'🚀 报告系统启动: http://0.0.0.0:{port}')
    app.run(host='0.0.0.0', port=port)
