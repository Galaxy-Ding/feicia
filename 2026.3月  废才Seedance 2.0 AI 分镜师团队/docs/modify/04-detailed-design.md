# 详细设计

## 1. 设计总则

保留现有目录与三阶段流程，只在关键节点插入 schema、validator、registry 和 structured review。

## 2. 导演阶段设计

### 2.1 新增结构化产物

建议新增：

- `outputs/<ep>/01-director-analysis.json`

核心字段：

```json
{
  "episode": "ep01",
  "plot_points": [
    {
      "id": "P01",
      "title": "回到空屋",
      "characters": ["林薇"],
      "scenes": ["深夜住宅客厅"],
      "shot_group_type": "single_shot",
      "duration_seconds": 8,
      "beats": [
        {"type": "action", "text": "推门进入"},
        {"type": "action", "text": "摸黑走向沙发"},
        {"type": "camera", "text": "侧脸推向杯子特写"}
      ],
      "safe_zone": {
        "head_seconds": 0.5,
        "tail_seconds": 0.5
      },
      "narration": "..."
    }
  ]
}
```

### 2.2 Director Validator

新增校验项：

- `narration_min_sentence_count`
- `abstract_word_ratio`
- `missing_action_chain`
- `missing_camera_direction`
- `missing_light_specificity`
- `beat_density_overflow`
- `safe_zone_violation`

### 2.3 抽象词规则

维护抽象词表，例如：

- 悲伤
- 孤独
- 疲惫
- 紧张
- 忧郁

不是一刀禁止，而是要求当抽象词出现时，必须有对应物理行为或环境承载句。

## 3. 服化道阶段设计

### 3.1 全局资产注册表

建议新增：

- `assets/registry/asset-registry.json`
- `assets/registry/character-index.json`
- `assets/registry/scene-index.json`

### 3.2 状态机

资产状态建议：

- `PROMPT_DRAFTED`
- `PROMPT_APPROVED`
- `IMAGE_PENDING`
- `IMAGE_REGISTERED`
- `READY_FOR_STORYBOARD`
- `RETIRED`

### 3.3 角色资产规则

- 新增：新角色，新 ID。
- 复用：指向已有 ID。
- 变体：新 ID，`variant_of` 指向原资产。

### 3.4 场景宫格拆分规则

宫格图只是一张“生产中间件”，不直接作为 Storyboard 引用对象。
必须把每个格子登记为独立 `scene_panel_asset`。

## 4. Storyboard 阶段设计

### 4.1 引用映射输入

Storyboard 不直接读取 `assets/*.md` 的原始全文，而是读取：

- 导演 JSON
- 已就绪资产清单
- `reference-map.json`

### 4.2 新增映射文件

建议新增：

- `outputs/<ep>/reference-map.json`

结构示例：

```json
{
  "episode": "ep01",
  "references": [
    {
      "ref_id": "@图片1",
      "asset_id": "char-linwei-v1",
      "asset_type": "character",
      "file_path": "assets/library/characters/char-linwei-v1.png",
      "purpose": "林薇主角"
    }
  ]
}
```

### 4.3 Seedance Prompt Validator

每条 Prompt 需要抽取：

- 图片引用数
- 视频引用数
- 音频引用数
- 总文件数
- 动作节拍数
- 镜头动作数
- 音频设计项

校验规则：

- 图片 <= 9
- 视频 <= 3
- 音频 <= 3
- 总文件 <= 12
- 单连续镜头 `beats <= floor((duration - 1.0) / 2.5)`
- 头尾 0.5 秒不放关键动作或关键台词

## 5. 审核协议设计

### 5.1 业务审核 JSON

```json
{
  "result": "FAIL",
  "average_score": 7.6,
  "has_item_below_6": true,
  "dimension_scores": {
    "fidelity": 8,
    "visual_clarity": 7,
    "action_executability": 5,
    "camera_executability": 8,
    "audio_design": 7,
    "emotion_accuracy": 8
  },
  "issues": [
    {
      "id": "ISSUE-001",
      "severity": "high",
      "location": "P03",
      "problem": "动作节拍超密",
      "fix_direction": "拆分为两个镜头组"
    }
  ],
  "report": "..."
}
```

### 5.2 合规审核 JSON

```json
{
  "result": "PASS",
  "violations": [],
  "issues": [],
  "report": "..."
}
```

### 5.3 自动接受逻辑

- `business.result == PASS`
- `average_score >= 8`
- `has_item_below_6 == false`
- `compliance.result == PASS`

任一失败则不可自动 ACCEPT。

## 6. 会话设计

当前 `SessionStore` 已能保存历史，但调用前未拼接历史消息。

改造要求：

- `get_or_create()` 后读取历史。
- 对生成、审核、修订分别设置历史窗口。
- 历史压缩采用摘要而非无限累积。

## 7. 状态检测设计

`status.py` 需要新增以下判断：

- 资产提示词已出但图片未登记：`ASSET_IMAGE_PENDING`
- 图片已登记但映射未生成：`REFERENCE_MAPPING_PENDING`
- Prompt 已出但结构化校验失败：`PROMPT_VALIDATION_FAILED`

## 8. 兼容策略

- 保留现有 Markdown 输出路径不变。
- 新增 JSON 和 registry 文件，不破坏老命令。
- CLI 增加新命令时采用增量方式，例如：
  - `register-asset-image`
  - `build-reference-map`
  - `validate director|design|prompt`
