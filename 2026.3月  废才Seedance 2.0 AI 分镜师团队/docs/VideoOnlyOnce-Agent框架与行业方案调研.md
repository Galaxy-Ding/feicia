# VideoOnlyOnce Agent 框架与行业方案调研

## 1. 文档目的

本文件是对 [VideoOnlyOnce-全流程两阶段实施方案.md](/home/galaxy/work/feicia/2026.3月%20%20废才Seedance%202.0%20AI%20分镜师团队/docs/VideoOnlyOnce-全流程两阶段实施方案.md) 的补充调研。

调研目标：

- 现有开源 Agent 框架里，哪些适合搭建 `VideoOnlyOnce`
- 目前闭源产品里，哪些已经接近“输入剧本输出视频”
- 是否已经存在成熟的“输入小说/剧本，直接输出专业叙事视频”的完整体系
- 如果没有，小说改剧本、剧本改视频到底需要哪些专业角色
- 哪些岗位可以由 Agent 替代，哪些岗位必须保留人工

调研日期：

- 2026-03-26

## 2. 先给结论

### 2.1 当前没有公开可验证的“成熟一体化系统”能稳定做到

- 输入长篇小说
- 自动完成合法改编
- 自动完成剧本重写
- 自动完成角色定稿
- 自动完成多镜头一致性视频生成
- 自动完成配音、声音、剪辑、连续性校验
- 直接输出可交付的专业叙事成片

这是我基于官方产品页、官方帮助文档、官方开发文档和近一两年的研究论文做出的结论。

更准确地说：

- 已有很多“脚本到视频”产品
- 已有不少“多 Agent 故事视频研究框架”
- 但公开可验证的成熟体系，大多只覆盖其中一部分链路
- 尤其缺“长篇 IP 改编”“角色一致性长期维护”“影视级连续性”“法务/版权/开发流程”

### 2.2 最接近你目标的，不是单个模型，而是“三层架构”

- 第一层：工作流/Agent 编排框架
- 第二层：图像/视频/语音模型与平台
- 第三层：人工开发与验收岗位

### 2.3 对 `VideoOnlyOnce` 最合理的路线

不是追求一个“全自动神奇 Agent”，而是：

- 用工作流框架编排多 Agent
- 用视频平台做素材生成
- 用知识库和角色锚定资产控制一致性
- 在关键节点保留人工把关

## 3. 开源 Agent 框架调研

## 3.1 最值得关注的通用编排框架

### A. LangGraph

适合度：高

原因：

- 官方明确强调它面向 Agent 编排
- 重点能力包括：
  - `durable execution`
  - `human-in-the-loop`
  - 长时状态
  - 生产级可观测性

为什么适合 `VideoOnlyOnce`：

- 你的流程不是一次 LLM 调用，而是长链路、多阶段、多产物、多人工审核点
- 角色锚定、分镜、图片、视频、TTS、合成都需要状态恢复和阻断推进
- LangGraph 的图式编排比“单纯对话式 Agent”更稳

不够的地方：

- 它是通用框架，不是影视专用框架
- 角色一致性、素材资产、镜头 schema、视频 QA 都得你自己实现

### B. Microsoft Agent Framework

适合度：高

原因：

- 官方文档已经把它定位成 AutoGen 与 Semantic Kernel 的继承者
- 支持：
  - Agents
  - Graph-based workflows
  - type-safe routing
  - checkpointing
  - human-in-the-loop
  - 会话状态与中间件

为什么适合 `VideoOnlyOnce`：

- 你的系统本质上不是“一个智能体”，而是“可控工作流 + 少量自治 Agent”
- 这个框架对企业化编排、状态控制、治理更强

不够的地方：

- 当前仍在 public preview
- 生态和内容创作样例不如 LangGraph 社区丰富

### C. AutoGen

适合度：中高

原因：

- 多 Agent 模式成熟
- 对“多个角色协作解决复杂任务”表达能力强
- 很适合快速原型验证“导演 Agent + 编剧 Agent + 审稿 Agent”

为什么适合 `VideoOnlyOnce`：

- 在前期验证角色协作范式时，效率很高
- 可以快速模拟“小说改编室”

不够的地方：

