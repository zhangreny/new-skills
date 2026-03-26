---
name: testcase-generator
description: 基于 Google Docs 链接、对话上传文件、Figma 链接或本地 Markdown 路径生成结构化中文测试用例。先收集并确认需求资料范围，在 Downloads 下创建任务工作目录、统一记录输入清单，再根据材料逐步完成维度拆解、组合展开、规则门禁自检和最终用例生成。
---

# 测试用例生成

## 文件读取和写入时的编码

由于文件中可能存在中文，因此所有文件读取和写入的编码都优先使用 utf-8。

## 执行流程

### Step1 调用脚本创建工作目录，用于本次用例生成任务的文件存储

执行如下脚本：

```bash
python scripts/step1_create_workdir.py
```

会输出工作目录的绝对路径和 `input_manifest.json` 的绝对路径，如：

```json
{
  "workdir": "C:/Users/username/Downloads/testcase-generate-20260323-100000",
  "input_manifest": "C:/Users/username/Downloads/testcase-generate-20260323-100000/input_manifest.json"
}
```

**全局参数**：本步骤返回的 `workdir` 路径，将作为后续所有操作的默认工作目录。后续步骤中，请勿将文件保存到其他位置。

### Step2 将用户输入分类写入文件清单

将用户的输入按下面规则写入 `input_manifest.json` 文件：

- `google_doc_url`：只记录 Google Docs 链接。
- `uploaded_files_by_agent`：记录用户在对话里上传给 agent 的 Markdown 文档；先把这些文件保存到工作目录，再回写为保存后的绝对路径。
- `figma_url`：只记录 Figma 链接。
- `user_file_directory`：记录用户明确指定的本地绝对路径，可以是文件或目录；先把这些文件或目录复制一份到工作目录，再回写为复制后的绝对路径。不要在这一步展开目录内容。

### Step3 处理 `uploaded_files_by_agent` 和 `user_file_directory` 中的 Markdown 文件

执行如下脚本，对 `input_manifest.json` 文件里的 `uploaded_files_by_agent` 和 `user_file_directory` 值进行处理，只保留 Markdown 文件，并清理 Markdown 文件中的图片 base64 内容：

```bash
python scripts/step3_validate_markdown_cancel_img_base64.py <input_manifest.json 的绝对路径>
```

**用户确认**：将处理后的 `input_manifest.json` 返回给用户确认，确认内容以脚本输出中的 `user_confirmation_message` 为准。

**用户交互**：如果用户对文件有修改意见，则需要重新执行 Step2 更新 `input_manifest.json`，并执行 Step3 重新保留和处理 Markdown 文件。只有在用户明确表示“继续”后，才可执行 Step4。

### Step4 若 `google_doc_url` 不为空，则尝试下载到本地

先执行如下脚本，检查 `input_manifest.json` 文件的 `google_doc_url` 字段值是否为空列表：

```bash
python scripts/step4_check_url_whether_blank.py <input_manifest.json 的绝对路径>
```

**跳过确认**：如果脚本输出中的 `google_doc_url_is_empty` 为 `true`，说明当前没有 Google Docs 链接，则当前 Step4 结束，直接进行 Step5。

如果脚本输出中的 `google_doc_url_is_empty` 为 `false`，说明当前存在 Google Docs 链接，需要执行如下脚本尝试下载并清理图片 base64 内容：

```bash
python scripts/step4_gog_download_markdown_and_cancal_img_base64.py <全局参数 workdir 的绝对路径>
```

**用户交互**：如果脚本输出中的 `download_failed` 为空，则当前 Step4 结束，直接进行 Step5。否则，将该 `download_failed` 不为空的列表内容返回给用户确认。

- 用户需要手动导出并上传这些失败链接 / ID 对应的 Markdown 文件，提示用户导出的时候选择 all tabs 确保下载完全。
- 如果用户上传文件的方式是：通过 agent 上传 markdown 文件，则应先把这些文件保存到工作目录，然后将 `input_manifest.json` 的 `google_doc_url` 中的下载失败 url 移除，并将保存后的绝对路径写入 `uploaded_files_by_agent`，然后不要回退到 Step3，而是仅执行下面的脚本：

```bash
python scripts/step3_validate_markdown_cancel_img_base64.py <input_manifest.json 的绝对路径>
```

