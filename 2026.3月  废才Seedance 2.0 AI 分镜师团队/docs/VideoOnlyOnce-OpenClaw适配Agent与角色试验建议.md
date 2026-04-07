# VideoOnlyOnce OpenClaw 适配 Agent 与角色试验建议

## 1. 文档目的

本文件回答三个问题：

- 对当前 `VideoOnlyOnce` 项目而言，`OpenClaw` 适合放在什么位置
- 结合中英文检索结果，哪些 Agent 框架更适合接在 `OpenClaw` 之上
- 哪些“角色型 Agent”最值得先在你当前项目里尝试

调研日期：

- 2026-03-26

相关内部文档：

- [VideoOnlyOnce-Agent框架与行业方案调研.md](/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/docs/VideoOnlyOnce-Agent框架与行业方案调研.md)
- [VideoOnlyOnce-全流程两阶段实施方案.md](/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/docs/VideoOnlyOnce-全流程两阶段实施方案.md)
- [VideoOnlyOnce-角色锚定资产流水线设计.md](/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/docs/VideoOnlyOnce-角色锚定资产流水线设计.md)
- [03-system-architecture.md](/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/zaomeng/docs/ALL/03-system-architecture.md)
- [04-detailed-design.md](/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/zaomeng/docs/ALL/04-detailed-design.md)

## 2. 先给结论

### 2.1 `OpenClaw` 适合做“执行层”，不适合做你的总编排层

基于 `OpenClaw` 官方文档和你仓库里的 `zaomeng` 实现，我的判断是：

- `OpenClaw` 很适合承担浏览器执行、技能装配、网页自动化和本地工具调用
- `OpenClaw` 不适合直接承担 `VideoOnlyOnce` 全链路的状态化生产编排
- 对你最合理的结构是：
  - 上层：工作流/状态机/多 Agent 编排
  - 下层：`OpenClaw Browser Operator` 负责即梦网页动作

换句话说：

- `OpenClaw` 更像“浏览器执行员”
- 不是“总制片 + 总导演 + 审片主管”

### 2.2 真正比较好用的，不是一个万能 Agent，而是“6 个核心角色 + 1 个执行器”

最值得先试的角色型 Agent 是：

1. `Producer / Orchestrator Agent`
2. `Character Anchor Agent`
3. `Storyboard Director Agent`
4. `Prompt Packaging Agent`
5. `Review / Critic Agent`
6. `Continuity Agent`
7. `OpenClaw Browser Runner`

其中前 6 个是“上层智能角色”，最后 1 个是“下层执行角色”。

### 2.3 如果只做一轮最小可行试验，优先顺序应该是

1. `Character Anchor Agent`
2. `Storyboard Director Agent`
3. `Review / Critic Agent`
4. `OpenClaw Browser Runner`
5. `Continuity Agent`
6. `Producer / Orchestrator Agent`

原因很简单：

- 你现在最缺的不是“再多一个聊天 Agent”
- 而是“角色稳定 + 分镜稳定 + 出图复核 + 前后帧稳定”

## 3. 本次中英文检索范围

## 3.1 中文关键词

- `OpenClaw 浏览器 自动化`
- `OpenClaw skill`
- `多智能体 分镜 视频生成`
- `故事视频生成 角色一致性`
- `AI 分镜师 Agent`

### 结论

- 中文网页能搜到一些二手介绍和项目复述
- 但一手资料明显不如英文完整
- 真正可直接用于工程判断的资料，仍然主要来自：
  - 英文官方文档
  - arXiv 论文摘要
  - 项目官方仓库/官方文档

## 3.2 英文关键词

- `OpenClaw browser official`
- `OpenClaw skills official`
- `OpenClaw browser login official`
- `LangGraph durable execution human in the loop`
- `Microsoft Agent Framework workflows checkpointing`
- `AutoGen AgentChat GraphFlow`
- `CrewAI flows state`
- `StoryAgent storytelling video generation`
- `MM-StoryAgent`
- `AniMaker storytelling animation`
- `The Script is All You Need agentic cinematic video`

