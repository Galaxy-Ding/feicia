# 系统架构

## 1. 架构目标

第一阶段架构目标只有三个：

1. 给 `fenjing_program` 和 `zaomeng` 建立统一中控边界
2. 给后续阶段建立低耦合的统一契约
3. 给测试、问题、验收建立统一工程骨架

## 2. 总体架构

```text
root
  -> docs/modify-action-phase1
  -> video_only_once_phase1
      -> unified CLI
      -> workspace model
      -> task contract
      -> gate contract
      -> security guard
  -> fenjing_program
  -> zaomeng
```

## 3. 分层设计

### 3.1 文档层

负责：

- 需求
- 范围
- 架构
- 设计
- 任务
- 测试
- 验收
- 阶段总结
- 问题闭环

### 3.2 集成层

由 `video_only_once_phase1` 负责：

- 识别项目根目录
- 统一管理两个子系统路径
- 输出统一状态
- 生成子系统执行命令
- 负责集成级安全校验

### 3.3 执行层

- `fenjing_program`
- `zaomeng`

这两层在第一阶段保持原边界，不做大规模侵入式改写。

## 4. 核心模块

### 4.1 Workspace Resolver

负责统一解析：

- 项目根目录
- `fenjing_program` 路径
- `zaomeng` 路径
- 集成目录
- 运行目录

### 4.2 Contract Builder

负责统一构建：

- 阶段任务元数据
- gate 决策结果
- 子系统命令参数

### 4.3 Integration Bridge

负责：

- 构建 `fenjing_program` 命令
- 构建 `zaomeng` 命令
- 输出统一集成视图

### 4.4 Security Guard

负责：

- 路径越界拦截
- 浏览器类型白名单
- 集成命令参数基本校验

## 5. 架构原则

- 中控不重写子系统
- 中控优先桥接，不优先复制代码
- 统一契约先于统一运行时
- 安全校验先于自动执行

## 6. 后续演进方向

第一阶段完成后，后续可以继续演进为：

- Phase 02：统一 episode manifest
- Phase 03：统一事件日志和队列
- Phase 04：统一状态图编排器
