---
name: testcase-generator
description: 基于 Google Docs 链接、对话上传文件、Figma 链接或本地 Markdown 路径生成结构化中文测试用例。用于 Codex 需要先收集并确认需求资料范围、在 Downloads 下创建任务工作目录、统一记录输入清单，再在用户明确确认后整理来源材料并输出需求总结、测试用例、覆盖矩阵和待确认问题的场景。
---

# 测试用例生成

## 执行流程

### Step1 调用脚本创建工作目录，用于本次用例生成任务的文件存储

执行如下脚本

```bash
python scripts/step1_create_workdir.py
```

会输出工作目录的绝对路径和 `input-manifest.json` 的绝对路径，如：

```json
{
  "workdir": "C:/Users/username/Downloads/testcase-generate-20260323-100000",
  "input-manifest": "C:/Users/username/Downloads/testcase-generate-20260323-100000/input-manifest.json"
}
```

**全局参数**：本步骤返回的 `workdir` 路径，将作为后续所有操作的默认工作目录，后续步骤中，请勿将文件保存到其他位置。

### Step2 将用户的输入，分类落入文件清单

将用户的输入按下面规则写入 `input-manifest.json` 文件：
- `google doc url`：只记录 Google Docs 链接。
- `uploaded files by agent`：记录用户在对话里上传给 agent 的 markdown 文档；先把这些文件保存到工作目录，再回写为保存后的绝对路径。
- `figma url`：只记录 Figma 链接。
- `user file directory`：只记录用户明确指定的本地绝对路径，可以是文件或目录；不要在这一步展开目录内容。

如果 uploaded files by agent 且 user file directory 的值都为空，则跳过 Step3，否则仍需执行 Step3

### Step3 markdown 文件格式校验

执行如下脚本对 `input-manifest.json` 文件的 `uploaded files by agent` 和 `user file directory` 值进行处理，只保留 markdown 文件，且 markdown 文件后面的图片 base64 已被清理掉。

```bash
python scripts/step3_validate_markdown.py <input-manifest.json 的绝对路径>
```



