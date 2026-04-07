# 系统架构

## 1. 当前架构问题

当前架构分层是正确的，但规则落点偏软：

- `CLAUDE.md + agents + skills` 负责方法论。
- `pipeline.py` 负责流程编排。
- `artifact_utils.py` 负责结构检查。
- `review_store.py` 负责报告和推荐。

问题在于：

- 方法论集中在 Prompt 文本，不在可执行规则层。
- 审核结论缺少结构化判定核心。
- 资产层只有 Markdown，没有真实素材对象。

## 2. 目标架构

### 2.1 分层

- 流程层：`Pipeline / CLI / Status Router`
- 协议层：`schemas / structured review payloads / asset manifest`
- 规则层：`director validators / asset validators / seedance validators / compliance rule registry`
- 资产层：`prompt assets / generated reference assets / manifest / mapping`
- 报告层：`reviews / assessments / acceptance / traceability`

## 3. 核心模块

### 3.1 Director Schema Engine

负责把导演产物拆成：

- Markdown 成文
- 可校验结构化对象

结构化对象至少包含：

- episode
- plot_points[]
- character_list[]
- scene_list[]

### 3.2 Asset Registry

负责全局资产唯一标识与状态管理。

建议对象：

- `character_assets`
- `scene_assets`
- `scene_panels`

每条资产记录至少包含：

- `asset_id`
- `asset_type`
- `name`
- `episode_origin`
- `status`
- `prompt_text_path`
- `image_path`
- `variant_of`

### 3.3 Reference Material Manager

负责区分两类资产：

- 提示词资产：还没有图
- 可引用资产：图已生成并已登记

只有“可引用资产”才能进入 Storyboard 对应表。

### 3.4 Structured Review Engine

审核输出改为 JSON 协议，不再由 `review_store.py` 从自然语言里猜分。

### 3.5 Seedance Validator

负责检查：

- 引用边界
- 场景拆图独立性
- 节拍密度
- 安全区
- 叙述连续性
- 音频设计完整度

### 3.6 Session Context Manager

把 `sessions.py` 中的历史真正纳入调用上下文，支持：

- 续写
- 修订
- 审核复盘

## 4. 目标数据流

1. 导演阶段读取剧本，产出 Markdown + Director JSON。
2. Director Validator 校验失败则回修。
3. 服化道阶段读取导演 JSON 和资产注册表，只为新增 / 变体生成内容。
4. 设计完成后登记到资产注册表，等待人工出图。
5. 人工生成参考图后，将图片登记到 registry。
6. Storyboard 阶段只使用“已登记图片资产”建立 `@引用` 映射。
7. Seedance Validator 和 Structured Review Engine 联合验收。
8. 通过后写入最终产物与追踪报告。

## 5. 架构原则

- 规则单一来源：同一规则不能只存在于 Skill 文本。
- 结构与成文分离：Markdown 用于阅读，JSON 用于校验。
- 资产实体化：引用对象必须是资产，不是段落文字。
- 审核结果可计算：通过与否必须来自结构化字段。
