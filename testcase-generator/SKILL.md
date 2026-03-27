---
name: testcase-generator  
description: 基于 Google Docs 链接、对话上传文件、Figma 链接或本地 Markdown 路径生成结构化中文测试用例。先收集并确认需求资料范围，再在 Step6 做产品知识装载、产品资料理解、资源类型识别与黄金参考判断，随后按 Step7 测试蓝图、Step8 组合展开、Step9 用例执行、Step10 用例强制细分门限执行，并在 Step6-8 强制返回产物给用户确认。
---

# 测试用例生成

## 资料分层

本 skill 的资料分成五层：

- `references/UI-former-testcase-analyse/Everoute/everoute_common_testcase_rules.md` 与各产品 `everoute_*_testcase_rules.md`：唯一生效的规则层。
- `references/UI-former-testcase-analyse/Everoute/*/everoute_*_product_knowledge.md`：产品知识摘要层，用于对象树、子标题编排习惯、拆分轴、固定块和术语校准。
- `references/Everoute-SmartX-docs/`：产品资料库，用于 Step6 的理解增强、版本边界提醒和资源识别。
- `references/UI-former-testcase-analyse/Everoute/*/<历史样本目录>/`：历史需求、Figma 图片与历史 testcase，仅在有明确相似度时作为黄金参考候选。
- `scripts/`：执行辅助脚本与输出模板。

## 编码

由于文件中可能包含中文，所有文件读取和写入都优先使用 UTF-8。

## 执行前提

如果执行环境中 `python` 和 `python3` 命令均不可用，不要擅自改流程，应先向用户说明这是当前 blocker。

## 规则读取顺序

### 通用规则

始终先读取：

- `references/UI-former-testcase-analyse/Everoute/everoute_common_testcase_rules.md`

### 产品主规则

根据主产品和补充产品读取：

- `references/UI-former-testcase-analyse/Everoute/负载均衡/everoute_lb_testcase_rules.md`
- `references/UI-former-testcase-analyse/Everoute/虚拟专有云网络/everoute_vpc_testcase_rules.md`
- `references/UI-former-testcase-analyse/Everoute/Everoute 服务运维/everoute_ops_testcase_rules.md`
- `references/UI-former-testcase-analyse/Everoute/分布式防火墙/everoute_dfw_testcase_rules.md`

### 产品知识摘要

Step6-10 必须优先读取主产品与补充产品的产品知识摘要：

- `references/UI-former-testcase-analyse/Everoute/负载均衡/everoute_lb_product_knowledge.md`
- `references/UI-former-testcase-analyse/Everoute/虚拟专有云网络/everoute_vpc_product_knowledge.md`
- `references/UI-former-testcase-analyse/Everoute/Everoute 服务运维/everoute_ops_product_knowledge.md`
- `references/UI-former-testcase-analyse/Everoute/分布式防火墙/everoute_dfw_product_knowledge.md`

### SmartX docs

Step6 按需从以下目录挑选有助于理解当前材料的产品资料：

- `references/Everoute-SmartX-docs/`

默认优先读取：

1. 主产品与补充产品的产品知识摘要
2. 同产品管理指南
3. 同产品技术白皮书
4. 术语表
5. 发布说明
6. 安装与升级指南

运维场景例外：若主产品或补充产品命中 `ops`，优先补充安装与升级指南、发布说明和术语表，再结合其他产品资料理解具体功能边界。

SmartX docs 只用于理解增强、对象关系校准、术语校准、版本边界提醒和资源识别，不能直接替代需求文档、figma 或历史 testcase。

## 主产品判定

- 若主流程发生在 LB 对象或 LB 页面内，即使同时出现 VPC 资源过滤或 VPC 影响，默认仍以 LB 为主，VPC 为补充。
- 若主流程发生在 VPC 原生对象内，LB 仅作为影响项，则 VPC 为主，LB 为补充。
- 运维和 DFW 若其对象明显承载主流程，可作为主产品；但展开仍需先以 common 规则和产品知识摘要为骨架。

