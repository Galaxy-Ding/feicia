# ep01 样例清单模板与 agent 复刻说明

## 1. 文档目标

这份文档解决两件事：

- 给你一个可以直接填写的样例清单模板
- 把我这次做事的思路、工具和困难按任务拆开，方便你复刻成 agent

## 2. 任务拆解记录

### 任务 A：帮 ep01 设计该放哪几张图最合适

#### A1. 我打算怎么做

我先不碰“怎么命名”，先回答“该选哪类图”。

具体步骤是：

1. 看 `ep01` 剧本，提炼核心人物和核心空间
2. 看 `character-prompts.md`，确认角色资产池
3. 看 `scene-prompts.md`，确认场景资产池
4. 对照验收目标，优先选“主角、关键线索、关键空间”
5. 再从这些对象里挑适合做变体的一组

#### A2. 我实际用了什么工具

- `Get-Content`
  - 读取剧本
  - 读取角色 prompt
  - 读取场景 prompt
- `Get-ChildItem`
  - 检查是否已经存在 `outputs/`
  - 检查是否已经存在真实图片样例

#### A3. 我遇到什么困难

- 没有 `outputs/`，无法从现有产物倒推
- 没有真实已登记图片，无法从 registry 里挑成图
- 终端存在中文编码噪声，只能结合结构和上下文判断

#### A4. 我最后怎么解决

- 放弃“从已有图片里挑”
- 改成“从剧本与提示词反推最关键的样例候选”
- 先给最小集合，再给完整集合

### 任务 B：给出一个可直接填写的样例清单模板

#### B1. 我打算怎么做

模板必须满足三件事：

1. 能直接填写
2. 能直接落到文件目录
3. 能被后续 agent 稳定复用

所以模板我按下面的结构设计：

- 黄金样例清单
- 变体样例清单
- 文件落点
- 完成状态
- 验收复跑命令

#### B2. 我实际用了什么工具

- 文本编辑
- 本地文件结构对照
- `acceptance_runner.py` 的目录规则阅读

#### B3. 我遇到什么困难

- 当前代码只检查“目录里有没有图片”，不会检查图片和 registry 的语义绑定
- 所以模板不能只写“放图即可”，还得提示优先放那些能回接到资产体系的图

#### B4. 我最后怎么解决

- 模板里显式增加“来源资产 / 是否已 register-image / 是否进入 reference-map”三个字段
- 即使当前程序不强校验，人工验收时也能看出证据质量

## 3. 建议给 agent 的工作流

如果你要做一个类似 agent，我建议把提示词逻辑固化为：

1. 读取指定 episode 的剧本
2. 读取角色 prompt 文件
3. 读取场景 prompt 文件
4. 检查 `outputs/<ep>/` 是否存在
5. 检查 `assets/acceptance/<ep>/golden/` 和 `variants/` 是否存在
6. 输出：
   - 黄金样例建议
   - 变体样例建议
   - 可填写清单模板
   - 当前缺失项

推荐 agent 输出结构：

- `输入盘点`
- `关键角色`
- `关键场景`
- `黄金样例建议`
- `变体样例建议`
- `待补文件路径`
- `可填写模板`
- `复跑命令`

## 4. ep01 可直接填写的样例清单模板

下面这份模板你可以直接复制使用。

---

# ep01 样例清单

## A. 黄金样例清单

| 序号 | 建议文件名 | 样例类型 | 对应角色/场景 | 来源文件 | 是否已生成真实图 | 是否已 register-image | 是否已进入 reference-map | 备注 |
|---|---|---|---|---|---|---|---|---|
| 1 | `char-gu-xinglan-golden-standard.png` | 黄金样例 | 顾星澜标准角色 | `assets/character-prompts.md` | [ ] | [ ] | [ ] | 主角标准图 |
| 2 | `char-shen-junbai-golden-standard.png` | 黄金样例 | 沈钧白标准角色 | `assets/character-prompts.md` | [ ] | [ ] | [ ] | 核心事件人物 |
| 3 | `scene-shen-study-golden-clue.png` | 黄金样例 | 沈钧白书房 | `assets/scene-prompts.md` | [ ] | [ ] | [ ] | 关键取证场景 |
| 4 | `scene-gu-room-golden-strategy.png` | 黄金样例 | 顾星澜算房 | `assets/scene-prompts.md` | [ ] | [ ] | [ ] | 主角推演空间 |

