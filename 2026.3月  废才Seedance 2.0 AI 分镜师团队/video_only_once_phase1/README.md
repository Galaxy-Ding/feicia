# VideoOnlyOnce Phase 1

`video_only_once_phase1` 是根目录下的统一集成工作区。

第一阶段目标：

- 统一识别 `fenjing_program` 和 `zaomeng`
- 建立统一 CLI 集成骨架
- 建立统一路径、安全和任务契约
- 为后续 Phase 02+ 提供单一入口

当前命令：

```bash
PYTHONPATH=src python3 -m video_only_once_phase1.cli status --project-root ..
PYTHONPATH=src python3 -m video_only_once_phase1.cli prepare --project-root .. --book-id demo-book --episode ep01 --browser mock
PYTHONPATH=src python3 -m video_only_once_phase1.cli show-commands --project-root .. --book-id demo-book --episode ep01 --browser mock
```

Phase 02 接入内容：

- 统一 episode manifest 输出到 `runtime/manifests/episode-manifest-<episode>.json`
- 统一暴露知识库入口、角色锚定输出目录、图片任务目录和 registry 回写目标
- `show-commands` 会同时输出角色锚定链路、图片回写链路和 `zaomeng` 桥接命令

测试：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```