## 执行流程

### Step1 创建工作目录

执行：

```bash
python scripts/step1_create_workdir.py
```

输出：

```json
{
  "workdir": "C:/Users/username/Downloads/testcase-generate-20260323-100000",
  "input_manifest": "C:/Users/username/Downloads/testcase-generate-20260323-100000/input_manifest.json"
}
```

`workdir` 是后续所有步骤的默认工作目录。

### Step2 记录输入清单

将用户输入写入 `input_manifest.json`：

- `google_doc_url`：仅记录 Google Docs 链接。
- `uploaded_files_by_agent`：记录用户在对话中上传给 agent 的 Markdown 文档；先保存到工作目录，再回写绝对路径。
- `figma_url`：仅记录 Figma 链接。
- `user_file_directory`：记录用户指定的本地绝对路径；先复制到工作目录，再回写绝对路径。不要在此步骤展开目录内容。

### Step3 清理 Markdown 输入

执行：

```bash
python scripts/step3_validate_markdown_cancel_img_base64.py <input_manifest.json 的绝对路径>
```

要求：

- 只保留 Markdown 文件。
- 清理 Markdown 文件中的图片 base64 内容。
- 将处理后的 `input_manifest.json` 返回给用户确认，以脚本输出中的 `user_confirmation_message` 为准。
- 只有用户明确表示“继续”后，才能进入 Step4。

### Step4 下载 Google Docs

先检查：

```bash
python scripts/step4_check_url_whether_blank.py <input_manifest.json 的绝对路径>
```

若 `google_doc_url_is_empty` 为 `true`，直接进入 Step5。

否则执行：

```bash
python scripts/step4_gog_download_markdown_and_cancal_img_base64.py <workdir 的绝对路径>
```

要求：

- 如果 `download_failed` 为空，则进入 Step5。
- 如果 `download_failed` 非空，先返回给用户确认。
- 用户补充 Markdown 文件后，只更新 `input_manifest.json`，然后重新执行 Step3，不回退到 Step2。

### Step5 下载 Figma 顶层业务图片

先检查：

```bash
python scripts/step5_check_figma_url_whether_blank.py <input_manifest.json 的绝对路径>
```

若 `figma_url_is_empty` 为 `true`，直接进入 Step6。

否则执行：

```bash
python scripts/step5_download_top_level_figma_sections.py <workdir 的绝对路径>
```

要求：

- 如果 `download_failed` 非空，先返回给用户确认。
- 用户修正 Figma 链接或 token 后，重新执行当前 Step5。

### Step6 产品理解

先执行：

```bash
python scripts/step6_collect_materials.py "<workdir>"
```

如果脚本输出中的 `should_generate_product_context` 为 `false`，说明当前没有可用于理解的原始材料，应先要求用户补充需求文档、Markdown 文件或 Figma 图片。

Step6 必须读取：

- 全量原始材料：`markdown_files`、`image_files`
- `references/UI-former-testcase-analyse/Everoute/everoute_common_testcase_rules.md`
- 脚本输出的 `product_knowledge_candidates`
- 脚本输出的 `smartx_doc_candidates`
- 脚本输出的 `resource_type_hints`
- 脚本输出的 `golden_reference_candidates`
- 脚本输出的 `effective_rule_files`

Step6 的目标：

- 先用产品知识摘要校准对象树、页面入口、子标题习惯、固定块和高优先级拆分轴。
- 再筛出哪些 SmartX docs 对当前材料“有助于理解”。
- 解释这些资料如何帮助识别对象、对象关系、页面入口、字段组、术语、网络模式、主备关系、版本边界。
- 提前归纳当前任务涉及哪些测试资源类型。
- 说明哪些资源是前置资源，哪些资源会消耗、占用、归还，哪些资源决定版本、容量、权限、主备、过滤或文案分支。
- 明确哪些资料当前不采用，以及为什么不采用。

Step6 输出文件固定为：

- `<workdir>/step6_product_context.md`

Step6 必须遵循：

