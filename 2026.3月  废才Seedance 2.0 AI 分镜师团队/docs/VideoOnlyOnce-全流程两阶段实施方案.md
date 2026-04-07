# VideoOnlyOnce 全流程两阶段实施方案

## 1. 项目目标

`VideoOnlyOnce` 的目标是：

- 输入：一份小说剧本或单集剧本
- 输出：一个带配音、对白、镜头衔接的完整视频

本方案基于当前仓库已有两个子系统联合落地：

- `fenjing_program`：负责剧本理解、导演分析、角色/场景设计、分镜提示词生成
- `zaomeng`：负责网页端图片生成自动化、下载、重命名、归档

建议不要把项目拆成“6 个互相断开的零散脚本”，而是统一成“2 个总阶段 + 6 个执行子阶段”的工程化流程。

## 2. 两阶段总览

### 阶段 A：理解与设计阶段

目标：把原始小说或剧本，转成可执行的结构化分镜生产包。

包含子阶段：

- 阶段 0：前 30 章预读与世界观建档
- 阶段 1：剧本分镜化与角色/场景设定
- 阶段 2：图片生成任务包输出

阶段 A 的核心输出不是图片，而是“可审计、可复用、可回滚”的结构化文档和任务文件。

### 阶段 B：素材生成与成片阶段

目标：把阶段 A 的任务包，转成图片、视频、语音，并最终拼成成片。

包含子阶段：

- 阶段 3：图片生成与筛图
- 阶段 4：视频生成
- 阶段 5：对白提炼与 TTS
- 阶段 6：音视频合成与总片输出

## 3. 6 个子阶段详细任务流

## 3.1 阶段 0：前 30 章预读与项目世界观建档

### 目标

在正式做单集分镜前，先理解这个 IP 的长期设定，避免后面出现角色长相漂移、修仙体系错位、时代风格混乱、场景纹理不统一。

### 输入

- 小说前 30 章正文
- 已有的人设图、封面图、参考图（如果有）
- 已知的风格偏好和平台限制

### 处理任务

1. 识别题材标签。
2. 识别世界观类型：
   - 古代修仙
   - 现代修仙
   - 诡异修仙
   - 都市异能
   - 国风玄幻
3. 提炼主角团和核心配角：
   - 年龄感
   - 气质
   - 身份
   - 战斗方式
   - 口头禅
   - 服装与标志物
4. 提炼高频场景：
   - 宗门
   - 城市
   - 山林
   - 洞府
   - 市井
   - 战场
   - 梦境/诡域
5. 提炼视觉母题：
   - 法器
   - 灵气颜色
   - 符文样式
   - 火焰/烟雾/水墨/粒子风格
6. 输出项目默认风格建议和禁用项。

### 输出文档

- `story_bible.md`
- `character_bible.md`
- `scene_bible.md`
- `style_bible.json`
- `term_glossary.json`

### 必须包含的字段

- 世界观类型
- 时间背景
- 主视觉关键词
- 禁止漂移项
- 主角团清单
- 角色外观锚点
- 场景锚点
- 常见镜头语法
- 配音基调

### 验收门

- 同一个角色必须能用 5 到 8 个稳定关键词复现
- 同一个主场景必须能用固定环境锚点复现
- 风格描述不能只写“唯美、电影感、震撼”这种空词
- 必须给出禁用风格词和禁用设定词

### 推荐由谁实现

- 继续扩展 `fenjing_program` 的 `start` 阶段
- 增加 `novel-intake` 或 `bible` 命令

## 3.2 阶段 1：角色锚定 + 剧本分镜化与角色/场景设定

### 目标

先把主角与高频角色稳定下来，再把“可读剧本”变成“可生产分镜”。

这里必须强调一个前提：

- 分镜不是角色设定的起点
- 分镜只是消费“已经稳定的人物锚定资产”

如果主角的人物外观、服饰、发型、人种气质、首饰和默认姿态没有先定下来，后面的图片和视频阶段会持续出现人物漂移。

当前 `fenjing_program` 已有基础能力：

