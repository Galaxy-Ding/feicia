# Feicai Seedance 2.0 Local Runner

这个项目把原本分散的 Prompt 流程，整理成一个可本地执行、可审核运营、可回注会话历史、可追踪真实图片资产的工程化流水线。

## 当前命令

- `status`
- `start [ep01]`
- `design [ep01]`
- `register-image <ep01> <asset_id> <image_path>`
- `build-reference-map <ep01>`
- `prompt [ep01]`
- `revise <ep01> <director|art|storyboard> <feedback>`
- `review <ep01> <director|design|prompt|all>`
- `accept <ep01> <director|design|prompt|all>`
- `acceptance-evidence <ep01>`
- `help`

## 配置方式

主配置文件是 `project-config.json`，这里现在只保存非敏感配置，以及 API Key 的环境变量名。

如果你想按 `chat_ccswitch_openai.py` 的方式继续走“本地文件带 key”的使用习惯，请使用不入库的 `project-config.local.json`：

```json
{
  "providers": {
    "codex": {
      "base_url": "http://127.0.0.1:6543/v1",
      "api_key": "sk-example-codex"
    },
    "claude": {
      "base_url": "http://127.0.0.1:6543/v1",
      "api_key": "sk-example-claude"
    }
  }
}
```

仓库里提供了样例文件 `project-config.local.example.json`。真正的 `project-config.local.json` 已加入 `.gitignore`。

安全约束：

- `project-config.json` 不再接受明文 API Key。
- 运行时优先读取 `project-config.local.json` 里的 `api_key`。
- 如果本地覆盖文件没有提供 key，则回退到 `api_key_env` 指向的环境变量。
- OpenAI 兼容基址会自动规范到 `/v1` 路径。

## 快速开始

1. 使用 Python 3.11+ 解释器。
2. 按需修改 `project-config.json`。
3. 选择一种凭据方式：
   - 设置环境变量 `CCSWITCH_CODEX_API_KEY` / `CCSWITCH_CLAUDE_API_KEY`
   - 或复制 `project-config.local.example.json` 为 `project-config.local.json` 后填入本地 key
4. 将剧本放入 `script/`
5. 运行流程

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
python -m feicai_seedance.cli acceptance-evidence ep01
```

## 资产闭环

- `design` 会把角色、场景宫格、场景拆图同步写入 `assets/registry/asset-registry.json`
- `register-image` 会把真实图片复制到 `assets/library/` 并记录到 `assets/manifests/image-generation-log.jsonl`
- `build-reference-map` 会基于导演 JSON 和已登记的 READY 资产生成 `outputs/<ep>/reference-map.json`
- `prompt` 阶段强依赖真实图片资产，如果 `reference-map.json` 不可用或仍有缺失资产，会直接阻断

## 验收证据

为了收口 Phase 5/6，新增了 `acceptance-evidence` 命令。它会生成：

- `reports/acceptance/<ep>/evidence.json`
- `reports/acceptance/<ep>/evidence.md`

它会检查：

- 三个阶段的 acceptance 状态
- 关键输出物、validation、review summary、asset registry、reference-map 是否齐全
- `assets/acceptance/<ep>/golden/` 下是否已有黄金样例
- `assets/acceptance/<ep>/variants/` 下是否已有变体样例

推荐约定：

- 黄金样例放在 `assets/acceptance/<ep>/golden/`
- 变体样例放在 `assets/acceptance/<ep>/variants/`

这样补齐样例后，只需要重新执行一次：

```bash
python -m feicai_seedance.cli acceptance-evidence ep01
```

## 测试

如果系统默认 `python` 不是 3.11+，请显式指定新版解释器。

```bash
py -3.14 -m unittest discover -s tests -v
```

当前回归结果：`54 passed`
