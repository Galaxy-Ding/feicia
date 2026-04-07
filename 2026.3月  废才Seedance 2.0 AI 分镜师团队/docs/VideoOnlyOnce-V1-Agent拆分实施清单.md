# VideoOnlyOnce V1 Agent 拆分实施清单

## 1. 文档目的

本文件不是调研文档，而是第一版落地清单。

目标只有一个：

- 把 `VideoOnlyOnce` 拆成一组可以分阶段实现、分阶段验收的 Agent 与执行模块

本清单直接面向开发，不再讨论大而泛的行业方案。

相关文档：

- [VideoOnlyOnce-OpenClaw适配Agent与角色试验建议.md](/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/docs/VideoOnlyOnce-OpenClaw适配Agent与角色试验建议.md)
- [VideoOnlyOnce-全流程两阶段实施方案.md](/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/docs/VideoOnlyOnce-全流程两阶段实施方案.md)
- [VideoOnlyOnce-角色锚定资产流水线设计.md](/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/docs/VideoOnlyOnce-角色锚定资产流水线设计.md)
- [VideoOnlyOnce-小说分类扩展与知识库Agent设计.md](/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/docs/VideoOnlyOnce-小说分类扩展与知识库Agent设计.md)

## 2. V1 总原则

V1 只做三件事：

1. 角色稳定
2. 分镜稳定
3. 图片与前后帧筛选稳定

V1 暂不追求：

- 全自动长篇小说改编
- 全自动视频成片闭环
- 全自动法务/版权判断
- 每个岗位都变成独立自治 Agent

V1 的判断标准不是“Agent 数量多不多”，而是：

- 每个模块边界是否清楚
- 输入输出是否结构化
- 失败点是否可定位
- 能否逐步接入 `OpenClaw`

## 3. V1 目标架构

```text
script / knowledge base
  -> Character Anchor Agent
  -> Storyboard Director Agent
  -> Prompt Packaging Agent
  -> Review / Critic Agent
  -> Continuity Checker
  -> OpenClaw Browser Runner
  -> asset registry / evidence store
```

其中：

- 前 5 个是业务 Agent
- `OpenClaw Browser Runner` 是执行器
- registry 和 evidence store 是基础设施

## 4. V1 只保留的 6 个核心模块

## 4.1 `character-anchor`

### 作用

- 识别当前集人物
- 建角色卡
- 产出角色锚定 prompt
- 为后续分镜提供稳定角色引用包

### 对应现有基础

- `fenjing_program`
- [VideoOnlyOnce-角色锚定资产流水线设计.md](/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/docs/VideoOnlyOnce-角色锚定资产流水线设计.md)

### 输入

- 单集剧本
- `character_bible.md`
- 小说知识库角色实体

### 输出

- `outputs/<ep>/characters/character-candidate-list.json`
- `outputs/<ep>/characters/character-sheets.json`
- `outputs/<ep>/characters/character-sheets.md`
- `outputs/<ep>/characters/character-image-tasks.json`
- `outputs/<ep>/characters/character-anchor-pack.json`

### 阻断门

- 主角缺失外观锚点
- 主角默认服装不明确
- 主角没有标准视图任务

### V1 必做

- `extract-characters`
- `build-character-sheets`
- `export-character-image-tasks`

### V1 可后置

- 自动补群演模板扩展
- 跨集角色演化追踪

## 4.2 `storyboard-director`

### 作用

- 把剧本拆成镜头级结构
- 生成镜头意图、动作、空间、机位、节奏
- 为每个镜头挂接角色资产和场景资产

### 对应现有基础

- `fenjing_program start`
- `fenjing_program prompt`

### 输入

- 单集剧本
- `character-anchor` 已通过的角色资产
- `scene_bible.md`
- 项目风格配置

### 输出

- `outputs/<ep>/storyboard/storyboard.json`
- `outputs/<ep>/storyboard/storyboard.md`
- `outputs/<ep>/storyboard/shot-asset-map.json`

### 阻断门

- 镜头没有角色引用
- 镜头没有场景描述
- 镜头文本无法映射到可执行图片任务

### V1 必做

- 镜头拆解 schema 固定
- 每个镜头都有 `shot_id`
- 每个镜头都有角色、场景、动作、镜头目标字段

### V1 可后置

- 高级导演风格模板
- 自动多版本镜头重写

## 4.3 `prompt-packager`

### 作用

- 把分镜结构、角色资产、场景资产打包成平台可执行 prompt
- 区分图片 prompt 和视频 prompt

### 对应现有基础

- `fenjing_program` prompt builders
- `zaomeng` workflow prompt 输入层

### 输入

- `storyboard.json`
- `character-anchor-pack.json`
- 场景资产或场景提示词

### 输出

