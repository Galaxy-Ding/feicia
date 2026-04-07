---
title: character-design 单独测试与 Debug 指南
---

# character-design 单独测试与 Debug 指南

这份文档的目标不是跑完整分镜流程，而是单独验证 `character-design` 这个角色是否能：

1. 从小说章节里提取出你真正想要的人物
2. 给出基本可信的人物形象
3. 根据章节内容，大致描述人物穿着

本次测试固定使用以下输入文件：

- 小说章节：`/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/fenjing_program/script/ep01-时辰守门局.md`
- 角色定义：`/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/update_document/agents/character-design.md`
- 技能定义：`/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/update_document/skills/character-design-skill/SKILL.md`
- 输出模板：`/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/update_document/skills/character-design-skill/templates/character-design-template.md`

---

## 先说明一个关键事实

当前 `fenjing_program` 里的代码入口，还没有真正接入你新写的 `character-design` 文档。

也就是说：

- 你现在测试 `character-design`，最佳方式是先做“手工单 Agent 测试”
- `fenjing_program` 里的 `extract-characters` 只能作为“程序对照测试”
- 不要把这两种测试混在一起，否则你会以为 agent 没生效，但其实是代码根本没接进去

---

## 第一部分：先定测试标准

在第一轮测试前，你必须先决定下面这条规则，否则后面会一直误判“对”还是“不对”。

### 规则 1：是否提取“被提及但未正面出场的人物”

这章里至少有两类人物：

- 正面出场人物：顾星澜、守门内侍
- 重要但主要通过文稿/回忆/对话被提及的人物：沈钧白、庄恒之、萧景琛、谢时行

你要先决定你的测试标准属于哪一种：

### 标准 A：只提取本章有明确画面承载的人物

适合做角色设定图、分镜角色卡。

这一标准下，第一轮你通常希望至少提取出：

- 顾星澜
- 守门内侍

这一标准下，以下人物即使被提到，也不一定要求做完整穿着描述：

- 沈钧白
- 庄恒之
- 萧景琛
- 谢时行

### 标准 B：提取本章对剧情推进重要的全部人物

适合做小说人物总表或角色库建设。

这一标准下，你通常希望至少识别出：

- 顾星澜
- 守门内侍
- 沈钧白
- 庄恒之
- 萧景琛
- 谢时行

但要注意：

- “识别出人物” 不等于 “都能写出完整穿着”
- 没有出场的人物，穿着只能非常保守地推断，不能胡编

建议你第一轮先用 `标准 A` 测。

原因：

- 更容易判断对错
- 更接近角色设定/分镜前置资料的真实需求
- 能先验证“人物筛选”能力，再验证“人物覆盖范围”

---

## 第二部分：手工单 Agent 测试

这一部分测试的，才是你刚写的 `character-design` 文档本身。

### Step 1：新建一份测试记录文件

建议你手工记录每轮测试结果，避免第二轮开始以后忘了哪里变好了、哪里变坏了。

推荐新建文件：

- `fenjing_program/docs/modify/character-design-test-log.md`

第一轮先写一个最简单的头：

```markdown
# character-design 测试记录

## Round 1

**测试标准**：标准 A（只提取本章有明确画面承载的人物）

**目标**：
- 能提取顾星澜
- 能提取守门内侍
- 不要乱扩写未出场人物的穿着
- 人物形象和穿着要尽量贴合原文
```

### Step 2：用下面这段测试 Prompt 直接跑第一轮

你可以把下面整段提示词直接发给模型测试。

```markdown
你现在扮演 character-design agent。

请严格遵守以下角色与技能定义：

【Agent 定义】
/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/update_document/agents/character-design.md

【Skill 定义】
/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/update_document/skills/character-design-skill/SKILL.md

【输出模板】
/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/update_document/skills/character-design-skill/templates/character-design-template.md

【输入小说章节】
/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/fenjing_program/script/ep01-时辰守门局.md

测试要求：
1. 本轮采用“标准 A”：只提取本章有明确画面承载的人物
2. 不要输出分析过程
3. 不要凭空补完过多服装细节
4. 如果原文没有明确服装信息，只能做保守推断
5. 输出为 markdown

额外要求：
请在结果最后附加一个“测试备注”小节，简短说明：
- 哪些人物被纳入
- 哪些人物被排除
- 排除原因是什么
```

