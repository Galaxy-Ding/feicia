# VideoOnlyOnce 角色锚定资产流水线设计

## 1. 文档目标

本文件定义 `VideoOnlyOnce` 的角色锚定资产流水线，直接作为开发规格使用。

范围只覆盖：

- 人物提取
- 人物分层
- 角色关键词提炼
- 角色标准视图 prompt 生成
- 角色图生成任务
- 角色图复核
- 角色资产入库
- 给分镜和视频阶段导出角色引用包

不覆盖：

- 场景锚定
- 分镜拆解
- 视频生成
- TTS
- 总片合成

## 2. 设计原则

- 主角先定，分镜后做。
- 角色资产必须结构化，不允许只留 markdown 描述。
- 角色图必须先过审，再允许进入分镜和视频阶段。
- 群演不按“名字”建库，按“模板角色”建库。
- 所有角色资产必须可追溯到章节、任务、图片来源和审核记录。

## 3. 固定术语

- `character_candidate`
  - 从小说或剧本中提取出的候选人物
- `character_sheet`
  - 已结构化的人物设定卡
- `pose_pack`
  - 一个角色的标准视图集合
- `reference_image`
  - 审核通过的人物参考图
- `character_template`
  - 群演或高频职业模板
- `anchor_ready`
  - 角色锚定完成，可被分镜消费

## 4. 流水线总览

```text
章节/剧本
  -> extract-characters
  -> build-character-sheets
  -> export-character-image-tasks
  -> generate-character-images
  -> review-character-images
  -> approve-character-assets
  -> export-character-reference-pack
  -> 分镜阶段消费
```

## 5. 命令定义

所有命令建议挂在 `fenjing_program` 的 CLI 下。

## 5.1 extract-characters

### 命令

```bash
python -m feicai_seedance.cli extract-characters <book_id> <episode_id>
```

### 作用

从小说知识库和当前剧本中抽取“当前集涉及人物”，并按优先级输出候选人物清单。

### 输入

- `project_data/knowledge_base/entities/characters.json`
- `script/<episode_id>-*.md`
- `project_data/knowledge_base/character_bible.md`

### 输出

- `outputs/<episode_id>/characters/character-candidate-list.json`

### 阻断条件

- 当前集剧本不存在
- 知识库角色实体不存在且也无法从剧本中识别出人物

## 5.2 build-character-sheets

### 命令

```bash
python -m feicai_seedance.cli build-character-sheets <book_id> <episode_id>
```

### 作用

将候选人物转成角色卡，补齐外观锚点、服饰、发型、默认姿态、配件和提示词基座。

### 输入

- `outputs/<episode_id>/characters/character-candidate-list.json`
- `project_data/knowledge_base/entities/characters.json`
- `project_data/knowledge_base/visual_motifs.md`
- `project_data/style_presets/*.json`

### 输出

- `outputs/<episode_id>/characters/character-sheets.json`
- `outputs/<episode_id>/characters/character-sheets.md`

### 阻断条件

- 主角缺失外观锚点
- 主角未能确定默认服饰
- 主角未能确定默认武器或手持物

## 5.3 export-character-image-tasks

### 命令

```bash
python -m feicai_seedance.cli export-character-image-tasks <book_id> <episode_id>
```

### 作用

为角色卡导出标准视图出图任务。

### 输入

- `outputs/<episode_id>/characters/character-sheets.json`

### 输出

- `outputs/<episode_id>/characters/character-image-tasks.json`

### 默认产图视图

- `front_full_body`
- `side_full_body`
- `back_full_body`
- `front_half_body`

### 可选补充视图

- `walking_pose`
- `turn_back_pose`
- `raise_hand_pose`
- `weapon_hold_pose`
- `spell_cast_start_pose`

## 5.4 generate-character-images

### 命令

```bash
python -m feicai_seedance.cli generate-character-images <book_id> <episode_id> --browser <mock|openclaw>
```

### 作用

调用图片生成执行层，为角色标准视图批量出图。

### 输入

- `outputs/<episode_id>/characters/character-image-tasks.json`

### 输出

- `downloads/staging/characters/<episode_id>/...`
- `downloads/images/characters/<episode_id>/...`
- `outputs/<episode_id>/characters/character-image-run.json`

### 说明

第一版可以调用 `zaomeng` 的浏览器执行层，区别只是 prompt 来源从场景图任务换成人物图任务。

## 5.5 review-character-images

### 命令

```bash
python -m feicai_seedance.cli review-character-images <book_id> <episode_id>
```

### 作用

对生成人物图进行结构化审核，输出通过、驳回和待人工确认结果。

### 输入

- `outputs/<episode_id>/characters/character-sheets.json`
- `downloads/images/characters/<episode_id>/...`

### 输出

- `outputs/<episode_id>/characters/character-review.json`
- `outputs/<episode_id>/characters/character-review.md`