- 官方仓库已经提示新用户优先看 Microsoft Agent Framework
- 如果要做强工作流、强状态恢复、强人工审核门，最好直接用更新的框架能力

### D. CrewAI

适合度：中

原因：

- 它擅长“角色化协作”
- 很适合把流程直观拆成：
  - 小说分析员
  - 改编编剧
  - 人物设定师
  - 分镜导演
  - 审核员

为什么适合 `VideoOnlyOnce`：

- 适合做业务表达清晰的多角色工作流
- 上手成本较低

不够的地方：

- 影视项目真正麻烦的是状态、资产、审查、恢复，不只是“角色协作”
- 纯 Crew 式设计容易把复杂工程误写成对话式任务链

## 3.2 如果要做 `VideoOnlyOnce`，我建议怎么选

### 推荐排序

1. `LangGraph`
2. `Microsoft Agent Framework`
3. `AutoGen`
4. `CrewAI`

### 推荐原因

`VideoOnlyOnce` 更像：

- 一个状态化内容生产系统

而不是：

- 一个聊天型多 Agent demo

所以优先级应该偏向：

- 强工作流
- 强状态
- 强人工介入
- 强中间产物

而不是先追求“角色扮演感”。

## 4. 开源“故事到视频”相关框架与研究系统

## 4.1 已公开代码的代表

### MM-StoryAgent

定位：

- 多模态、多 Agent 的故事视频生成框架

官方特点：

- 官方仓库明确说它是论文的官方实现
- 通过多 Agent + 多阶段流水线来生成故事、图像、语音、声音和视频
- 用户可以定义自己的 expert tools

为什么有价值：

- 它和你的方向高度相似
- 尤其适合借鉴：
  - 多阶段写作 pipeline
  - 图文音多模态协作
  - 可替换模块设计

局限：

- 研究型系统
- 更偏故事书/叙事视频，不等于影视工业生产系统
- 不能直接当成生产框架拿来就用

## 4.2 研究前沿但不算成熟开源产品

### StoryAgent

定位：

- 面向 customized storytelling video generation 的多 Agent 框架

论文强调：

- 按专业制作流程拆分成 story design、storyboard generation、video creation、coordination、evaluation 等 agent
- 重点解决 protagonist consistency

价值：

- 它证明“按影视专业角色拆 agent”是对的
- 也证明“角色一致性”是故事视频系统的核心难点，不是边角料

局限：

- 研究系统，不是成熟 SaaS
- 公开可直接工业落地的信息有限

### AniMaker

定位：

- 多 Agent 动画故事生成框架

论文强调：

- 通过多候选片段生成和故事感知选择，提高全局一致性和故事连贯性

价值：

- 对你有帮助的点不是“能不能直接用”
- 而是它把“候选生成 + 评价筛选”做成了正式机制

这和你后面的人物图复核、镜头视频复核思路一致。

### The Script Is All You Need

定位：

- 面向 long-horizon dialogue-to-cinematic video generation 的 agentic framework

论文强调：

- 用脚本驱动长程视频生成
- 用 CriticAgent 和对齐度指标强化 script faithfulness

价值：

- 非常接近你想做的“剧本驱动视频”
- 说明脚本对齐不是 prompt 小问题，而是系统级问题

局限：

- 仍是研究前沿，不是现成商品化系统

## 4.3 对开源侧的判断

目前开源世界里：

- 有“通用 Agent 编排框架”
- 有“故事到视频”的研究原型
- 但没有公开成熟到足以直接替代完整影视前后期团队的工程化系统

更现实的说法是：

- 你现在是在搭“行业拼装系统”
- 不是去找一个已经成型的开源总框架

## 5. 闭源产品与公司方案调研

## 5.1 最接近“剧本到视频工作台”的产品

### A. LTX Studio

接近度：目前最高

原因：

- 官方直接提供 `Script to Video`
- 可以上传 script
- 自动拆成 scenes 和 shots
- 自动抽取 `characters`、`objects`
- 有 `Elements` 概念管理角色、物体、地点一致性
- 官方平台同时覆盖：
  - scripting
  - storyboarding
  - keyframes/references
  - sound design
  - timeline editor
  - final delivery

它为什么重要：

