# 第一步：创建工作目录并写入输入清单

## 目标

先创建一个独立工作目录，再把当前轮收到的输入写成统一 JSON，为第二步的输入判断脚本提供稳定入口。

## 执行顺序

1. 先运行 `scripts/create_workdir.py`。
2. 记录脚本返回的绝对路径。
3. 打开脚本生成的 `input-manifest.json`。
4. 把当前轮收到的输入填进去。
5. 再进入第二步判断。

## 工作目录规则

- 目录名固定为 `testcase-generate-YYYYMMDD-HHMMSS`。
- 目录位置固定在当前操作系统用户 `Downloads` 目录下。
- 所有中间资料和最终产物都放在这个目录中。
- 脚本会在目录下自动创建 `input-manifest.json`。
- 除了你明确要求的文件，不要提前在这个目录下创建额外中间文件。

初始目录内容保持最小化：

```text
testcase-generate-YYYYMMDD-HHMMSS/
  input-manifest.json
```

## input-manifest.json 结构

固定结构如下：

```json
{
  "google doc url": [],
  "uploaded files by agent": [],
  "figma url": [],
  "user file directory": []
}
```

四个字段都必须存在，即使为空也保留空数组。

## 填写规则

### google doc url

- 只放 Google Docs 链接。
- 一轮内有多个链接时全部写入数组。

### uploaded files by agent

- 记录用户在对话中上传给 agent 的文档。
- 在进入第二步确认前，先把这些文档保存到第一步创建的工作目录。
- 保存后，把 `uploaded files by agent` 回写为这些已保存文件的绝对路径。
- 第二步及后续步骤都以这些绝对路径作为准入输入。

### figma url

- 只放 Figma 链接。
- 一轮内有多个链接时全部写入数组。

### user file directory

- 只放用户明确指定的本地绝对路径。
- 可以是文件，也可以是目录。
- 不要在这一步展开目录内容，交给第二步脚本处理。
- 如果是目录，第二步只提取该目录下的 Markdown 文档用于返回确认。

## 示例

```json
{
  "google doc url": [
    "https://docs.google.com/document/d/xxx/edit"
  ],
  "uploaded files by agent": [
    "C:/Users/27845/Downloads/testcase-generate-20260322-200000/prd-login.md",
    "C:/Users/27845/Downloads/testcase-generate-20260322-200000/api-error-code.md"
  ],
  "figma url": [
    "https://www.figma.com/file/xxx/login-flow"
  ],
  "user file directory": [
    "C:/project/docs",
    "C:/project/notes/login-rules.md"
  ]
}
```

## 注意事项

- 第一步不复制文件，不整理 Markdown，不读取目录下内容。
- 第一步的职责只有建目录和记录输入。
- 如果用户没有提供某一类输入，保留空数组，不要删除字段。
- 第二步确认前，不要在该目录里额外落盘辅助结果文件。
- 如果用户在第二步阶段补充了新输入，要先回写 `input-manifest.json`，再重新执行第二步。
- 如果用户在第二步阶段补充的是 agent 上传文档，要先保存到工作目录，再把 `uploaded files by agent` 更新为绝对路径。
