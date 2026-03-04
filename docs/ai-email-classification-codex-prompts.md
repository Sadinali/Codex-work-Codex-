# 邮箱管理员接入 AI：下一步实施与 Codex 提示词模板

> 目标：在你现有 PR1（规则引擎）基础上，逐步升级为“规则 + AI”的可控系统，先做到**自动分析与分类**，再扩展到摘要、风险识别、人工复核闭环。

---

## 1. 先明确升级策略（建议）

当前 `email_ops_mvp.py` 已经具备：

- 规则分类（`detect_prefix`）
- 风险识别（`detect_phishing_risk`）
- 优先级决策（`decide_priority`）
- 三行摘要（`build_summary`）

建议不要一次性替换，采用 **AI + 规则兜底**：

1. 先新增 `ai_classifier.py`（只负责调用模型并返回标准 JSON）
2. 在主流程加入 `--mode`：`rules` / `ai` / `hybrid`
3. `hybrid` 模式下：
   - 先跑 AI
   - 如果 AI 输出格式错误或置信度低，则退回规则引擎
4. 结果统一写回现有 CSV/JSON，保持输出兼容

---

## 2. 你与 Codex 协作的最佳节奏（按 PR 拆分）

建议按 4 个小 PR 推进（每个 PR 都可独立验证）：

### PR-A：接入 AI 分类器（最小可用）

- 新增 `ai_classifier.py`
- 支持环境变量读取 API Key
- 输入邮件，输出标准字段：`prefix/priority/status/phishing_risk/summary_3_lines`

### PR-B：接入主流程 + 混合模式

- 在 `email_ops_mvp.py` 增加 `--mode`
- 增加 AI 输出校验和回退逻辑
- 不中断现有规则流程

### PR-C：提示词版本化 + 评估脚本

- 新增 `prompts/email_triage_v1.txt`
- 新增 `scripts/eval_classifier.py`
- 对样本集输出准确率/召回率（先粗粒度）

### PR-D：人工复核闭环

- 对低置信度邮件标记 `needs_human_review=true`
- 输出 `review_queue.csv`
- 增加“人工确认后回写”的最小流程

---

## 3. 可直接发给 Codex 的提示词（复制即用）

> 用法：每次只发一个任务，避免“大而全”导致代码不稳。

### 模板 1：实现 AI 分类器（PR-A）

```text
请在当前仓库实现“最小可运行”的 AI 邮件分类器，要求：
1) 新建 ai_classifier.py
2) 提供函数 classify_email_with_ai(email: dict) -> dict
3) 返回 JSON 字段固定为：
   - prefix: GOV|COM|FIN|OPS|CUS|INT
   - priority: P0|P1|P2
   - status: Action Needed|Waiting External|Closed
   - phishing_risk: low|medium|high
   - summary_3_lines.background
   - summary_3_lines.key_points (长度3)
   - summary_3_lines.required_action
4) 通过环境变量读取 OPENAI_API_KEY，禁止硬编码
5) 如果模型输出非 JSON，抛出可读错误
6) 新增 tests/test_ai_classifier.py，覆盖：成功解析、JSON 解析失败、字段缺失
7) 不引入复杂框架，保持与现有项目风格一致
请给出完整代码改动。
```

### 模板 2：主流程支持 hybrid（PR-B）

```text
请基于当前仓库实现 hybrid 模式，要求：
1) 在 email_ops_mvp.py 增加 --mode 参数：rules|ai|hybrid（默认 rules）
2) mode=ai 时仅使用 AI 分类
3) mode=hybrid 时先走 AI，若出现以下任一条件则回退 rules：
   - AI 报错
   - AI 输出字段不完整
   - AI 置信度 < 0.7（你可在 ai_classifier.py 增加 confidence 字段）
4) 输出 CSV/JSON 字段保持兼容，新增 classifier_source 字段（ai/rules/fallback_rules）
5) 补充单元测试，覆盖 3 种 mode
6) 代码注释用中文
```

### 模板 3：提示词与评估（PR-C）

```text
请在仓库中新增“提示词版本化 + 离线评估脚本”：
1) 新建 prompts/email_triage_v1.txt（保存系统提示词）
2) 新建 scripts/eval_classifier.py：
   - 读取 samples/mock_emails.json
   - 跑指定模式（rules/ai/hybrid）
   - 输出每类 prefix 的 precision/recall（可简化实现）
3) 评估结果写入 outputs/eval_report.json
4) 新增 README 的使用说明
5) 不改动现有输出结构，除非必要
```

### 模板 4：人工复核闭环（PR-D）

```text
请在当前仓库增加人工复核机制：
1) 当满足以下条件之一时标记 needs_human_review=true：
   - phishing_risk=high
   - confidence < 0.7
   - prefix=GOV 且 priority=P0
2) 生成 outputs/review_queue.csv，字段包含：message_id, reason, suggested_owner, due_at
3) 增加 tests/test_review_queue.py
4) 更新 README：如何查看待复核队列
```

---

## 4. AI 分类系统提示词（建议 v1）

将以下内容放到 `prompts/email_triage_v1.txt`：

```text
你是企业邮件分诊助手。你的任务是根据输入邮件生成严格 JSON。

【输出格式】
{
  "prefix": "GOV|COM|FIN|OPS|CUS|INT",
  "priority": "P0|P1|P2",
  "status": "Action Needed|Waiting External|Closed",
  "phishing_risk": "low|medium|high",
  "confidence": 0.0,
  "summary_3_lines": {
    "background": "...",
    "key_points": ["...", "...", "..."],
    "required_action": "负责人+截止日期+动作"
  }
}

【判定规则】
1) 政府/税务/监管来信 -> 优先 GOV；默认不低于 P1；若存在明确时限/处罚风险 -> P0。
2) 发票/付款/银行/对账 -> FIN。
3) 客诉/售后 -> CUS；合同/报价/商业合作 -> COM；物流/运维 -> OPS；内部通知/会议 -> INT。
4) 若疑似钓鱼（异常域名、诱导点击、紧急账号验证）-> phishing_risk=high 且 priority=P0。
5) 不确定时给出最可能分类，并在 required_action 添加“需人工复核”。

【严格要求】
- 只能输出 JSON，禁止输出解释文本。
- key_points 必须恰好 3 条。
- confidence 取值范围 [0,1]。
```

---

## 5. 给你的实操建议（避免走弯路）

1. **先打通最小链路**：`1封邮件 -> AI JSON -> 写入 outputs`，别一开始追求完美准确率。
2. **一定保留规则兜底**：AI 不是 100% 稳定，`hybrid` 模式更安全。
3. **提示词要版本化**：每次只改一处规则，便于回归验证。
4. **优先做“高价值邮件”准确率**：先盯 GOV/FIN/P0，其他类别可后续迭代。
5. **每次只让 Codex 做一件事**：按上面 4 个模板拆分，质量会明显提高。