## 4. `OpenClaw` 在你项目里的正确定位

## 4.1 官方文档给出的能力边界

从 `OpenClaw` 官方文档看，它当前明确擅长：

- 独立浏览器 profile
- 浏览器页面打开、点击、输入、截图、下载
- skills 加载与覆盖
- 本地工具和 agent run 期间的环境注入

对你有直接价值的点：

- 适合做即梦图片页/视频页的网页动作执行
- 适合把项目私有 skill 放在 workspace 里覆盖公共 skill
- 适合把同一套浏览器动作封装成稳定 skill 反复复用

## 4.2 官方文档给出的风险边界

对你特别重要的两条官方建议：

- 登录推荐人工完成，不要把账号密码直接交给模型
- 第三方 skills 视为不可信代码，启用前必须审查

这和你仓库里当前的设计是一致的：

- `zaomeng` 已经把“首次登录人工完成，后续自动化复用登录态”作为架构前提
- 这条路线应该保留，不要反过来做成“模型全自动登录”

## 4.3 对应你仓库的实际映射

你仓库里已经有非常清晰的边界：

- `fenjing_program`
  - 负责剧本理解、角色/场景设计、分镜 prompt 生成
- `zaomeng`
  - 负责即梦网页自动化、下载、归档、评分、视频生成
- `OpenClawBrowserOperator`
  - 已经非常明确地被实现为浏览器执行层

所以不建议把架构改成：

- `OpenClaw` 直接统领全项目

建议保持为：

- 上层编排器调度 `fenjing_program`
- 上层编排器在需要出图/出视频时调用 `zaomeng`
- `zaomeng` 内部再调用 `OpenClawBrowserOperator`

## 5. 哪些 Agent 框架更适合接在 `OpenClaw` 之上

## 5.1 推荐排序

1. `LangGraph`
2. `Microsoft Agent Framework`
3. `AutoGen`
4. `CrewAI`

## 5.2 为什么 `LangGraph` 仍然最适合你

官方文档到 2026 年仍然强调三件事：

- long-running, stateful agents
- durable execution
- human-in-the-loop / interrupts

这正好对应你的核心工程需求：

- 剧本到视频是长链路任务
- 中间产物很多
- 人工审核点很多
- 任意节点都可能失败重试

把 `LangGraph` 接在 `OpenClaw` 上的方式应该是：

- `LangGraph` 负责状态图、恢复点、人工阻断点
- `OpenClaw` 只是其中一个工具节点或执行节点

## 5.3 为什么 `Microsoft Agent Framework` 值得排第二

Microsoft 官方文档已经明确把它定位为：

- AutoGen 与 Semantic Kernel 的直接继承者
- 同时提供 `Agents` 和 `Workflows`
- 支持 graph-based workflows、checkpointing、human-in-the-loop、session state

它和 `VideoOnlyOnce` 的匹配点非常强：

- 工作流是显式图，而不是纯对话串联
- 有企业化状态、路由、中间件、会话概念
- 比较适合未来你把本项目从原型推进到正式系统

当前限制也要说清楚：

- 目前仍处于 public preview
- 社区里“影视/分镜”现成案例仍少于 LangGraph

## 5.4 为什么 `AutoGen` 适合做原型，不建议做你的主干

AutoGen 官方文档现在仍然很适合做：

- 多角色协作原型
- AgentChat
- selector/group chat
- GraphFlow 工作流试验

但它更适合验证：

- “导演 + 审稿 + 评分”这种角色协作是否有效

不如前两者适合承担：

- 长链路生产状态机
- 强恢复点
- 强人工审核门

## 5.5 为什么 `CrewAI` 可用，但更适合“角色表达层”

CrewAI 官方文档这两年补了很多：

- crews
- flows
- state
- memory
- training

它已经不是早期那种只会“角色扮演串对话”的形态了。

但对你这个项目，我仍然把它放第四，是因为：

- 你的难点不是“角色名字起得像不像”
- 而是“状态、资产、审核、恢复、引用关系能不能稳”

