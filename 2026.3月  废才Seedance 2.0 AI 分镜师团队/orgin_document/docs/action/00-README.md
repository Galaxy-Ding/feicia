# 废才 Seedance 2.0 AI 分镜师团队实施文档包

## 1. 文档目的

本目录用于把当前项目中已经沉淀好的 Prompt 工程方法，整理成一套可以独立复制、独立开发、独立验收的实施文档。

当前项目的本质不是传统代码仓库，而是一套完整的 AI 工作流规范，核心资产已经存在于以下文件中：

| 来源文件 | 作用 | 对应实施层 |
|---|---|---|
| `CLAUDE.md` | 总控编排规则 | 制片人/编排器 |
| `agents/director.md` | 导演 Agent 系统提示词 | 阶段一执行 + 全阶段审核 |
| `agents/art-designer.md` | 服化道 Agent 系统提示词 | 阶段二执行 |
| `agents/storyboard-artist.md` | 分镜师 Agent 系统提示词 | 阶段三执行 |
| `skills/director-skill/*` | 导演讲戏方法、模板 | 剧本拆解与讲戏 |
| `skills/art-design-skill/*` | 人物/场景提示词方法、模板 | 角色与场景参考图提示词 |
| `skills/seedance-storyboard-skill/*` | Seedance 2.0 分镜方法、模板 | 动态视频提示词 |
| `skills/*review-skill/*` | 三阶段业务审核规则 | 质量闭环 |
| `skills/compliance-review-skill/*` | 合规审核规则 | 平台风控闭环 |

结论：要“完全复制一模一样的工程方法”，不是重写这些 Prompt，而是把它们当成运行时配置，外面补一个稳定的流程引擎、状态管理、API 适配层和文件落盘机制。

## 2. 交付内容

本目录包含以下文档：

1. `01-requirements-report.md`：需求报告
2. `02-project-scope.md`：项目范围
3. `03-system-architecture.md`：系统架构
4. `04-detailed-design.md`：详细设计
5. `05-model-and-prompt-design.md`：模型与 Prompt 编排设计
6. `06-data-structure-and-directory.md`：数据结构与目录规范
7. `07-work-breakdown.md`：任务清单
8. `08-issue-log.md`：问题日志
9. `09-test-plan.md`：测试计划
10. `10-acceptance-plan.md`：验收计划
11. `11-acceptance-checklist.md`：验收清单
12. `12-final-acceptance-report.md`：最终验收报告模板

## 3. 建议阅读顺序

1. 先读 `01-requirements-report.md`
2. 再读 `03-system-architecture.md`
3. 然后读 `04-detailed-design.md`
4. 开发前读 `05-model-and-prompt-design.md` 和 `06-data-structure-and-directory.md`
5. 执行阶段使用 `07-work-breakdown.md`、`09-test-plan.md`、`10-acceptance-plan.md`
6. 交付阶段使用 `11-acceptance-checklist.md` 与 `12-final-acceptance-report.md`

## 4. 复刻原则

- 原项目中 `agents/` 与 `skills/` 下的 Markdown 文件应视为核心产品资产，不建议改写成碎片化 prompt。
- 第一版实现建议继续使用“文件系统 + Markdown 产物 + JSON 状态文件”，不要过早上数据库。
- 审核机制必须保留“双审核闭环”：业务审核 + 合规审核。
- 阶段产物必须严格保持和原项目一致的文件名、写入策略和内容结构。
- 如果只能接一个大模型 API，优先保证“导演执行/审核”能力，其次是分镜师，最后是服化道。

## 5. 落地定义

本套实施方案的“完成”标准，不是做出一个类似产品，而是满足以下四点：

1. 同一份剧本输入，能产出与当前项目同结构的 `01-director-analysis.md`、`character-prompts.md`、`scene-prompts.md`、`02-seedance-prompts.md`
2. 支持 `start/design/prompt/status/help` 这套流程命令
3. 支持跨阶段审核循环与失败后重生成功能
4. 支持跨集素材复用、变体标记、Agent 上下文恢复