- `start`：导演分析
- `design`：角色与场景设计
- `prompt`：Seedance 分镜提示词

但要升级为 `VideoOnlyOnce`，需要把这一阶段拆成两个连续子流程：

- 阶段 1A：人物锚定资产生产
- 阶段 1B：分镜结构化与镜头引用挂接

### 输入

- 单集剧本
- 阶段 0 的 `story_bible.md`
- 阶段 0 的 `character_bible.md`
- 阶段 0 的 `scene_bible.md`
- 项目默认风格配置

### 阶段 1A：人物锚定资产生产

### 目标

在分镜开始前，优先产出主角的稳定参考图和人物文档。

### 处理任务

1. 从剧本和知识库中提取当前已出现人物。
2. 将人物分层：
   - `tier_a`
     - 主角
     - 第一主配角
     - 高频反派
   - `tier_b`
     - 重要配角
     - 高频路人模板
   - `tier_c`
     - 普通观众
     - 背景群众
     - 一次性工具人
3. 主角优先定稿，其他配角可延后，但高频配件和高频身份模板要先补。
4. 为每个重点人物提炼外观锚点关键词：
   - 性别表现
   - 年龄感
   - 人种/族裔感
   - 身材
   - 发型
   - 发色
   - 脸型
   - 眼型
   - 肤色
   - 服饰
   - 首饰
   - 武器/法器
   - 气质
5. 为每个重点人物生成标准姿态提示词：
   - 正面全身
   - 侧身全身
   - 背身全身
   - 正面半身
   - 默认站姿
6. 默认动作用统一基准：
   - 垂直双手
   - 站在原地
   - 身体不夸张扭曲
   - 便于观察服装和轮廓
7. 对主角补充少量高频动作锚定：
   - 走
   - 回头
   - 抬手
   - 握武器
   - 施法起手
8. 组织人物图生成任务。
9. 生成人物参考图后进行人工或规则复核。
10. 将通过的人物图登记为角色参考资产，并形成正式人物文档。

### 人物资产优先级

- 第一优先：
  - 主角完整角色包
- 第二优先：
  - 高频主配角角色包
- 第三优先：
  - 高频职业模板
  - 高频群众模板
  - 高频道具模板

### 普通观众/群众角色如何处理

普通观众不需要每个名字都做独立角色包，但必须按“模板化人群”建库，否则后面镜头里的背景人物也会严重串味。

建议最少建立这些模板：

- 宗门弟子模板
- 城市百姓模板
- 酒楼客人模板
- 官差模板
- 世家侍从模板
- 士兵模板
- 商贩模板
- 学生/研究员模板
- 邪教/诡异信徒模板

每个模板至少区分：

- 时代表达
- 身份表达
- 服饰层次
- 发型规则
- 人种/族裔感
- 常见配件

### 人物文档建议字段

`character_sheet.json` 每个角色建议至少包含：

```json
{
  "character_id": "char_lin_du",
  "priority": "tier_a",
  "name": "林渡",
  "role_type": "主角",
  "visual_keywords": [
    "黑发",
    "清瘦",
    "浅灰道袍",
    "冷静",
    "旧剑",
    "二十岁上下"
  ],
  "costume_keywords": ["浅灰道袍", "旧布腰带", "布靴"],
  "hair_keywords": ["黑发", "半束发"],
  "face_keywords": ["清瘦", "冷峻", "东方面孔"],
  "accessories": ["旧剑", "木牌"],
  "default_pose_set": [
    "front_full_body",
    "side_full_body",
    "back_full_body",
    "front_half_body"
  ],
  "default_prompt_base": "主角站立，垂直双手，正面全身视角，角色设定展示图",
  "reference_images": [
    "characters/char_lin_du/front.png",
    "characters/char_lin_du/side.png",
    "characters/char_lin_du/back.png"
  ]
}
```

### 人物锚定图建议输出物

- `outputs/<episode>/characters/character-candidate-list.json`
- `outputs/<episode>/characters/character-sheets.json`
- `outputs/<episode>/characters/character-image-tasks.json`
- `outputs/<episode>/characters/character-review.json`
- `assets/library/characters/...`
- `assets/registry/character-index.json`

