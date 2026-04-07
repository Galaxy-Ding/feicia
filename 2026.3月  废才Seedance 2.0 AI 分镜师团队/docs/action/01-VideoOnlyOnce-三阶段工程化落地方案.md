# VideoOnlyOnce 三阶段工程化落地方案

## 1. 文档目标

本文件把现有文档里的方向，收敛成一份可直接执行的工程方案。

目标不是继续讨论“理想中的全自动 AI 制片厂”，而是明确：

- 当前仓库怎么接起来才最稳
- 自动化如何分三阶段逐步提升
- 每个子阶段如何独立调试和单独验收
- 如何在低耦合前提下保留后续自我成长空间

## 2. 基于现状的判断

结合根目录 `docs/`、`fenjing_program/`、`zaomeng/` 当前内容，可以直接采用下面的现实判断：

- `fenjing_program` 适合作为总控和结构化产物层
- `zaomeng` 适合作为图片/视频网页执行层
- `OpenClaw` 适合作为隔离执行器，不适合作为总编排器
- 当前最成熟的是：
  - CLI 驱动
  - 文件驱动
  - 审核 gate
  - asset registry
  - reference map
- 当前还不适合一上来就做：
  - 全自动长篇改编闭环
  - 无限制自治 Agent
  - 让浏览器执行器承担总控

所以本方案采用：

- 先 `CLI + JSON contract + 文件状态机`
- 再 `统一编排器`
- 最后 `无人工批处理`

## 3. 设计原则

### 3.1 低耦合原则

所有模块只通过明确契约通信，不直接跨模块读取对方内部状态。

允许的通信方式只有 4 类：

- 结构化输入文件
- 结构化输出文件
- 受控 CLI / 函数调用
- 统一事件日志

禁止：

- 模块 A 直接解析模块 B 的临时日志猜状态
- 浏览器执行层反向决定业务流程
- 审核结果只存在自然语言 markdown，不写结构化 sidecar

### 3.2 可调试原则

每个子阶段必须满足：

- 单独运行
- 单独重跑
- 单独回滚
- 单独验收
- 单独定位失败原因

### 3.3 可成长原则

系统的“成长”不依赖某个神奇 Agent 突然变聪明，而依赖 5 类可沉淀资产：

- 知识库
- 角色与场景锚定资产
- 审核记录
- 失败案例与修复动作
- 模板、策略、阈值与评分器

### 3.4 安全原则

- 浏览器自动化只做白名单动作
- 登录由人工建立，自动化只复用登录态
- 内容分类先于自动执行
- 所有有副作用动作都保留可审计证据

## 4. 总体架构

推荐采用 4 层架构。

```text
Layer 1: Contract Layer
  JSON schema / manifest / status / gate result / event log

Layer 2: Orchestration Layer
  fenjing_program CLI now
  graph orchestrator later

Layer 3: Execution Layer
  knowledge agent
  character anchor
  storyboard
  prompt packager
  image runner
  review runner
  continuity checker
  video runner
  audio runner
  render runner

Layer 4: Learning Layer
  evidence store
  failed cases
  score history
  prompt/policy evolution
  experiment registry
```

### 4.1 三个中心

整套工程建议按三个中心组织。

#### A. 编排中心

负责：

- 决定当前 episode 跑到哪一步
- 决定是否进入下一 gate
- 决定重试、回退、转人工还是终止

现阶段实现：

- `fenjing_program` CLI + pipeline

后续升级：

- `LangGraph` 或等价状态图编排器

#### B. 执行中心

负责：

- 产出图片、视频、音频
- 回收执行结果
- 记录下载、命名、元数据和截图证据

现阶段实现：

- `zaomeng`
- `OpenClaw Browser Operator`
- 后续新增 `video_operator`、`result_callback`

#### C. 成长中心

负责：

- 记录每次任务的输入、输出、评分、失败原因
- 产出更稳的模板、阈值和默认策略
- 为后续批量自动化提供可复用经验

现阶段建议：

- 先文件化
- 后续再接数据库或向量检索

## 5. 模块拆分

建议稳定为 10 个低耦合模块。

## 5.1 `novel-knowledge`

职责：

- 持续读取小说章节
- 提炼世界观、角色、场景、视觉母题、听觉母题
- 导出给单集消费的 `context-pack`

输入：

- 原始章节
- 既有知识库
- 人工修订记录

输出：

- `story_bible.md`
- `character_bible.md`
- `scene_bible.md`
- `continuity_rules.json`
- `exports/context-pack-epXX.json`

## 5.2 `character-anchor`

职责：

- 识别当前集角色
- 生成角色卡
- 生成标准视图任务
- 审核角色图并入库

输入：

