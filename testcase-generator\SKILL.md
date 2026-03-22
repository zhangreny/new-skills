---
name: testcase-generator
description: 生成企业级测试用例。用于用户提供 Google Docs 链接、对话上传文件、Figma 链接或本地 Markdown 绝对路径时，先在 Downloads 创建任务目录并写入输入清单 JSON，再判断本次使用哪些资料并必须向用户确认，只有在用户明确确认后，才整理确认后的文件与需求资料并输出结构化测试用例、覆盖矩阵和待确认问题。
---

# 测试用例生成

## 目标

先建立独立任务目录，再把用户输入记录成统一 JSON，先做输入判断和确认，再处理文件与需求资料，最后生成可评审、可执行、可追溯的测试用例。

## 资源

- `scripts/create_workdir.py`：在当前操作系统的 `Downloads` 下创建 `testcase-generate-YYYYMMDD-HHMMSS` 目录，并初始化 `input-manifest.json`。
- `scripts/inspect_input_manifest.py`：读取 `input-manifest.json`，展开本地目录或文件路径，并直接返回本次使用文件清单和建议的用户确认项。
  对于用户指定目录，只返回目录下的 `.md` 和 `.markdown` 文件用于用户确认。
- `references/step-1-workdir.md`：读取第一步的目录和 JSON 约束。
- `references/step-2-input-judgement.md`：读取第二步的输入判断和确认规则。
- `references/step-3-processing.md`：读取第三步的文件存储、资料整理和需求处理规则。
- `references/testcase-spec.md`：读取测试用例结构、覆盖要求、优先级规则和输出模板。

## 工作流

### 第一步：创建工作目录并写入输入清单 JSON

1. 先运行 `scripts/create_workdir.py`，把输出的目录绝对路径记为本次任务工作目录。
2. 本次 skill 的所有中间文件和最终产物都写入这个目录，不要散落到其他位置。
3. 读取 `references/step-1-workdir.md`，按其中详细约束填写工作目录中的 `input-manifest.json`。
4. 第一步只负责建目录和记录输入，不在这一步复制、转换或整理业务文件。

### 第二步：判断输入并返回确认项

1. 读取 `references/step-2-input-judgement.md`。
2. 如果当前轮存在用户通过 agent 上传的文档，先把这些文档保存到第一步创建的工作目录，并把 `input-manifest.json` 中 `uploaded files by agent` 回写为这些已保存文件的绝对路径。
3. 运行 `scripts/inspect_input_manifest.py <input-manifest.json 绝对路径>`。
4. 按 reference 中的规则判断输入完整性、目录展开结果和确认项类型。
5. 必须先把判断结果返回给用户，并等待用户明确确认。
6. 如果用户在第二步期间继续补充新的链接、文件或目录，先更新 `input-manifest.json`；如果补充的是 agent 上传文档，则同样先保存到工作目录并回写绝对路径，再重新执行第二步并再次向用户确认。
7. 第二步只做识别、展开和确认，不生成测试用例，不提前整理成需求文档。

### 第三步：存储文件、处理资料并生成测试用例

1. 只有在用户明确确认第二步结果后，才进入文件存储和处理。
2. 读取 `references/step-3-processing.md`，把确认后的资料沉淀到工作目录。
3. 不要额外创建未明确提及的中间文件；只创建实际需要的资料文件和最终产物。
4. 再读取 `references/testcase-spec.md`，严格按其中结构输出。
5. 最少生成以下产物：
   - `requirements-summary.md`：归纳确认过的需求、业务规则、角色和约束。
   - `testcases.md`：详细测试用例主体。
   - `coverage-matrix.md`：功能点到测试用例的覆盖映射。
   - `open-questions.md`：信息不足、来源冲突、依赖外部确认的项目。
6. 每条测试用例都要可执行，至少包含：编号、模块、标题、优先级、类型、前置条件、测试数据、步骤、预期结果、来源文件。
7. 默认覆盖以下维度，只在明确不适用时才省略：
   - 正向主流程
   - 反向和异常流程
   - 边界值与空值
   - 权限与角色差异
   - 状态流转与重复操作
   - Figma 中体现出的交互、文案和视觉规则
8. 不要把未经证实的实现细节写成确定事实。对推断内容要标记为“假设”或“待确认”。

## 输出要求

- 优先产出结构清晰、便于评审和复制到测试管理平台的 Markdown。
- 在 `requirements-summary.md` 中先写“已确认信息”和“假设与缺口”。
- 在 `testcases.md` 中保持编号稳定；增量更新时尽量复用既有编号。
- 在 `coverage-matrix.md` 中确保每个关键功能点至少能映射到一个正向用例和一个风险用例。
