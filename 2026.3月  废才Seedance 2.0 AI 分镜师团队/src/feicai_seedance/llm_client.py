from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from .models import ApiSettings, ModelSettings


class LLMClient(Protocol):
    def chat(self, model: ModelSettings, messages: list[dict[str, str]]) -> str: ...


@dataclass(slots=True)
class OpenAICompatibleClient:
    settings: ApiSettings

    def chat(self, model: ModelSettings, messages: list[dict[str, str]]) -> str:
        api_key = self._resolve_api_key()
        if not api_key:
            raise RuntimeError(f"Missing API key env: {self.settings.api_key_env}")

        if self.settings.wire_api == "responses":
            return self._responses_api(api_key, model, messages)
        return self._chat_completions_api(api_key, model, messages)

    def _chat_completions_api(self, api_key: str, model: ModelSettings, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": model.name,
            "temperature": model.temperature,
            "max_tokens": model.max_tokens,
            "messages": messages,
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url=f"{self.settings.base_url.rstrip('/')}/chat/completions",
            method="POST",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )

        with urllib.request.urlopen(request, timeout=self.settings.timeout_seconds) as response:
            raw = json.loads(response.read().decode("utf-8"))
        return raw["choices"][0]["message"]["content"]

    def _responses_api(self, api_key: str, model: ModelSettings, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": model.name,
            "temperature": model.temperature,
            "max_output_tokens": model.max_tokens,
            "input": [
                {
                    "role": message["role"],
                    "content": [{"type": "input_text", "text": message["content"]}],
                }
                for message in messages
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url=f"{self.settings.base_url.rstrip('/')}/responses",
            method="POST",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )

        with urllib.request.urlopen(request, timeout=self.settings.timeout_seconds) as response:
            raw = json.loads(response.read().decode("utf-8"))
        output_text = raw.get("output_text")
        if output_text:
            return output_text

        output = raw.get("output", [])
        fragments: list[str] = []
        for item in output:
            for content in item.get("content", []):
                text = content.get("text")
                if text:
                    fragments.append(text)
        if fragments:
            return "".join(fragments)
        raise RuntimeError("Responses API returned no text output")

    def _resolve_api_key(self) -> str | None:
        key_or_env = self.settings.api_key_env.strip()
        api_key = os.environ.get(key_or_env)
        if api_key:
            return api_key

        # Backward compatibility: some local configs store the raw key here.
        if key_or_env.startswith(("sk-", "sk_", "sess-")):
            return key_or_env
        return None


class RoutedOpenAICompatibleClient:
    def __init__(self, providers: dict[str, ApiSettings]) -> None:
        self.clients = {name: OpenAICompatibleClient(settings) for name, settings in providers.items()}

    def chat(self, model: ModelSettings, messages: list[dict[str, str]]) -> str:
        provider_name = model.provider or "default"
        client = self.clients.get(provider_name)
        if client is None:
            raise RuntimeError(f"Unknown provider '{provider_name}' for model '{model.name}'")
        return client.chat(model, messages)


class MockLLMClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def chat(self, model: ModelSettings, messages: list[dict[str, str]]) -> str:
        prompt = messages[-1]["content"]
        self.calls.append({"model": model.name, "provider": model.provider or "default", "prompt": prompt})

        if "业务审核" in prompt and "返回严格 JSON 审核结果" in prompt:
            return json.dumps(
                {
                    "result": "PASS",
                    "average_score": 8.6,
                    "has_item_below_6": False,
                    "dimension_scores": {
                        "fidelity": 9,
                        "visual_clarity": 8,
                        "action_executability": 8,
                        "camera_executability": 8,
                        "audio_design": 9,
                        "emotion_accuracy": 9,
                    },
                    "report": "✅ 业务审核通过",
                    "issues": [],
                },
                ensure_ascii=False,
            )

        if "合规审核" in prompt and "返回严格 JSON 审核结果" in prompt:
            return json.dumps(
                {
                    "result": "PASS",
                    "violations": [],
                    "report": "✅ 合规审核通过",
                    "issues": [],
                },
                ensure_ascii=False,
            )

        if "你需要修订当前阶段一产物" in prompt:
            return self.chat(model, [{"role": "user", "content": "阶段一：导演分析\n剧本内容如下"}])

        if "你需要修订当前阶段二产物" in prompt:
            return self.chat(model, [{"role": "user", "content": "阶段二：服化道设计"}])

        if "你需要修订当前阶段三产物" in prompt:
            return self.chat(model, [{"role": "user", "content": "阶段三：Seedance 2.0 分镜编写"}])

        if "阶段一：导演分析" in prompt or ("阶段一" in prompt and "剧本内容如下" in prompt):
            return (
                "# 导演讲戏本\n\n"
                "## P01 开场建立\n\n"
                "- 人物：林书白\n"
                "- 场景：简陋住处\n"
                "- 镜头组：单镜头\n"
                "- 时长建议：8s\n\n"
                "**导演阐述**：林书白坐在狭小破旧的住处里，桌上的冷白灯勉强照亮他眼下的疲惫。"
                "他抬手揉了揉太阳穴，视线从残破书页移到窗外。镜头从桌面缓慢推近到他的侧脸，"
                "空气里只有纸张翻动和远处风声，灰蓝色夜色压住整个房间。\n\n---\n\n"
                "## 人物清单\n\n| 人物 | 年龄 | 外观关键词 | 素材状态 |\n|---|---|---|---|\n| 林书白 | 20 | 清瘦、黑发、旧布衣 | 新增 |\n\n"
                "## 场景清单\n\n| 场景 | 时间 | 光线/色调 | 氛围关键词 | 素材状态 |\n|---|---|---|---|---|\n| 简陋住处 | 夜晚 | 冷白台灯、灰蓝夜色 | 压抑、贫寒 | 新增 |\n"
            )

        if "阶段二：服化道设计" in prompt:
            return (
                "# 人物提示词\n\n## 林书白（ep01 新增）\n\n"
                "**出图要求**：一张图，左半边面部特写，右半边全身正面、侧面、背面设定图，白色背景\n\n"
                "**提示词**：角色设定图，白色背景。左半边是林书白的面部特写，清瘦的青年面容，黑色束发，眼神隐忍，肤色偏白但略带病气。"
                "右半边是全身正面、侧面、背面设定图，他穿洗旧的灰青色布衣，腰间系磨损布带，布鞋旧而干净，整体带贫寒书生气质。\n"
                "\n---\n\n# 场景道具提示词\n\n## ep01 场景宫格\n\n请生成一张 3×3 宫格布局的电影场景环境图像。\n\n"
                "### 视觉规范\n整体风格：写实影视感\n色彩基调：灰蓝冷调\n材质质感：旧木桌、斑驳墙面\n\n"
                "### Panel Breakdown（场景拆解）\n\n格1——【简陋住处】\n视角：狭小的室内空间里只有旧木桌、破窗和单盏冷白台灯，"
                "灰蓝夜色从窗缝渗入，墙面斑驳，桌角堆着翻旧的书页，空间压抑而寒冷。\n重点：冷白台灯与灰蓝夜色的对比。\n"
            )

        if "阶段三：Seedance 2.0 分镜编写" in prompt:
            return (
                "## 素材对应表\n\n| 引用编号 | 素材类型 | 对应素材 |\n|---|---|---|\n| @图片1 | 人物参考 | 林书白 |\n| @图片2 | 场景参考 | 简陋住处 |\n\n"
                "---\n\n## P01 开场建立\n\n**Seedance 2.0 提示词**：以@图片1中的林书白为主角，场景参考@图片2的简陋住处。"
                "开场先给室内环境一个短暂建立，旧木桌与破窗都静止在灰蓝夜色里。随后镜头缓慢推近林书白，"
                "他抬手揉太阳穴，把视线从书页移向窗外，呼吸很轻，纸页摩擦声和远处风声贴着画面推进。"
                "冷白台灯从上方压在他的脸侧，整体压抑而克制，电影感。"
            )

        return "未匹配到 mock 输出。"
