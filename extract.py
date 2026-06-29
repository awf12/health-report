#!/usr/bin/env python3
"""
精准数据提取 — 从PDF提取数值 → 替换模板数据
只有数值来自PDF，其余(名称/描述/食物来源)保持模板不变
"""
import sys, json, re, pdfplumber

PDF_PATH = sys.argv[1] if len(sys.argv) > 1 else 'Lily.pdf'

# 1) 提取全文 + 分页
with pdfplumber.open(PDF_PATH) as pdf:
    page_texts = [p.extract_text() or '' for p in pdf.pages]
    full = '\n'.join(page_texts)

print(f'📄 PDF: {PDF_PATH} ({len(pdf.pages)}页)')

# 2) 提取 Meta
meta = {'name':'','gender':'','birthDate':'','testDate':'','visitNumber':'','soc':'',
        'practitioner':'','clinic':'','address':'','phone':'','country':'中国','reportDate':''}

p3 = page_texts[2] if len(page_texts) > 2 else ''

# 名字: page 3 "报告创建对象" 之后的一行，有时跟着 Female/Male
nm = re.search(r'(?:报告创建对象|对象)[：:\s]*\n?(\S+?)\s+(?:会话日期|\d{4}/)', p3)
if not nm:
    nm = re.search(r'(\S{2,15})\s+(?:Female|Male)\s', p3)
if not nm:
    nm = re.search(r'(\S{2,15})\s+\d{4}/\d{1,2}/\d{1,2}\s*\n?\s*(?:Female|Male)', p3)
meta['name'] = nm.group(1).strip() if nm else '未识别'

# 性别
meta['gender'] = '女' if re.search(r'Female', p3) else ('男' if re.search(r'Male', p3) else '')
# 日期 - "会话日期" 后面
dt = re.search(r'会话日期[：:\s]*(\d{4}/\d{1,2}/\d{1,2})', p3)
if not dt:
    dt = re.search(r'(\d{4}/\d{1,2}/\d{1,2})\s*(?:就诊|SOC)', p3)
meta['testDate'] = dt.group(1) if dt else ''
bd = re.search(r'出生日[期]?\s*[：:]?\s*(\d{4}/\d{1,2}/\d{1,2})', p3)
meta['birthDate'] = bd.group(1) if bd else ''
vi = re.search(r'就诊编号[：:\s]*(\d+)', p3)
meta['visitNumber'] = vi.group(1) if vi else ''
soc = re.search(r'SOC\s+(\d+)', p3)
meta['soc'] = soc.group(1) if soc else ''
meta['reportDate'] = meta['testDate']

print(f'👤 {meta["name"]} | {meta["gender"]} | {meta["testDate"]} | 就诊#{meta["visitNumber"]}')

# 3) 建立值映射: { lowercase_key: value }
# 从PDF的各个表格中提取 名称→数值 的映射
VALUE_MAP = {}

def extract_pairs(text, section_start_pat, section_end_pat=None):
    """从文本中提取 名称→数值 的键值对"""
    pairs = {}
    m = re.search(section_start_pat, text, re.IGNORECASE)
    if not m: return pairs
    sec = text[m.end():]
    if section_end_pat:
        em = re.search(section_end_pat, sec, re.IGNORECASE)
        if em: sec = sec[:em.start()]

    for line in sec.split('\n'):
        line = line.strip()
        if not line or len(line) < 3: continue
        # 匹配: 一些文字 然后数字
        vmatch = re.search(r'(\d{1,4})\s*(?:%|很好)?\s*$', line)
        if vmatch:
            name = line[:vmatch.start()].strip().rstrip(',').rstrip('/')
            val = int(vmatch.group(1))
            if name and 0 <= val <= 2000:
                key = name.lower().strip()
                # 保留更具体的名称
                pairs[key] = val
    return pairs

def extract_table_pairs(text, section_start_pat, section_end_pat=None):
    """从两列表格中提取 名称→数值 映射"""
    pairs = {}
    m = re.search(section_start_pat, text, re.IGNORECASE)
    if not m: return pairs
    sec = text[m.end():]
    if section_end_pat:
        em = re.search(section_end_pat, sec, re.IGNORECASE)
        if em: sec = sec[:em.start()]

    lines = [l.strip() for l in sec.split('\n') if l.strip()]
    for line in lines:
        # 两列: 名称 数值 名称 数值
        cols = re.findall(r'(\S+(?:\s+\S+)*?)\s+(\d+)', line)
        for name, val in cols:
            name = name.strip().rstrip(',')
            if name and 0 <= int(val) <= 2000:
                VALUE_MAP[name.lower().strip()] = int(val)

    return pairs

