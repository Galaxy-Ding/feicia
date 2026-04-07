# 任务清单

## 1. Phase 01 方案与基线

### T1 文档与契约

- T1.1 建立 `docs/character-action/` 文档包
- T1.2 冻结需求、范围、架构、详细设计
- T1.3 冻结数据结构、Schema 和数据库草案
- T1.4 建立测试、验收、问题日志基线

### T2 技术选型确认

- T2.1 确认 `LangGraph` 版本与持久化方式
- T2.2 确认 `HanLP` 版本与可用模型
- T2.3 确认 `BookNLP` 版本、运行方式与资源需求
- T2.4 确认 LLM provider、成本预算与重试策略

## 2. Phase 02 核心工程骨架

### T3 基础工程

- T3.1 建立 `character_action/` 工程目录
- T3.2 建立 CLI 与配置体系
- T3.3 建立 SQLite repo 和迁移脚本
- T3.4 建立基础日志与审计模块

### T4 预处理层

- T4.1 接入中文 `HanLP` 适配器
- T4.2 接入英文 `BookNLP` 适配器
- T4.3 建立统一 `normalized_text_units`
- T4.4 建立文本切 chunk 策略

## 3. Phase 03 抽取与质检

### T5 抽取链路

- T5.1 实现规则抽取器
- T5.2 实现 LLM 抽取器
- T5.3 实现 alias merge
- T5.4 实现 relation build

### T6 编排与审核

- T6.1 建立 LangGraph 状态图
- T6.2 建立 checkpoint 与恢复机制
- T6.3 建立 review queue
- T6.4 建立 QA 规则引擎

## 4. Phase 04 生产化与联调

### T7 存储与服务

- T7.1 切换 Postgres
- T7.2 建立 API / 导出能力
- T7.3 建立监控、告警与运行报表

### T8 下游联调

- T8.1 对接人物卡消费方
- T8.2 对接关系图消费方
- T8.3 对接分镜与角色锚定系统

## 5. 当前进展

### 2026-03-27 / Phase 01

- 已完成：T1.1
- 已完成：T1.2
- 已完成：T1.3
- 已完成：T1.4
- 待完成：T2 全部
- 待完成：T3 及以后全部

### 2026-03-27 / Phase 02

- 已完成：T3.1 建立 `character_action/` 工程目录
- 已完成：T3.2 建立 CLI 与配置体系
- 已完成：T3.3 建立 SQLite repo 与基础建表逻辑
- 已完成：T3.4 建立基础日志与运行记录
- 已完成：T4.3 建立统一 `normalized_text_units`
- 已完成：T4.4 建立文本切 chunk 策略与 evidence span 编码规则
- 部分完成：T4.1 中文 `HanLP` 适配器已先落 fallback contract，真实 HanLP 待接入
- 部分完成：T4.2 英文 `BookNLP` 适配器已先落 fallback contract，真实 BookNLP 待接入
- 待完成：T5 及以后全部

### 2026-03-28 / Phase 03

- 已完成：T5.3 初版 alias merge
- 已完成：T5.4 初版 relation build
- 已完成：T6.3 初版 review queue
- 已完成：T6.4 初版 QA 规则引擎
- 已完成：运行时 schema 校验骨架
- 已完成：`doctor` 依赖检查命令
- 已完成：`video_only_once_phase1` 对 `character_action` 的 manifest 与桥接命令接入
- 部分完成：T4.1 / T4.2 已支持 native-or-fallback 双路径，当前环境未安装真实 `HanLP` / `BookNLP`
- 部分完成：T5.1 规则抽取当前以 mention 聚合和别名规则为主，仍待扩展更强规则
- 待完成：T5.2 LLM extractor
- 待完成：T6.1 LangGraph 状态图
- 待完成：T6.2 checkpoint 与恢复机制
- 待完成：T6.4 QA 规则引擎深化

## 6. 下一阶段前置

- 先完成技术选型确认
- 再建立工程骨架
- 在 Phase 02 开始前，先回顾 `阶段01-问题点.md`
- 在 Phase 03 开始前，先回顾 `阶段02-阶段总结.md` 与 `阶段02-问题点.md`
- 在下一阶段开始前，先回顾 `阶段03-阶段总结.md` 与 `阶段03-问题点.md`