- 这是目前公开信息里，最像“创作工作台”而不是“单一模型入口”的产品
- 如果你要 benchmark 行业产品，首个参考对象就该是它

但它仍然不等于你要的系统：

- 它并没有公开宣称“长篇小说改编成专业影视成片”已完全自动化
- 它解决的是工作台与生成链路，不是完整改编开发流程
- 角色一致性、剧情重构、知识库、审核流程仍需要人为介入

### B. Google Flow

接近度：高

原因：

- 官方直接把它叫做 `AI filmmaking tool`
- 强调 cinematic clips、scenes、stories
- 官方强调：
  - Camera Controls
  - Scenebuilder
  - Asset Management
  - 与 Veo、Imagen、Gemini 联动
- 还提到 Veo 3 原生音频能力，可把环境声与角色对白直接带入视频生成

它为什么重要：

- 它代表大厂“电影制作台”方向
- 不是只做短视频模板，而是明显朝“创作者电影工作台”发展

但不足：

- 官方也明确说 still early
- 它依然偏“创意制作工具”
- 不是一套公开的小说改编生产操作系统

### C. Runway

接近度：中高

原因：

- Runway 的官方帮助文档已经开始系统讲“如何做更长的视频和电影”
- 明确提出：
  - storyboard and shot planning
  - character plates
  - environment plates
  - local editor / in-app editor 拼接

它为什么重要：

- Runway 的建议本身就是行业经验
- 特别是 `character plates` 的说法，和你提出的“主角先出正面/侧面/背面参考图”高度一致

但它说明了一个现实：

- 即便 Runway 这种一线平台，也仍然要求用户先做 storyboard、shot planning、character plates，然后再生成，再编辑

也就是说：

- “脚本直接成熟成片”在实践中并不存在

### D. Sora

接近度：中

原因：

- 有 storyboard
- 支持按时间戳控制卡片
- 支持上传图片/视频或文本描述每个时间点的画面
- 支持 stitch clips together

优势：

- 适合做片段式控制和预可视化

不足：

- 官方公开信息更像“编辑器能力”而非完整改编生产系统
- 不覆盖小说解析、人物知识库、影视开发岗位、长篇改编工作流

### E. Adobe Firefly Boards

接近度：中

原因：

- 官方直接面向 storyboard
- 强调：
  - script-based prompts
  - 保持角色、产品、场景一致
  - 协作反馈

它更像什么：

- 强预演 / pre-production 工具

它不像什么：

- 不像完整叙事视频自动生产系统

## 5.2 更偏营销/内容生产的脚本转视频产品

### A. InVideo

特点：

- 提供 `script to video`
- 能按脚本生成场景、配 stock footage、加 voiceover
- 官方甚至有 `script to film` 工作流入口

但定位更偏：

- 营销视频
- YouTube 内容
- explainer video

不适合直接类比影视叙事改编。

### B. Pictory

特点：

- 强调 script/text to video
- 自动配素材、音乐、语音

定位：

- 营销、课程、内容创作

不适合直接类比“小说改影视”。

### C. Elai

特点：

- 更偏 avatar / presenter / narrated video

定位：

- 企业培训、演示、课程、说明类视频

也不适合直接类比影视叙事改编。

## 5.3 对闭源侧的判断

### 目前行业分两类

第一类：

- LTX
- Flow
- Runway
- Sora
- Firefly

这类更接近：

- 创意制作工作台
- 预演 + 分镜 + 片段生成 + 一定编辑能力

第二类：

- InVideo
- Pictory
- Elai

这类更接近：

- 脚本到营销视频
- stock footage + 旁白 + 自动剪辑

### 对你最有参考价值的 benchmark

按参考价值排序：

1. `LTX Studio`
2. `Google Flow`
3. `Runway`
4. `Sora`
5. `Adobe Firefly Boards`

## 6. 小说改剧本到视频，需要哪些专业角色

这里区分三个层面：

- 必须有的核心角色
- 建议有的增强角色
- 可高度 agent 化的执行角色

## 6.1 必须有的核心角色

### 1. 权利与法务负责人

职责：

- 确认底层 IP 是否可改编
- 处理 option / adaptation rights
- 明确 source material 的授权边界

为什么必须有：