所以如果用 `CrewAI`，更适合：

- 做一层业务表达清晰的角色外壳
- 不适合做系统最底层的主状态机

## 6. 哪些“人物/角色 Agent”最 work

这里的“人物”我按“专业岗位型 Agent”理解，因为这和你项目的实际工程结构最匹配。

## 6.1 P0：必须先试的 5 个角色

### A. `Character Anchor Agent`

职责：

- 从小说/剧本提取人物
- 建角色卡
- 提炼固定外观锚点
- 输出标准视图 prompt
- 校验角色图是否达到 `anchor_ready`

为什么最 work：

- 你后面几乎所有问题都会先死在角色漂移上
- 这个角色与现有 [VideoOnlyOnce-角色锚定资产流水线设计.md](/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/docs/VideoOnlyOnce-角色锚定资产流水线设计.md) 完全同向
- 也是最容易形成结构化输入输出的一环

最适合先做成：

- 强 schema agent
- 输出 JSON + Markdown 双份结果

### B. `Storyboard Director Agent`

职责：

- 把当前集剧本拆成镜头
- 产出镜头意图、人物动作、场景信息、机位、镜头调度
- 明确每个镜头要引用哪些角色锚定资产和场景资产

为什么很 work：

- 这正是 `fenjing_program` 当前已有能力的自然升级方向
- 论文里最稳定重复出现的角色之一就是 `storyboard` / `director`

注意点：

- 这个角色不能自己随便重新发明人物设定
- 它必须消费 `Character Anchor Agent` 的已通过资产

### C. `Review / Critic Agent`

职责：

- 对图片、前后帧、短视频做结构化评分
- 输出通过、驳回、需人工确认
- 指出具体问题项，而不是只给一句“不错”

为什么很 work：

- 你 `zaomeng` 已经有 `Review Agent` 架构位置
- 论文里 `evaluation / reviewer / critic` 角色反复出现
- 这是把“候选生成”变成“可控筛选”的关键环节

必须坚持的原则：

- 不让执行网页动作的角色同时担任评分角色

### D. `OpenClaw Browser Runner`

职责：

- 只负责即梦网页动作
- 不负责审美判断
- 不负责剧情判断
- 不负责角色设定

为什么很 work：

- 边界清晰
- 失败原因清晰
- 容易重试和落证据
- 与当前 `OpenClawBrowserOperator` 完全一致

### E. `Continuity Agent`

职责：

- 检查前后镜头之间的人物一致性
- 检查服饰、姿态、手持物、光线时段、空间连续性
- 检查前后帧是否能安全送进视频阶段

为什么值得尽快加入：

- 研究系统普遍证明“单张图好看”不等于“长链路视频可用”
- 你后续视频生成最容易在这一层翻车

## 6.2 P1：第二批值得加的 4 个角色

### F. `Producer / Orchestrator Agent`

职责：

- 管状态机
- 决定下一步跑哪一阶段
- 决定是否重试、转人工、还是推进到下游

为什么是 P1 不是 P0：

- 你仓库里已经有一部分编排能力
- 先把角色锚定、分镜、评分做好，收益更直接

### G. `Prompt Packaging Agent`

职责：

- 把分镜信息、角色资产、场景资产、镜头目的合并成最终平台 prompt
- 生成适合图片阶段和视频阶段的不同 prompt 模板

为什么有价值：

- 很多失败并不是分镜错，而是 prompt 打包错
- 它可以把“导演语言”转成“平台可执行语言”

### H. `Asset Librarian Agent`

职责：

- 管角色引用包
- 管场景引用包
- 管黄金样例、变体样例、前后帧素材池

为什么有价值：

- 你的项目不是一次性生成，而是资产累积型项目
- 这个角色能防止后续多人或多 Agent 把同一角色反复造新图

### I. `Dialogue / TTS Prep Agent`

职责：

- 从剧本和分镜中提炼对白
- 标记谁在说话
- 输出 TTS 所需台词、情绪、停顿、语速、时长建议

为什么可以晚一点：

