# 详细设计

## 1. 运行目录约定

```text
project/
├─ script/
├─ assets/
├─ outputs/
├─ prompts/
├─ logs/
├─ .agent-state.json
└─ project-config.json
```

说明：

- `prompts/` 在工程实现中建议映射或复制当前项目的 `CLAUDE.md`、`agents/`、`skills/`
- 如果直接以内置目录读取当前 Prompt 文件，也可以不单独建立 `prompts/`

## 2. 状态机设计

每集状态只允许在如下节点间流转：

```text
WAIT_SCRIPT
  -> DIRECTOR_ANALYSIS
  -> DIRECTOR_REVIEW
  -> ART_DESIGN
  -> ART_REVIEW
  -> STORYBOARD
  -> STORYBOARD_REVIEW
  -> DONE
```

失败分支：

- `DIRECTOR_REVIEW_FAIL -> DIRECTOR_ANALYSIS`
- `ART_REVIEW_FAIL -> ART_DESIGN`
- `STORYBOARD_REVIEW_FAIL -> STORYBOARD`

## 3. 集数识别规则

### 3.1 文件命名规则

推荐使用：

- `ep01-xxx.md`
- `ep02-xxx.md`
- `ep03-xxx.txt`

### 3.2 识别正则

建议使用：

```regex
ep\d{2}
```

### 3.3 默认集数选择

优先级：

1. 用户命令明确指定
2. 最近未完成集数
3. `script/` 中按集数排序后的第一未完成项

## 4. 项目状态检测算法

伪代码：

```text
scan scripts
for each episode:
  if outputs/<ep>/ not exists:
    stage = DIRECTOR_ANALYSIS
  else if 01-director-analysis exists and current ep assets not ready:
    stage = ART_DESIGN
  else if assets ready and 02-seedance-prompts not exists:
    stage = STORYBOARD
  else if both output files exist:
    stage = DONE
```

补充约束：

- 是否“assets ready”不能只判断文件存在，还要判断本集相关人物/场景是否已追加
- 第一版可以通过 `epXX 新增`、`epXX 变体` 标签文本判断

## 5. 指令设计

### 5.1 `~start [epXX]`

执行流程：

1. 确定目标集数
2. 加载剧本
3. 恢复或创建 director Agent 会话
4. 调用导演执行 Prompt
5. 写入 `01-director-analysis.md`
6. 调用业务审核
7. 调用合规审核
8. 如失败则回修并循环
9. 成功后提示下一步 `~design`

### 5.2 `~design [epXX]`

执行流程：

1. 校验 `01-director-analysis.md`
2. 恢复或创建 art-designer Agent
3. 只为“新增/变体”素材生成提示词
4. 追加写入 `character-prompts.md` 与 `scene-prompts.md`
5. 恢复 director Agent 执行业务审核
6. 执行合规审核
7. 如失败则回修并循环
8. 成功后提示下一步 `~prompt`

### 5.3 `~prompt [epXX]`

执行流程：

1. 校验导演分析文件与素材提示词文件
2. 恢复或创建 storyboard-artist Agent
3. 建立素材对应表
4. 生成 `02-seedance-prompts.md`
5. 恢复 director Agent 执行业务审核
6. 执行合规审核
7. 如失败则回修并循环
8. 成功后标记本集完成

### 5.4 `~status`

输出：

- 各剧本文件状态
- 当前默认集数
- 当前阶段
- 子 Agent 是否恢复
- 下一步建议命令

### 5.5 `~help`

输出：

- 指令列表
- 使用示例
- 文件准备说明

## 6. 审核循环设计

伪代码：

```text
run executor_agent(stage)
write artifact(stage)

business_result = run_director_review(stage_skill)
compliance_result = run_compliance_review()

if both PASS:
  return success
else:
  merged_feedback = merge(business_result, compliance_result)
  run executor_agent(stage, merged_feedback)
  overwrite_or_append(stage)
  repeat
```

关键点：

- 必须把两类审核意见合并后一次性交给执行 Agent，避免来回修改
- 每次循环都重写对应阶段产物

## 7. 追加与覆盖策略

### 7.1 覆盖写

- `outputs/<集数>/01-director-analysis.md`
- `outputs/<集数>/02-seedance-prompts.md`

理由：

- 这两个文件代表该集当前阶段的最新完整结果

### 7.2 追加写

- `assets/character-prompts.md`
- `assets/scene-prompts.md`

理由：

- 资产是跨集累积的
- 复用项不重复写入
- 变体项在文件末尾追加

## 8. 修改请求回流设计

### 8.1 影响范围判断

规则：

- 修改剧情点内容 -> 回流导演分析，后续阶段全部可能失效
- 修改人物外观或场景视觉 -> 回流服化道设计与分镜
- 修改镜头、运镜、声音 -> 只回流分镜阶段

### 8.2 回流执行

1. 恢复对应 Agent
2. 注入用户修改意见
3. 重写受影响文件
4. 重新执行该阶段审核
5. 如影响下游，提示用户是否继续重跑下游

## 9. 异常处理设计

### 9.1 模型调用失败

- 重试 2-3 次
- 记录失败原因
- 保留当前阶段上下文状态

### 9.2 输出结构不合法

- 先做格式校验
- 不合格则要求同一 Agent 重新按模板输出

### 9.3 审核死循环

- 单阶段最多 3 轮自动回修
- 超过阈值后转人工介入

### 9.4 编码异常

- 统一 UTF-8
- 读写前进行编码检测

## 10. 第一版建议实现方式

- 语言：Python 或 Node.js 均可
- 持久化：本地文件系统
- 配置：JSON/YAML
- 命令入口：CLI
- 日志：JSONL

理由：足够快，且与当前项目方法最贴合。
