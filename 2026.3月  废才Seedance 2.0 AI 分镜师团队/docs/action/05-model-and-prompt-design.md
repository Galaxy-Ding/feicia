# 模型与 Prompt 编排设计

## 1. 设计原则

要复刻当前项目，最关键的不是“换哪个模型名”，而是保留下面三层结构：

1. 角色 Prompt
2. 技能 Prompt
3. 编排 Prompt

其中：

- 角色 Prompt 定义身份与职责
- 技能 Prompt 定义执行方法
- 编排 Prompt 定义先后顺序、文件读写、审核闭环

## 2. Prompt 资产映射

| 运行时角色 | 原始文件 | 用法 |
|---|---|---|
| 制片人/总控 | `CLAUDE.md` | 系统总提示词 |
| 导演 Agent | `agents/director.md` | Agent 系统提示词 |
| 服化道 Agent | `agents/art-designer.md` | Agent 系统提示词 |
| 分镜师 Agent | `agents/storyboard-artist.md` | Agent 系统提示词 |
| 导演执行 Skill | `skills/director-skill/SKILL.md` | 阶段一加载 |
| 服化道执行 Skill | `skills/art-design-skill/SKILL.md` | 阶段二加载 |
| 分镜执行 Skill | `skills/seedance-storyboard-skill/SKILL.md` | 阶段三加载 |
| 阶段一业务审核 | `skills/script-analysis-review-skill/SKILL.md` | 导演审核 |
| 阶段二业务审核 | `skills/art-direction-review-skill/SKILL.md` | 导演审核 |
| 阶段三业务审核 | `skills/seedance-prompt-review-skill/SKILL.md` | 导演审核 |
| 合规审核 | `skills/compliance-review-skill/SKILL.md` | 全阶段审核 |

## 3. 推荐模型能力分工

### 3.1 制片人/编排器

能力要求：

- 长上下文
- 强指令遵循
- 稳定结构化输出
- 能处理路由、状态判断、错误恢复

建议：

- 使用你手里最强的推理模型
- 温度低

### 3.2 导演 Agent

能力要求：

- 强叙事理解
- 强剧情拆解
- 强审稿能力
- 长文输出稳定

建议：

- 使用最强模型或与编排器相同模型
- 生成温度中低
- 审核温度更低

### 3.3 服化道 Agent

能力要求：

- 视觉语言丰富
- 细节描述稳定
- 长段叙事式图像提示词能力强

建议：

- 可使用次一级模型，但必须保证中文长文能力
- 温度略高于导演审核

### 3.4 分镜师 Agent

能力要求：

- 能把导演阐述转成动态镜头语言
- 能控制动作、运镜、音效、节拍密度
- 能稳定产出长段 Seedance 风格提示词

建议：

- 使用强指令遵循模型
- 如预算允许，与导演同级

## 4. 单模型部署与双模型部署

### 4.1 单模型部署

适用：

- API 预算有限
- 先做验证版

方案：

- 制片人、导演、服化道、分镜、审核全部使用同一模型
- 通过不同系统 Prompt 和温度差异实现角色区分

### 4.2 双模型部署

适用：

- 追求稳定性与成本平衡

方案：

- 强推理模型：制片人、导演执行、全部审核
- 性价比模型：服化道、分镜生成

## 5. 参数建议

| 角色 | 温度 | 最大输出 | 说明 |
|---|---:|---:|---|
| 制片人 | 0.2 | 4k-8k | 以稳定路由为主 |
| 导演执行 | 0.4 | 8k-16k | 允许一定创造性 |
| 导演审核 | 0.1-0.2 | 6k-12k | 审稿要保守 |
| 服化道 | 0.5-0.7 | 8k-16k | 细节丰富 |
| 分镜师 | 0.4-0.6 | 8k-16k | 保持叙事与镜头张力 |
| 合规审核 | 0.1 | 4k-8k | 尽量确定性 |

## 6. 运行时 Prompt 组装方式

### 6.1 阶段一执行

运行时上下文建议为：

1. 制片人总控规则
2. 导演角色 Prompt
3. 导演 Skill
4. 模板文件
5. 剧本内容
6. 历史素材摘要

### 6.2 阶段二执行

运行时上下文建议为：

1. 制片人总控规则
2. 服化道角色 Prompt
3. 服化道 Skill
4. 图片提示词指南
5. 相关示例
6. 导演分析文件
7. 历史 assets 文件

### 6.3 阶段三执行

运行时上下文建议为：

1. 制片人总控规则
2. 分镜师角色 Prompt
3. Seedance Skill
4. Seedance 方法论
5. Seedance 示例
6. 导演分析文件
7. 角色/场景提示词文件

## 7. 审核 Prompt 组装方式

### 7.1 业务审核

统一原则：

- 仍由导演 Agent 执行
- 只是切换加载不同 review skill

### 7.2 合规审核

统一原则：

- 同样由导演 Agent 执行
- 加载 `compliance-review-skill`

## 8. 建议模型配置文件

```json
{
  "provider": "openai-compatible",
  "base_url": "https://your-api-base/v1",
  "api_key_env": "LLM_API_KEY",
  "models": {
    "orchestrator": "your-best-reasoning-model",
    "director_generate": "your-best-reasoning-model",
    "director_review": "your-best-reasoning-model",
    "art_designer": "your-creative-longform-model",
    "storyboard_artist": "your-strong-instruct-model",
    "compliance_review": "your-best-reasoning-model"
  },
  "params": {
    "orchestrator": { "temperature": 0.2, "max_tokens": 8000 },
    "director_generate": { "temperature": 0.4, "max_tokens": 12000 },
    "director_review": { "temperature": 0.1, "max_tokens": 10000 },
    "art_designer": { "temperature": 0.6, "max_tokens": 12000 },
    "storyboard_artist": { "temperature": 0.5, "max_tokens": 12000 },
    "compliance_review": { "temperature": 0.1, "max_tokens": 8000 }
  }
}
```

## 9. 强制约束

- 所有输出必须为中文
- 审核环节必须使用低温度
- Prompt 文件尽量原样复用，不随意精简
- 模型升级时，只替换配置，不重构流程
