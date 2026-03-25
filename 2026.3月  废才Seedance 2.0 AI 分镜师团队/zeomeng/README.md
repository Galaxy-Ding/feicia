# 即梦一期本地实施骨架

本目录基于一期文档，落地以下内容：

- 本地可运行的任务编排、状态管理、日志、下载重命名与映射记录
- 面向后续 `OpenClaw + browser skill` 的浏览器适配接口
- 一个用于本机验证链路的模拟浏览器实现
- 单元、功能、集成、安全测试
- 分阶段总结、问题点与问题日志更新机制

当前机器仍然遵循部署边界：不安装、不运行 OpenClaw，只完成本地脚本层与接口边界准备。

## 快速运行

```bash
python run_pipeline.py run --browser mock
pytest
```

## 目录

```text
src/zaomeng_automation/      核心实现
tests/                       测试
workflow/configs/            配置模板
workflow/selectors/          选择器模板
workflow/prompts/            提示词样例
docs/phase-reports/          各阶段总结与问题点
```