# 4) 从各页面提取值
# 先定义哪些页面包含数据（0-based index）
# 页面: 5=VARHOP, 7=风险, 9=草药, 11=氨基酸, 13=矿物质, 15=芳香
# 19-22=维生素+消化, 24=体质+病原体, 25=外源, 26=额外, 27=原因, 28=加重
# 29-30=情绪, 31=器官, 32-33=神经递质

def extract_page_pairs(page_idx):
    """从单页提取 名称→数值 对"""
    if page_idx >= len(page_texts):
        return
    page = page_texts[page_idx]
    for line in page.split('\n'):
        line = line.strip()
        if not line or len(line) > 200:  # 跳过太长和空行
            continue
        if re.match(r'^\d+\s*/\s*\d+$', line):  # 跳过页码 "17 / 33"
            continue
        if re.match(r'^©|^QX WORLD|^保留所有', line):  # 跳过页脚
            continue
        # 匹配: 标签(可能包含括号) 然后数值
        # 例如: "Phenylalanine (pain control,nerves) 44 0 %"
        # 格式: name value [improvement%]
        m = re.match(r'^(.+?)\s+(\d{1,4})\b', line)
        if m:
            name = m.group(1).strip().rstrip(',').rstrip('，')
            val = int(m.group(2))
            if name and 0 <= val <= 2000 and len(name) >= 2:
                VALUE_MAP[name.lower().strip()] = val

def extract_page_two_col(page_idx):
    """从单页两列表格提取"""
    if page_idx >= len(page_texts):
        return
    page = page_texts[page_idx]
    for line in page.split('\n'):
        line = line.strip()
        if not line or len(line) > 200:
            continue
        if re.match(r'^\d+\s*/\s*\d+$', line):
            continue
        # 两列: 名称 数值  名称 数值
        # 例如: "CIRCULATION 85 BLOOD 70"
        pairs = re.findall(r'(\S[\s\S]{1,60}?)\s+(\d{1,4})\b', line)
        for name, val in pairs:
            name = name.strip().rstrip(',').rstrip('，')
            if name and 0 <= int(val) <= 2000 and len(name) >= 2:
                VALUE_MAP[name.lower().strip()] = int(val)

