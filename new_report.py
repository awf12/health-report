#!/usr/bin/env python3
"""
一键生成新顾客报告
用法: python3 new_report.py 顾客名.pdf
示例: python3 new_report.py Tom.pdf
"""
import sys
import shutil
import os

if len(sys.argv) < 2:
    print('用法: python3 new_report.py <顾客PDF文件名>')
    print('示例: python3 new_report.py Tom.pdf')
    sys.exit(1)

pdf_file = sys.argv[1]

if not os.path.exists(pdf_file):
    print(f'❌ 找不到文件: {pdf_file}')
    sys.exit(1)

# 用新PDF生成数据
print(f'📄 正在解析 {pdf_file} ...')

# 替换 generate_data.py 中的 PDF 文件名
with open('generate_data.py', 'r') as f:
    code = f.read()

# 替换 PDF 文件名为新的
old_pdf = "pdfplumber.open('Lily.pdf')"
new_pdf = f"pdfplumber.open('{pdf_file}')"
code = code.replace(old_pdf, new_pdf)

# 写入临时脚本并运行
with open('_temp_gen.py', 'w') as f:
    f.write(code)

os.system('python3 _temp_gen.py')
os.remove('_temp_gen.py')

# 重建 HTML
print('🏗️  正在生成网页报告...')
os.system('python3 build_html.py')

print(f'\n✅ 完成！新报告: index.html')
print(f'   顾客PDF: {pdf_file}')
print('   直接在浏览器打开 index.html 即可查看')
