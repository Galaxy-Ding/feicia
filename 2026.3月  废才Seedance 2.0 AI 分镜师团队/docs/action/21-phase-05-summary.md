# 第五阶段总结：人工放行与审核报告闭环

## 1. 回顾上一阶段

第四阶段的真实剧本联调证明：

- 三阶段真实生成是通的
- 真正卡住流程的是自动审核无法收敛

因此第五阶段目标很明确：补足“人工决策层”。

## 2. 已完成内容

- 新增人工放行命令：`accept <ep> <director|design|prompt|all>`
- 新增审核报告独立落盘目录：`reports/reviews/<ep>/<stage>/`
- 新增审核摘要：`summary.json`
- 新增人工放行状态：`reports/acceptance/<ep>.json`
- 状态路由现在会识别 `DIRECTOR_REVIEW_PENDING`、`ART_REVIEW_PENDING`、`STORYBOARD_REVIEW_PENDING`
- 自动通过时写入 `accepted:auto`
- 自动不收敛时写入 `pending`
- 手工执行 `accept` 后写入 `accepted:manual`

## 3. 评分机制结论

本阶段确定了评分机制的角色：

1. 评分必须有
2. 评分只能辅助决策
3. 人工放行不能只看 PASS/FAIL，必须同时看：
   - 业务分数
   - 合规结果
   - 问题列表
   - 审核器给出的 recommendation

当前实现采用：

- 自动从审核报告中提取业务分数
- 自动生成 recommendation
- 由人工通过 `accept` 作最终选择

## 4. ep01 的人工放行结果

### director

- business_score = 7.9
- compliance = PASS
- recommendation = `manual_accept_candidate`

### design

- business_score = 8.33
- compliance = PASS
- recommendation = `manual_accept_candidate`

### prompt

- business_score = 8.0
- compliance = PASS
- recommendation = `manual_accept_candidate`

最终处理：

- 已执行 `accept ep01 all`
- `ep01` 当前状态已闭环为 `DONE`

## 5. 本阶段结论

现在这套工程具备两条完整路径：

1. 自动审核通过 -> 自动完成
2. 自动审核不收敛 -> 生成人工评估材料 -> 人工放行闭环

这比之前“只能等自动 PASS”更符合真实内容生产。