### 人物锚定阶段验收门

- 主角必须至少有正面、侧身、背身三张稳定参考图
- 主角必须有一份正式 `character_sheet`
- 主角的服饰、发型、武器、首饰必须可复现
- 角色图通过后，后续镜头只能引用已通过的人物参考图
- 高频配角未定稿时，可以阻断相关镜头分镜

### 阶段 1B：分镜结构化与镜头引用挂接

1. 将剧本切成 plot points。
2. 将每个 plot point 切成 shot。
3. 为每个 shot 标注：
   - 镜头编号
   - 镜头时长
   - 画幅建议
   - 景别
   - 运镜
   - 人物动作
   - 场景变化
   - 表情变化
   - 对白
   - 环境音
   - 后续是否需要首尾帧
4. 从已经通过的人物锚定资产和场景设定中，为每个 shot 自动挂接引用资产。
5. 产出图片 prompt、视频 prompt、音频脚本三套中间件。

### 输出文档

- `outputs/<episode>/01-director-analysis.md`
- `outputs/<episode>/01-director-analysis.json`
- `assets/character-prompts.md`
- `assets/scene-prompts.md`
- `outputs/<episode>/characters/character-sheets.json`
- `outputs/<episode>/02-shot-plan.json`
- `outputs/<episode>/03-image-prompts.json`
- `outputs/<episode>/04-video-prompts.json`
- `outputs/<episode>/05-audio-script.json`

### 新增建议字段

`02-shot-plan.json` 中每个镜头至少包含：

```json
{
  "shot_id": "ep01-s001",
  "plot_id": "P01",
  "duration_seconds": 5,
  "shot_type": "medium_close_up",
  "camera_move": "push_in",
  "characters": ["主角-林渡"],
  "character_refs": ["char_lin_du_front_v1"],
  "scene_id": "scene-mountain-gate-night",
  "action": "抬头看向山门，右手握紧令牌",
  "emotion": "警惕中带压抑",
  "dialogue": "这地方，不对劲。",
  "sfx": ["夜风", "木牌轻响"],
  "needs_image_pair": true,
  "style_preset": "ink_fantasy_v1"
}
```

### 验收门

- 分镜前必须先完成主角人物锚定
- 每个镜头必须有明确动作，不允许只有情绪词
- 每个镜头必须可映射到角色、人物参考图和场景资产
- 每个镜头必须标明时长或者帧数，后续视频生成才可控
- 对白和镜头必须一一对应，不能后面再猜

### 推荐由谁实现

- 继续用 `fenjing_program` 作为主编排器
- 在 `structured_protocols.py` 扩展人物锚定 schema 和 shot 级 JSON schema

## 3.3 阶段 2：图片生成任务包输出

### 目标

把阶段 1 的分镜文档，转成 `zaomeng` 可以直接消费的图片任务清单。

### 输入

- `02-shot-plan.json`
- `03-image-prompts.json`
- 角色/场景资产引用表

### 处理任务

1. 为每个镜头生成图片任务。
2. 如果镜头需要视频，至少生成：
   - 首帧图
   - 尾帧图
   - 必要时中间关键帧
3. 将 prompt 归一化：
   - 主体
   - 场景
   - 动作
   - 光线
   - 镜头
   - 风格
   - 负向约束
4. 每个任务生成稳定 ID。
5. 输出给 `zaomeng` 的任务文件。

### 推荐输出格式

- `outputs/<episode>/image-tasks.json`

```json
[
  {
    "task_id": "ep01-s001-f01",
    "shot_id": "ep01-s001",
    "frame_type": "start",
    "prompt": "主角站在夜色山门前，半侧身回头，冷青月光，衣摆轻动，中近景，国风水墨奇幻，统一角色设定",
    "negative_prompt": "多人串脸，手部畸形，低清晰度，现代路灯",
    "style_preset": "ink_fantasy_v1"
  }
]
```

### 验收门

- 每个镜头任务数明确
- 每个任务都能反查到 `shot_id`
- 每个任务都保留风格预设与负向提示词
- 不允许只有自然语言 markdown，没有结构化 JSON

