# 数据结构与目录规范

## 1. 当前实际目录

```text
docs/
  1-pahse/
  phase-reports/
downloads/
  staging/
  images/
logs/
  runs/
  errors/
src/
  zaomeng_automation/
    browser/
state/
  tasks/
  browser/
tests/
workflow/
  configs/
  prompts/
  selectors/
```

## 2. 目录说明

- `src/zaomeng_automation/`：一期核心实现
- `src/zaomeng_automation/browser/`：浏览器抽象与模拟实现
- `tests/`：单元、功能、集成、安全测试
- `workflow/configs/`：下载目录、超时、profile 路径配置
- `workflow/selectors/`：图片页选择器模板
- `workflow/prompts/`：待执行提示词文件
- `downloads/staging/`：原始下载目录
- `downloads/images/`：重命名后的归档目录
- `logs/runs/`：运行日志和运行摘要
- `logs/errors/`：错误日志和诊断文本
- `state/tasks/`：任务状态文件
- `state/browser/`：浏览器 profile 引用目录
- `docs/phase-reports/`：阶段总结与问题点

## 3. 当前任务数据结构

```json
{
  "task_id": "img001-001",
  "batch": "img001",
  "prompt": "雨夜街头，角色回头，电影感光影",
  "status": "GENERATING",
  "submitted_at": "2026-03-25T14:30:00+08:00",
  "job_id": "job-img001-001",
  "downloaded_files": [],
  "last_error": null,
  "retry_count": 0
}
```

## 4. 当前下载映射结构

```json
{
  "task_id": "img001-001",
  "prompt": "雨夜街头，角色回头，电影感光影",
  "raw_filename": "jimeng-img001-001-001.png",
  "final_filename": "img001_001_20260325T145621_rainy-street-turnback.png",
  "saved_path": "downloads/images/img001/img001-001/...",
  "downloaded_at": "2026-03-25T14:56:21+08:00",
  "index": 1,
  "batch": "img001"
}
```

## 5. 选择器配置字段

每个元素当前约定以下字段：

- `name`
- `primary_selector`
- `fallback_selectors`
- `match_text`
- `timeout_seconds`
- `notes`

## 6. 运行证据文件

当前实际运行证据包括：

- `logs/runs/run-*.jsonl`
- `logs/runs/run-*-summary.json`
- `downloads/images/<batch>/run-*-mapping.jsonl`
- `state/tasks/*.json`
