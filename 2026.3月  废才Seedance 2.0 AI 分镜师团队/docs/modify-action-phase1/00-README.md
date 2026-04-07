# VideoOnlyOnce Phase 1 文档包

## 1. 文档目的

本目录用于沉淀 `VideoOnlyOnce` 第一阶段改造文档。

这一阶段不追求“整条链路无人值守”，而是先完成两件事：

- 把 `fenjing_program` 和 `zaomeng` 纳入同一套工程边界
- 建立后续分阶段改造所需的统一文档、目录、任务、测试和验收基线

## 2. 第一阶段定义

`Phase 01` 的范围是：

- 建立统一代码工作区
- 明确统一目录、统一契约、统一状态边界
- 建立统一 CLI 集成骨架
- 建立统一问题日志、测试计划、验收计划
- 为后续 Phase 02+ 的真实功能接入提供入口

本阶段不是最终交付阶段，因此：

- 最终成片链路不要求本阶段完成
- 真正的图片/视频批量自动化不要求本阶段完成
- 但后续改造必须从本阶段骨架继续推进，不再散落到两套独立工程里

## 3. 文档清单

- `01-requirements-report.md`
- `02-project-scope.md`
- `03-system-architecture.md`
- `04-detailed-design.md`
- `05-data-structure-and-directory.md`
- `06-work-breakdown.md`
- `07-issue-log.md`
- `08-test-plan.md`
- `09-acceptance-plan.md`
- `10-acceptance-checklist.md`
- `11-final-acceptance-report.md`
- `阶段01-阶段总结.md`
- `阶段01-问题点.md`

## 4. 建议阅读顺序

1. 先读 `01-requirements-report.md`
2. 再读 `02-project-scope.md` 和 `03-system-architecture.md`
3. 再读 `04-detailed-design.md` 和 `05-data-structure-and-directory.md`
4. 实施过程中持续更新 `06-work-breakdown.md` 和 `07-issue-log.md`
5. 测试与验收使用 `08`、`09`、`10`、`11`
6. 每轮阶段完成后更新 `阶段01-阶段总结.md` 和 `阶段01-问题点.md`

## 5. 阶段推进规则

- 每次进入新阶段前，必须先回顾上一阶段总结
- 每次阶段结束后，必须输出阶段总结和阶段问题点
- 问题日志必须同步更新，不允许只在总结里记录问题
- 遇到无法继续的问题，先检索开源实现或相关库，再决定是否升级为待确认项

## 6. 当前阶段状态

当前阶段：`Phase 01`

本阶段已定义为：

- 统一工程骨架阶段
- 统一文档与测试基线阶段
- 统一代码工作区初始化阶段