- `context-pack`
- 当前集剧本
- 历史角色资产

输出：

- `character-sheets.json`
- `character-image-tasks.json`
- `character-review.json`
- `character-anchor-pack.json`

## 5.3 `storyboard-builder`

职责：

- 把剧本拆成 scene / shot
- 给 shot 挂接角色与场景资产
- 输出后续可执行的镜头计划

输出：

- `shot-plan.json`
- `storyboard.md`

## 5.4 `task-packager`

职责：

- 把分镜结构转成平台可执行任务
- 分离图片任务、视频任务、音频任务
- 补齐 prompt 模板、风格模板、负面词和参考图

输出：

- `image-tasks.json`
- `video-tasks.json`
- `audio-tasks.json`

## 5.5 `image-runner`

职责：

- 读取图片任务
- 调用 `zaomeng`
- 产出下载、重命名、归档和回写

输出：

- `image-run-summary.json`
- `downloads/images/...`
- `assets/manifests/image-generation-log.jsonl`

## 5.6 `image-review`

职责：

- 对图片做规则评分和 LLM 审查
- 输出 `pass / reject / pending_manual`
- 为 continuity 阶段筛出候选帧

输出：

- `image-review.json`
- `image-review-report.md`

## 5.7 `continuity-checker`

职责：

- 检查相邻镜头的人物、服装、镜位、方向、光线、节奏连续性
- 为视频阶段挑选可用前后帧对

输出：

- `continuity-report.json`
- `video-input-pack.json`

## 5.8 `video-runner`

职责：

- 调用视频页自动化
- 上传参考图或前后帧
- 下载视频结果并记录元数据

输出：

- `video-run-summary.json`
- `video-review.json`

## 5.9 `audio-runner`

职责：

- 提炼对白与旁白
- 生成角色声线与 TTS 任务
- 回写音频时长与文本对齐信息

输出：

- `audio-script.json`
- `tts-manifest.json`

## 5.10 `render-runner`

职责：

- 合成镜头视频、配音、字幕、音效
- 输出最终成片和成片 manifest

输出：

- `final/video.mp4`
- `final/final-manifest.json`

## 6. 统一契约

这是低耦合的关键。建议所有模块统一遵守 6 类 contract。

## 6.1 任务 contract

每个任务都必须有：

- `project_id`
- `book_id`
- `episode_id`
- `stage`
- `task_id`
- `task_type`
- `upstream_artifacts`
- `inputs`
- `policy_version`
- `created_at`

## 6.2 结果 contract

每个结果都必须有：

- `task_id`
- `status`
- `outputs`
- `scores`
- `error_code`
- `error_message`
- `operator`
- `started_at`
- `finished_at`

## 6.3 Gate contract

每个 gate 都必须输出：

- `gate_name`
- `episode_id`
- `pass`
- `reason_codes`
- `manual_required`
- `retryable`
- `evidence_refs`

## 6.4 事件日志 contract

统一采用 JSONL，至少记录：

- `event_time`
- `episode_id`
- `stage`
- `task_id`
- `event_type`
- `message`
- `payload_ref`

## 6.5 版本 contract

所有关键产物都带版本：

- `schema_version`
- `prompt_template_version`
- `policy_version`
- `review_rule_version`

## 6.6 错误码 contract

每个子阶段都必须输出稳定错误码，例如：

- `SCRIPT_PARSE_FAILED`
- `CHARACTER_REFERENCE_MISSING`
- `IMAGE_PLATFORM_SUBMIT_FAILED`
- `IMAGE_SCORE_LOW`
- `CONTINUITY_BROKEN`
- `VIDEO_DOWNLOAD_TIMEOUT`
- `TTS_DURATION_MISMATCH`

## 7. 三阶段自动化路线

## 7.1 阶段一：可落地的人机协作版

目标：

- 单集稳定跑通
- 允许人工介入
- 优先把结构化产物和失败定位做扎实

单次运行允许的人工点：

- 人工确认知识库关键歧义
- 人工定主角黄金参考图
- 人工处理 `pending_manual`
- 人工决定关键镜头是否回炉
- 人工最终放行单集

这一阶段重点不是追求人工最少，而是追求：

- 边界清楚
- 证据完整
- 重跑稳定

推荐实现：

- `fenjing_program` 继续做主入口
- `zaomeng` 继续做图片执行
- `OpenClaw` 只在图片阶段接入
- 视频、TTS、合成先做单集最小闭环

阶段一放行条件：

- 每个子阶段都有结构化输入输出
- 每个子阶段都能单独重跑
- 至少能形成一个单集可播放版本
- 失败能落到明确模块，而不是“整条链路坏了”

## 7.2 阶段二：人工干预不超过 2 次

目标：