## B. 变体样例清单

| 序号 | 建议文件名 | 样例类型 | 对应角色/场景 | 变体维度 | 来源文件 | 是否已生成真实图 | 是否已 register-image | 是否已进入 reference-map | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `char-gu-xinglan-variant-night-duty.png` | 变体样例 | 顾星澜 | 同角色，不同状态或光线 | `assets/character-prompts.md` | [ ] | [ ] | [ ] | 优先补 |
| 2 | `scene-shen-study-variant-searched.png` | 变体样例 | 沈钧白书房 | 同场景，不同叙事状态 | `assets/scene-prompts.md` | [ ] | [ ] | [ ] | 优先补 |
| 3 | `scene-gu-room-variant-dawn-shift.png` | 变体样例 | 顾星澜算房 | 同场景，不同时段 | `assets/scene-prompts.md` | [ ] | [ ] | [ ] | 次优先 |
| 4 | `char-xiao-jingyan-variant-court-pressure.png` | 变体样例 | 萧景琰 | 同角色，不同场合气场 | `assets/character-prompts.md` | [ ] | [ ] | [ ] | 补充项 |

## C. 文件实际落点

### 黄金样例目录

- `assets/acceptance/ep01/golden/char-gu-xinglan-golden-standard.png`
- `assets/acceptance/ep01/golden/char-shen-junbai-golden-standard.png`
- `assets/acceptance/ep01/golden/scene-shen-study-golden-clue.png`
- `assets/acceptance/ep01/golden/scene-gu-room-golden-strategy.png`

### 变体样例目录

- `assets/acceptance/ep01/variants/char-gu-xinglan-variant-night-duty.png`
- `assets/acceptance/ep01/variants/scene-shen-study-variant-searched.png`
- `assets/acceptance/ep01/variants/scene-gu-room-variant-dawn-shift.png`
- `assets/acceptance/ep01/variants/char-xiao-jingyan-variant-court-pressure.png`

## D. 完成后复跑

```bash
python -m feicai_seedance.cli acceptance-evidence ep01
```

---

## 5. 给后续 agent 的模板判断规则

如果后面要做 agent 自动输出这个模板，我建议写死以下判断规则：

### 规则 1：先出最小集

最小集固定为：

- 2 张角色黄金图
- 1 张关键场景黄金图
- 1 张角色变体图
- 1 张场景变体图

### 规则 2：优先级按叙事价值排序

排序顺序建议为：

1. 主角
2. 关键事件人物
3. 核心线索场景
4. 核心推演场景
5. 权力对立角色

### 规则 3：优先推荐“同对象变体”

变体建议必须尽量满足：

- 同一个角色的不同状态
- 同一个场景的不同状态

而不是换成一个完全无关的新角色或新场景。

### 规则 4：模板字段不要省

至少保留这些字段：

- 建议文件名
- 样例类型
- 对应角色/场景
- 来源文件
- 是否已生成真实图
- 是否已 register-image
- 是否已进入 reference-map
- 备注

## 6. 当前结论

如果你接下来就要开始补图，我建议你直接从这 5 个文件开始：

- `assets/acceptance/ep01/golden/char-gu-xinglan-golden-standard.png`
- `assets/acceptance/ep01/golden/char-shen-junbai-golden-standard.png`
- `assets/acceptance/ep01/golden/scene-shen-study-golden-clue.png`
- `assets/acceptance/ep01/variants/char-gu-xinglan-variant-night-duty.png`
- `assets/acceptance/ep01/variants/scene-shen-study-variant-searched.png`

这是当前最小成本、同时也最像“最终验收证据”的一组起步方案。
