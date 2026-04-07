# 测试计划

## 1. 测试目标

验证一期自动化流程能够稳定完成“配置加载、提示词读取、真实图片页定位、提示词提交、生成等待、下载归档、重命名、日志记录”闭环，并完成 OpenClaw 真实浏览器验收。

## 2. 测试范围

- 配置加载与路径安全
- 提示词文件解析
- 命名规则
- 文件稳定性判断
- 下载归档与映射记录
- 日志脱敏
- 任务状态持久化
- 模拟浏览器端到端流程
- OpenClaw 浏览器命令封装、快照解析与下载接口
- 安全边界校验

## 3. 测试类型

### 3.1 单元测试

要求：每个核心单元函数至少 3 组随机测试样例。

当前覆盖：

- `slugify_prompt()`
- `build_final_filename()`
- `load_app_config()`
- `load_prompt_tasks()`
- `wait_for_stable_file()`
- `archive_downloads()`
- `sanitize_for_log()`
- `TaskRepository.save()/load()`

### 3.2 功能测试

- 模拟浏览器单次运行 3 条提示词
- 单次运行生成 12 个归档文件
- 映射 JSONL 与状态文件同步产出

### 3.3 集成测试

- `RunOrchestrator + MockBrowserOperator + FileManager + Logger + StateStore`
- 覆盖成功链路与失败链路

### 3.4 安全测试

- 路径穿越拦截
- 日志敏感字段脱敏
- 配置模板中不保存明文密码

## 4. 当前自动化测试文件

| 测试文件 | 类型 | 说明 |
|---|---|---|
| `tests/test_naming.py` | 单元 | slug、task_id、命名格式 |
| `tests/test_config.py` | 单元 | 配置加载与路径解析 |
| `tests/test_prompts.py` | 单元 | JSON/CSV/Markdown 提示词加载 |
| `tests/test_file_manager.py` | 单元 | 文件稳定性与归档映射 |
| `tests/test_logging_utils.py` | 单元 / 安全 | 日志脱敏与摘要输出 |
| `tests/test_state_store.py` | 单元 | 状态文件读写 |
| `tests/test_orchestrator.py` | 功能 / 集成 | 端到端成功与失败流程 |
| `tests/test_openclaw_browser_operator.py` | 单元 / 功能 | OpenClaw 命令拼装、快照解析、提交与下载接口 |
| `tests/test_security.py` | 安全 | 路径穿越与凭证泄漏拦截 |

## 5. 当前测试结果

执行时间：`2026-03-26`

执行命令：

```bash
python3 -m pytest
python3 run_pipeline.py run --browser mock
python3 run_pipeline.py run --config workflow/configs/project-smoke.json --browser openclaw
python3 run_pipeline.py run --config workflow/configs/project-batch.json --browser openclaw
python3 run_pipeline.py run --config workflow/configs/project-acceptance.json --browser openclaw
```

执行结果：

- 总计 `17` 项测试
- 通过 `17`
- 失败 `0`
- `mock` 链路执行成功，结果为 `COMPLETED`
- `openclaw` 烟雾批次执行成功，结果为 `COMPLETED`
- `openclaw` 3 条小批量执行成功，结果为 `COMPLETED`
- `openclaw` 正式验收批次执行成功，结果为 `COMPLETED`
- 真实环境已验证 `ProseMirror contenteditable` 输入、提交、等待、下载、映射、状态和日志闭环

## 6. 通过准则

- 所有 P0 能力测试通过
- 单元核心函数具备至少 3 组随机样例
- 功能、集成、安全测试全部通过
- 本地模拟链路完整产生日志、状态、映射和下载结果
- 真实 OpenClaw 链路必须通过 smoke / 3 条 batch / acceptance 三类批次
- 真实运行必须产出图片文件、映射 JSONL、任务状态文件和运行日志