### 阻断条件

- 主角四视图未至少通过三张
- 主角正面全身图未通过
- 同一角色不同视图出现严重串脸

## 5.6 approve-character-assets

### 命令

```bash
python -m feicai_seedance.cli approve-character-assets <book_id> <episode_id>
```

### 作用

把审核通过的人物图正式入库，并更新角色索引。

### 输入

- `outputs/<episode_id>/characters/character-review.json`

### 输出

- `assets/library/characters/<character_id>/...`
- `assets/registry/character-index.json`
- `assets/registry/asset-registry.json`
- `outputs/<episode_id>/characters/character-anchor-pack.json`

### 阻断条件

- 主角未达到 `anchor_ready`
- 审核状态仍有 `pending_manual`

## 5.7 export-character-reference-pack

### 命令

```bash
python -m feicai_seedance.cli export-character-reference-pack <book_id> <episode_id>
```

### 作用

导出给分镜阶段和视频阶段消费的角色引用包。

### 输入

- `outputs/<episode_id>/characters/character-anchor-pack.json`
- `assets/registry/character-index.json`

### 输出

- `outputs/<episode_id>/characters/character-reference-pack.json`

## 6. 状态机定义

角色资产流水线状态固定如下：

- `CANDIDATE`
- `SHEET_READY`
- `TASK_READY`
- `IMAGE_GENERATED`
- `REVIEW_PENDING`
- `REVIEW_FAILED`
- `REVIEW_PASSED`
- `ANCHOR_READY`
- `BLOCKED`

### 状态推进规则

- `extract-characters` 完成后进入 `CANDIDATE`
- `build-character-sheets` 完成后进入 `SHEET_READY`
- `export-character-image-tasks` 完成后进入 `TASK_READY`
- 图片生成完成后进入 `IMAGE_GENERATED`
- 审核中进入 `REVIEW_PENDING`
- 审核不通过进入 `REVIEW_FAILED`
- 审核通过但未入库前保持 `REVIEW_PASSED`
- 入库完成后进入 `ANCHOR_READY`

## 7. 目录结构

目录固定如下：

```text
project_data/
  knowledge_base/
    entities/
      characters.json
    character_bible.md
    visual_motifs.md

assets/
  library/
    characters/
      <character_id>/
        front_full_body_v1.png
        side_full_body_v1.png
        back_full_body_v1.png
        front_half_body_v1.png
        weapon_hold_pose_v1.png
  registry/
    character-index.json
    asset-registry.json

downloads/
  staging/
    characters/
      <episode_id>/
        <task_id>/
  images/
    characters/
      <episode_id>/
        <task_id>/

outputs/
  <episode_id>/
    characters/
      character-candidate-list.json
      character-sheets.json
      character-sheets.md
      character-image-tasks.json
      character-image-run.json
      character-review.json
      character-review.md
      character-anchor-pack.json
      character-reference-pack.json
```

## 8. 文件 Schema

## 8.1 `character-candidate-list.json`

### 结构

```json
{
  "book_id": "book001",
  "episode_id": "ep01",
  "generated_at": "2026-03-26T20:00:00+08:00",
  "characters": [
    {
      "character_id": "char_lin_du",
      "name": "林渡",
      "role_type": "主角",
      "priority": "tier_a",
      "source_chapters": ["ch001", "ch002", "ch003"],
      "source_episode": "ep01",
      "confidence": 0.95
    }
  ],
  "templates": [
    {
      "template_id": "tmpl_sect_disciple_male",
      "name": "宗门男弟子模板",
      "priority": "tier_b",
      "usage_reason": "群演高频"
    }
  ]
}
```

### 必填字段

- `book_id`
- `episode_id`
- `generated_at`
- `characters`

### 校验规则

- `characters` 不允许为空
- 必须至少存在一个 `role_type=主角`
- `priority` 仅允许 `tier_a`、`tier_b`、`tier_c`

## 8.2 `character-sheets.json`

### 结构

```json
{
  "book_id": "book001",
  "episode_id": "ep01",
  "style_preset": "ink_fantasy_v1",
  "characters": [
    {
      "character_id": "char_lin_du",
      "name": "林渡",
      "role_type": "主角",
      "priority": "tier_a",
      "status": "SHEET_READY",
      "ethnicity_hint": "东方面孔",
      "age_impression": "二十岁上下",
      "body_type": "清瘦修长",
      "temperament": ["冷静", "警惕", "隐忍"],
      "visual_keywords": ["黑发", "浅灰道袍", "旧剑", "清瘦", "东方面孔"],
      "costume_keywords": ["浅灰道袍", "旧布腰带", "布靴"],
      "hair_keywords": ["黑发", "半束发"],
      "face_keywords": ["清瘦", "冷峻", "细长眼"],
      "accessories": ["旧剑", "木牌"],
      "default_pose_set": [
        "front_full_body",
        "side_full_body",
        "back_full_body",
        "front_half_body"
      ],
      "optional_pose_set": [
        "turn_back_pose",
        "weapon_hold_pose"
      ],
      "default_prompt_base": "东方面孔青年男性，黑发半束发，浅灰道袍，旧剑，垂直双手，站在原地，正面全身，角色设定展示图",
      "negative_prompt": "多人，背景剧情画面，夸张透视，手部畸形，现代西装，欧美甲胄",
      "source_refs": ["ch001", "ch002", "ep01-script"],
      "review_notes": []
    }
  ]
}
```

