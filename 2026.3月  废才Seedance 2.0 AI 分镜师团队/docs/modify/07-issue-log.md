# 问题日志

## ISSUE-001 产物校验过于结构化表面化

- 严重级别：高
- 现象：校验器只检查标题和固定字段是否存在，没有检查动作链、运镜方向、光影具体度、节拍密度等业务核心质量。
- 证据：`src/feicai_seedance/artifact_utils.py:70-91`
- 影响：低质量内容可能只要格式齐全就进入下一阶段。
- 建议：引入 schema + 语义 validator，分层校验“结构完整”和“内容可执行”。

## ISSUE-002 审核协议缺少结构化评分

- 严重级别：高
- 现象：业务审核和合规审核只要求返回 `result/report/issues`。
- 证据：`src/feicai_seedance/prompt_builders.py:96-140`
- 影响：系统无法稳定执行“平均分 < 8 或单项 < 6 即 FAIL”。
- 建议：审核输出增加平均分、维度分项、是否存在单项低于 6、问题优先级。

## ISSUE-003 分数从自然语言报告中抽取

- 严重级别：高
- 现象：分数通过正则从报告正文中提取；自动推荐逻辑只看 `PASS` 或 `score >= 7.5 && issues <= 8`。
- 证据：`src/feicai_seedance/review_store.py:11-15`, `src/feicai_seedance/review_store.py:54-55`, `src/feicai_seedance/review_store.py:94-105`
- 影响：即使审核 Skill 写了更严规则，程序也无法严格执行。
- 建议：废除自然语言抽分，改为结构化 JSON 判定。

## ISSUE-004 自动接受条件与目标验收标准不一致

- 严重级别：高
- 现象：当前自动接受只依赖 `business.result == PASS && compliance.result == PASS`。
- 证据：`src/feicai_seedance/pipeline.py:347-374`
- 影响：如果模型输出 PASS 但未给出完整评分，系统仍可能自动接受。
- 建议：增加强制字段校验和通过门槛判定。

## ISSUE-005 会话历史未真正参与模型调用

- 严重级别：高
- 现象：`SessionStore` 可以保存历史，但 `Pipeline` 调模型时只传当前轮消息。
- 证据：`src/feicai_seedance/sessions.py:37-60`, `src/feicai_seedance/pipeline.py:66-69`, `src/feicai_seedance/pipeline.py:100-110`, `src/feicai_seedance/pipeline.py:148-157`, `src/feicai_seedance/pipeline.py:389-391`, `src/feicai_seedance/pipeline.py:404-419`
- 影响：所谓 resumable subagents 在工程上并未真正成立。
- 建议：生成、审核、修订均加载历史或历史摘要。

## ISSUE-006 资产库没有实体化的图片资产层

- 严重级别：高
- 现象：`assets/` 只有 `character-prompts.md` 和 `scene-prompts.md`，没有实际图片资产索引。
- 证据：当前 `assets/` 目录仅包含两个 Markdown 文件；`run_prompt` 只检查 Markdown 文件存在，见 `src/feicai_seedance/pipeline.py:134-147`
- 影响：Storyboard 阶段没有面向真实参考图闭环，`@引用` 只能停留在文本概念层。
- 建议：新增 asset registry、图片登记和 reference map。

## ISSUE-007 状态检测忽略图片资产准备状态

- 严重级别：中
- 现象：状态检测只看 episode block 和接受状态，不看图片是否已生成登记。
- 证据：`src/feicai_seedance/status.py:22-49`
- 影响：系统可能在没有真实参考图的情况下继续分镜阶段。
- 建议：增加 `IMAGE_PENDING`、`READY_FOR_STORYBOARD` 等状态。

## ISSUE-008 场景宫格规格工具存在但未接入

- 严重级别：中
- 现象：`choose_grid_spec()` 已实现，但当前源码未实际接入生成或校验主流程。
- 证据：`src/feicai_seedance/utils.py:25-34`
- 影响：场景数量与宫格规格不匹配时缺少程序保护。
- 建议：在设计阶段和审核阶段都接入。

## ISSUE-009 Seedance 关键技术约束只存在于 Skill 文本