- 格式遵循 `scripts/step6_product_context_output_template.md`
- 不得输出 testcase、组合树或 testcase 级结论
- 必须写出已扫描资料、已选资料、未采用资料和原因
- 必须写出测试资源类型以及资源前提与消耗/归还规则
- 必须写出黄金参考候选与采用结论

**用户确认**：生成 `step6_product_context.md` 后，必须将该文件返回给用户确认。只有在用户明确表示“继续”后，才可执行 Step7。

### Step7 测试蓝图

Step7 必须完整读取：

- 全量原始材料：`markdown_files`、`image_files`
- `<workdir>/step6_product_context.md`
- `references/UI-former-testcase-analyse/Everoute/everoute_common_testcase_rules.md`
- 主产品与补充产品的产品主规则
- Step6 选中的产品知识摘要
- 若存在高相似黄金参考候选，则读取对应历史 testcase 样本
- `scripts/step7_test_blueprint_output_template.md`

Step7 的目标：

- 产出“对象 -> subsection -> 适用维度 -> 资源类型映射 -> 固定块 -> 资源前提 -> 排除项 -> 来源映射”的测试蓝图。
- 明确哪些维度适用于哪些对象和 subsection。
- 将 Step6 的产品理解、对象树和资源识别结果收敛成后续可直接展开的结构。
- 若采用黄金参考，明确继承哪些结构；若未采用，也必须显式写跳过原因。
- 标记后续可能触发 Step10 的复合 case 风险点。

Step7 输出文件固定为：

- `<workdir>/step7_test_blueprint.md`

Step7 必须遵循：

- 结构遵循 `scripts/step7_test_blueprint_output_template.md`
- 不得输出组合树或 `[C]`
- 固定块不得遗漏：事件审计、权限管理、异常限制，以及当前任务相关的跨产品影响块
- 必须写出资源类型映射和黄金参考继承策略
- 不得直接照搬历史样本中的复合 case 标题

**用户确认**：生成 `step7_test_blueprint.md` 后，必须将该文件返回给用户确认。只有在用户明确表示“继续”后，才可执行 Step8。

### Step8 组合展开

Step8 必须完整读取：

- 全量原始材料：`markdown_files`、`image_files`
- `<workdir>/step7_test_blueprint.md`
- Step7 使用的同一组规则文件
- Step7 选中的产品知识摘要
- `scripts/step8_combination_output_template.md`

Step8 的目标：

- 把 Step7 中确认过的对象、subsection、维度轴和资源前提展开成可执行组合。
- 把 Step7 中确认过的资源类型映射同步展开，不允许在 Step8 再临时发明新的资源前提。
- 每个节点都要能解释它承接自 Step7 的哪一部分蓝图。
- Step8 仍然不生成 testcase。
- 对历史样本中的“同时 / 反复 / 批量 / 多个 / 复合”写法，必须继续拆成中间层组合，而不是直接落叶子。

Step8 输出文件固定为：

- `<workdir>/step8_combination_expansion.md`

Step8 必须遵循：

- 输出是树形缩进列表
- 不得出现 `[C]`
- 每个节点必须紧跟 `描述：`、`来源：`、`承接：`
- 不允许把不同版本、不同权限、不同主备关系、不同结果、不同资源模式提前合并

**用户确认**：生成 `step8_combination_expansion.md` 后，必须将该文件返回给用户确认。只有在用户明确表示“继续”后，才可执行 Step9。

### Step9 最终测试用例

Step9 必须完整读取：

- 全量原始材料：`markdown_files`、`image_files`
- `<workdir>/step6_product_context.md`
- `<workdir>/step7_test_blueprint.md`
- `<workdir>/step8_combination_expansion.md`
- Step7 / Step8 使用的同一组规则文件
- Step7 选中的产品知识摘要
- `scripts/step9_rule_gate_report_template.md`
- `scripts/step9_ui_cases_review_template.md`
- `scripts/step9_ui_cases_output_template.md`

Step9 开始前必须先执行：

```bash
python scripts/step9_build_title_bank.py "<workdir>"
```