- `outputs/<ep>/prompt/image-tasks.json`
- `outputs/<ep>/prompt/video-tasks.json`
- `outputs/<ep>/prompt/prompt-pack-report.md`

### 阻断门

- 缺少角色引用编号
- 缺少平台约束字段
- prompt 未标明镜头归属

### V1 必做

- 固定 prompt 模板
- 固定字段：
  - `task_id`
  - `episode`
  - `shot_id`
  - `prompt`
  - `characters`
  - `scene_refs`
  - `intended_role`

### V1 可后置

- 多平台 prompt 适配
- 自动风格强化/弱化重写

## 4.4 `review-critic`

### 作用

- 对图片与前后帧做结构化评分
- 决定通过、驳回、待人工

### 对应现有基础

- `zaomeng` 中的 `Review Agent` 位置
- 现有评分结构设计

### 输入

- 图片路径
- prompt
- shot 上下文
- 角色引用包

### 输出

- `reviews/<task_id>.json`
- `reviews/<task_id>.md`
- 聚合结果 `outputs/<ep>/review/review-summary.json`

### 阻断门

- 未能判断 `pass / reject / pending_manual`
- 未给出分项问题
- 评分结果不能映射到下一步筛选

### V1 必做

- 评分维度固定：
  - 构图
  - 人物一致性
  - 场景一致性
  - 镜头叙事有效性
  - 前后帧稳定性
- 输出固定字段：
  - `overall_score`
  - `dimension_scores`
  - `pass`
  - `issues`
  - `recommended_role`

### V1 可后置

- 视频段落级评分
- 自动审片意见合并

## 4.5 `continuity-checker`

### 作用

- 检查前后镜头和前后帧之间的连续性
- 确认是否可以进入视频阶段

### 对应现有基础

- 现有文档中的 `continuity rules`
- `小说分类扩展与知识库Agent设计` 中提到的 continuity 设计方向

### 输入

- 候选前帧
- 候选后帧
- `storyboard.json`
- `character-anchor-pack.json`

### 输出

- `outputs/<ep>/continuity/frame-pair-report.json`
- `outputs/<ep>/continuity/frame-pair-report.md`
- `outputs/<ep>/continuity/approved-frame-pairs.json`

### 阻断门

- 同角色出现明显串脸
- 服饰、持物、时间段不连续
- 无法形成可提交视频的 `pre/post` 对

### V1 必做

- 只检查最关键的 5 类连续性：
  - 人物
  - 服装
  - 手持物
  - 场景空间
  - 光线时段

### V1 可后置

- 多镜头长程 continuity
- 剪辑节奏 continuity

## 4.6 `openclaw-browser-runner`

### 作用

- 打开即梦网页
- 提交图片/视频任务
- 轮询完成
- 下载结果

### 对应现有基础

- [openclaw.py](/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/zaomeng/src/zaomeng_automation/browser/openclaw.py)
- `zaomeng` Browser Operator 架构

### 输入

- `image-tasks.json`
- `video-tasks.json`
- 浏览器 profile 配置

### 输出

- `downloads/staging/...`
- `downloads/images/...`
- `downloads/videos/...`
- `logs/...`

### 阻断门

- 登录态失效
- 页面结构失效
- 下载失败

### V1 必做

- 图片页提交
- 图片下载
- 视频页提交
- 视频下载
- 失败重试
- 证据截图

### V1 可后置

- 更复杂的网页自愈定位
- 多账号调度

## 5. 模块间固定边界

V1 必须遵守以下边界：

## 5.1 `character-anchor` 不做什么

- 不负责网页操作
- 不负责评分
- 不负责视频生成

## 5.2 `storyboard-director` 不做什么

- 不重新发明角色设定
- 不直接操作浏览器
- 不自己决定图片是否通过

## 5.3 `prompt-packager` 不做什么

- 不改剧情
- 不做审美打分
- 不管理下载文件

## 5.4 `review-critic` 不做什么

- 不自己出图
- 不自己提交网页任务
- 不直接重命名原图

## 5.5 `continuity-checker` 不做什么

- 不替代单图评分
- 不直接生成视频

## 5.6 `openclaw-browser-runner` 不做什么

- 不做剧情判断
- 不做角色判断
- 不做质量判断

## 6. V1 开发顺序

建议不要并行做满 6 个模块，而是按依赖顺序推进。

## 6.1 第一阶段

1. `character-anchor`
2. `review-critic`

目标：

- 先证明主角角色包能稳定产出并通过审核

交付物：

- 角色候选提取
- 角色卡
- 角色出图任务
- 角色图审核结果

## 6.2 第二阶段

1. `storyboard-director`
2. `prompt-packager`

目标：

- 先证明单集 5 到 8 个镜头可以稳定变成图片任务

