# 数据结构与目录设计

## 1. 建议目录结构

```text
character_action/
  configs/
    dev.yaml
    prod.yaml
  data/
    raw_books/
    normalized/
    exports/
  prompts/
    zh/
    en/
  schemas/
    book.schema.json
    chapter.schema.json
    character.schema.json
    relation.schema.json
    evidence.schema.json
    review_task.schema.json
  src/
    character_action/
      ...
  tests/
    fixtures/
      books/
      expected/
```

## 2. 中间数据对象

### 2.1 Book

- `book_id`
- `title`
- `language`
- `author`
- `source_path`
- `chapter_count`

### 2.2 Chapter

- `chapter_id`
- `book_id`
- `chapter_index`
- `title`
- `raw_text`

### 2.3 Chunk

- `chunk_id`
- `chapter_id`
- `chunk_index`
- `text`
- `char_start`
- `char_end`

### 2.4 Mention

- `mention_id`
- `chunk_id`
- `surface_form`
- `normalized_form`
- `entity_type`
- `speaker_hint`
- `span_start`
- `span_end`

### 2.5 Character

- `character_id`
- `book_id`
- `canonical_name`
- `aliases`
- `roles`
- `summary`
- `confidence`

### 2.6 Relation

- `relation_id`
- `book_id`
- `source_character_id`
- `target_character_id`
- `relation_type`
- `direction`
- `confidence`

### 2.7 Evidence

- `evidence_id`
- `book_id`
- `chapter_id`
- `chunk_id`
- `quote_text`
- `span_start`
- `span_end`
- `linked_object_type`
- `linked_object_id`

### 2.8 Review Task

- `task_id`
- `run_id`
- `task_type`
- `target_id`
- `reason_codes`
- `status`
- `review_patch`

## 3. 数据库表建议

### 3.1 核心业务表

- `books`
- `chapters`
- `chunks`
- `mentions`
- `characters`
- `character_aliases`
- `relations`
- `evidences`
- `review_tasks`
- `review_actions`

### 3.2 运行态表

- `pipeline_runs`
- `pipeline_checkpoints`
- `node_events`
- `qa_findings`
- `schema_versions`

## 4. SQLite 与 Postgres 差异约束

### 4.1 保持一致

- 表字段语义
- 主键命名
- 外键关系
- Schema 版本字段

### 4.2 允许差异

- SQLite 可先用简单索引与 JSON 文本字段
- Postgres 应优先使用 `jsonb`、复合索引和更严格约束

## 5. 索引建议

- `characters(book_id, canonical_name)`
- `character_aliases(book_id, alias)`
- `relations(book_id, source_character_id, target_character_id)`
- `evidences(book_id, chapter_id, chunk_id)`
- `review_tasks(status, task_type)`
- `pipeline_runs(book_id, status)`

## 6. 导出结构

最终建议支持三类导出：

- `character_cards.json`
- `relation_graph.json`
- `review_queue.json`

## 7. 命名规则

- 书籍：`book_<slug>`
- 章节：`ch_<4位序号>`
- chunk：`ch_<4位序号>_ck_<4位序号>`
- 人物：`char_<6位序号>`
- 关系：`rel_<6位序号>`
- 证据：`ev_<6位序号>`

## 8. 工程落点决策

### 8.1 代码目录

`character_action` 的实现代码放在独立工程目录：

```text
character_action/
```

不直接并入：

- `fenjing_program`
- `zaomeng`

### 8.2 原因

- `character_action` 是小说角色知识抽取与结构化的上游系统
- `fenjing_program` 是分镜与角色锚定消费方，不应混入小说级抽取职责
- `zaomeng` 是浏览器执行层，不应承载角色知识建模
- 独立工程更利于后续双语 NLP、SQLite/Postgres、LangGraph 与审核闭环独立演进

### 8.3 调度关系

统一调度入口保持放在：

```text
video_only_once_phase1/
```

后续关系定义为：

- `video_only_once_phase1` 负责统一 manifest、桥接命令和阶段编排
- `character_action` 负责上游角色抽取、证据回链和结构化输出
- `fenjing_program` 负责消费 `character_action` 的人物结果，继续角色锚定与分镜链路
