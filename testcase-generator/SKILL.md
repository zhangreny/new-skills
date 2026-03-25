---
name: testcase-generator
description: 基于 Google Docs 链接、对话上传文件、Figma 链接或本地 Markdown 路径生成结构化中文测试用例。先收集并确认需求资料范围，在 Downloads 下创建任务工作目录、统一记录输入清单，再根据材料并输出 UI 前端测试用例。
---

# 测试用例生成

## 文件读取和写入时的编码

由于文件中可能存在中文，因此所有文件读取和写入的编码都优先使用 utf-8

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

- 如果用户上传文件的方式是：通过指定 markdown 文件的绝对路劲，则应先把这些文件复制一份到工作目录，然后将 `input_manifest.json` 的 `google_doc_url` 中的下载失败 url 移除，并将复制后的文件绝对路径写入 `user_file_directory`，然后不要回退到 Step3，而是仅执行下面的脚本：

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

### Step6 并行调用两个独立 subagent，各自读取全量材料并直接生成 UI 测试用例

先执行如下脚本，收集当前 `workdir` 下可用于 Step6 的全量材料：

```bash
python scripts/step6_collect_materials.py <全局参数 workdir 的绝对路径>
```

脚本输出的 `markdown_files`、`image_files` 将用于完整传递给两独立 Subagent 作为输入。

**读取 markdown 文档模板**：在调用 subagent 之前，先读取 `scripts/step6_ui_cases_output_template.md`，后续 Step6 的所有产出都必须遵循该模板约束。

**并行启动两独立 subagent**：使用 `spawn_agent` 并行启动两个彼此独立的 subagent，两个 agent 和当前主 agent 需要使用相同的模型。两者都必须读取同一份全量材料，禁止将材料按文件拆分给不同 subagent。目标不是分工摘录，而是让两次独立推理分别产出两套完整 UI 测试用例，然后由主 agent 做交叉汇总。

给 subagent 的任务描述至少要包含以下信息：

- 当前 `workdir` 绝对路径
- 全量 `markdown_files`
- 全量 `image_files`
- 对应输出文件绝对路径
- `step6_ui_cases_output_template.md` 的绝对路径
- “直接生成完整 UI 测试用例，不要等待另一位 agent，不要与另一位 agent 协调”的要求
- 

可直接复用如下 prompt 骨架，分别替换输出文件路径后传给两个 subagent：

```text
读取下列全量材料并直接生成完整 UI 测试用例，保存到 <output_file>。不要只给大纲，不要拆分材料，不要等待另一位 agent。所有输出必须遵循 <case_template_file> 的 markdown 结构。

workdir: <workdir>
markdown_files:
<markdown_files>

image_files:
<image_files>
```

**Step6 结束条件**：只有在 `step6_subagent_a_ui_cases.md` 与 `step6_subagent_b_ui_cases.md` 都已经生成后，当前 Step6 才算完成，随后进入 Step7。

### Step7 汇总 Step6 的两 subagent 的用例并生成 merged 版本用例 markdown 文档

必须完整读取 `step6_subagent_a_ui_cases.md` 和 `step6_subagent_b_ui_cases.md` 的全部内容，遵循以下规则进行用例汇总：

- 去重同义或明显重复的用例。
- 对于覆盖范围相近但表述不同的用例，保留更清晰、边界更完整的版本。
- 对于两份产物中互补的内容，合并保留，不要因为重复章节名而误删有效用例。
- 统一标题层级与命名风格，但不要改变原始测试意图。
- `来源：` 必须保留，并在需要时合并多个来源，明确对应的 markdown 文件或截图依据。

### Step8 主 skill review 复核 merged 结果并生成最终版本

主 skill 必须再次回看全量原始材料，并结合以下文件进行复核：
- `step7_ui_cases_merged.md`

复核时必须完成两件事：
- 生成 `step8_ui_cases_review.md`，作为 review 记录自由表达结论、问题和修正意见，不要求遵循固定模板。
- 生成最终版本 `step8_ui_cases_final.md`。`step8_ui_cases_final.md` 仍需遵循 `step6_ui_cases_output_template.md` 的 markdown 结构。如果 review 发现遗漏、重复、描述不清、来源不实或层级混乱，则直接修正后写入 final；如果 review 未发现问题，也要将 reviewed 版本保存为 `step8_ui_cases_final.md`，不要缺失 final 文件。

**Step8 结束前强制校验**：执行如下脚本。脚本只对用例类 markdown 文件校验模板结构；对 review 文件仅做基础编码检查：

```bash
python scripts/step6_8_validate_generated_markdown.py <全局参数 workdir 的绝对路径>
```

如果校验失败，主 skill 必须先修复对应 markdown 文件并重新执行校验，直到脚本返回成功，再将 `step8_ui_cases_final.md` 作为 Step8 最终产物返回给用户。