交付物：

- `storyboard.json`
- `shot-asset-map.json`
- `image-tasks.json`

## 6.3 第三阶段

1. `openclaw-browser-runner`
2. `review-critic`

目标：

- 先证明图片生成、下载、筛选能形成闭环

交付物：

- 规范图片下载目录
- 评分结果
- 通过/驳回分流

## 6.4 第四阶段

1. `continuity-checker`
2. `openclaw-browser-runner`

目标：

- 先证明前后帧进入视频阶段前有一道明确质量门

交付物：

- `approved-frame-pairs.json`
- 试跑视频结果

## 7. V1 文件与目录建议

如果要正式实现 Agent 拆分，建议先统一目录约定。

## 7.1 `fenjing_program`

建议新增：

```text
src/feicai_seedance/agents/
  character_anchor.py
  storyboard_director.py
  prompt_packager.py
  continuity_checker.py
src/feicai_seedance/schemas/
  character_schema.py
  storyboard_schema.py
  prompt_task_schema.py
  continuity_schema.py
```

## 7.2 `zaomeng`

建议新增或强化：

```text
src/zaomeng_automation/review/
  critic.py
  schemas.py
src/zaomeng_automation/evidence/
  capture.py
```

## 7.3 `docs`

建议持续维护：

```text
docs/
  VideoOnlyOnce-V1-Agent拆分实施清单.md
  VideoOnlyOnce-角色锚定资产流水线设计.md
  VideoOnlyOnce-OpenClaw适配Agent与角色试验建议.md
```

## 8. V1 CLI 建议

V1 不需要一上来就引入真正的复杂多 Agent runtime。
先把每个 Agent 变成清晰的 CLI 子命令更稳。

说明：

- `extract-characters`、`build-character-sheets`、`export-character-image-tasks`、`review-character-images` 在现有文档中已经有清晰定义
- `build-storyboard`、`package-image-prompts`、`review-shot-images`、`check-continuity` 目前是本清单建议新增的命令名

建议命令：

```bash
python -m feicai_seedance.cli extract-characters <book_id> <ep>
python -m feicai_seedance.cli build-character-sheets <book_id> <ep>
python -m feicai_seedance.cli export-character-image-tasks <book_id> <ep>
python -m feicai_seedance.cli generate-character-images <book_id> <ep> --browser <mock|openclaw>
python -m feicai_seedance.cli review-character-images <book_id> <ep>
python -m feicai_seedance.cli build-storyboard <book_id> <ep>
python -m feicai_seedance.cli package-image-prompts <book_id> <ep>
python -m feicai_seedance.cli review-shot-images <book_id> <ep>
python -m feicai_seedance.cli check-continuity <book_id> <ep>
```

后面如果要接 `LangGraph`，也是把这些 CLI 或函数节点包成 graph node，而不是推倒重来。

## 9. V1 验收清单

以下项目全部满足，才算 V1 Agent 拆分成功。

## 9.1 角色锚定

- [ ] 主角可生成标准视图任务
- [ ] 主角至少 3 张标准视图审核通过
- [ ] 至少 1 张黄金样例入库
- [ ] `character-anchor-pack.json` 可供后续镜头引用

## 9.2 分镜结构

- [ ] 单集至少能稳定输出 5 个镜头
- [ ] 每个镜头都有 `shot_id`
- [ ] 每个镜头都有角色、场景、动作字段
- [ ] 每个镜头都能映射到图片任务

## 9.3 出图与评分

- [ ] 图片任务可以送入 `zaomeng`
- [ ] 图片下载后有规范命名与元数据
- [ ] 每张图都有结构化评分结果
- [ ] 评分结果能自动分流到 pass/reject/pending_manual

## 9.4 连续性

- [ ] 至少形成 3 组可用前后帧
- [ ] continuity 报告能指出具体问题
- [ ] 通过的帧对能直接进入视频试跑

## 10. 第一版任务分配建议

如果你要把团队工作拆开，建议按下面分，不要按“每人一个大而全 Agent”去分。

## 10.1 文本与结构侧

- `character-anchor`
- `storyboard-director`
- `prompt-packager`

## 10.2 审核与规则侧

- `review-critic`
- `continuity-checker`

## 10.3 执行与证据侧

- `openclaw-browser-runner`
- evidence capture
- asset registry

## 11. 最终建议

V1 不要试图证明：

- “我们已经有完整 AI 制片厂”

V1 应该只证明：

1. 角色锚定能稳定产出
2. 分镜能稳定挂接资产
3. 图片任务能稳定执行与评分
4. 前后帧能形成可控视频输入

如果这四件事做稳了，再接真正的多 Agent 编排框架，成本会低很多，失败定位也会清楚很多。