脚本会生成：

- `<workdir>/step9_title_bank.json`

用途：

- 基于 Step8 最细组合路径，优先检索当前已采用黄金参考中的历史标题。
- 再扩展检索主产品目录和补充产品目录下的历史 testcase。
- 为 Step9 生成最终 `[C]` 标题提供语义近邻，而不是直接照搬复合 case 标题。

Step9 必须生成以下文件：

- `<workdir>/step9_rule_gate_report.md`
- `<workdir>/step9_ui_cases_review.md`
- `<workdir>/step9_ui_cases_final.md`

其中：

- `step9_rule_gate_report.md`：记录已加载资料、采用规则、继承的蓝图与组合、剪枝与未落地组合、违规项与修正结果、黄金参考对比或跳过说明。
- `step9_ui_cases_review.md`：记录覆盖结论、去重与拆分原则、固定块检查、主要风险与缺口。
- `step9_ui_cases_final.md`：最终 testcase 树，必须遵循 `scripts/step9_ui_cases_output_template.md`。

Step9 必须遵循：

- `[C]` 只能落在最细层
- 每个节点必须紧跟 `描述：`、`来源：`、`承接：`
- Step9 生成最终 `[C]` 标题时，必须优先写成“动作 + 条件 + 结果”的具体交互语义。
- `step9_title_bank.json` 中的历史标题只可作为语义模板，不能直接复制复合 case 标题。
- `显示入口 / 显示默认值 / 显示说明文案 / 显示资源范围 / 列表可见 / 详情可见 / 状态正确 / 提交成功 / 按钮置灰 / 提示必填 / 提示格式错误 / 提示资源冲突 / 保留原状态 / 详情显示限制` 不能直接作为最终 `[C]` 标题。
- 先执行 Step9 中文字符乱码校验，再执行结构校验与黄金参考对比
- Step8 的核心组合，要么在 Step9 落成 testcase，要么在 `step9_rule_gate_report.md` 中解释剪枝原因
- 若 Step6 已采用黄金参考，则结构和覆盖优先向该黄金参考对齐，并按相对数量级检查；默认只对低于 `0.8x` 的明显缩水做门禁，高于 `1.2x` 时只在报告中说明原因，不强制压缩
- 若 Step6 未采用黄金参考，则不对数量设 gate，只检查结构、覆盖、固定块和 traceability

## Step9 结束前校验

先执行语义标题校验：

```bash
python scripts/step9_validate_leaf_title_semantics.py "<workdir>"
```

脚本会检查：

- `step9_ui_cases_final.md`

脚本会输出：

- `ok`
- `generic_title_count`
- `generic_title_examples`
- `repetitive_subtrees`
- `issues`

若语义标题校验失败，Step9 必须只重生成 `step9_ui_cases_final.md`，不能直接进入乱码校验或结构校验。

先执行中文字符乱码校验：

```bash
python scripts/step9_validate_chinese_garble.py "<workdir>"
```

脚本会检查：

- `step9_rule_gate_report.md`
- `step9_ui_cases_review.md`
- `step9_ui_cases_final.md`

脚本会输出：

- `ok`
- `checked_files`
- `issues`

其中每条 `issue` 至少包含：

- `file`
- `line`
- `matched_text`
- `reason`

乱码判定范围固定为：

- 任意 `�`
- 长度大于等于 2 的连续 ASCII `?`

单个 `?` 不算乱码。

若乱码校验失败，Step9 必须只重生成受影响的 Step9 文件，然后重新执行乱码校验。默认最多修复 2 轮；若 2 轮后仍存在乱码，必须停止继续执行，并直接将乱码校验脚本输出返回给用户，不能进入结构校验或黄金参考对比。

乱码校验通过后，再执行结构校验：

```bash
python scripts/step6_9_validate_generated_markdown.py "<workdir>"
```

脚本会检查：

- `step6_product_context.md`
- `step7_test_blueprint.md`
- `step8_combination_expansion.md`
- `step9_rule_gate_report.md`
- `step9_ui_cases_review.md`
- `step9_ui_cases_final.md`