- 单集主流程尽量自动推进
- 人工只处理真正高价值决策

建议把人工点压缩成 2 个以内：

1. 开集放行
2. 异常队列处理或最终成片抽检

说明：

- 正常任务路径不再要求人工逐阶段确认
- 只有命中低置信度、风险内容、连续性异常、平台异常时才进人工队列

这一阶段必须新增：

- policy router
- 自动重试策略
- 任务优先级和队列
- 异常分流中心
- 自动回退策略

建议执行规则：

- `PASS` 直接推进
- `RETRYABLE_FAIL` 自动重试限定次数
- `LOW_CONFIDENCE` 进入人工队列
- `HARD_FAIL` 停止并记录 root cause

阶段二的关键不是减少人工本身，而是把“需要人工”的条件精确定义。

阶段二放行条件：

- 80% 以上正常 episode 无需逐阶段人工确认
- 人工介入点压缩到 2 次以内
- 自动重试不引发无限循环
- 异常任务能进入统一队列而不是散落日志

## 7.3 阶段三：无人工干预版

目标：

- 对白名单题材、白名单平台、白名单模板实现批量无人值守

前提：

- 题材风险可控
- 模板稳定
- 角色资产库成熟
- 审核阈值已经通过足够样本验证

这里的“无人工干预”建议限定为：

- 生产运行过程中无人工
- 不是取消前期策略配置、账号准备和内容白名单

阶段三必须新增：

- 自动 episode 排产
- 自动模板选择
- 自动阈值调优
- 自动失败归因聚类
- 自动生成下轮优化建议

阶段三的核心不是“彻底不要人”，而是：

- 人从执行环路退出
- 人只维护策略、模板和边界

阶段三放行条件：

- 批量运行成功率稳定
- 回退与熔断机制可靠
- 失败任务不会污染资产库
- 输出质量波动在可接受范围内

## 8. 子阶段调试设计

每个子阶段都必须具备固定的调试入口。

## 8.1 调试原则

- 每个阶段都有独立命令
- 每个阶段都有独立输入目录
- 每个阶段都有独立输出目录
- 每个阶段都有独立日志
- 每个阶段都有独立 acceptance gate

## 8.2 推荐调试矩阵

| 子阶段 | 当前主入口 | 最小输入 | 关键输出 | 常见问题 | 首先检查 |
| --- | --- | --- | --- | --- | --- |
| 知识库建档 | 新增 `knowledge build` | 章节文本 | `context-pack` | 分类错、设定漏提 | `chapter_extractions` |
| 角色锚定 | 新增 `character-anchor` | 剧本 + context | `character-anchor-pack.json` | 人设漂移 | `character-review.json` |
| 分镜生成 | 复用/新增 `build-storyboard` | 剧本 + anchor pack | `shot-plan.json` | shot 结构不稳 | `storyboard validation` |
| 图片任务打包 | 新增 `package-image-tasks` | shot plan | `image-tasks.json` | prompt 缺字段 | task schema |
| 图片执行 | `zaomeng run` | `image-tasks.json` | 下载图 + run summary | 平台提交失败 | operator logs |
| 图片审核 | 新增 `review-shot-images` | 图片集 | `image-review.json` | 错图漏拦 | score 明细 |
| 连续性检查 | 新增 `check-continuity` | pass 图集 | `continuity-report.json` | 帧间不连续 | pair evidence |
| 视频执行 | 新增 `video-runner` | video input pack | 视频文件 | 上传/下载失败 | video operator logs |
| 音频生成 | 新增 `build-audio` | 剧本对白 | `tts-manifest.json` | 时长不准 | duration compare |
| 最终合成 | 新增 `render-episode` | 视频+音频 | `final-manifest.json` | 字幕错位 | render report |

## 8.3 故障定位规则

建议统一使用“最先失败阶段负责”原则。

示例：

- 如果 `image-runner` 成功、`image-review` 失败，责任归 `image-review`
- 如果 `continuity-checker` 发现角色引用缺失，责任反查到 `character-anchor` 或 `task-packager`
- 如果最终视频节奏差，但上游结构都通过，责任先归 `video-runner` 和 `audio-runner`

## 9. 自我成长架构

“自我成长”必须工程化，不建议写成一个模糊的自治 Agent。

建议拆成 4 条成长回路。

## 9.1 知识成长回路

输入：

- 新章节
- 已跑过的 episode
- 人工修订记录

输出：

- 更稳的 `story_bible`
- 更稳的 `continuity_rules`
- 更准的题材与视觉标签

## 9.2 资产成长回路

输入：

- 通过审核的角色图、场景图、镜头图、视频

输出：

- 更稳的参考图包
- 更好的模板角色
- 更精细的 reference pack