- 美国版权局明确把“基于小说的 screenplay”视为 derivative work
- 没有授权，技术上能生成，不代表法律上能做

这一角色不能交给纯 Agent 决策。

### 2. 制片 / 开发制片

职责：

- 统筹项目边界、预算、进度、风格目标、交付定义
- 决定哪些集先做、哪些镜头先做、哪些环节人工复核

为什么必须有：

- 没有 producer，就没有真正的项目控制中心

### 3. 改编编剧 / Head Writer

职责：

- 将小说内容改造成影视叙事
- 决定删减、合并、改写、结构重排
- 产出 outline、treatment、scriptment、draft

为什么必须有：

- 小说不是天然剧本
- “忠于原著”与“适合上屏”经常冲突
- 这个判断高度依赖创作意图

### 4. Script Editor / Story Editor

职责：

- 提供结构与故事编辑反馈
- 协助 writer、director、producer 修整剧本

为什么必须有：

- Screen Ireland 对 script editor 的定义就是：给 writer / directors / producers 提供 1:1 支持，提供 critical editorial feedback 和 creative solutions

### 5. 导演 / 视觉总监

职责：

- 定镜头语法
- 定叙事节奏
- 定风格边界
- 决定哪些动作、哪些场景、哪些表演必须被看见

为什么必须有：

- 角色一致性和镜头语言最终都要服从一个统一导演视角

### 6. 角色设计 / 概念设计负责人

职责：

- 定主角与高频角色的视觉锚点
- 定角色包、服装包、配件包、视角包

为什么必须有：

- 没有这个岗位，后面所有镜头都会漂

### 7. 剪辑负责人

职责：

- 最终决定节奏、结构、信息顺序、镜头保留与删改

为什么必须有：

- ScreenSkills 对 editor 的职责描述已经很明确：editor 不只是拼镜头，还要和 director / producers 一起解决 story issues，甚至重组结构

### 8. 连续性负责人 / Script Supervisor

职责：

- 保证剧情日、服装、动作、情绪、道具、时长、镜头衔接不崩

为什么必须有：

- ScreenSkills 明确把 script supervisor 定义为导演与剪辑之间的桥梁，并负责 continuity

## 6.2 建议有的增强角色

### 1. 原著顾问

职责：

- 确认改编是否偏离核心人物弧线和世界观

### 2. 分镜导演 / Prev​​iz 负责人

职责：

- 把剧本文学语言转为 shot list、storyboard、animatic

### 3. 美术总监 / 场景设计负责人

职责：

- 保证世界观统一、场景纹理统一

### 4. 声音设计负责人

职责：

- 配音、环境音、SFX、BGM 的情绪一致性

### 5. 合规与品牌风险审核

职责：

- 审核版权风格模仿、平台违规元素、敏感题材风险

## 6.3 可高度 Agent 化的执行角色

以下角色高度适合 Agent 化，但不建议完全无人工：

- 小说分析研究员
- 世界观知识库维护员
- 人物候选提取员
- 场景母题提取员
- 改编草稿生成员
- 分镜拆解员
- 角色 prompt 设计员
- 场景 prompt 设计员
- 图片任务导出员
- 素材评分员
- TTS 任务员
- 字幕对齐员
- 产物清单与 manifest 生成员

## 7. 哪些工作可以交给 Agent，哪些必须人来做

## 7.1 适合 Agent 主导

### A. 资料整理与知识抽取

- 章节摘要
- 人物表
- 场景表
- 法器/势力/关系表
- 视觉母题抽取
- 听觉母题抽取
- continuity rules 初稿

### B. 结构化文档生产

- `story_bible`
- `character_bible`
- `scene_bible`
- `shot_plan`
- `image_tasks`
- `tts_tasks`
- `render_manifest`

### C. 大批量执行工作

- 图片任务生成
- 批量调用出图平台
- 批量审核打分
- 语音合成
- 字幕时间轴生成
- ffmpeg 拼接脚本生成

## 7.2 适合 Agent + 人工协作

### A. 小说改编为剧本

原因：

- Agent 很适合出初稿、备选结构、删改方案
- 但“戏剧取舍”与“人物弧光”仍需要人工判断

### B. 角色设计定稿

原因：