### 推荐由谁实现

- 在 `fenjing_program` 新增 `export-image-tasks`
- 输出文件直接兼容 `zaomeng` 的 prompt loader

## 3.4 阶段 3：图片生成与筛图

### 目标

通过 `zaomeng` 自动化批量出图，并将合格图回写到 `fenjing_program` 的资产系统。

### 当前现状

`zaomeng` 目前已经具备：

- 读取 prompt 文件
- 浏览器执行图片生成
- 下载图片
- 重命名与归档
- 任务状态记录

### 还需要补的能力

- 图片质量评分
- 首尾帧配对管理
- 回写 `fenjing_program register-image`
- 镜头级筛图结果表

### 输入

- `outputs/<episode>/image-tasks.json`

### 处理任务

1. 人工先完成平台登录。
2. `zaomeng` 执行批量出图。
3. 每个任务下载 4 图或平台默认图数。
4. 本地执行图片筛选：
   - 人物一致性
   - 场景一致性
   - 动作匹配度
   - 构图可用性
   - 手部/面部异常检测
5. 选出每个任务的最佳图。
6. 将通过图片登记进 `fenjing_program` 资产库。
7. 生成 `reference-map.json`。

### 输出物

- `downloads/images/...`
- `outputs/<episode>/image-review.json`
- `outputs/<episode>/reference-map.json`

### 推荐实现方式

- `zaomeng` 增加 `review_agent.py`
- `fenjing_program` 继续用现有：
  - `register-image`
  - `build-reference-map`

### 验收门

- 每个 `shot_id` 的首帧和尾帧都必须有合格图
- 图像未通过时，不得直接进入视频阶段
- 所有入库图片必须有来源记录和任务 ID

## 3.5 阶段 4：视频生成

### 目标

把“图片 + 动作描述 + 场景变化 + 镜头语法”转成每个镜头的短视频片段。

### 当前现状

仓库中 `zaomeng` 的视频阶段还没有正式实现，只在文档架构中留了 `Video Operator` 边界，因此这部分属于新增开发。

### 输入

- `04-video-prompts.json`
- `reference-map.json`
- 通过筛选的首尾帧或关键帧

### 处理任务

1. 将每个镜头的视频提示词与图片引用拼装成平台实际输入。
2. 调用视频页自动化：
   - 打开视频生成页
   - 上传首帧/尾帧
   - 填写动作 prompt
   - 提交生成
   - 等待完成
   - 下载视频
3. 对视频进行基础审查：
   - 人物是否串脸
   - 动作是否崩坏
   - 首尾帧是否漂移
   - 时长是否正确
4. 不合格则重试或回退到图片阶段重新出关键帧。

### 输出物

- `downloads/videos/...`
- `outputs/<episode>/video-review.json`
- `outputs/<episode>/shot-video-manifest.json`

### 推荐技术

- 继续扩展 `zaomeng`
- 新增 `video_operator.py`
- 继续沿用状态机，增加：
  - `FRAME_READY`
  - `VIDEO_PAGE_READY`
  - `VIDEO_GENERATING`
  - `VIDEO_DOWNLOADED`

### 验收门

- 每个镜头都有独立视频文件
- 视频时长与 shot plan 偏差不超过可配置阈值
- 首尾帧角色一致性达标

## 3.6 阶段 5：对白提炼与 TTS

### 目标

把台词、旁白、情绪和节奏变成可对齐的音频文件。

### 输入

- `05-audio-script.json`
- `02-shot-plan.json`

### 处理任务

1. 提取对白、旁白、语气、停顿。
2. 为每段语音生成：
   - `voice_id`
   - `shot_id`
   - `speaker`
   - `text`
   - `emotion`
   - `target_duration`
3. 调用 TTS 生成音频。
4. 进行长度校正：
   - 超长则调整语速
   - 超短则补停顿
5. 生成字幕时间轴。

### 输出物

- `outputs/<episode>/tts-tasks.json`
- `outputs/<episode>/audio/<shot_id>.wav`
- `outputs/<episode>/subtitles/<episode>.srt`
- `outputs/<episode>/voice-manifest.json`