## 9.3 评分成长回路

输入：

- 自动评分结果
- 人工复核结果
- 最终是否被采用

输出：

- 阈值调整建议
- 误杀样本池
- 漏检样本池

## 9.4 Prompt / Policy 成长回路

输入：

- 失败样本
- 高分样本
- 平台异常样本

输出：

- prompt 模板版本升级
- 负面词和风格模板升级
- 平台动作策略升级

## 9.5 成长数据目录建议

```text
project_data/
  learning/
    experiments/
    failed_cases/
    accepted_cases/
    score_history/
    policy_versions/
    prompt_versions/
    threshold_reports/
```

## 10. 推荐目录规划

建议在根目录统一成下面这套布局。

```text
docs/
  action/
    00-README.md
    01-VideoOnlyOnce-三阶段工程化落地方案.md

project_data/
  novels/
  scripts/
  knowledge_base/
  style_presets/
  learning/

outputs/
  ep01/
    intake/
    character/
    storyboard/
    image_tasks/
    image_run/
    image_review/
    continuity/
    video_run/
    audio/
    render/

assets/
  registry/
  library/
  manifests/

downloads/
  staging/
  images/
  videos/

logs/
  orchestrator/
  stages/
  operators/
```

## 11. 对现有仓库的落地方式

## 11.1 现阶段直接复用

- `fenjing_program/src/feicai_seedance/cli.py`
- `fenjing_program/src/feicai_seedance/pipeline.py`
- `fenjing_program/src/feicai_seedance/asset_registry.py`
- `fenjing_program/src/feicai_seedance/structured_protocols.py`
- `zaomeng/src/zaomeng_automation/cli.py`
- `zaomeng/src/zaomeng_automation/orchestrator.py`
- `zaomeng/src/zaomeng_automation/browser/openclaw.py`

## 11.2 第一批建议新增命令

建议先不要引入复杂 runtime，先补 CLI。

推荐新增：

```bash
python -m feicai_seedance.cli knowledge-build <book_id>
python -m feicai_seedance.cli extract-characters <book_id> <ep>
python -m feicai_seedance.cli build-character-sheets <book_id> <ep>
python -m feicai_seedance.cli export-character-image-tasks <book_id> <ep>
python -m feicai_seedance.cli review-character-images <book_id> <ep>
python -m feicai_seedance.cli build-storyboard <book_id> <ep>
python -m feicai_seedance.cli package-image-tasks <book_id> <ep>
python -m feicai_seedance.cli review-shot-images <book_id> <ep>
python -m feicai_seedance.cli check-continuity <book_id> <ep>
python -m feicai_seedance.cli build-audio <book_id> <ep>
python -m feicai_seedance.cli render-episode <book_id> <ep>
```

`zaomeng` 建议补：

```bash
python -m zaomeng_automation.cli run --config workflow/configs/project.json --browser mock
python -m zaomeng_automation.cli run --config workflow/configs/project.json --browser openclaw
```

后续如果接 `LangGraph`，应把这些命令包成 graph nodes，不要推倒重来。

## 12. 推荐实施顺序

## 12.1 第 1 批

先完成阶段一最关键的 4 件事：

1. 知识库输出 `context-pack`
2. 角色锚定输出 `character-anchor-pack`
3. 图片执行结果自动回写 registry
4. continuity 输出结构化报告

## 12.2 第 2 批

再补阶段二需要的能力：

1. 异常队列
2. 自动重试
3. gate router
4. episode 级状态机

## 12.3 第 3 批

最后再做阶段三：

1. 批处理排产
2. 自动模板选择
3. 阈值自动调整
4. 失败聚类和优化建议

## 13. 成功标准

如果这套工程方案成立，最终应该出现下面这些结果：

- 新增一个子阶段时，不需要重写全链路
- 某个子阶段失败时，10 分钟内能定位到责任模块
- 从阶段一升到阶段二，主要是调 gate 和策略，不是推翻架构
- 从阶段二升到阶段三，主要是提升规则和阈值，不是改系统边界
- 所有成长都能回溯到真实数据，而不是依赖主观印象

## 14. 最终结论

对当前项目，最稳的路线不是“直接做一个全自动总 Agent”，而是：

- 让 `fenjing_program` 继续做总控与结构化中枢
- 让 `zaomeng + OpenClaw` 继续做受控执行层
- 用 `contract + gate + evidence + learning loop` 做真正的工程骨架

这样可以同时满足：

- 第一阶段能落地
- 第二阶段能把人工压缩到 2 次以内
- 第三阶段具备走向无人值守的架构可能

并且整套系统在任何阶段都保留：

- 可拆分
- 可调试
- 可审计
- 可持续演进
