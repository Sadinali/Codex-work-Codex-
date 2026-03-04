#!/usr/bin/env bash
set -euo pipefail

echo "[1/3] 运行邮件规则MVP..."
python3 email_ops_mvp.py

echo "[2/3] 运行单元测试..."
python3 -m unittest tests/test_email_ops_mvp.py

echo "[3/3] 输出文件预览..."
python3 - <<'PY'
import json
from pathlib import Path

json_path = Path('outputs/processed_emails.json')
rows = json.loads(json_path.read_text(encoding='utf-8'))
print(f'共处理 {len(rows)} 封邮件')
for row in rows:
    print(f"- {row['message_id']} | {row['prefix']}-{row['priority']} | owner={row['owner']} | due={row['due_at']}")
PY

echo "完成。查看 outputs/processed_emails.csv 和 outputs/processed_emails.json"
