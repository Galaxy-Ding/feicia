# 即梦浏览器自动化实施文档包

## 1. 文档目的

本目录用于沉淀“人工首次登录即梦 2.0 网页，随后由 OpenClaw 接管浏览器，完成图片生成、下载命名、评分筛选、短视频生成”的完整实施文档。

这套文档的目标不是描述一个抽象想法，而是为后续开发、联调、测试、验收提供统一依据。文档默认面向以下场景：

- 团队内部通过 OpenClaw skill 和 browser tool 驱动网页操作
- 人工只在必要节点介入，例如首次登录、验证码、风控、最终抽验
- 图片与视频产物需要落盘、命名、评分、筛选、追踪和复用

## 2. 文档清单

1. `01-requirements-report.md`：需求报告
2. `02-project-scope.md`：项目范围
3. `03-system-architecture.md`：系统架构
4. `04-detailed-design.md`：详细设计
5. `05-data-structure-and-directory.md`：数据结构与目录规范
6. `06-work-breakdown.md`：任务清单
7. `07-issue-log.md`：问题日志
8. `08-test-plan.md`：测试计划
9. `09-acceptance-plan.md`：验收计划
10. `10-acceptance-checklist.md`：验收清单
11. `11-final-acceptance-report.md`：最终验收报告模板

## 3. 建议阅读顺序

1. 先阅读 `01-requirements-report.md`，统一业务目标与成功标准
2. 再阅读 `02-project-scope.md` 和 `03-system-architecture.md`，确认边界与模块划分
3. 然后阅读 `04-detailed-design.md` 和 `05-data-structure-and-directory.md`，作为实施依据
4. 开发和联调阶段配合 `06-work-breakdown.md`、`07-issue-log.md`、`08-test-plan.md`
5. 交付阶段使用 `09-acceptance-plan.md`、`10-acceptance-checklist.md`、`11-final-acceptance-report.md`

## 4. 当前关键原则

- 登录态优先复用人工首次登录后的浏览器 profile，不在模型中明文保存账号密码
- 浏览器自动化优先使用页面语义定位和多重后备选择器，避免写死单一 DOM
- 图片下载、命名、评分、筛选必须可追踪，可回溯到任务、提示词、时间、评分结果
- 视频生成必须依赖“已通过评分的前后帧”，不允许跳过评分直接生成
- 遇到验证码、风控弹窗、页面重大改版时，流程应暂停并转人工处理

## 5. 完成定义

本实施包可视为完成，至少应满足以下条件：

1. 能够在人工首次登录后稳定进入即梦图片生成页并提交任务
2. 能够自动等待生成完成并下载图片到本地规范目录
3. 能够把图片交给独立评分角色打分，并产出结构化评分结果
4. 能够根据阈值筛选保留前后帧，并基于合格帧发起 0-5 秒视频生成
5. 能够留下完整日志、任务元数据、失败原因和验收证据
