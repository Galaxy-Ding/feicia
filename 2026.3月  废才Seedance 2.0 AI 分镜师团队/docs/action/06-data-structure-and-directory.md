# 数据结构与目录规范

## 1. 目录规范

建议实现目录如下：

```text
project/
├─ script/
│  ├─ ep01-xxx.md
│  └─ ep02-xxx.md
├─ assets/
│  ├─ character-prompts.md
│  └─ scene-prompts.md
├─ outputs/
│  ├─ ep01/
│  │  ├─ 01-director-analysis.md
│  │  └─ 02-seedance-prompts.md
│  └─ ep02/
│     ├─ 01-director-analysis.md
│     └─ 02-seedance-prompts.md
├─ logs/
│  ├─ run-log.jsonl
│  └─ review-log.jsonl
├─ prompts/
│  ├─ CLAUDE.md
│  ├─ agents/
│  └─ skills/
├─ .agent-state.json
└─ project-config.json
```

## 2. 核心文件职责

| 路径 | 职责 | 写入方式 |
|---|---|---|
| `script/*.md` | 输入剧本 | 手工维护 |
| `outputs/<ep>/01-director-analysis.md` | 导演分析产物 | 覆盖写 |
| `assets/character-prompts.md` | 人物资产提示词 | 追加写 |
| `assets/scene-prompts.md` | 场景资产提示词 | 追加写 |
| `outputs/<ep>/02-seedance-prompts.md` | Seedance 分镜提示词 | 覆盖写 |
| `.agent-state.json` | Agent 恢复状态 | 覆盖写 |
| `logs/*.jsonl` | 运行与审核日志 | 追加写 |

## 3. `.agent-state.json` 结构

```json
{
  "episode": "ep01",
  "director": "agent_xxx",
  "art-designer": "agent_yyy",
  "storyboard-artist": "agent_zzz",
  "updated_at": "2026-03-23T16:30:00+08:00"
}
```

规则：

- 同一集内有效
- 跨集时重置为新对象或清空字段

## 4. `project-config.json` 建议结构

```json
{
  "project_name": "Feicai Seedance 2.0",
  "language": "zh-CN",
  "visual_style": "由用户首次指定",
  "target_media": "短剧",
  "max_episode_count": 10,
  "command_prefix": "~",
  "review": {
    "max_auto_fix_rounds": 3
  },
  "paths": {
    "scripts": "./script",
    "assets": "./assets",
    "outputs": "./outputs",
    "logs": "./logs",
    "prompts": "./prompts"
  }
}
```

## 5. 日志结构

### 5.1 `run-log.jsonl`

每行一个 JSON：

```json
{
  "time": "2026-03-23T16:35:00+08:00",
  "episode": "ep01",
  "command": "~start ep01",
  "stage": "DIRECTOR_ANALYSIS",
  "status": "SUCCESS",
  "model": "director_generate_model",
  "output_file": "outputs/ep01/01-director-analysis.md"
}
```

### 5.2 `review-log.jsonl`

```json
{
  "time": "2026-03-23T16:40:00+08:00",
  "episode": "ep01",
  "stage": "DIRECTOR_REVIEW",
  "review_type": "business",
  "result": "FAIL",
  "round": 1,
  "issues_count": 3
}
```

## 6. 产物结构约束

### 6.1 `01-director-analysis.md`

必须包含：

- 导演讲戏本
- 人物清单
- 场景清单

### 6.2 `character-prompts.md`

必须满足：

- 角色名
- 集数标签
- 出图要求
- 完整提示词

### 6.3 `scene-prompts.md`

必须满足：

- 宫格规格
- 视觉规范
- 布局说明
- Panel Breakdown

### 6.4 `02-seedance-prompts.md`

必须满足：

- 素材对应表
- 每个剧情点的 Seedance 提示词

## 7. 资源状态枚举

建议统一使用：

- `新增`
- `复用 char-xxx / scene-xxx`
- `变体 char-xxx（说明）`
- `变体 scene-xxx（说明）`

## 8. 命名规范

### 8.1 集数

- `ep01`
- `ep02`
- `ep03`

### 8.2 输出文件

- 固定命名，不允许自由发挥

### 8.3 角色与场景

- 角色名必须前后一致
- 场景名必须前后一致
- 不要同义词混用，否则会破坏素材映射

## 9. 第一版实现建议

第一版不要引入数据库实体模型，直接围绕这些文件结构开发。这样最贴近原工程，也最容易验证复刻是否成功。
