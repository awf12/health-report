#!/usr/bin/env python3
"""拖拽 data.json 到此程序上，自动生成填好的 Excel"""
import sys, json, openpyxl, os, shutil

def fill(data_file):
    if not os.path.exists(data_file):
        print(f'❌ 找不到 {data_file}')
        return

    with open(data_file) as f:
        data = json.load(f)
    if 'sections' in data: data = data['sections']

    template = os.path.join(os.path.dirname(__file__), '【报告模板-改5】.xlsx')
    if not os.path.exists(template):
        template = '【报告模板-改5】.xlsx'

    wb = openpyxl.load_workbook(template)

    SHEET_MAP = {
        '1.基本体质': '1.基本体质', '2.氨基酸': '2.氨基酸',
        '3.矿物质': '3.矿物质', '4.芳香疗法': '4.芳香疗法',
        '5.脊柱反应性': '5.脊柱反应性',
        '6.水溶性维生素': '6.水溶性维生素', '7.脂溶性维生素': '7.脂溶性维生素',
        '8.一般消化系统': '8.一般消化系统',
        '9.碳水化合物代谢': '9.碳水化合物代谢',
        '10.蛋白质和脂类代谢': '10.蛋白质和脂类代谢',
        '11.外源性物质': '11.外源性物质',
        '12.外源性物质额外因素': '12.外源性物质额外因素',
        '13.导致健康风险和健康恶化的原因': '13.导致健康风险和健康恶化的原因',
        '14.74项情绪': '14.74项情绪', '15.压力指数和来源': '15.压力指数和来源',
        '16.神经递质': '16.神经递质',
    }

    for data_key, sheet_name in SHEET_MAP.items():
        secs = data.get(data_key, [])
        ws = wb[sheet_name]
        row_offset = 0
        for sec in secs:
            items = sec.get('indicators', [])
            for i, item in enumerate(items):
                row = row_offset + i + 18 if data_key == '1.基本体质' else row_offset + i + 22
                if row > ws.max_row: break
                if item.get('value') is not None:
                    ws.cell(row=row, column=3).value = item['value']
            row_offset += len(items)

    out = data_file.replace('.json', '') + '_已填充.xlsx'
    wb.save(out)
    print(f'✅ 已生成: {out}')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for f in sys.argv[1:]:
            fill(f)
    else:
        # Interactive mode - look for data.json in current dir
        print('📋 健康检测报告 - 模板填充工具')
        print('=' * 40)
        data_file = input('请输入JSON文件路径（或拖拽文件到此处）: ').strip().strip('"').strip("'")
        if data_file:
            fill(data_file)
        else:
            print('未输入文件路径')
        input('\n按回车退出...')