- Agent 很适合先提关键词、出角色卡、出参考图任务
- 但主角定稿必须人工拍板

### C. 分镜与镜头设计

原因：

- Agent 能出 shot list 初稿
- 但关键戏的镜头表达、人设落点、表演密度仍需人工判断

### D. 图片/视频审核

原因：

- Agent 能先筛掉明显失败样本
- 但主角锚定图、关键剧情镜头最好保留人工复核

### E. 剪辑与最终节奏

原因：

- Agent 可以给 rough cut
- 但真正的 narrative pacing 仍建议由人拍板

## 7.3 必须人工负责

### A. IP 授权与法务

不能交给 Agent 决策。

### B. 最终改编方向

- 删哪些人物
- 合并哪些支线
- 改成群像还是单主角
- 悲剧改开放式还是保留原结局

这些必须人定。

### C. 主角与核心角色定稿

主角一旦定错，后面全线返工。

### D. 成片最终验收

是否真的“能看”“能播”“能交付”，必须人工负责。

## 8. 适合 `VideoOnlyOnce` 的角色拆分

## 8.1 建议的 Agent 清单

### 1. `novel_knowledge_agent`

职责：

- 读章节
- 维护知识库
- 导出当前集 context pack

### 2. `adaptation_agent`

职责：

- 把小说内容转为 outline / treatment / scriptment 初稿

### 3. `character_anchor_agent`

职责：

- 提主角与高频角色
- 生成人物 sheet
- 导出人物图任务

### 4. `scene_bible_agent`

职责：

- 生成场景锚点、环境模板和高频场景簇

### 5. `storyboard_agent`

职责：

- 生成 shot plan
- 生成 image/video prompts

### 6. `asset_review_agent`

职责：

- 审核角色图、场景图、视频片段

### 7. `dialogue_audio_agent`

职责：

- 台词提炼
- TTS
- 字幕时间轴

### 8. `post_pipeline_agent`

职责：

- 生成拼接计划
- 生成 ffmpeg 命令
- 输出 render manifest

## 8.2 建议必须保留的人工角色

### 必保留

- 制片 / 项目 owner
- 改编编剧或总编剧
- 导演或视觉总监
- 主角角色定稿人
- 最终审核人

### 建议保留

- script editor
- 合规审核
- 关键镜头审核

## 9. 对 `VideoOnlyOnce` 的架构建议

## 9.1 不建议的路线

- 纯对话式多 Agent 自由发挥
- 没有中间 JSON schema
- 没有人工审核门
- 让一个“大总管 Agent”全权改编、定角、出图、剪辑

这类方案短期 demo 看起来很聪明，长期一定失控。

## 9.2 推荐路线

### 总控框架

- 首选 `LangGraph`
- 或 `Microsoft Agent Framework`

### 原因

- 都支持工作流
- 都支持状态
- 都支持 human-in-the-loop
- 都适合做可恢复、可阻断、可回放的长链路系统

### 生成层

- 图片/视频平台优先接：
  - `LTX Studio / LTX-2`
  - `Flow / Veo`
  - `Runway`
  - `Sora`

### 资产层

- 强制保留：
  - 角色参考图
  - 场景参考图
  - 镜头 manifest
  - reference pack
  - review log

### 人工门

必须设置在：

- 改编大纲确认
- 主角角色定稿
- 分镜确认
- 关键镜头验收
- 最终成片验收

## 9.3 实际落地最稳的方式

第一阶段：

- 用 `fenjing_program` 继续做前置理解和结构化产物
- 用 `zaomeng` 做图片执行

第二阶段：

- 引入 `LangGraph` 或 `Microsoft Agent Framework`
- 把原本的命令行流程封装成 graph/workflow node

第三阶段：

- 接 LTX / Flow / Runway / Sora 等平台
- 做统一资产登记、统一审核和统一成片管理

## 10. 对“是否已有成熟体系程序框架”的最终判断

### 开源侧

有：

- 通用多 Agent 编排框架
- 故事到视频研究原型

没有：

- 公开成熟、可直接商用落地的“小说改编到影视成片”总框架

### 闭源侧

有：

- 接近工作台形态的产品
- 脚本到视频的局部成熟能力

没有：

