# Seedance 2.0 工程改造文档包

## 1. 结论

当前工程已经具备以下能力：

- 有明确的三阶段流水线：导演分析、服化道设计、Seedance 提示词生成。
- 有对应的 `agents/`、`skills/`、`src/feicai_seedance/` 和 `tests/`。
- 本地命令行、评审存储、阶段接受状态、日志记录均已打通。
- 单元测试和集成测试当前全部通过。

当前工程还**不满足**“稳定产出高质量内容”的目标，原因不在于没有流程，而在于关键质量规则还没有被工程化固化。现状更接近“有方法论的文档驱动流水线”，还不是“可验证、可追溯、可稳定收敛的内容生产系统”。

## 2. 当前核心问题

- 导演讲戏、服化道规格、Seedance 约束主要存在于 `skills/` 文本中，缺少结构化校验器。
- 审核结果只要求返回 `PASS|FAIL + report + issues`，分数依赖从自然语言报告中用正则抽取，无法程序化执行“平均分低于 8 或任一单项低于 6 即 FAIL”。
- `SessionStore` 会记录历史，但流水线没有把历史重新喂回模型，会话连续性没有真正生效。
- 资产层只有“参考图提示词”，没有“实际参考图文件索引 / 映射 / 上传状态”，下游 `@引用` 仍然无法面向真实资产闭环。
- Seedance 的引用上限、节拍密度、安全区、九宫格拆分等关键技术约束，没有形成硬校验。
- 测试主要覆盖流程通路和基础安全，不覆盖高质量内容约束的负向案例。

## 3. 文档清单

- `01-requirements-report.md`：需求报告
- `02-project-scope.md`：项目范围
- `03-system-architecture.md`：目标系统架构
- `04-detailed-design.md`：详细设计
- `05-data-structure-and-directory.md`：数据结构与目录设计
- `06-work-breakdown.md`：任务清单
- `07-issue-log.md`：问题日志
- `08-test-plan.md`：测试计划
- `09-acceptance-plan.md`：验收计划
- `10-acceptance-checklist.md`：验收清单
- `11-final-acceptance-report.md`：基线版最终验收报告

## 4. 使用方式

- 先读 `01` 和 `07`，快速理解“为什么当前版本不能直接验收”。
- 再读 `03`、`04`、`05`，作为实现依据。
- 按 `06` 执行改造。
- 用 `08`、`09`、`10` 做联调和验收。
- 改造完成后，更新 `11` 的结论和证据。

## 5. 当前实施进度

### 2026-03-25 / Phase 1-4 已完成

- 已新增结构化协议层，落地导演 JSON、Seedance Prompt JSON、业务审核 JSON、合规审核 JSON。
- 已新增 `outputs/<ep>/validation/*.json` 静态校验产物。
- 已将自动接受逻辑升级为：`business PASS + average_score >= 8 + 无单项低于 6 + compliance PASS`。
- 已初始化 `assets/registry/`、`assets/library/`、`assets/manifests/` 基础目录，为后续 Phase 3 资产闭环做准备。
- 已补充 Phase 2 validator，覆盖动作链、抽象词、运镜、光影、节拍密度、宫格规格、宫格误用和安全区风险词。
- 已完成 Phase 3 资产闭环第一版：design -> registry、图片登记、reference-map、prompt 前置真实图片约束。
- 已完成 Phase 4 关键能力：session history 回注模型调用、状态机新增 `IMAGE_PENDING / REFERENCE_MAPPING_PENDING`。
- 已补充测试并执行通过，当前基线为 `47 passed`。

### 下一阶段启动要求

- 启动后续测试/验收阶段前，必须先阅读 `阶段04-阶段总结.md`。
- 再根据 `阶段04-问题点.md` 中的未解决项，优先实施黄金样例验收、API Key 安全策略和更严格的时长/beat 结构化约束。
