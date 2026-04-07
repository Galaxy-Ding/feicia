# 测试计划

## 1. 测试目标

验证第一阶段新增的集成层具备：

- 正确的工作区解析
- 正确的任务契约构建
- 正确的命令桥接
- 正确的路径安全保护

## 2. 测试范围

- `workspace.py`
- `contracts.py`
- `integration.py`
- `cli.py`

## 3. 测试类型

### 3.1 单元测试

覆盖函数：

- `normalize_episode_id`
- `build_task_id`
- `build_episode_task`
- `decide_gate`
- `resolve_workspace`
- `ensure_within_root`
- `build_fenjing_status_command`
- `build_zaomeng_run_command`

要求：

- 每个函数至少 3 组随机测试样例

### 3.2 功能测试

- `prepare` 创建 runtime 目录
- `status` 输出统一状态
- `show-commands` 输出桥接命令

### 3.3 集成测试

- 真实根目录结构下，phase1 工作区可以正确解析 `fenjing_program` 和 `zaomeng`
- phase1 CLI 可以生成面向两个子系统的可执行命令文本

### 3.4 安全测试

- 路径越界被拒绝
- 非法浏览器被拒绝
- 非法 episode id 被拒绝

## 4. 测试数据策略

- 使用固定随机种子生成 3 组以上 episode 样例
- 使用临时目录模拟工作区
- 使用真实根目录做轻量集成测试

## 5. 通过标准

- 单元测试通过率 100%
- 功能测试通过率 100%
- 集成测试通过率 100%
- 安全测试通过率 100%

## 6. 当前执行记录

### 2026-03-26 / Phase 01

- 已执行：
  - 单元测试
  - 功能测试
  - 集成测试
  - 安全测试
- 执行命令：
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- 当前结果：
  - `12 tests`
  - `OK`
- 已验证：
  - `status`
  - `prepare`
  - `show-commands`
- 环境备注：
  - 当前环境无 `python` 命令，统一使用 `python3`