- 公开可验证的、真正覆盖小说改编开发全链路的成熟统一体系

### 结论

你现在做的事情，本质上不是“找现成框架拼一下”，而是：

- 参考通用 Agent 框架
- 参考视频平台工作台
- 参考影视专业岗位分工
- 自己做一个行业中间层

这正是 `VideoOnlyOnce` 的真正价值。

## 11. 参考来源

以下链接均为本次调研实际检索到的来源：

- LangGraph 官方概览：https://docs.langchain.com/oss/python/langgraph/overview
- Microsoft Agent Framework 官方概览：https://learn.microsoft.com/en-us/agent-framework/overview/
- Semantic Kernel Agent Framework：https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/
- AutoGen 官方仓库：https://github.com/microsoft/autogen
- CrewAI 官方仓库：https://github.com/crewAIInc/crewAI
- CrewAI 文档页：https://docs.together.ai/docs/crewai
- MM-StoryAgent 官方仓库：https://github.com/X-PLUG/MM_StoryAgent
- MM-StoryAgent 论文：https://arxiv.org/abs/2503.05242
- StoryAgent 论文：https://arxiv.org/abs/2411.04925
- AniMaker 论文：https://arxiv.org/abs/2506.10540
- The Script Is All You Need：https://arxiv.org/abs/2601.17737
- LTX Studio 首页：https://ltx.studio/
- LTX Studio Script to Video：https://ltx.studio/platform/script-to-video
- LTX 是否开源：https://support.ltx.studio/hc/en-us/articles/32485308551570-Is-the-LTX-model-open-source
- LTX-2 官方仓库：https://github.com/Lightricks/LTX-2
- Google Flow 官方介绍：https://blog.google/innovation-and-ai/products/google-flow-veo-ai-filmmaking-tool/
- Google Flow FAQ：https://labs.google/fx/tools/flow/faq
- Runway 官方帮助：How to create longer videos and films：https://help.runwayml.com/hc/en-us/articles/26871350018835-How-to-create-longer-videos-and-films
- OpenAI Sora 帮助：Using Storyboard in the Sora editor：https://help.openai.com/en/articles/9957612
- OpenAI Sora 产品页：https://openai.com/sora/
- Adobe Firefly Storyboard：https://www.adobe.com/products/firefly/features/storyboard.html
- InVideo Script Workflows：https://help.invideo.io/en/articles/9382180-how-can-i-create-a-video-using-my-script
- Pictory Script to Video：https://pictory.ai/es/texto-a-video
- Writers Guild of America: What Every Producer Needs to Know：https://www.wga.org/employers/employers/what-every-producer-needs-to-know
- Writers Guild of America: Creative Rights for Writers：https://www.wga.org/contracts/know-your-rights/creative-rights-for-writers
- Writers Guild of America: Understanding Separated Rights：https://www.wga.org/contracts/know-your-rights/understanding-separated-rights
- Screen Ireland: Script Editor role：https://www.screenireland.ie/news/call-for-script-editors-for-screen-irelands-perspectives-scheme
- Screen Australia Generate FAQs：https://www.screenaustralia.gov.au/getmedia/0679f450-9eda-495e-a2d3-b10df2af4534/Generate-FAQs.pdf
- ScreenSkills: Script Supervisor Job Title：https://www.screenskills.com/media/7610/final-jd-script-supervisor-110523.pdf
- ScreenSkills: Editor Job Title：https://www.screenskills.com/media/fevmvvj5/editor-skills-checklist.pdf
- WIPO《From Script to Screen》：https://www.wipo.int/edocs/pubdocs/en/wipo-pub-cr-film-script-to-screen-en-from-script-to-screen.pdf
- U.S. Copyright Office: Derivative Works：https://www.copyright.gov/eco/help-limitation.html

## 12. 对来源的简短判断

### 最可信、最适合作为产品设计依据的

- 官方产品页
- 官方帮助中心
- 官方开发文档
- 行业组织与版权机构文档
- WIPO / WGA / Screen Ireland / Screen Australia / ScreenSkills

### 需要谨慎使用的

- SaaS 营销文案
- 论文中的效果描述

原因：

- 这些来源更适合判断“方向”和“能力边界”
- 不适合直接当成“成熟可交付能力证明”
