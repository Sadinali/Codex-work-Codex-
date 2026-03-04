# Codex-work-Codex-
用于学习使用 AI 编程，以及练习 AI 软件、网站开发，完成一些工作任务。

## 运行 nihao.py
在仓库根目录执行以下命令：

```bash
python3 nihao.py
```

如果系统没有 `python3`，可以改用：

```bash
python nihao.py
```

## 邮件自动化机器人实施指南

已新增新手友好的落地指南文档：

- `docs/email-ops-bot-codex-guide.md`

该文档包含：标签体系、SLA、路由矩阵、三行摘要模板、实施路线，以及如何一步步向 Codex 下达任务。

---

## 本地模拟跑流程（无需真实邮箱）

你现在没有真实邮箱，也可以本地完整演示流程。下面按“零基础”步骤操作即可。

### 第 0 步：确认你在仓库根目录

```bash
pwd
```

输出应包含：

```text
/workspace/Codex-work-Codex-
```

### 第 1 步：一条命令跑完整流程（推荐）

```bash
./run_local_mvp.sh
```

这条命令会自动做三件事：

1. 运行规则引擎：`python3 email_ops_mvp.py`
2. 跑测试：`python3 -m unittest tests/test_email_ops_mvp.py`
3. 预览处理结果（message_id、分类、负责人、截止时间）

### 第 2 步：查看输出结果

运行后会生成：

- `outputs/processed_emails.csv`
- `outputs/processed_emails.json`

你可以用以下命令快速查看：

```bash
cat outputs/processed_emails.csv
```

### 第 3 步：自己改规则再重跑

你只要改这两个文件，就可以模拟不同业务场景：

- `samples/mock_emails.json`（模拟输入邮件）
- `config/routing_matrix.csv`（路由/负责人/SLA 规则）

改完后再次执行：

```bash
./run_local_mvp.sh
```

---

## 手动分步运行（可选）

如果你想理解每一步，可手动执行：

```bash
python3 email_ops_mvp.py
python3 -m unittest tests/test_email_ops_mvp.py
```

自定义输入/输出：

```bash
python3 email_ops_mvp.py \
  --input samples/mock_emails.json \
  --routing config/routing_matrix.csv \
  --out-csv outputs/processed_emails.csv \
  --out-json outputs/processed_emails.json
```
