#!/bin/bash
# 打包项目用于云部署
rm -f /tmp/health-report-deploy.zip
zip -r /tmp/health-report-deploy.zip \
  server.py extract.py build_html.py generate_data.py \
  data_template.json requirements.txt \
  "报告翻译词库-6.22.xlsx2.xlsx" \
  "【报告模板-改2】(1).xlsx" \
  -x "*.pdf" "customers/*" "__pycache__/*" ".git/*"
echo "✅ 部署包已生成: /tmp/health-report-deploy.zip ($(du -h /tmp/health-report-deploy.zip | cut -f1))"
