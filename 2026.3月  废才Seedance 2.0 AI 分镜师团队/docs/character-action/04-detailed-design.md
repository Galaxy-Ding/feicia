# 详细设计

## 1. 建议代码目录

建议后续新增独立工程目录：

```text
character_action/
  README.md
  pyproject.toml
  src/character_action/
    __init__.py
    cli.py
    config.py
    graph/
      state.py
      nodes.py
      router.py
      checkpoints.py
    preprocess/
      hanlp_adapter.py
      booknlp_adapter.py
      normalizer.py
    extractors/
      rule_extractor.py
      llm_extractor.py
      merge_engine.py
      relation_engine.py
    schemas/
      book.schema.json
      character.schema.json
      relation.schema.json
      review_task.schema.json
    storage/
      models.py
      sqlite_repo.py
      postgres_repo.py
      migrations/
    review/
      qa_rules.py
      review_queue.py
      audit_log.py
  tests/
    test_preprocess.py
    test_extractors.py
    test_graph.py
    test_storage.py
    test_review.py
```

## 2. LangGraph 状态设计

建议统一状态对象至少包含：

- `run_id`
- `book_id`
- `language`
- `current_stage`
- `chapter_cursor`
- `chunk_cursor`
- `normalized_units`
- `candidate_characters`
- `canonical_characters`
- `relations`
- `evidence_items`
- `qa_findings`
- `review_tasks`
- `manual_patches`
- `schema_version`

要求：

- 所有节点只读写明确字段
- 所有可恢复节点必须在节点结束后落 checkpoint
- 人工审核的输入与输出必须写入状态

## 3. 图节点设计

### 3.1 `ingest_book`

- 校验书籍元数据
- 建立书籍记录
- 执行章节切分

### 3.2 `route_language`

- 判断 `zh` / `en`
- 路由到 `HanLP` 或 `BookNLP` 适配器

### 3.3 `preprocess_chunks`

- 逐章节、逐 chunk 运行 NLP 预处理
- 统一中间格式

### 3.4 `extract_candidates_rule`

- 从命名实体、称谓、说话人、引号上下文中生成候选角色

### 3.5 `extract_candidates_llm`

- 对规则结果做补全
- 补出隐式提及、弱别名和复杂关系候选

### 3.6 `merge_aliases`

- 根据名字相似度、共指、上下文角色标签进行归并
- 对不确定 merge 生成待审核任务

### 3.7 `build_profiles`

- 汇总人物属性
- 生成角色摘要、标签、首次出场信息、典型证据

### 3.8 `build_relations`

- 生成关系边
- 输出方向、关系类型、置信度和证据引用

### 3.9 `run_qa`

- 检查 schema
- 检查证据缺失
- 检查冲突字段
- 检查重复 canonical character

### 3.10 `human_review_gate`

- 低置信度或冲突项中断
- 生成 review task
- 应用审核修正并恢复流程

### 3.11 `materialize_results`

- 写入人物表、别名表、关系表、证据表、审核表

## 4. 抽取器分工

### 4.1 规则抽取器

适合处理：

- 明确姓名提及
- 称谓模式
- 对话说话人
- 固定关系模式
- 章节首次出场定位

### 4.2 LLM 抽取器

适合处理：

- 隐式别名
- 指代消解补全
- 复杂身份总结
- 关系语义归纳
- 角色描述压缩

### 4.3 执行顺序

- 先规则抽
- 再 LLM 补
- 再 merge
- 再 QA

不允许跳过规则层直接把整本书丢给 LLM。

## 5. Schema 设计

### 5.1 Character Schema 关键字段

```json
{
  "character_id": "char_001",
  "book_id": "book_demo",
  "canonical_name": "林晚",
  "aliases": ["晚晚", "林小姐"],
  "language": "zh",
  "gender_guess": "female",
  "roles": ["主角", "医生"],
  "first_appearance": {
    "chapter_id": "ch_001",
    "chunk_id": "ch_001_ck_003"
  },
  "summary": "核心女主角，理性克制，职业是医生。",
  "evidence_ids": ["ev_101", "ev_102"],
  "confidence": 0.93,
  "review_status": "approved"
}
```

### 5.2 Relation Schema 关键字段

```json
{
  "relation_id": "rel_001",
  "book_id": "book_demo",
  "source_character_id": "char_001",
  "target_character_id": "char_002",
  "relation_type": "colleague",
  "direction": "bidirectional",
  "confidence": 0.81,
  "evidence_ids": ["ev_220"],
  "review_status": "pending"
}
```

### 5.3 Review Task Schema 关键字段

- `task_id`
- `run_id`
- `task_type`
- `target_type`
- `target_id`
- `reason_codes`
- `proposed_patch`
- `review_decision`
- `reviewer`

## 6. 持久化策略

### 6.1 SQLite

适用于：

- 开发联调
- 本地样书试跑
- 单人审核验证

### 6.2 Postgres

适用于：

- 多项目并行
- 多用户审核
- 大规模批处理
- 更严格的事务与索引控制

### 6.3 持久化原则

- 原始文本、规范化中间结构、最终结构化结果分层保存
- 所有表保留 `created_at`、`updated_at`
- 关键对象保留 `schema_version`

## 7. 人工审核设计

审核入口至少覆盖：

- 未能自动归并的别名
- 关系冲突
- 低置信度主角色
- 证据不足的人物属性

审核操作至少支持：

- 接受
- 拒绝
- 手动修正
- 拆分角色
- 合并角色

## 8. 日志与审计设计

- 图节点执行日志
- 抽取器输入输出摘要
- Schema 校验失败日志
- 审核操作审计日志
- 数据回写日志

## 9. 性能设计

- 章节级并行，书籍内 chunk 分批执行
- LLM 抽取器按候选集调用，避免对整章全文重复推理
- Postgres 对 `book_id`、`character_id`、`chapter_id`、`review_status` 建索引
