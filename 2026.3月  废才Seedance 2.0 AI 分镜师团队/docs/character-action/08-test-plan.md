# 测试计划

## 1. 测试目标

验证该角色系统在实施后具备：

- 双语链路一致性
- 人物抽取稳定性
- 证据回链可用性
- 图状态恢复能力
- 数据入库正确性

## 2. 测试范围

- `preprocess/`
- `extractors/`
- `graph/`
- `storage/`
- `review/`
- `schemas/`

## 3. 测试类型

### 3.1 单元测试

覆盖：

- chunk 切分
- HanLP adapter 映射
- BookNLP adapter 映射
- alias merge 规则
- relation normalize
- schema validate
- review task build

要求：

- 每个核心函数至少 3 组样例
- 中英文样例必须同时覆盖

### 3.2 功能测试

- 单章节中文小说能跑通完整链路
- 单章节英文小说能跑通完整链路
- 审核任务能生成并回写

### 3.3 集成测试

- LangGraph 从 `ingest_book` 到 `materialize_results` 可跑通
- SQLite 可正确写入人物、别名、关系、证据
- 指定 checkpoint 后可恢复执行

### 3.4 回归测试

- 固定样书输出结果稳定
- 关键人物数量、关系数量、证据覆盖率不发生异常漂移

### 3.5 安全与鲁棒性测试

- 空章节
- 异常编码
- 超长段落
- 模型调用失败重试
- 数据库写入失败回滚

## 4. 测试数据策略

- 中文样书至少 3 本
- 英文样书至少 3 本
- 每本书至少准备人工标注的基准角色集
- 至少准备 1 本高别名复杂度样书

## 5. 指标建议

- 角色发现召回率不低于 `0.85`
- 主角色 precision 不低于 `0.90`
- 别名归并准确率不低于 `0.88`
- 关系抽取 F1 不低于 `0.75`
- 证据可追溯率达到 `1.00`

## 6. 通过标准

- Schema 校验通过率 `100%`
- 关键链路集成测试通过率 `100%`
- 双语样书回归测试通过率 `100%`
- 人工审核回写后重跑结果一致

## 7. 当前执行记录

### 2026-03-27 / Phase 01

- 已完成：测试计划编制
- 未执行：自动化测试
- 原因：当前阶段仍为方案阶段，尚未落地代码实现

### 2026-03-27 / Phase 02

- 已执行：`character_action` 自动化测试，共 13 项
- 已执行：单元测试
  - `split_chapters`
  - `build_chunks`
  - `build_evidence_for_mention`
  - `normalize_text`
  - `route_adapter`
  - `HanLPAdapter.normalize_chunk`
  - `BookNLPAdapter.normalize_chunk`
- 已执行：功能测试
  - `prepare`
  - `preprocess-book` 中文样书
  - `preprocess-book` 英文样书
- 已执行：集成测试
  - CLI `prepare` + `status`
  - SQLite 落库与状态统计
- 已执行：安全测试
  - 路径越界
  - 非法 overlap 配置
  - `book_id` 规范化
- 结果：全部通过
- 备注：本阶段的“每个核心公开函数至少 3 组随机样例”已在单元测试中落实；LangGraph、alias merge、review queue 待 Phase 03 扩展后补对应测试

### 2026-03-28 / Phase 03

- 已执行：`character_action` 自动化测试，共 21 项
- 已执行：`video_only_once_phase1` 自动化测试，共 14 项
- 已新增：单元测试
  - native HanLP mock
  - native BookNLP mock
  - alias merge
  - review queue
  - schema validator
- 已新增：功能测试
  - `doctor`
  - `extract-characters`
- 已新增：集成测试
  - `preprocess-book -> extract-characters -> status`
  - `video_only_once_phase1 status/show-commands/prepare`
- 已新增：安全测试
  - 非法 adapter_mode
- 结果：全部通过
- 当前限制：真实 `hanlp` / `booknlp` 依赖未安装，因此真实 native 运行仅完成 mock 级验证，待后续补实机验证
