import os
from anthropic import Anthropic, DefaultHttpxClient

# 用你账号里当前可用的模型名替换这里
MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 1024

# 优先读取你手动设置的 PROXY_URL
# 如果没设，再尝试常见代理环境变量
proxy = (
    os.getenv("PROXY_URL")
    or os.getenv("HTTPS_PROXY")
    or os.getenv("ALL_PROXY")
    or os.getenv("HTTP_PROXY")
)

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise RuntimeError("缺少环境变量 ANTHROPIC_API_KEY")

if proxy:
    client = Anthropic(
        api_key=api_key,
        http_client=DefaultHttpxClient(proxy=proxy),
    )
    print(f"[info] using proxy: {proxy}")
else:
    client = Anthropic(api_key=api_key)
    print("[info] no proxy configured")

history = []

print("输入内容开始聊天，输入 /clear 清空上下文，输入 exit 退出。")

while True:
    try:
        user_text = input("\nYou: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n退出。")
        break

    if not user_text:
        continue

    if user_text.lower() in {"exit", "quit"}:
        print("退出。")
        break

    if user_text == "/clear":
        history.clear()
        print("[info] 已清空上下文")
        continue

    history.append({"role": "user", "content": user_text})

    print("Claude: ", end="", flush=True)
    assistant_text_parts = []

    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=history,
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                assistant_text_parts.append(text)

        print()
        assistant_text = "".join(assistant_text_parts).strip()
        history.append({"role": "assistant", "content": assistant_text})

    except Exception as e:
        print(f"\n[error] {type(e).__name__}: {e}")
        # 失败时把刚才那条 user 消息撤掉，避免污染上下文
        if history and history[-1]["role"] == "user":
            history.pop()
