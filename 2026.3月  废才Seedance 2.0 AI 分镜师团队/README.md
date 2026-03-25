# Feicai Seedance 2.0 Local Runner

这个项目把原有 Prompt 工程落成了一个本地可执行流程，支持从剧本到导演分析、服化道设计、Seedance 分镜提示词，再到审核、人工复核、人工放行的完整闭环。

## 当前命令

- `status`：查看当前剧集进度
- `start [ep01]`：执行导演分析阶段
- `design [ep01]`：执行服化道设计阶段
- `prompt [ep01]`：执行分镜提示词阶段
- `register-image <ep01> <asset_id> <image_path>`：登记真实图片资产并写入 registry
- `build-reference-map <ep01>`：基于已登记图片资产生成 `reference-map.json`
- `revise <ep01> <director|art|storyboard> <feedback>`：按反馈回修指定阶段
- `review <ep01> <director|design|prompt|all>`：生成人工审核决策报告
- `accept <ep01> <director|design|prompt|all>`：人工放行指定阶段
- `help`：查看命令说明

## 快速开始

1. 按 `project-config.json` 配置环境变量
   - Codex provider: `OPENAI_API_KEY`
   - Claude provider: `ANTHROPIC_AUTH_TOKEN`
2. 按需修改 `project-config.json`
3. 将剧本放入 `script/`
4. 直接运行：

```bash
python -m feicai_seedance.cli status
python -m feicai_seedance.cli start ep01
python -m feicai_seedance.cli review ep01 director
python -m feicai_seedance.cli accept ep01 director
python -m feicai_seedance.cli design ep01
python -m feicai_seedance.cli review ep01 design
python -m feicai_seedance.cli accept ep01 design
python -m feicai_seedance.cli register-image ep01 <asset_id> <image_path>
python -m feicai_seedance.cli build-reference-map ep01
python -m feicai_seedance.cli prompt ep01
python -m feicai_seedance.cli review ep01 prompt
python -m feicai_seedance.cli accept ep01 prompt
```

## 审核与放行

- 自动审核原始轮次报告保存到 `reports/reviews/<ep>/<stage>/`
- 面向人工决策的独立报告保存到 `reports/assessments/<ep>/`
- `overview.md` 提供整集总览
- `accept` 仍然只保留一个命令，阶段通过参数区分
- `review` 只负责给人工看结论、分数、亮点、不足、否决项和建议动作，不做放行

## 资产闭环

- 设计阶段会把人物、场景宫格和场景拆图同步进 `assets/registry/asset-registry.json`
- 真实图片登记后会复制到 `assets/library/` 并写入 `assets/manifests/image-generation-log.jsonl`
- `build-reference-map` 会基于导演 JSON 和 READY 资产生成 `outputs/<ep>/reference-map.json`
- `prompt` 阶段现在强依赖 `reference-map.json`，没有真实图片资产不会继续

## 测试

仓库根目录可直接运行：

```bash
python -m unittest discover -s tests -v
```