### 必填字段

- `character_id`
- `name`
- `role_type`
- `priority`
- `status`
- `visual_keywords`
- `costume_keywords`
- `hair_keywords`
- `face_keywords`
- `default_pose_set`
- `default_prompt_base`
- `negative_prompt`

### 校验规则

- 主角的 `default_pose_set` 必须包含 4 个标准视图
- `visual_keywords` 最少 5 个，最多 12 个
- `costume_keywords` 最少 2 个
- `default_prompt_base` 不允许为空

## 8.3 `character-image-tasks.json`

### 结构

```json
{
  "book_id": "book001",
  "episode_id": "ep01",
  "tasks": [
    {
      "task_id": "ep01-char_lin_du-front_full_body-v1",
      "character_id": "char_lin_du",
      "pose_type": "front_full_body",
      "priority": "tier_a",
      "prompt": "东方面孔青年男性，黑发半束发，浅灰道袍，旧剑，垂直双手，站在原地，正面全身，角色设定展示图，纯净背景，方便观察服饰轮廓",
      "negative_prompt": "多人，背景剧情画面，夸张透视，手部畸形，现代西装，欧美甲胄",
      "style_preset": "ink_fantasy_v1",
      "shots_reserved_for": []
    }
  ]
}
```

### 必填字段

- `task_id`
- `character_id`
- `pose_type`
- `prompt`
- `negative_prompt`
- `style_preset`

### 校验规则

- 同一 `character_id + pose_type + version` 不可重复
- 主角必须生成至少 4 条任务

## 8.4 `character-review.json`

### 结构

```json
{
  "book_id": "book001",
  "episode_id": "ep01",
  "reviewed_at": "2026-03-26T21:00:00+08:00",
  "characters": [
    {
      "character_id": "char_lin_du",
      "overall_status": "passed",
      "pose_reviews": [
        {
          "task_id": "ep01-char_lin_du-front_full_body-v1",
          "pose_type": "front_full_body",
          "selected_image": "downloads/images/characters/ep01/ep01-char_lin_du-front_full_body-v1/best.png",
          "scores": {
            "face_consistency": 0.91,
            "costume_consistency": 0.95,
            "accessory_consistency": 0.88,
            "body_visibility": 0.98,
            "pose_clarity": 0.96,
            "style_match": 0.92
          },
          "decision": "pass",
          "issues": []
        }
      ],
      "manual_flags": [],
      "ready_for_anchor": true
    }
  ]
}
```

### 必填字段

- `character_id`
- `overall_status`
- `pose_reviews`
- `ready_for_anchor`

### 校验规则

- 主角 `overall_status` 不是 `passed` 时，不允许入库
- 每条 `pose_reviews` 必须包含 `decision`
- `decision` 仅允许 `pass`、`reject`、`pending_manual`

## 8.5 `character-anchor-pack.json`

### 结构

```json
{
  "book_id": "book001",
  "episode_id": "ep01",
  "generated_at": "2026-03-26T21:30:00+08:00",
  "characters": [
    {
      "character_id": "char_lin_du",
      "anchor_status": "ANCHOR_READY",
      "reference_images": {
        "front_full_body": "assets/library/characters/char_lin_du/front_full_body_v1.png",
        "side_full_body": "assets/library/characters/char_lin_du/side_full_body_v1.png",
        "back_full_body": "assets/library/characters/char_lin_du/back_full_body_v1.png",
        "front_half_body": "assets/library/characters/char_lin_du/front_half_body_v1.png"
      },
      "selected_visual_keywords": ["黑发", "浅灰道袍", "旧剑", "清瘦", "东方面孔"],
      "selected_accessories": ["旧剑", "木牌"],
      "usable_for_storyboard": true
    }
  ]
}
```

### 校验规则

- 主角必须 `usable_for_storyboard=true`
- 主角四视图缺任意关键图时，不能导出到分镜阶段

## 8.6 `character-reference-pack.json`

### 结构