- 如果用户上传文件的方式是：通过指定 markdown 文件的绝对路径，则应先把这些文件复制一份到工作目录，然后将 `input_manifest.json` 的 `google_doc_url` 中的下载失败 url 移除，并将复制后的文件绝对路径写入 `user_file_directory`，然后不要回退到 Step3，而是仅执行下面的脚本：

```bash
python scripts/step3_validate_markdown_cancel_img_base64.py <input_manifest.json 的绝对路径>
```

### Step5 若 `figma_url` 不为空，则调用脚本下载仅顶层业务 section 的 png 文件

先执行如下脚本，检查 `input_manifest.json` 文件里的 `figma_url` 字段值是否为空列表：

```bash
python scripts/step5_check_figma_url_whether_blank.py <input_manifest.json 的绝对路径>
```

**跳过确认**：如果脚本输出中的 `figma_url_is_empty` 为 `true`，说明当前没有 Figma 链接，则当前 Step5 结束，直接进入 Step6。

如果脚本输出中的 `figma_url_is_empty` 为 `false`，说明当前存在 Figma 链接，则执行如下脚本：

```bash
python scripts/step5_download_top_level_figma_sections.py <全局参数 workdir 的绝对路径>
```

**用户交互**：如果脚本输出中的 `download_failed` 不为空，则将失败列表返回给用户确认。只有在用户补充可访问的 Figma 链接或修正 token 后，才重新执行当前 Step5。

- 如果用户给了新的 figma 文档链接，则将 `input_manifest.json` 的 `figma_url` 中的下载失败的 url 移除，将新的 figma url 写入文件，然后不要回退到 Step5，而是仅执行下面的脚本：

```bash
python scripts/step5_download_top_level_figma_sections.py <全局参数 workdir 的绝对路径>
```

### Step6 加载规则库，生成分组维度供用户确认

先执行如下脚本，收集当前 `workdir` 下可用于 Step6 的全量材料：

```bash
python scripts/step6_collect_materials.py <全局参数 workdir 的绝对路径>
```

如果脚本输出中的 `should_generate_dimensions` 为 `false`，说明当前没有可用于分析的原始材料。此时禁止继续生成维度拆解，应先告知用户并要求补充需求文档、Markdown 文件或 Figma 设计稿。

在 Step6 中，必须先加载规则库，再做维度拆解。规则库路径如下：

- Common rules：`C:\Users\27845\Desktop\UI-former-testcase-analyse\Everoute\everoute_common_testcase_rules.md`
- Gate rules：`C:\Users\27845\Desktop\UI-former-testcase-analyse\Everoute\everoute_generation_gate.md`
- Ops rules：`C:\Users\27845\Desktop\UI-former-testcase-analyse\Everoute\Everoute 服务运维\everoute_ops_testcase_rules.md`
- DFW rules：`C:\Users\27845\Desktop\UI-former-testcase-analyse\Everoute\分布式防火墙\everoute_dfw_testcase_rules.md`
- VPC rules：`C:\Users\27845\Desktop\UI-former-testcase-analyse\Everoute\虚拟专有云网络\everoute_vpc_testcase_rules.md`
- LB rules：`C:\Users\27845\Desktop\UI-former-testcase-analyse\Everoute\负载均衡\everoute_lb_testcase_rules.md`

规则加载顺序固定为：

1. 始终加载 Common rules
2. 根据主需求所属产品加载一个主产品规则文件
3. 如果材料里包含其他产品的独立 UI 变更，再额外加载对应产品规则作为补充规则
4. Step6 不使用 Gate rules 做最终门禁，只用来提醒不得输出 testcase 级结论

主产品判断原则：

- 优先看需求文档主题和所在目录
- 如果需求主题明显属于某一个产品，则该产品规则为主
- 如果需求跨多个产品，但只有一个产品承载主流程，则该产品为主，其余为补充
- 主产品规则决定顶层分组，补充规则只影响相关子树，不得反客为主

Step6 的目标不是直接生成测试用例，而是基于 rules 产出“可复用分组维度”。必须全量阅读 `markdown_files`、`image_files` 中的全部材料，并遵循 `scripts/step6_dimension_output_template.md` 的格式约束。

Step6 只允许停留在“可复用分组维度”这一层，不得出现：

