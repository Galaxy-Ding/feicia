# 测试计划

## 1. 测试目标

验证改造后系统不仅“流程可跑”，还能够：

- 拒绝不合格内容
- 追踪真实资产
- 严格执行审核阈值
- 保证 Storyboard 使用真实参考图

## 2. 测试范围

- schema 校验
- validator 校验
- 资产 registry
- reference map
- review gate
- session continuity
- CLI 兼容性

## 3. 测试分层

### 3.1 单元测试

- Director schema 解析
- 抽象词检测
- 动作链缺失检测
- 光影具体度检测
- 宫格规格选择
- Prompt 引用计数
- 节拍密度计算
- 安全区校验
- review JSON 判定逻辑

### 3.2 集成测试

- 从剧本到导演 JSON
- 从导演 JSON 到资产 registry
- 图片登记后构建 reference map
- 从 reference map 到 Seedance Prompt
- review FAIL 后自动回修
- review PASS 后自动接受

### 3.3 回归测试

- 老命令 `start/design/prompt/review/accept` 仍可使用
- 老 Markdown 路径不变
- 多 episode 互不污染

## 4. 测试用例设计

### 4.1 导演质量负例

- 使用抽象情绪词但无动作承载
- 运镜只有“镜头移动”无方向
- 光影只有“昏暗”“柔和”无具体来源
- 8 秒镜头塞 5 个节拍
- 关键对白放在前 0.5 秒

### 4.2 服化道负例

- 角色条目未标注新增 / 复用 / 变体
- 场景 11 个却仍输出 3x3
- 变体未关联原资产
- Storyboard 引用未登记图片资产

### 4.3 Seedance 负例

- 单条 Prompt 图片引用 10 张
- 场景九宫格整图被当作单个场景引用
- 无音频设计
- 动作顺序前后矛盾
- 关键动作占用尾部 0.5 秒

### 4.4 审核负例

- 平均分 7.9 仍返回 PASS
- 平均分 8.3 但单项 5.0
- 合规 FAIL 但业务 PASS

## 5. 测试数据

- 最少准备 3 套黄金剧本：
  - 单镜头静态情绪段
  - 多镜头蒙太奇段
  - 多角色高密度对话段

## 6. 通过标准

- 单元测试通过率 100%
- 集成测试通过率 100%
- 黄金样例验收通过率 100%
- 至少 10 个负例可被正确拒收

## 7. Phase 1 已执行结果

### 已落地测试

- `tests/test_structured_protocols.py`
  - 覆盖导演 Markdown -> JSON
  - 覆盖 Seedance Markdown -> JSON
  - 覆盖业务 / 合规 review payload 解析
  - 覆盖自动接受 gate
  - 覆盖 registry 初始化
- `tests/test_acceptance_and_reviews.py`
  - 已改为验证结构化 `average_score`
  - 已验证 recommendation 逻辑升级
- `tests/test_pipeline_integration.py`
  - 已验证 JSON sidecar 输出
  - 已验证 `validation/*.json` 输出
  - 已验证 registry bootstrap

### 已执行结果

- 当前执行结果：`39 passed`
- 当前已满足：
  - 单元测试
  - 集成测试
  - 基础安全测试
- 当前仍待补足：
  - 设计阶段 schema 深测
  - reference-map 集成测试
  - session continuity 回归测试
  - 黄金样例验收测试

## 8. Phase 2 已执行结果

### 新增覆盖

- 导演 validator：
  - 节拍过密负例
  - 运镜缺失负例
  - 光源缺失负例
  - 抽象词无动作承载负例
- 设计 validator：
  - 宫格规格不匹配负例
- Seedance validator：
  - 整张宫格图误用负例
  - 安全区风险词负例
  - 节拍过密负例

### 已执行结果

- 当前执行结果：`41 passed`
- 当前已新增 Phase 2 规则回归保护。
- 当前仍待补足：
  - registry 生命周期测试
  - reference-map 构建与引用一致性测试
  - session continuity 回归测试
  - 更强的安全策略测试

## 9. Phase 3-4 已执行结果

### 新增覆盖

- `tests/test_asset_registry.py`
  - design -> registry 同步
  - 图片登记
  - reference-map 生成
- `tests/test_pipeline_integration.py`
  - 完整闭环改为 `design -> register-image -> build-reference-map -> prompt`
  - prompt 缺少 reference-map 时阻断
  - session history 回注回归
- `tests/test_status.py`
  - `IMAGE_PENDING`
  - `REFERENCE_MAPPING_PENDING`

### 已执行结果

- 当前执行结果：`47 passed`
- 当前已补齐：
  - 资产闭环第一版回归
  - session continuity 基础回归
  - 状态机升级回归
- 当前仍待补足：
  - 黄金样例验收
  - 最终 acceptance 证据
  - API Key 安全策略测试