### 推荐技术

第一版优先本地稳定落地：

- `edge-tts`：快，轻量，适合先跑通
- `ffmpeg`：做静音补齐、裁切、混音

第二版再考虑：

- `CosyVoice`
- `Fish Speech`
- 商业 TTS API

### 验收门

- 每条台词都能反查到 `shot_id`
- TTS 输出时长必须接近镜头时长
- 人物音色必须有固定映射，不能每镜头随机换声

## 3.7 阶段 6：音视频合成与总片输出

### 目标

把镜头视频、对白、环境音、BGM 和字幕合成一个完整视频。

### 输入

- `shot-video-manifest.json`
- `voice-manifest.json`
- BGM 配置
- 字幕文件

### 处理任务

1. 按 `shot_plan` 顺序拼接镜头视频。
2. 按时间轴叠加对白音频。
3. 混入环境音和 BGM。
4. 加入字幕。
5. 导出总片。
6. 输出工程级清单，方便重做和追溯。

### 输出物

- `outputs/<episode>/final/<episode>-final.mp4`
- `outputs/<episode>/final/<episode>-final.srt`
- `outputs/<episode>/final/render-manifest.json`

### 推荐技术

- `ffmpeg` 作为第一版主方案
- Python 负责生成 concat 清单、mix 清单、字幕映射

### 验收门

- 音画同步误差不超过阈值
- 片头片尾、黑场、空镜必须在 shot plan 中有记录
- 最终成片必须可回溯到镜头、图片、语音来源

## 4. 默认风格策略

### 4.1 不建议直接把“宫崎骏画风”设成系统默认词

原因：

- 风格指向过于具体，存在平台审核和版权风格模仿风险
- 不利于长期统一成自己的项目资产语言
- 后期做多题材扩展时会被单一风格绑死

### 4.2 推荐做成“风格预设”

每个项目只选一个默认预设，单镜头允许少量 override。

建议预设：

- `anime3d_v1`
  - 关键词：3D 动漫、体积光、电影级材质、镜头运动稳定
- `semi2d_cel_v1`
  - 关键词：半 2D、赛璐璐、边缘清晰、轻体积光
- `flat2d_story_v1`
  - 关键词：2D 平涂、手绘感、色块明确、轮廓清晰
- `ink_fantasy_v1`
  - 关键词：国风水墨、留白、墨色扩散、山水灵气
- `warm_fairy_animation_v1`
  - 关键词：温暖童话、自然风、手绘背景、柔和阳光

`warm_fairy_animation_v1` 可以作为“宫崎骏感”的安全替代表达，但不要直接写具体作者名。

### 4.3 风格预设至少要有这些字段

```json
{
  "preset_id": "ink_fantasy_v1",
  "visual_keywords": ["国风", "水墨", "灵气流动", "山雾", "冷暖对比"],
  "camera_keywords": ["慢推镜", "留白构图", "远近层次"],
  "lighting_keywords": ["晨雾逆光", "冷青月光"],
  "negative_keywords": ["现代城市", "塑料质感", "欧美盔甲"],
  "consistency_rules": ["主角发型不可漂移", "法器颜色固定", "服装纹样固定"]
}
```

## 5. 推荐系统架构

## 5.1 主编排关系

建议由 `fenjing_program` 做总控，由 `zaomeng` 做执行器。

原因：

- `fenjing_program` 已经掌握剧本、角色、场景、审核、资产登记
- `zaomeng` 更适合作为浏览器自动化和素材获取层

### 编排关系

```text
小说/剧本
  -> fenjing_program
  -> 输出 shot plan / image tasks / video tasks / audio tasks
  -> zaomeng 执行图片与视频生成
  -> 回写图片与视频结果
  -> ffmpeg + tts 模块合成
  -> final video
```

## 5.2 建议新增模块

在 `fenjing_program` 新增：

- `novel_intake.py`
- `shot_planner.py`
- `task_exporter.py`
- `audio_script_builder.py`

在 `zaomeng` 新增：