- 严重级别：高
- 现象：节拍密度、安全区、引用上限、九宫格拆图规则写在 Skill 内，但没有代码侧 enforcement。
- 证据：`skills/director-skill/SKILL.md:42-60`, `skills/seedance-prompt-review-skill/SKILL.md:35-46`
- 影响：质量依赖模型自觉，无法稳定复现。
- 建议：沉淀为 validator 和 structured review 字段。

## ISSUE-010 测试覆盖流程，不覆盖内容质量

- 严重级别：中
- 现象：集成测试主要验证文件生成、日志、接受流程。
- 证据：`tests/test_pipeline_integration.py:43-58`
- 影响：关键规则退化不会被测试及时发现。
- 建议：增加质量规则负测、限额测试、审核阈值测试、资产闭环测试。

## ISSUE-011 配置文件允许明文 API Key 回退

- 严重级别：中
- 现象：若 `api_key_env` 字段本身以 `sk-` 开头，则直接当作密钥使用。
- 证据：`src/feicai_seedance/llm_client.py:92-100`
- 影响：存在凭据泄漏风险，不利于交付和运维规范。
- 建议：改为只接受环境变量名，明文 key 仅限开发模式。

## 2026-03-25 / Phase 1 更新

### 已关闭

- ISSUE-002：已完成结构化业务审核协议，业务审核不再只有 `result/report/issues`。
- ISSUE-003：已移除“从自然语言报告正文抽分”作为主判定路径，当前以结构化 `average_score` 和分项字段为准。
- ISSUE-004：已将自动接受规则升级为 `PASS + 平均分 >= 8 + 无单项低于 6 + 合规 PASS`。

### 部分解决

- ISSUE-001：已新增导演结构化 sidecar 与基础 validator，但动作链深度、节拍密度等仍需 Phase 2 细化。
- ISSUE-006：已初始化 `assets/registry/` 基础目录和 schema 文件，但尚未形成真实图片资产闭环。
- ISSUE-009：已把部分规则下沉到代码，包括结构化审核、Prompt 引用数量与音频设计基础检查；仍需继续沉淀安全区、九宫格拆图等规则。
- ISSUE-010：已新增结构化协议、评审 gate、sidecar JSON 的单测和集测；内容质量负例覆盖仍需继续扩充。

### 未解决

- ISSUE-005：会话历史仍未真实回注模型调用。
- ISSUE-007：状态检测仍未纳入图片与 reference-map 状态。
- ISSUE-008：宫格规格工具仍未接入主流程。
- ISSUE-011：明文 API Key 回退仍未处理。

## 2026-03-25 / Phase 2 更新

### 已推进

- ISSUE-001：已把动作链、抽象词、运镜、光影、节拍密度等规则继续下沉到 validator。
- ISSUE-008：`choose_grid_spec()` 已接入设计阶段校验路径，虽然尚未接入生成阶段，但不再是“完全未接入”。
- ISSUE-009：已新增整图宫格误用、安全区风险词、节拍密度启发式检查，规则下沉进一步扩大。
- ISSUE-010：已新增更多负例测试，覆盖导演节拍过密、Prompt 宫格误用和设计宫格规格不匹配。

### 仍未关闭

- ISSUE-005：未解决。
- ISSUE-006：仅完成目录与 schema 初始化，未完成资产闭环。
- ISSUE-007：未解决。
- ISSUE-011：未解决。

## 2026-03-25 / Phase 3-4 更新

### 已关闭

- ISSUE-005：已让 session history 真实参与生成、审核、修订调用。
- ISSUE-007：已新增 `IMAGE_PENDING`、`REFERENCE_MAPPING_PENDING` 状态并接入状态检测。

### 部分解决

- ISSUE-006：已完成 registry 初始化、设计阶段同步、图片登记和 reference-map 生成；但复用 / 变体 / 自动拆图仍未完结。
- ISSUE-008：宫格规格已接入校验，场景拆图已进入 registry；但自动拆图仍未实现。
- ISSUE-009：Prompt 已开始使用真实 reference-map，规则下沉继续推进，但仍未覆盖全部技术约束。
- ISSUE-010：已补资产闭环、状态机、会话连续性测试，仍缺黄金样例验收。

### 仍未关闭

- ISSUE-011：明文 API Key 回退仍未处理。