### Step 3：把第一轮结果保存下来

建议保存为：

- `fenjing_program/docs/modify/character-design-round01-output.md`

不要急着改 prompt，先对照原文检查。

---

## 第三部分：第一轮怎么验收

你不要一上来就问“像不像”，先按下面 5 个维度逐条检查。

### 检查 1：人物有没有漏

对着原文问这几个问题：

- 顾星澜有没有被提取出来
- 守门内侍有没有被提取出来
- 有没有把明显该保留的人漏掉

如果第一轮用的是 `标准 A`，那最重要的是别漏掉：

- 顾星澜
- 守门内侍

### 检查 2：有没有乱抓人

重点看是否把下面这些都直接做成完整人物卡：

- 萧景琛
- 谢时行
- 庄恒之

如果你本轮用的是 `标准 A`，这几位不一定该被做成完整设定。

如果模型把他们全都展开成长篇人物造型，并写了完整穿着，这通常说明：

- 人物筛选规则不够收敛
- “被提及” 和 “在本章承担画面” 被混淆了

### 检查 3：形象是否贴原文

顾星澜这一章从原文能稳定提炼出的东西，大致是：

- 女官
- 行动利落
- 长期从事历算和观测
- 克制、冷静、能快速判断

如果结果里出现下面这种内容，就要警惕：

- 过度华丽的服装
- 明显宫廷嫔妃风
- 与“太史局女官”身份不符的夸张饰品
- 过多原文没有支撑的外貌设定

### 检查 4：穿着有没有胡编

这章对服装的直接描写其实不多，所以你要重点盯这一点。

合理结果应该更像：

- 太史局女官的素雅官服
- 方便行动、利于观测和书房行动的穿着
- 色调偏克制

不合理结果通常像：

- 精细到原文完全没给出的繁复纹样
- 完整色板、复杂材质、珠宝层层叠加
- 与工作场景和时间不符的夸张礼服

### 检查 5：是否区分“稳定外观”和“本章状态”

这是后面最好用的一个检查点。

你要看输出有没有把这两层分开：

- 稳定外观：年龄段、体型、气质、身份感
- 本章状态：本章穿着、动作状态、是否匆忙、是否简洁、是否带随身工具

如果两层混在一起，后面跨章节复用会非常难。

---

## 第四部分：第一轮出问题以后怎么 Debug

每次只改一类问题，不要一轮改 5 条规则。

### 场景 1：提取人物过多

症状：

- 把所有被提及的人都写成完整角色卡

解决方式：

在下一轮 prompt 增加一条硬规则：

```markdown
只输出本章有明确画面承载、动作、对话或场景存在感的人物。
仅被信件、回忆、口述提及的人物，不建立完整角色卡，只能在测试备注里列出。
```

### 场景 2：漏掉守门内侍这类功能角色

症状：

- 主角有了，但功能性强、出场清晰的角色被漏掉

解决方式：

补一条规则：

```markdown
除主角外，本章中承担关键动作、对话、阻拦、转折功能的人物，也应纳入角色提取。
```

### 场景 3：服装写得太花

症状：

- 原文没写，结果却补出一整套很复杂的服饰系统

解决方式：

补一条规则：

```markdown
服装描述必须保守。原文没有明确写到的细节，不要扩写为复杂花纹、贵重材质和多层首饰，只写到足以支持视觉理解的程度。
```

### 场景 4：人物气质不对

症状：

- 顾星澜被写成柔弱、艳丽或纯恋爱向角色

解决方式：

补一条规则：

```markdown
人物气质优先服从其在本章中的行为证据，不要使用模板化女性角色审美词。顾星澜应体现理性、克制、迅速判断和执行力。
```

### 场景 5：输出结构不稳定

症状：

