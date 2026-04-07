# 系统架构

## 1. 架构目标

本系统架构目标有四个：

1. 用统一状态图编排中文和英文小说处理流程
2. 用确定性 NLP 预处理减少 LLM 漂移
3. 用 JSON Schema 和数据库约束稳定输出
4. 用审核与 QA 闭环保证结果可追溯

## 2. 总体架构

```text
Novel Input
  -> Language Router
  -> Preprocess Layer
      -> Chinese: HanLP
      -> English: BookNLP
  -> LangGraph Orchestrator
      -> chunk planning
      -> rule extraction
      -> LLM extraction
      -> alias merge
      -> relation build
      -> QA check
      -> human review gate
      -> final materialization
  -> JSON Schema Validator
  -> SQLite/Postgres
  -> Character API / downstream storyboard system
```

## 3. 分层设计

### 3.1 接入层

负责：

- 书籍元数据录入
- 文本文件导入
- 语言选择与编码校验
- 章节和 chunk 切分

### 3.2 预处理层

负责：

- 中文：分词、词性、命名实体、依存、共指线索
- 英文：tokens、entities、coref、quotes、speakers
- 输出统一的 `normalized_text_units`

### 3.3 编排层

由 `LangGraph` 负责：

- 持久状态
- 节点执行
- checkpoint
- interrupt
- human-in-the-loop
- 指定节点恢复

### 3.4 抽取层

由两类抽取器组成：

- 规则抽取器
- LLM 抽取器

规则抽取器优先负责高确定性项，LLM 抽取器负责：

- 模糊别名补全
- 隐式关系判断
- 长距离指代理解
- 描写归纳

### 3.5 质检层

负责：

- JSON Schema 校验
- 角色重复检测
- 关系冲突检测
- 证据缺失检测
- 审核任务生成

### 3.6 存储层

- SQLite：本地开发与小规模试跑
- Postgres：生产部署与多用户审核

## 4. 语言分流设计

### 4.1 中文链路

```text
book -> chapter split -> HanLP -> rule extractor -> LLM extractor
     -> alias merge -> profile build -> relation build -> QA -> review -> store
```

### 4.2 英文链路

```text
book -> chapter split -> BookNLP -> rule extractor -> LLM extractor
     -> alias merge -> profile build -> relation build -> QA -> review -> store
```

### 4.3 共用层

以下能力必须共用：

- LangGraph 状态模型
- JSON Schema
- 数据库存储模型
- 审核与 QA 规则
- API 输出格式

## 5. 核心模块

### 5.1 Ingestion Service

负责书籍导入、章节切分、chunk 管理和编码清洗。

### 5.2 NLP Adapter

负责把 `HanLP` 或 `BookNLP` 输出转换成统一中间结构。

### 5.3 Extraction Graph

负责执行抽取流程图，并把节点产物保存在持久状态中。

### 5.4 Merge Engine

负责 canonical character 建模、alias merge、冲突检测和人工修正应用。

### 5.5 Evidence Store

负责把人物结论与原文 span 绑定。

### 5.6 Review Queue

负责把低置信度或冲突项路由给人工审核。

## 6. 架构原则

- 预处理尽量确定性，复杂推理再交给 LLM
- 先抽证据，再下结论
- 先生成候选，再做归并
- 任何最终入库数据都必须过 Schema 校验
- 审核修正必须能回写到后续重跑逻辑

## 7. 后续演进方向

- 接入更多语言处理器
- 接入向量检索辅助证据召回
- 接入分镜与角色资产锚定系统
- 接入指标看板与观测体系
