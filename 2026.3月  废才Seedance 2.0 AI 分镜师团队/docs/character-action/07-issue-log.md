# 问题日志

## 1. 使用规则

- 所有问题先进入本日志
- 方案问题与实现问题共用同一日志体系
- 关闭问题时必须写清楚处理方式与验证方式

## 2. 问题模板

| 编号 | 日期 | 严重级别 | 阶段 | 问题描述 | 影响 | 当前状态 | 处理建议 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CAS-001 | 2026-03-27 | 高 | Phase 01 | BookNLP 与 HanLP 输出结构不统一 | 双语共用 schema 难以落地 | Open | 建立统一 NLP adapter 层 |

## 3. 初始问题

| 编号 | 日期 | 严重级别 | 阶段 | 问题描述 | 影响 | 当前状态 | 处理建议 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CAS-001 | 2026-03-27 | 高 | Phase 01 | 中文与英文预处理产物字段天然不同 | 上层图状态与抽取器会分叉 | Open | 强制增加统一中间结构 |
| CAS-002 | 2026-03-27 | 高 | Phase 01 | 人物 alias merge 的正确率直接影响后续关系图质量 | 角色卡重复、关系边污染 | In Progress | 已建立初版 merge + review queue，继续提升规则与审核闭环 |
| CAS-003 | 2026-03-27 | 高 | Phase 01 | 证据 span 若不稳定，后续审校无法追责 | 结果不可审计 | Open | 固化 chunk 与 span 编码规则 |
| CAS-004 | 2026-03-27 | 中 | Phase 01 | SQLite 与 Postgres 的 JSON 能力差异较大 | 开发环境与生产环境行为可能不一致 | Open | 提前约束字段与迁移策略 |
| CAS-005 | 2026-03-27 | 中 | Phase 01 | BookNLP 对英文长书运行成本和速度需要验证 | 英文链路吞吐未知 | Open | 建立样书性能基线 |
| CAS-006 | 2026-03-27 | 中 | Phase 01 | HanLP 所用模型和许可证需要逐项确认 | 生产部署有合规风险 | Open | 锁定模型版本并做合规复核 |
| CAS-007 | 2026-03-27 | 中 | Phase 01 | LLM 抽取 prompt 如果不做版本管理，结果难回放 | QA 和回归难稳定 | Open | 增加 prompt_version 字段 |
| CAS-008 | 2026-03-27 | 中 | Phase 01 | 人工审核策略若过宽，会拖慢整体交付 | 成本与时效失控 | Open | 设置置信度阈值和审核优先级 |
| CAS-009 | 2026-03-27 | 低 | Phase 01 | 当前仅完成方案文档，尚未进入真实代码实现 | 不能视为系统已上线 | Open | 进入 Phase 02 开发 |
| CAS-010 | 2026-03-27 | 中 | Phase 02 | 当前 `HanLP` / `BookNLP` 仅落 fallback contract，未接真实外部引擎 | 预处理质量与正式链路仍有差距 | Resolved | 已补 native-or-fallback 双路径，并于 2026-03-28 在本机完成中英文 native 样书验证 |
| CAS-011 | 2026-03-27 | 中 | Phase 02 | 章节与 chunk 命名规则是书内唯一，数据库必须持续维持复合主键策略 | 多书并行时易出现覆盖写入 | Open | SQLite 与 Postgres 保持 `book_id + object_id` 复合约束 |
| CAS-012 | 2026-03-27 | 中 | Phase 02 | `video_only_once_phase1` 尚未正式桥接 `character_action` 命令与 manifest | 统一调度链还未打通 | Resolved | 已补 workspace、manifest 与 bridge commands |
| CAS-013 | 2026-03-28 | 中 | Phase 03 | 当前环境未安装 `hanlp` / `booknlp`，native path 只能通过 `doctor` 验证与 mock 测试 | 无法在本机直接验证真实模型运行结果 | Resolved | 已在 2026-03-28 完成依赖安装、中文 HanLP native 验证、英文 BookNLP native 验证 |
| CAS-016 | 2026-03-28 | 中 | Phase 03 | relation build 已开始产出 `relation_graph.json`，但当前仍以局部共现和关键词规则为主，复杂隐式关系与冲突检测未覆盖 | 关系图可用性已有基线，但准确率和关系类型覆盖仍有限 | Open | 在 QA 规则与后续 LLM extractor 阶段继续补 relation normalize、冲突检测与审核扩展 |
| CAS-015 | 2026-03-28 | 中 | Phase 03 | native 依赖存在版本与资源耦合：`setuptools>=81`、`transformers 5.x`、缺失 spaCy 模型或 Hugging Face 主站不可达都会导致实机失败 | 换机或 CI 环境容易复现安装失败 | Open | 固化 `requirements-native.txt`，并补脚本化安装与 `doctor` 资源检查 |
| CAS-014 | 2026-03-28 | 中 | Phase 03 | 当前 review queue 已覆盖低置信度、歧义别名、代词角色名、低证据人物与低置信度关系，但关系冲突与属性冲突仍未覆盖 | 审核闭环已扩展一轮，但仍未完整 | In Progress | 继续在 QA 规则引擎阶段补更多 task_type |

## 4. 本阶段状态

### 已关闭

- CAS-001
  - 处理方式：在 `character_action/` 中建立统一 `NormalizedTextUnit`、中英文 fallback adapter 和统一 CLI 预处理入口
  - 验证方式：中英文样书预处理通过，自动化测试通过
- CAS-003
  - 处理方式：固化 chunk 切分与 `build_evidence_for_mention` span 规则，并落到 SQLite
  - 验证方式：evidence 单元测试通过，中文/英文样书 `evidence_count` 正常输出
- CAS-009
  - 处理方式：已进入真实代码开发，建立 `character_action/` 工程骨架
  - 验证方式：CLI、SQLite、样书预处理与测试均已执行
- CAS-012
  - 处理方式：已在 `video_only_once_phase1` 中加入 `character_action` workspace、manifest 与桥接命令
  - 验证方式：`status`、`show-commands`、`prepare` 已在真实工作区执行通过

### 仍待处理

- CAS-002
- CAS-004
- CAS-005
- CAS-006
- CAS-007
- CAS-008
- CAS-010
- CAS-011
- CAS-013
- CAS-014
- CAS-015
- CAS-016
