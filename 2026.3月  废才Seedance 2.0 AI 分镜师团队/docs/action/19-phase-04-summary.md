# 第四阶段总结：真实剧本联调

## 1. 回顾上一阶段

第三阶段结束时，工程已经具备本地可执行能力，支持：

- `status`
- `start`
- `design`
- `prompt`
- `revise`
- 会话恢复
- 资产分块管理

本阶段的目标不是继续搭功能，而是用真实剧本走完一次实际生产链路。

## 2. 本阶段输入

真实剧本已写入：

- `script/ep01-时辰守门局.md`

## 3. 实际执行过程

### 3.1 状态检测

成功执行 `status`，识别到：

- `ep01: DIRECTOR_ANALYSIS`

### 3.2 阶段一 `start`

- 真实模型成功生成导演稿
- 自动审核与自动回修实际运行
- 但业务审核在多轮后仍未通过
- 原因不是接口错误，而是审核器对“信息密度/时序逻辑/资产筛选”的要求持续高于生成器输出

处理结果：

- 从 `.sessions/ep01/director.json` 提取最新版导演稿
- 手动写入 `outputs/ep01/01-director-analysis.md`

### 3.3 阶段二 `design`

- 真实模型成功生成人物/场景提示词
- 自动审核与自动回修实际运行
- 但阶段二也未在自动回修轮次内通过

处理结果：

- 从 `.sessions/ep01/art-designer.json` 提取最新版产物
- 拆分后写入：
  - `assets/character-prompts.md`
  - `assets/scene-prompts.md`

### 3.4 阶段三 `prompt`

- 真实模型成功生成 Seedance 分镜稿
- 自动审核与自动回修实际运行
- 但阶段三同样未在自动回修轮次内通过

处理结果：

- 从 `.sessions/ep01/storyboard-artist.json` 提取最新版产物
- 写入 `outputs/ep01/02-seedance-prompts.md`

## 4. 本阶段最终产物

已产出：

- `outputs/ep01/01-director-analysis.md`
- `assets/character-prompts.md`
- `assets/scene-prompts.md`
- `outputs/ep01/02-seedance-prompts.md`

状态检测结果已显示：

- `ep01: DONE`

## 5. 关键结论

这次真实联调证明了两件事：

1. 真实模型调用链路是通的，三阶段都能真实生成内容。
2. 当前系统的“自动审核闭环”在真实长文本场景下过严，容易导致生成完成但审核不收敛。

## 6. 下一步建议

下一步最应该做的不是继续改 Prompt，而是补一个“人工验收/人工放行”机制：

1. 自动审核失败超过阈值后，允许人工确认当前版本可接受并落盘
2. 将审核问题作为修订 backlog，而不是阻断主流程
3. 为真实联调增加“审稿器偏差”专项测试