# 精确按页面提取
data_pages = [4, 6, 8, 10, 12, 14, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
for p in data_pages:
    extract_page_pairs(p)
    extract_page_two_col(p)

# VARHOP 单独处理
for pat, key in [
    (r'Volt\s+(\d+)', 'volt'), (r'Amper\s+(\d+)', 'amper'),
    (r'Resistance\s+(\d+)', 'resistance'), (r'Hydration\s+(\d+)', 'hydration'),
    (r'Oxidation\s+(\d+)', 'oxidation'),
    (r'Proton pressure\s+(\d+)', 'proton_pressure'),
    (r'Electron pressure\s+(\d+)', 'electron_pressure'),
    (r'Major resonant frequency[^\d]*(\d+)', 'resonant_frequency'),
    (r'Reactance speed index\s+(\d+)', 'reactance_speed'),
    (r'Phase angle\s+(\d+)', 'phase_angle'),
    (r'Phase response react\s+(\d+)', 'phase_response'),
    (r'Impedance\s+(\d+)', 'impedance'),
    (r'Parts per seconds[^\d]*(\d+)', 'reaction_speed'),
    (r'Body fat\s+(\d+%?)', 'body_fat'),
    (r'Cellular vitality[^\d]*(\d+)', 'cellular_vitality'),
]:
    m = re.search(pat, full)
    if m:
        v = m.group(1).replace('%','')
        try: VALUE_MAP[key] = int(v)
        except: VALUE_MAP[key] = v

# 风险概况单独 (两列表格, page 7, index 6)
risk_page = page_texts[6] if len(page_texts) > 6 else ''
for line in risk_page.split('\n'):
    line = line.strip()
    if not line or len(line) > 200: continue
    if re.match(r'^\d+\s*/\s*\d+$', line): continue
    cols = re.findall(r'(\S[\s\S]{1,40}?)\s+(\d{1,4})\b', line)
    for name, val in cols:
        name = name.strip().rstrip(',')
        if name and 0 <= int(val) <= 200:
            VALUE_MAP[name.lower().strip()] = int(val)

print(f'📊 从PDF提取了 {len(VALUE_MAP)} 个数值映射')

# 5) 查找函数: 给定英文名，从 VALUE_MAP 找对应的值
def lookup(*names):
    """按优先级查找值 - 先精确再模糊"""
    for name in names:
        key = name.lower().strip()
        if not key:
            continue
        # 精确匹配
        if key in VALUE_MAP:
            return VALUE_MAP[key]
        # 去掉括号内容后匹配: "calcium (weak bones...)" → "calcium"
        for k, v in VALUE_MAP.items():
            k_clean = re.sub(r'\s*\(.*', '', k).strip()
            if key == k_clean:
                return v
        # 包含匹配: key 包含在 k 中
        for k, v in VALUE_MAP.items():
            if key in k:
                return v
        # 反向包含: k 包含在 key 中
        for k, v in VALUE_MAP.items():
            if len(k) >= 3 and k in key:
                return v
        # 首词匹配: "beta carotene" 的首词 "beta" 匹配
        first_word = key.split()[0] if key else ''
        if len(first_word) >= 3:
            for k, v in VALUE_MAP.items():
                k_first = k.split()[0] if k else ''
                if first_word == k_first:
                    return v
    return None

# 6) 构建完整数据 — 始终从干净模板开始，只替换PDF中的值
TEMPLATE_JSON = 'data_template.json'
if not __import__('os').path.exists(TEMPLATE_JSON):
    import subprocess
    subprocess.run(['python3', 'generate_data.py'], check=True, capture_output=True)
    __import__('shutil').copy('data.json', TEMPLATE_JSON)

with open(TEMPLATE_JSON, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 更新 meta
data['meta'].update(meta)

# 更新各板块的值
S = data['sections']
updated_count = 0

def update_section_items(section_key, lookup_map):
    """更新列表中每项的值，lookup_map: {item_name_in_data: pdf_key1, pdf_key2, ...}"""
    global updated_count
    items = S.get(section_key, [])
    if not isinstance(items, list):
        return

    for item in items:
        name = item.get('name', '')
        cn_name = item.get('cn', '')
        old_val = item.get('value')

        # 查找策略：先按cn(英文名)查，再按name(中文名)查
        # 对于每个item，尝试多种匹配方式

        # 1) 直接用 cn / name 查找
        search_keys = []
        if cn_name:
            search_keys.append(cn_name)
        if name:
            search_keys.append(name)

        found = False
        for sk in search_keys:
            v = lookup(sk)
            if v is not None and v != old_val:
                item['value'] = v
                updated_count += 1
                found = True
                break

        # 2) 如果没找到，尝试只匹配英文部分
        if not found and cn_name:
            # 提取第一个词
            first_word = cn_name.split()[0].strip('(),.')
            if first_word:
                v = lookup(first_word)
                if v is not None and v != old_val:
                    item['value'] = v
                    updated_count += 1

# 更新所有板块
for section_key in S:
    items = S[section_key]
    if isinstance(items, list) and len(items) > 0:
        update_section_items(section_key, VALUE_MAP)

# 更新 risk_profile (dict)
risk = S.get('risk_profile', {})
for key in list(risk.keys()):
    v = lookup(key.replace('_', ' '))
    if v is not None:
        risk[key] = v
        updated_count += 1

# 更新 varhop
vh = S.get('varhop', {})
for key in list(vh.keys()):
    if key in VALUE_MAP:
        vh[key] = VALUE_MAP[key]
        updated_count += 1

# 更新 spine
spine_status_map = {}
# 从PDF提取脊柱状态
for spine_page_idx in [16, 17]:
    if spine_page_idx < len(page_texts):
        for line in page_texts[spine_page_idx].split('\n'):
            m = re.match(r'(\S+)\s*/\s*(.+)$', line)
            if m:
                vertebra = m.group(1)
                desc = m.group(2).strip()
                # 解析描述中的状态
                status_map = {
                    '退化': '退化', 'degeneration': '退化',
                    '已校正': '已校正', 'corrected': '已校正',
                    '神经压迫': '神经压迫', 'nervcompression': '神经压迫',
                    '半脱位': '半脱位', 'subluxation': '半脱位',
                    '未校正': '未校正', 'not corrected': '未校正',
                    '炎症': '炎症', 'inflammation': '炎症',
                    '暂时性神经压迫': '暂时性神经压迫', 'temp nerve comp': '暂时性神经压迫',
                    '困难': '困难', 'difficult': '困难',
                }
                for k, v in status_map.items():
                    if k in desc.lower():
                        spine_status_map[vertebra] = v
                        break
                if vertebra not in spine_status_map:
                    spine_status_map[vertebra] = desc[:10]

for item in S.get('spine', []):
    v = item.get('vertebra', '')
    if v in spine_status_map:
        item['status'] = spine_status_map[v]
        updated_count += 1

# 7) 写入 data.json
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'✅ 更新了 {updated_count} 个数值')
print(f'✅ data.json 已就绪')