```json
{
  "episode_id": "ep01",
  "characters": [
    {
      "character_id": "char_lin_du",
      "shot_ref_id": "char_lin_du_front_v1",
      "primary_image": "assets/library/characters/char_lin_du/front_full_body_v1.png",
      "alternate_images": [
        "assets/library/characters/char_lin_du/side_full_body_v1.png",
        "assets/library/characters/char_lin_du/back_full_body_v1.png"
      ],
      "keywords": ["黑发", "浅灰道袍", "旧剑", "清瘦", "东方面孔"]
    }
  ]
}
```

### 用途

该文件直接供 `02-shot-plan.json` 和视频 prompt 构建器引用。

## 9. 审核规则

## 9.1 统一审核维度

每张角色图固定从以下维度评分：

- `face_consistency`
- `hair_consistency`
- `costume_consistency`
- `accessory_consistency`
- `species_ethnicity_match`
- `body_visibility`
- `pose_clarity`
- `style_match`
- `clean_background`
- `deformation_risk`

## 9.2 评分区间

- 0.90 到 1.00：优秀，可直接通过
- 0.80 到 0.89：可通过，但允许人工复核
- 0.70 到 0.79：默认驳回，必要时人工复核
- 0.00 到 0.69：直接驳回

## 9.3 主角通过规则

主角满足以下条件才算 `anchor_ready`：

- `front_full_body` 必须通过
- `side_full_body` 和 `back_full_body` 至少通过一张中的两张
- `front_half_body` 必须通过
- `costume_consistency >= 0.90`
- `face_consistency >= 0.85`
- `body_visibility >= 0.90`
- `deformation_risk >= 0.80`

## 9.4 配角通过规则

- 至少通过 `front_full_body`
- 其他视图允许缺失
- 若该配角在本集出现镜头数 >= 3，则必须补齐 `front_half_body`

## 9.5 模板角色通过规则

- 只要求模板风格统一
- 不要求严格人脸唯一性
- 但服饰、身份、时代感不能错

## 9.6 直接驳回规则

出现以下任一项直接 `reject`：

- 多人混入
- 手部严重畸形
- 脚部严重畸形
- 服饰时代错位
- 武器/法器缺失
- 发型明显漂移
- 人种/族裔感错误
- 画面不是展示图而是剧情图
- 看不清全身轮廓

## 9.7 待人工确认规则

出现以下情况记为 `pending_manual`：

- 主角脸部略有变化，但服饰和气质高度一致
- 首饰缺失但不影响主识别
- 武器版本有轻微变化
- 颜色偏差小，但整体风格正确

## 10. 命名规则

## 10.1 角色 ID

格式固定：

```text
char_<slug>
```

示例：

- `char_lin_du`
- `char_su_wan`

## 10.2 模板 ID

格式固定：

```text
tmpl_<scene_or_role>_<gender_or_type>
```

示例：

- `tmpl_sect_disciple_male`
- `tmpl_city_commoner_female`

## 10.3 人物图任务 ID

格式固定：

```text
<episode_id>-<character_id>-<pose_type>-v<version>
```

示例：

- `ep01-char_lin_du-front_full_body-v1`

## 10.4 资产文件名

格式固定：

```text
<pose_type>_v<version>.png
```

示例：

- `front_full_body_v1.png`
- `weapon_hold_pose_v1.png`

## 11. 分镜阶段消费规则

分镜阶段只能消费 `character-reference-pack.json`，不能直接绕过引用原始下载图。

### 固定规则

- 一个镜头里出现主角，必须挂 `character_refs`
- 若镜头是近景或特写，优先引用 `front_half_body`
- 若镜头是背身离场，优先引用 `back_full_body`
- 若镜头包含转身动作，优先引用 `side_full_body` 或 `turn_back_pose`

### `02-shot-plan.json` 建议字段

```json
{
  "shot_id": "ep01-s001",
  "characters": ["char_lin_du"],
  "character_refs": ["char_lin_du_front_v1"],
  "scene_id": "scene_mountain_gate_night",
  "action": "抬头看向山门，右手握紧令牌"
}
```

## 12. 最小实现顺序

第一版严格按下面顺序开发：

1. `extract-characters`
2. `build-character-sheets`
3. `export-character-image-tasks`
4. `review-character-images`
5. `approve-character-assets`
6. `export-character-reference-pack`

`generate-character-images` 可以先复用 `zaomeng` 现有图片生成能力，后面再做专门适配。

## 13. 验收清单

- 命令行可独立跑通人物锚定链路
- 主角可输出 4 个标准视图任务
- 主角可形成 `character_sheet`
- 主角可形成 `character-anchor-pack`
- 分镜阶段可引用 `character-reference-pack`
- 所有角色图都能追溯到 task_id 和审核记录

## 14. 结论

角色锚定资产流水线必须视为分镜之前的独立生产阶段，不是附属步骤。

这条链路跑通之后，后续的：

- 分镜图片
- 视频参考图
- 角色一致性控制
- 镜头级引用

才会真正稳定。