当前任务若 Step6 已采用黄金参考，再执行黄金参考对比：

```bash
python scripts/step9_compare_with_golden_reference.py "<workdir>"
```

该脚本会输出：

- 生成用例数与黄金参考用例数
- 高价值对象簇分布
- 黄金参考高价值簇是否缺失
- 当前相对数量级是否低于默认下限
- 当前相对数量级是否高于默认上限
- 当前相对数量级是否落在默认参考带内

若 Step6 未采用黄金参考，则该脚本应输出 `skipped` 结果而不是报错。

如果结构校验或黄金参考对比暴露明显缩水，主 skill 必须先修复对应文件，再进入 Step10；若仅高于默认上限，应在 `step9_rule_gate_report.md` 中说明原因，而不是为了回落到 `1.2x` 内强制压缩语义化叶子。

### Step10 强制细分闸门

Step10 必须完整读取：

- 全量原始材料：`markdown_files`、`image_files`
- `<workdir>/step6_product_context.md`
- `<workdir>/step7_test_blueprint.md`
- `<workdir>/step8_combination_expansion.md`
- `<workdir>/step9_rule_gate_report.md`
- `<workdir>/step9_ui_cases_review.md`
- `<workdir>/step9_ui_cases_final.md`
- Step7 / Step8 / Step9 使用的同一组规则文件
- Step7 选中的产品知识摘要
- `scripts/step9_ui_cases_output_template.md`
- `scripts/step10_case_split_report_template.md`

Step10 先执行 gate 脚本：

```bash
python scripts/step10_case_split_gate.py "<workdir>" --round-index <当前轮次>
```

如需基于上一轮的 Step10 结果继续细分，可显式指定：

```bash
python scripts/step10_case_split_gate.py "<workdir>" --round-index <当前轮次> --case-file step10_ui_cases_final.md
```

gate 脚本会输出：

- `figma_total_bytes`
- `target_min_case_count`
- `current_case_count`
- `count_gap`
- `numeric_gate_skipped`
- `split_signal_count`
- `split_signal_examples`
- `needs_more_split`
- `round_index`

Step10 的目标：

- 若 gate 返回 `needs_more_split=true`，继续细分 `step9_ui_cases_final.md` 或上一轮 `step10_ui_cases_final.md`。
- 若当前 workdir 存在 Figma 下载目录，则以 `ceil(figma_total_bytes / 12000)` 作为最低数量目标。
- 若当前 workdir 没有 Figma 下载目录，则跳过数量闸门，但仍必须对复合 case 进行结构化细分审计。
- 对每个命中复合信号的 case，检查是否还能按对象、动作、结果、资源模式、主备、通信方向、许可矩阵等继续拆开。
- 不允许把“同时 / 反复 / 复合 / 批量 / 多个动作 / 多个结果 / 多个资源模式”压成单条 case。
- 只根据 gate 结果继续或停止，不要在生成内容中自行声明“最后一轮”“已经到轮次上限”“可以不用继续拆”。

Step10 必须生成以下文件：

- `<workdir>/step10_case_split_report.md`
- `<workdir>/step10_ui_cases_final.md`

其中：

- `step10_case_split_report.md`：记录轮次概览、数量闸门结果、命中的拆分信号、已拆分用例、未拆分原因和最终结论。
- `step10_ui_cases_final.md`：沿用 `scripts/step9_ui_cases_output_template.md` 的树形 testcase 格式，作为最终交付文件。

## Step10 结束前校验

执行：

```bash
python scripts/step6_9_validate_generated_markdown.py "<workdir>" --include-step10
```

脚本会额外检查：

- `step10_case_split_report.md`
- `step10_ui_cases_final.md`

如果 Step10 仍存在结构问题、明显复合 case 或数量闸门未通过，主 skill 必须继续修复对应文件，再重新运行 gate 与结构校验，直到 gate 返回 `needs_more_split=false` 后，才将 `step10_ui_cases_final.md` 作为最终产物返回给用户。
