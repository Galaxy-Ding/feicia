# 详细设计

## 1. 一期工作流

当前实际实现的工作流如下：

1. 读取 `workflow/configs/project.json`
2. 加载 `workflow/selectors/` 与 `workflow/prompts/`
3. 通过 `BrowserOperator.validate_login()` 校验登录态
4. 通过 `BrowserOperator.open_generation_page()` 打开图片页
5. 逐条加载提示词并调用 `submit_prompt()`
6. 调用 `wait_for_generation()` 等待结果完成
7. 调用 `download_images()` 将原始文件放入 `downloads/staging/<task_id>/`
8. 通过 `archive_downloads()` 复制、重命名并写入映射记录
9. 在每次状态迁移后写入 `state/tasks/*.json`
10. 在日志目录写入运行日志、错误日志和运行摘要

## 2. 登录态设计

### 2.1 当前实现

- 配置中保留 `profile_path`
- `login_markers` 作为后续真实页面的登录态校验依据
- 当前由模拟浏览器根据标识清单返回校验结果

### 2.2 后续真实接入要求

- 人工在目标浏览器中完成登录
- OpenClaw / browser skill 启动时复用同一 profile
- 若命中登录页或验证码页，则任务直接标记 `BLOCKED`

## 3. 图片页定位设计

### 3.1 当前实现

- 选择器模板保存在 `workflow/selectors/jimeng-image-page.json`
- 元素包括：
  - 图片生成入口
  - 提示词输入框
  - 生成按钮
  - 下载按钮

### 3.2 真实环境策略

- 主定位：基于文本、placeholder、role
- 后备定位：基于相邻区域和按钮语义
- 所有选择器必须配置化，禁止写死在主流程中

## 4. 提示词输入设计

### 4.1 当前实现

- 支持 `JSON / CSV / Markdown / TXT`
- 统一转换为 `PromptTask`
- 自动生成 `task_id` 与 `prompt_slug`

### 4.2 命名规则

任务 ID 格式：

`{batch}-{ordinal:03d}`

示例：

`img001-003`

## 5. 生成等待设计

### 5.1 当前实现

- 当前由模拟浏览器返回完成信号
- 超时参数仍保留在配置中：默认 600 秒
- 轮询间隔默认 5 秒

### 5.2 后续真实环境判断信号

任一条件满足即可判定为完成：

- 页面出现可下载按钮
- 新结果缩略图加载完成
- 任务卡片状态显示完成

## 6. 下载与命名设计

### 6.1 当前实现

- 原始文件保留在 `downloads/staging/<task_id>/`
- 归档文件输出到 `downloads/images/<batch>/<task_id>/`
- 命名函数为 `build_final_filename()`
- 稳定性判断函数为 `wait_for_stable_file()`

### 6.2 当前命名格式

`{batch}_{index}_{timestamp}_{slug}.png`

示例：

`img001_003_20260325T145621_rainy-street-turnback.png`

### 6.3 当前映射字段

- `task_id`
- `prompt`
- `raw_filename`
- `final_filename`
- `saved_path`
- `downloaded_at`
- `index`
- `batch`

## 7. 失败处理设计

### 7.1 当前已实现

- 任意步骤异常均写入错误日志
- 任务状态写为 `FAILED`
- 生成同名诊断文本到 `logs/errors/`

### 7.2 待真实环境补齐

- 页面截图证据
- 真实浏览器重试策略
- 验证码 / 风控场景分流

## 8. 恢复点设计

当前状态文件已覆盖以下恢复点：

- 登录态已校验
- 页面已打开
- 提示词已提交
- 图片生成中
- 图片已下载
- 图片已重命名
- 任务已完成 / 已失败