- 每轮格式都不一样，难以对照

解决方式：

强制要求：

```markdown
严格按模板输出，不得自行改动字段顺序。
```

---

## 第五部分：建议你怎么做第二轮

如果第一轮只是“差一点”，不要重写整份 agent，先改测试 prompt。

推荐第二轮只增加这 4 条约束：

```markdown
补充约束：
1. 只提取本章有明确画面承载的人物
2. 功能性关键角色不能漏
3. 穿着描述必须保守，不能过度脑补
4. 人物气质必须服从本章行为证据
```

然后把第二轮结果存成：

- `fenjing_program/docs/modify/character-design-round02-output.md`

再和第一轮逐项对比：

- 漏人是否减少
- 乱抓是否减少
- 穿着是否更收敛
- 顾星澜是否更贴人物

---

## 第六部分：程序级对照测试

这一部分不是测你新写的 agent 文档，而是测当前程序里现成的人物提取链路。

你可以把它当成“基线参考”。

### Step 1：进入项目目录

```bash
cd '/home/galaxy/work/feicia/2026.3月  废才Seedance 2.0 AI 分镜师团队/fenjing_program'
```

### Step 2：跑人物提取

```bash
PYTHONPATH=src python -m feicai_seedance.cli extract-characters book-debug ep01 --project-root .
```

这一条会生成：

- `outputs/ep01/characters/character-candidate-list.json`

### Step 3：查看提取结果

```bash
python -m json.tool outputs/ep01/characters/character-candidate-list.json
```

你重点看：

- `name`
- `role_type`
- `priority`
- `confidence`

### Step 4：继续生成人物设定表

```bash
PYTHONPATH=src python -m feicai_seedance.cli build-character-sheets book-debug ep01 --project-root .
```

这一条会生成：

- `outputs/ep01/characters/character-sheets.json`
- `outputs/ep01/characters/character-sheets.md`

### Step 5：查看程序生成的人物设定

```bash
sed -n '1,240p' outputs/ep01/characters/character-sheets.md
```

### Step 6：理解程序测试的局限

程序当前这套逻辑主要依赖：

- 小说正文
- `outputs/ep01/01-director-analysis.json`
- `assets/character-prompts.md`
- 可选知识库 `project_data/knowledge_base`

但它目前不是按你新写的 `character-design` 文档做自然语言推理。

所以你看到下面这种情况，不要误判成 agent 文档有问题：

- 提取逻辑偏规则化
- 人物外观偏模板化
- 穿着描述保守但不够灵动

这说明的是“代码没接上 agent”，不是“agent 规范写错了”。

---

## 第七部分：推荐的人工验收表

你每轮都可以照着这个表打分。

```markdown
## Round X 验收

- 人物提取准确：是 / 否
- 主角无遗漏：是 / 否
- 功能角色无遗漏：是 / 否
- 未正面出场人物处理合理：是 / 否
- 外观描述可信：是 / 否
- 穿着描述保守且贴文：是 / 否
- 输出结构稳定：是 / 否

### 本轮最大问题
- 

### 下一轮只改这 1-2 条
- 
```

---

## 第八部分：你现在最推荐的测试顺序

不要跳步骤，按这个顺序来：

1. 先用 `标准 A` 做一轮手工单 Agent 测试
2. 保存结果，不改文档
3. 按“人物提取、乱抓、穿着脑补、气质偏差、结构稳定”五项验收
4. 只补充 1 到 2 条 prompt 约束，再跑第二轮
5. 第二轮稳定以后，再决定要不要切到 `标准 B`
6. 最后才去看 `fenjing_program` 的程序输出，把它当基线对照

---

## 最后的判断标准

如果第一轮结束后能达到下面这几点，就说明你的 `character-design` 已经可以继续迭代，而不是需要推倒重写：

- 顾星澜能稳定提取
- 守门内侍不漏
- 不会把所有被提及人物都强行展开
- 穿着描述基本保守，没有明显胡编
- 气质和身份大方向贴原文

如果做不到，再回到上面的 Debug 场景逐项修。