- 某个具体场景下“成功 / 报错 / 不报错”的完整结论句
- 带有明确动作、前提、结果三段式的 testcase 标题
- 已经把多个维度值组合在一起的完整组合结果

Step6 的输出文件固定为：

- `<workdir>/step6_dimension_breakdown.md`

Step6 的输出前，必须先做一次“规则执行回合”，并在返回给用户的说明中显式列出：

- 已加载的规则来源
- 当前采用的主产品规则
- 当前采用的分组维度
- 被排除的 testcase 级结论类型

**用户确认**：生成 `step6_dimension_breakdown.md` 后，必须将该文件返回给用户确认。只有在用户明确表示“继续”后，才可执行 Step7。

### Step7 基于维度和规则库展开组合，生成组合展开结果供用户确认

Step7 必须完整读取：

- 全量原始材料：`markdown_files`、`image_files`
- `<workdir>/step6_dimension_breakdown.md`
- Common rules
- 主产品 rules
- 补充产品 rules（如果有）
- `scripts/step7_combination_output_template.md`

Step7 的目标是把 Step6 中确认过的分组维度展开成“可执行组合”，但仍然不生成 testcase。Step7 只允许输出组合树，不允许出现 `[C]`。

Step7 的输出文件固定为：

- `<workdir>/step7_combination_expansion.md`

Step7 必须遵循以下规则：

- 优先按主场景分组，再按主变量轴继续分组
- 高优先级变量轴包括但不限于：版本、对象、环境对象、容量状态、权限状态、联动关系、结果归属
- 不允许把不同版本、不同状态、不同权限、不同结果的组合提前合并
- 如果一个叶子节点同时表达两个以上独立结果，必须继续拆开

Step7 的输出前，必须再次做一次“规则执行回合”，并在返回给用户的说明中显式列出：

- 已加载的规则来源
- 当前采用的分层模板
- 当前采用的主展开轴
- 当前显式保留的禁止项

**用户确认**：生成 `step7_combination_expansion.md` 后，必须将该文件返回给用户确认。只有在用户明确表示“继续”后，才可执行 Step8。

### Step8 基于组合和 rules + gate 生成最终测试用例

Step8 必须完整读取：

- 全量原始材料：`markdown_files`、`image_files`
- `<workdir>/step6_dimension_breakdown.md`
- `<workdir>/step7_combination_expansion.md`
- Common rules
- 主产品 rules
- 补充产品 rules（如果有）
- Gate rules
- `scripts/step8_ui_cases_output_template.md`

Step8 必须生成以下 3 个文件：

- `<workdir>/step8_rule_gate_report.md`
- `<workdir>/step8_ui_cases_review.md`
- `<workdir>/step8_ui_cases_final.md`

其中：

- `step8_rule_gate_report.md`：记录本次规则执行回合，包括已加载规则、采用的分层模板、采用的展开轴、发现的违规项、修正结果。
- `step8_ui_cases_review.md`：记录 review 结论，说明最终 testcase 是否遵守 rules，哪些地方做了去重、拆分或修正。
- `step8_ui_cases_final.md`：最终 testcase 文件，必须遵循 `scripts/step8_ui_cases_output_template.md` 的树形结构。

Step8 必须遵循以下门禁：

- `step8_ui_cases_final.md` 中的 `[C]` 必须都落在最细层
- 不允许把“新集群成功 / 旧集群报错”或“有权限可编辑 / 无权限只读”压成一条 case
- 不允许遗漏主产品 rules 中标明的固定块
- 不允许出现来源过粗、层级突降、后半段明显缩减分组深度
- Step7 的每个核心组合，要么在 Step8 落成 testcase，要么在 `step8_rule_gate_report.md` 中明确记录为何不落

### Step8 结束前强制校验

执行如下脚本：

```bash
python scripts/step6_8_validate_generated_markdown.py <全局参数 workdir 的绝对路径>
```

脚本会强制检查以下文件都存在并满足基本结构：

- `step6_dimension_breakdown.md`
- `step7_combination_expansion.md`
- `step8_rule_gate_report.md`
- `step8_ui_cases_review.md`
- `step8_ui_cases_final.md`

如果校验失败，主 skill 必须先修复对应文件并重新执行校验，直到脚本返回成功，再将 `step8_ui_cases_final.md` 作为最终产物返回给用户。
