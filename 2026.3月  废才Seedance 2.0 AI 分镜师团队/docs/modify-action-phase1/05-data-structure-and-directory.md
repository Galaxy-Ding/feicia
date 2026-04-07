# 数据结构与目录设计

## 1. 根目录新增项

```text
docs/
  modify-action-phase1/

video_only_once_phase1/
  README.md
  pyproject.toml
  src/
  tests/
  runtime/
    logs/
    manifests/
```

## 2. 运行目录设计

```text
video_only_once_phase1/runtime/
  logs/
    phase1-run.jsonl
  manifests/
    phase1-task-template.json
```

## 3. 工作区对象结构

```json
{
  "project_root": "/abs/path/project",
  "phase1_root": "/abs/path/project/video_only_once_phase1",
  "fenjing_root": "/abs/path/project/fenjing_program",
  "zaomeng_root": "/abs/path/project/zaomeng",
  "runtime_root": "/abs/path/project/video_only_once_phase1/runtime",
  "logs_root": "/abs/path/project/video_only_once_phase1/runtime/logs",
  "manifests_root": "/abs/path/project/video_only_once_phase1/runtime/manifests"
}
```

## 4. 任务结构

```json
{
  "project_id": "video_only_once",
  "book_id": "book-demo",
  "episode_id": "ep01",
  "phase": "phase01",
  "stage": "integration",
  "task_id": "phase01-ep01-integration",
  "upstream": [],
  "manual_checkpoints": 1
}
```

## 5. Gate 结构

```json
{
  "episode_id": "ep01",
  "stage": "integration",
  "decision": "AUTO_CONTINUE",
  "manual_required": false,
  "retryable": false,
  "reason_codes": []
}
```

## 6. 输出目录说明

- `logs/`
  - 记录集成层运行日志
- `manifests/`
  - 记录 phase1 模板任务或后续真实 episode 任务

## 7. 演进原则

- 后续阶段只扩展 `runtime/` 子目录
- 不随意改动根路径命名
- 契约字段只增不随意删