- 目前主矛盾还在视觉链路稳定性

## 6.3 P2：暂时不要优先投入的角色

### 不建议 1：`万能总导演 Agent`

问题：

- 它会把角色锚定、分镜、审片、执行全部混在一起
- 一旦结果差，你很难知道是哪一层出了问题

### 不建议 2：`浏览器执行 + 评分二合一 Agent`

问题：

- 会产生明显自评偏差
- 也不利于证据沉淀和责任归因

### 不建议 3：`每个群演一个独立角色 Agent`

问题：

- 成本太高
- 维护毫无必要
- 你文档里已经正确指出群众角色应当模板化

### 不建议 4：`全自动法务改编 Agent`

问题：

- 这是高风险岗位
- 当前公开系统没有成熟可靠的自动闭环

## 7. 从论文里能提炼出的共同规律

中英文一手资料虽然分散，但有几个规律非常一致。

## 7.1 有效系统都不是“一个 Agent 包打天下”

从 `AesopAgent`、`StoryAgent`、`MM-StoryAgent`、`AniMaker`、`The Script is All You Need` 看，成熟方向都在收敛到：

- 脚本拆解
- 分镜生成
- 视频生成
- 评价/批评
- 协调/状态控制

这和你项目现在的拆分方向是一致的。

## 7.2 `Reviewer / Critic` 几乎是标配

这是很重要的信号：

- 生成不是终点
- 评价与筛选是生产闭环的一半

所以你应该继续强化 `Review Agent`，而不是把它当附属功能。

## 7.3 `Character Consistency` 是故事视频系统的主问题，不是边角问题

不管是 `StoryAgent` 还是 `MM-StoryAgent`，都把角色一致性放在很靠前的位置。

这说明你目前把资源优先放到：

- 角色锚定
- 黄金样例
- 变体样例
- 前后帧一致性

是对的。

## 7.4 `候选生成 + 评价筛选` 比“单次一把过”更现实

`AniMaker` 明确把多候选 clip 生成和 reviewer 选择做成正式机制。

这对你的启发非常直接：

- 不要追求每个镜头只生成 1 版
- 应该允许：
  - 多候选图
  - 多候选前后帧
  - 结构化评分后再选

## 8. 对你项目最建议先做的三轮试验

## 8.1 试验一：角色锚定闭环

目标：

- 先证明主角和关键配角能稳定出图并复用

最小角色组合：

- 主角 1 名
- 关键配角 1 名
- 权力对立角色 1 名
- 模板群众角色 1 类

Agent 组合：

- `Character Anchor Agent`
- `Review / Critic Agent`
- `OpenClaw Browser Runner`

通过标准：

- 同角色 4 视图至少 3 张通过
- 至少 1 张黄金样例 + 1 张变体样例入库

## 8.2 试验二：单集分镜到图片闭环

目标：

- 证明从剧本到镜头图的链路可跑通

Agent 组合：

- `Storyboard Director Agent`
- `Prompt Packaging Agent`
- `OpenClaw Browser Runner`
- `Review / Critic Agent`

通过标准：

- 单集挑 5 到 8 个镜头
- 每个镜头至少保留 1 张可用图
- 每张图都能追溯到镜头 ID、角色引用包、评分结果

## 8.3 试验三：前后帧到视频闭环

目标：

- 证明前后帧筛选机制真的能服务视频阶段

Agent 组合：

- `Continuity Agent`
- `OpenClaw Browser Runner`
- `Review / Critic Agent`

通过标准：

- 至少完成 3 个镜头的视频试跑
- 明确哪些失败是前后帧问题，哪些失败是平台视频模型问题

## 9. 最建议落地的工程结构

## 9.1 上层编排

建议首选：

- `LangGraph`

备选：

- `Microsoft Agent Framework`

职责：

- 管长流程状态
- 管人工审核门
- 管恢复点
- 管失败重试

## 9.2 中层业务 Agent

建议先固定这些角色：

- `character-anchor`
- `storyboard-director`
- `prompt-packager`
- `review-critic`
- `continuity-checker`
- `asset-librarian`