- `review_agent.py`
- `video_operator.py`
- `result_callback.py`

在仓库根目录新增：

- `video_only_once/tts_pipeline.py`
- `video_only_once/render_pipeline.py`

## 6. 安全落地原则

## 6.1 账号与平台安全

- 人工首登，自动化只复用登录态
- 浏览器 profile 单独存放，不混用个人日常环境
- 记录任务日志，不记录明文密码
- 设置批次并发上限和每日任务上限

## 6.2 内容安全

- 不直接使用具体在世艺术家姓名做默认风格
- 对暴力、宗教、未成年人、敏感政治内容单独设审核门
- 剧本先做内容标签分类，再决定是否允许自动执行

## 6.3 资产安全

- 所有生成图、视频都保留来源 task_id
- 所有中间件都保留 JSON manifest
- 原始下载文件不覆盖，只归档
- 最终成片必须能追溯到镜头级素材

## 6.4 质量安全

- 每一阶段都设 acceptance gate
- 不合格图片不得直接推进视频
- 不合格视频不得直接进入总片
- TTS 与镜头时长不匹配时必须阻断

## 6.5 工程安全

- 先文件驱动，后数据库
- 先单集跑通，后多集批处理
- 先图片链路跑通，后视频链路
- 先人工复核，后半自动放量

## 7. 推荐技术选型

## 7.1 编排与结构化

- Python 3.11+
- JSON + Markdown 双输出
- 现有 `fenjing_program` 命令行作为主入口

## 7.2 图片/视频网页自动化

- 继续沿用 `zaomeng`
- 浏览器适配继续走 `BrowserOperator`
- 视频页沿用同样的 operator 抽象，不把 DOM 逻辑写死在主流程

## 7.3 质量审查

- 第一版：规则评分 + LLM 审查
- 第二版：加入人脸一致性、图像质量、字幕对齐等模型评分

## 7.4 配音与后期

- `edge-tts`
- `ffmpeg`
- 可选 `pydub` 做轻量音频处理

## 8. 第一版最小可落地范围

不要一开始就追求“整本小说自动出完全集”。

建议 V1 只做：

1. 单本小说建立世界观 bible。
2. 单集剧本生成 shot plan。
3. 自动批量出图并筛选。
4. 每个镜头生成短视频。
5. 为单集生成配音。
6. 合成一个可播放的成片。

V1 暂不做：

- 多集连续人物成长自动继承
- 高级口型匹配
- 全自动 BGM 创作
- 全自动镜头级重写
- 完整 Web 平台

## 9. 建议目录规划

```text
docs/
  VideoOnlyOnce-全流程两阶段实施方案.md

project_data/
  novels/
  scripts/
  style_presets/

outputs/
  ep01/
    01-director-analysis.md
    02-shot-plan.json
    03-image-prompts.json
    04-video-prompts.json
    05-audio-script.json
    image-review.json
    video-review.json
    reference-map.json
    final/

assets/
  registry/
  library/

downloads/
  images/
  videos/
```

## 10. 实施顺序建议

### 第 1 步

先扩展 `fenjing_program`，补齐：

- 前 30 章预读
- shot plan 结构化输出
- image/video/audio task 导出

### 第 2 步

扩展 `zaomeng`，把图片链路打通到可回写：

- 批量出图
- 筛图
- `register-image`
- `build-reference-map`

### 第 3 步

再补 `zaomeng` 视频链路：

- 上传参考图
- 生成镜头视频
- 下载和审查

### 第 4 步

最后接入：

- TTS
- ffmpeg 合成
- 成片 manifest

## 11. 结论

`VideoOnlyOnce` 可以落地，但正确路径不是一次性做“6 个松散阶段脚本”，而是：

- 用 `fenjing_program` 做前置理解和结构化设计总控
- 用 `zaomeng` 做图片/视频生成执行层
- 用 `TTS + ffmpeg` 做后段合成
- 用“风格预设 + 资产回写 + 阶段验收门”保证可控、可审计、可持续扩展

如果按这个方案实施，最稳的节奏是先做单集闭环，再做多集批处理。
