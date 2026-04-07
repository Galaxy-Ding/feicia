# 详细设计

## 1. 统一代码目录

建议新增：

```text
video_only_once_phase1/
  README.md
  pyproject.toml
  src/video_only_once_phase1/
    __init__.py
    cli.py
    contracts.py
    integration.py
    workspace.py
  tests/
    test_contracts.py
    test_integration.py
    test_security.py
```

## 2. 工作区模型设计

统一工作区对象需要至少包含：

- `project_root`
- `phase1_root`
- `fenjing_root`
- `zaomeng_root`
- `runtime_root`
- `logs_root`
- `manifests_root`

要求：

- 所有路径都必须从 `project_root` 推导
- 所有路径都必须经过越界校验

## 3. 任务契约设计

### 3.1 Episode Task

```json
{
  "project_id": "video_only_once",
  "book_id": "demo-book",
  "episode_id": "ep01",
  "phase": "phase01",
  "stage": "integration",
  "task_id": "phase01-ep01-integration",
  "upstream": [],
  "manual_checkpoints": 1
}
```

### 3.2 Gate Result

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

## 4. CLI 设计

建议提供 3 个命令：

- `status`
  - 展示统一工作区状态
- `prepare`
  - 创建 phase1 runtime 目录
- `show-commands`
  - 输出调用两个子系统的推荐命令

## 5. 命令桥接设计

### 5.1 `fenjing_program`

集成层不直接调用内部函数，优先输出标准命令：

```bash
python -m feicai_seedance.cli status --project-root <fenjing_root>
```

### 5.2 `zaomeng`

集成层同样优先输出标准命令：

```bash
python -m zaomeng_automation.cli run --config <config> --browser mock
```

## 6. 安全设计

### 6.1 路径安全

- 所有传入路径必须确保在 `project_root` 下
- 禁止 `../` 越界使用

### 6.2 浏览器白名单

- 第一阶段只允许：
  - `mock`
  - `openclaw`

### 6.3 命令参数约束

- `episode_id` 必须规范化
- 空字符串和非法浏览器类型必须拦截

## 7. 测试设计

### 7.1 单元测试

- `normalize_episode_id`
- `build_task_id`
- `decide_gate`
- `resolve_workspace`
- `ensure_within_root`
- `build_bridge_commands`

每个函数至少 3 组随机样例。

### 7.2 功能测试

- `prepare` 能创建目录
- `status` 能识别两个子系统
- `show-commands` 能生成标准命令

### 7.3 集成测试

- phase1 工作区能与根目录真实结构对齐
- phase1 命令能生成真实可执行的子系统命令字符串

### 7.4 安全测试

- 路径越界
- 非法浏览器类型
- 非法 episode id
