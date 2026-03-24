---
name: testcase-generator
description: 基于 Google Docs 链接、对话上传文件、Figma 链接或本地 Markdown 路径生成结构化中文测试用例。用于 Codex 先收集并确认需求资料范围，在 Downloads 下创建任务工作目录、统一记录输入清单，再在用户明确确认后整理来源材料并输出需求总结、测试用例、覆盖矩阵和待确认问题。
---

# 测试用例生成

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

### Step5 打印 “skills 测试结束”

