# 小说人物角色系统文档包

## 1. 文档目的

本目录用于沉淀“小说人物角色系统”的开源落地方案文档。

本方案基于以下主干路线：

- 中文小说：`LangGraph + HanLP + 规则/LLM 抽取器 + JSON Schema + SQLite/Postgres`
- 英文小说：`LangGraph + BookNLP + 规则/LLM 抽取器 + JSON Schema + SQLite/Postgres`

这一轮交付的目标不是直接上线代码，而是先把后续实施所需的：

- 需求边界
- 系统架构
- 数据契约
- 任务拆解
- 测试计划
- 验收计划
- 问题闭环

全部收敛到一套统一文档包中。

## 2. 本阶段定义

当前阶段：`Phase 01 方案与实施基线阶段`

本阶段关注：

- 明确双语小说角色抽取系统的业务目标
- 明确中文与英文两条技术链路的共性与差异
- 明确 LangGraph 状态编排、抽取节点、审核节点和恢复机制
- 明确 JSON Schema 与数据库落库契约
- 明确测试、验收、问题跟踪和阶段推进规则

本阶段不要求：

- 完成完整代码开发
- 完成全量历史小说数据回灌
- 完成前端运营台
- 完成向后续分镜、镜头规划、资产锚定系统的正式联调

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
- `阶段02-阶段总结.md`
- `阶段02-问题点.md`
- `阶段03-阶段总结.md`
- `阶段03-问题点.md`

## 4. 建议阅读顺序

1. 先读 `01-requirements-report.md`
2. 再读 `02-project-scope.md` 和 `03-system-architecture.md`
3. 再读 `04-detailed-design.md` 和 `05-data-structure-and-directory.md`
4. 实施前阅读 `06-work-breakdown.md`
5. 测试与验收使用 `08`、`09`、`10`、`11`
6. 阶段推进过程持续更新 `07-issue-log.md` 与各阶段总结/问题点文档

## 5. 阶段推进规则

- 任何工程实施必须先遵守本目录中的契约与边界
- 中文与英文管线共用上层编排，不允许形成两套互不兼容的 orchestrator
- 所有结构化输出必须经过 JSON Schema 校验后才允许入库
- 所有人物、别名、关系、证据必须可追溯到原文 span
- 问题日志必须持续维护，不允许只在群聊或临时笔记中记录

## 6. 当前状态

当前文档包状态：

- 已完成方案级文档基线
- 已完成实施拆解、测试计划、验收计划与问题基线
- 已启动 `Phase 02` 最小可运行工程骨架
- 已建立独立工程目录 `character_action/`
- 已完成 `Phase 03` 第一轮抽取与审核骨架
- 尚未进入正式 LangGraph 编排、真实关系抽取、Postgres 与正式验收