## 9.3 下层执行

保留当前方向：

- `zaomeng` 作为即梦执行子系统
- `OpenClawBrowserOperator` 作为浏览器操作层

## 9.4 对应 `OpenClaw` 最值得先做的 5 个私有 skill

这里我不建议你优先去找“公共市场里某个神奇 skill”，而建议直接做项目私有 skill。

原因：

- 你的网页目标、命名规范、证据要求都很项目化
- `OpenClaw` 官方也明确支持本地 skill 覆盖与环境注入
- 第三方 skill 默认应视为不可信

最值得先做的 5 个私有 skill：

### A. `jimeng-image-submit`

职责：

- 打开图片生成页
- 定位 prompt 输入区
- 提交 prompt
- 返回任务 ID、提交时间、页面证据

### B. `jimeng-result-download`

职责：

- 轮询任务完成
- 下载结果图
- 落到 staging 目录
- 返回原始下载文件与任务映射

### C. `jimeng-video-submit`

职责：

- 打开视频生成页
- 上传前后帧
- 提交视频 prompt
- 轮询并下载视频

### D. `artifact-register`

职责：

- 把图片、视频、评分结果写入项目 registry
- 生成规范文件名
- 写入证据路径和来源映射

### E. `evidence-capture`

职责：

- 在关键步骤自动截图
- 保存 DOM 快照、当前 URL、时间戳
- 为失败任务保留回放证据

这 5 个 skill 做好以后，其他 Agent 就不必直接碰网页细节。
它们只需要：

- 发任务
- 收结果
- 做判断

## 10. 对当前项目的最终建议

如果你现在问我：

- “对应 `OpenClaw`，到底哪个 Agent 比较好用？”

我的答案是：

- `OpenClaw` 下面最好用的不是“某个神奇公共 Agent”
- 而是你自己项目内的 5 个业务角色 Agent，加 1 个专门的浏览器执行器

如果你再问：

- “哪些人物最 work？”

我的答案是：

1. `Character Anchor Agent`
2. `Storyboard Director Agent`
3. `Review / Critic Agent`
4. `Continuity Agent`
5. `Prompt Packaging Agent`
6. `OpenClaw Browser Runner`

如果只准先做两件事：

- 第一件：把角色锚定和角色图审核闭环做扎实
- 第二件：把分镜图候选生成和结构化评分闭环做扎实

这两件事做稳了，再去扩展视频、对白、总片，成功率会高很多。

## 11. 参考来源

以下为本次主要参考的一手来源。

### OpenClaw 官方

- Skills: https://docs.openclaw.ai/skills
- Browser: https://docs.openclaw.ai/tools/browser
- Browser Login: https://docs.openclaw.ai/tools/browser-login
- Security: https://docs.openclaw.ai/security
- ClawHub: https://docs.openclaw.ai/clawhub

### Agent 框架官方

- LangGraph overview: https://docs.langchain.com/oss/python/langgraph
- LangGraph durable execution: https://docs.langchain.com/oss/python/langgraph/durable-execution
- LangGraph human-in-the-loop / interrupts: https://docs.langchain.com/oss/python/langgraph/human-in-the-loop
- Microsoft Agent Framework overview: https://learn.microsoft.com/en-us/agent-framework/user-guide/overview
- Microsoft Agent Framework workflows: https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/overview
- AutoGen overview: https://microsoft.github.io/autogen/stable/index.html
- AutoGen AgentChat: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html
- CrewAI Flows: https://docs.crewai.com/en/concepts/flows
- CrewAI Knowledge: https://docs.crewai.com/en/concepts/knowledge

### 论文与研究系统

- AesopAgent: https://arxiv.org/abs/2403.07952
- Mora: https://arxiv.org/abs/2403.13248
- StoryAgent: https://arxiv.org/abs/2411.04925
- MM-StoryAgent: https://arxiv.org/abs/2503.05242
- AniMaker: https://arxiv.org/abs/2506.10540
- The Script is All You Need: https://arxiv.org/abs/2601.17737
