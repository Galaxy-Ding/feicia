# 数据结构与目录设计

## 1. 建议目录

```text
assets/
├─ character-prompts.md
├─ scene-prompts.md
├─ registry/
│  ├─ asset-registry.json
│  ├─ character-index.json
│  └─ scene-index.json
├─ library/
│  ├─ characters/
│  ├─ scenes/
│  └─ scene-panels/
└─ manifests/
   └─ image-generation-log.jsonl

outputs/
└─ ep01/
   ├─ 01-director-analysis.md
   ├─ 01-director-analysis.json
   ├─ 02-seedance-prompts.md
   ├─ 02-seedance-prompts.json
   ├─ reference-map.json
   └─ validation/
      ├─ director-validation.json
      ├─ design-validation.json
      └─ prompt-validation.json
```

## 2. 资产注册表字段

```json
{
  "asset_id": "char-linwei-v1",
  "asset_type": "character",
  "name": "林薇",
  "episode_origin": "ep01",
  "status": "READY_FOR_STORYBOARD",
  "prompt_entry_ref": "assets/character-prompts.md#林薇（ep01 新增）",
  "image_path": "assets/library/characters/char-linwei-v1.png",
  "variant_of": null,
  "tags": ["主角", "办公室线"],
  "updated_at": "2026-03-24T10:00:00+08:00"
}
```

## 3. Prompt 结构化产物字段

### 3.1 Director JSON

- `plot_points[]`
- `characters[]`
- `scenes[]`
- `rule_flags[]`

### 3.2 Seedance JSON

- `prompts[]`
- `reference_usage[]`
- `validation_summary`

## 4. 报告结构

建议把报告分成三层：

- `reviews/`：原始审核轮次输出
- `assessments/`：人工决策视角汇总
- `validation/`：规则引擎静态检查结果

## 5. 版本追踪

建议每个产物记录：

- `version`
- `source_version`
- `review_round`
- `accepted_by`
- `accepted_at`

## 6. 文件命名建议

- 角色图片：`char-<slug>-v<version>.png`
- 场景宫格图：`scenegrid-<episode>-v<version>.png`
- 场景拆图：`scene-<slug>-panel-<n>-v<version>.png`
- 参考映射：`reference-map.json`
