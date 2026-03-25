# 数据结构与目录规范

## 1. 目录建议

```text
docs/
  zaomeng/
workflow/
  configs/
  selectors/
  prompts/
downloads/
  staging/
  images/
    approved/
    rejected/
  videos/
logs/
  runs/
  errors/
reports/
  reviews/
  acceptance/
state/
  tasks/
  browser/
```

## 2. 目录说明

- `workflow/configs/`：任务配置、阈值、超时、浏览器 profile 信息引用
- `workflow/selectors/`：页面元素定位配置
- `workflow/prompts/`：提示词模板、视频过渡模板、评分提示模板
- `downloads/staging/`：浏览器原始下载目录
- `downloads/images/approved/`：评分通过的图片
- `downloads/images/rejected/`：评分不通过的图片
- `downloads/videos/`：下载完成的视频
- `logs/runs/`：执行日志
- `logs/errors/`：错误日志和截图
- `reports/reviews/`：评分报告
- `reports/acceptance/`：验收证据
- `state/tasks/`：任务状态 JSON
- `state/browser/`：浏览器 profile 引用和运行态缓存

## 3. 任务数据结构

建议任务 JSON 结构：

```json
{
  "task_id": "ep01-sc03-sh012-v02",
  "episode": "ep01",
  "scene": "sc03",
  "shot": "sh012",
  "prompt": "角色在雨夜街头回头，电影感，纪实光影",
  "status": "IMAGE_GENERATING",
  "retry_count": 0,
  "submitted_at": "2026-03-25T14:15:30+08:00",
  "downloaded_images": [],
  "selected_frames": {
    "pre": null,
    "post": null
  },
  "video_task": null
}
```

## 4. 图片元数据结构

```json
{
  "task_id": "ep01-sc03-sh012-v02",
  "raw_filename": "jimeng-9384281.png",
  "final_filename": "ep01_sc03_sh012_pre_v02_pass_8.7_20260325T141530.png",
  "prompt": "角色在雨夜街头回头，电影感，纪实光影",
  "download_path": "downloads/images/approved/ep01/...",
  "review_report": "reports/reviews/ep01-sc03-sh012-v02.json",
  "overall_score": 8.7,
  "recommended_role": "pre",
  "pass": true
}
```

## 5. 视频元数据结构

```json
{
  "task_id": "ep01-sc03-sh012-v02",
  "video_task_id": "video-20260325-001",
  "pre_frame": "downloads/images/approved/ep01/...",
  "post_frame": "downloads/images/approved/ep01/...",
  "duration_seconds": 5,
  "download_path": "downloads/videos/ep01/...",
  "status": "VIDEO_DOWNLOADED"
}
```

## 6. 评分结果结构

```json
{
  "task_id": "ep01-sc03-sh012-v02",
  "overall_score": 8.7,
  "dimension_scores": {
    "composition": 9.0,
    "character_consistency": 8.5,
    "scene_consistency": 8.0,
    "storytelling": 8.8,
    "frame_stability": 9.1
  },
  "pass": true,
  "recommended_role": "pre",
  "issues": [],
  "summary": "构图稳定，可作为视频前帧使用。"
}
```

## 7. 选择器配置建议

每个页面元素建议保存：

- `name`
- `primary_selector`
- `fallback_selectors`
- `match_text`
- `timeout_seconds`
- `notes`

这样页面微调时只改配置，不必立刻改 workflow 主逻辑。
