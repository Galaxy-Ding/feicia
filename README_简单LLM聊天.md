# 简单 LLM 聊天脚本

文件：`simple_llm_chat.py`

## 运行

```bash
python simple_llm_chat.py
```

启动后按提示输入：

1. `provider`
2. `API Key`

然后就可以一直聊天。

## 已内置的 provider

- `openai`
- `deepseek`
- `qwen`
- `kimi`
- `moonshot`
- `groq`
- `siliconflow`
- `together`
- `openrouter`
- `ollama`

## 常用命令

- `/reset`：清空上下文
- `/exit`：退出聊天

## 可选参数

```bash
python simple_llm_chat.py --provider deepseek --api-key 你的key
python simple_llm_chat.py --provider openai --api-key 你的key --model gpt-4o-mini
python simple_llm_chat.py --base-url https://你的兼容接口/v1 --model 你的模型名 --api-key 你的key
```

如果你的平台是 OpenAI 兼容接口，但不在内置列表里，可以直接使用 `--base-url` 和 `--model`。
