# 测试计划

## 1. 测试目标

验证本地工程是否能稳定执行三阶段工作流，并在自动审核不收敛时提供可执行的人审闭环。

## 2. 测试范围

- 状态检测
- 三阶段执行
- 自动审核与回修
- 人工审核报告生成
- 人工放行
- 输出文件结构
- 安全边界

## 3. 测试环境

- Windows 本地环境
- 用户自有模型 API
- UTF-8 文件系统
- Python 3.11+

## 4. 测试类型

### 4.1 单元测试

- 集数识别、路径安全、JSON 提取、网格规格判断
- 资产拆分与结构校验
- 评分提取、recommendation 生成
- 评分分层 `quality_band()`
- 审核亮点提取 `extract_highlights()`

### 4.2 功能测试

- `start / design / prompt` 产物生成
- `review` 报告生成
- `accept` 放行写入
- `revise` 回修路径

### 4.3 集成测试

- 从 `script/ep01` 到 `outputs/ep01/02-seedance-prompts.md`
- `review -> accept` 闭环
- 审核报告总览 `overview.md` 落盘

### 4.4 安全测试

- 非法 episode id 拦截
- 路径逃逸拦截
- 配置目录作用域检查

## 5. 核心测试用例

| 编号 | 名称 | 预期结果 |
|---|---|---|
| TC-01 | 空项目状态检测 | 返回待处理状态 |
| TC-02 | 导演分析生成 | 生成 `01-director-analysis.md` |
| TC-03 | 服化道设计生成 | 生成角色与场景资产 |
| TC-04 | 分镜提示词生成 | 生成 `02-seedance-prompts.md` |
| TC-05 | 审核摘要落盘 | 生成 `summary.json` |
| TC-06 | 人工审核报告落盘 | 生成 `reports/assessments/<ep>/<stage>.md` |
| TC-07 | 审核总览落盘 | 生成 `reports/assessments/<ep>/overview.md` |
| TC-08 | 人工放行 | 写入 `reports/acceptance/<ep>.json` |
| TC-09 | 回修 | 指定阶段可按反馈重新生成 |
| TC-10 | 路径安全 | 非法路径与非法 episode 被拦截 |

## 6. 随机测试要求

- `extract_episode_id()`：3 组随机文件名
- `sanitize_episode_id()`：3 组随机大小写/空格输入
- `choose_grid_spec()`：3 组随机区间输入
- `quality_band()`：3 组随机评分输入
- `extract_highlights()`：3 组随机正向语句输入
- 安全输入拦截：3 组随机非法 episode 输入

## 7. 当前执行结果

- 测试命令：`python -m unittest discover -s tests -v`
- 当前总测试数：29
- 当前结果：29/29 通过

## 8. 本阶段新增覆盖

- `review` 命令集成测试
- 人工审核决策报告内容测试
- 审核总览报告落盘测试
- 放行结果自动回填 `assessment_report` 测试
- 仓库根目录直接运行测试的可执行性验证

## 9. 后续补测建议

- 真实 API 下的 `review -> accept` 压测
- 更长剧本下审核总览的可读性检查
- 自动审核长期不收敛时的策略调参回归测试
