# 任务清单

## 1. 阶段划分与当前状态

| 阶段 | 目标 | 当前状态 | 当前产出 |
|---|---|---|---|
| 阶段 1：需求冻结 | 明确目标页面、目录、命名规则、提示词样例 | 已完成 | 配置模板、提示词样例、阶段 1 总结 |
| 阶段 2：登录态打通 | 人工登录 SOP、profile 复用、登录态校验 | 已完成本地抽象；真实联调待后续 | `profile_path`、`login_markers`、模拟校验 |
| 阶段 3：图片页自动化 | 页面定位、提示词输入、生成等待 | 已完成本地抽象；真实联调待后续 | 选择器模板、浏览器接口、模拟浏览器 |
| 阶段 4：下载与命名 | 下载监听、批量下载、重命名、映射记录 | 已完成 | `downloads/`、映射 JSONL、命名函数 |
| 阶段 5：日志与异常处理 | 运行日志、错误日志、恢复点 | 已完成 | `RunLogger`、`TaskRepository`、诊断文本 |
| 阶段 6：测试与验收 | 冒烟、功能、集成、安全测试与验收材料 | 已完成本地模拟验收 | `pytest` 全绿、验收清单、最终报告 |

## 2. 当前优先级

### P0

- 登录态复用接口
- 图片页定位接口
- 提示词提交接口
- 生成等待接口
- 图片下载与重命名
- 日志、映射、状态追踪

### P1

- 批量提示词扩展
- 失败恢复增强
- 真实浏览器截图证据
- OpenClaw 真实适配器

## 3. 阶段文档输出

当前已新增：

- `docs/phase-reports/阶段1-总结.md`
- `docs/phase-reports/阶段1-问题点.md`
- `docs/phase-reports/阶段2-总结.md`
- `docs/phase-reports/阶段2-问题点.md`
- `docs/phase-reports/阶段3-总结.md`
- `docs/phase-reports/阶段3-问题点.md`
- `docs/phase-reports/阶段4-总结.md`
- `docs/phase-reports/阶段4-问题点.md`
- `docs/phase-reports/阶段5-总结.md`
- `docs/phase-reports/阶段5-问题点.md`
- `docs/phase-reports/阶段6-总结.md`
- `docs/phase-reports/阶段6-问题点.md`
