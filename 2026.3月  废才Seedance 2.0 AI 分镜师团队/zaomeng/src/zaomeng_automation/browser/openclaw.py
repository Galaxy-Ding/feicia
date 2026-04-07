from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from ..models import AppConfig, PromptTask
from .base import BrowserOperator

CommandRunner = Callable[[Sequence[str]], str]

_CLICKABLE_ROLE_HINTS = ("button", "menuitem", "link", "tab")
_TEXT_INPUT_ROLE_HINTS = ("textbox", "textarea", "input", "combobox")
_DOWNLOAD_TEXTS = ("下载", "保存", "保存图片", "下载图片")
_GENERATION_READY_TEXTS = ("提示词", "输入文字", "创意无限可能", "图片生成", "文生图")
_SUBMIT_TEXTS = ("生成", "立即创作", "提交", "开始", "发送")
_VIEW_RESULT_TEXTS = ("去查看", "查看结果", "查看作品")


class OpenClawBrowserOperator(BrowserOperator):
    def __init__(
        self,
        *,
        browser_profile: str = "openclaw",
        openclaw_bin: Optional[Path] = None,
        command_runner: Optional[CommandRunner] = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.browser_profile = browser_profile
        self.openclaw_bin = openclaw_bin or self._discover_openclaw_bin()
        self.command_runner = command_runner or self._run_command
        self.sleep_fn = sleep_fn
        self.target_id: Optional[str] = None
        self.config: Optional[AppConfig] = None
        self.selectors: Dict[str, Any] = {}
        self.download_root = Path("/tmp/openclaw/downloads")
        self.previous_result_urls: set[str] = set()
        self.ready_result_urls: List[str] = []

    def validate_login(self, config: AppConfig) -> bool:
        self.config = config
        self.browser_profile = config.openclaw_browser_profile or self.browser_profile
        self._ensure_browser_started()
        self._ensure_target(config.jimeng_url)
        self._wait_for_page_ready()

        snapshot = self._snapshot()
        current_url = self._current_url()
        if self._has_login_gate(snapshot):
            return False
        has_login_marker = any(marker in snapshot for marker in config.login_markers)
        return has_login_marker or current_url.startswith(config.generation_url)

    def open_generation_page(self, config: AppConfig, selectors: Dict[str, Any]) -> bool:
        self.config = config
        self.selectors = selectors
        self.browser_profile = config.openclaw_browser_profile or self.browser_profile
        self._ensure_browser_started()
        self._ensure_target(config.generation_url)
        self._wait_for_page_ready()

        snapshot = self._snapshot()
        current_url = self._current_url()
        if not current_url.startswith(config.generation_url):
            self._open_target(config.generation_url)
            self._wait_for_page_ready()
            snapshot = self._snapshot()
            current_url = self._current_url()

        if current_url.startswith(config.generation_url) and self._resolve_prompt_input_ref(snapshot):
            return True

        entry_spec = self._selector_spec("image_generation_entry")
        entry_ref = self._find_ref(
            snapshot,
            self._selector_text_candidates(entry_spec) if entry_spec else [],
            role_hints=_CLICKABLE_ROLE_HINTS,
        )
        if entry_ref:
            self._browser("click", entry_ref)
            self._wait_for_page_ready()
            snapshot = self._snapshot()

        return self._resolve_prompt_input_ref(snapshot) is not None

    def _open_target(self, url: str) -> None:
        last_error: Optional[RuntimeError] = None
        for _ in range(3):
            try:
                output = self._browser("open", url)
                target_id = self._parse_target_id(output)
                if target_id:
                    self.target_id = target_id
                return
            except RuntimeError as exc:
                last_error = exc
                if "EAI_AGAIN" not in str(exc):
                    raise
                self.sleep_fn(1)

        if self.target_id:
            self._navigate_target(url)
            return

        if last_error:
            raise last_error

    def _navigate_target(self, url: str) -> None:
        args = ["navigate", url]
        if self.target_id:
            args.extend(["--target-id", self.target_id])
        self._browser(*args)

    def submit_prompt(self, task: PromptTask) -> str:
        prompt_ref = self._resolve_prompt_input_ref(self._snapshot())
        if not prompt_ref:
            raise RuntimeError("未找到提示词输入框，无法提交任务")

        self.previous_result_urls = self._normalized_result_url_set(
            self._collect_result_image_urls(limit=self._result_probe_limit())
        )
        self.ready_result_urls = []
        self._clear_input(prompt_ref)
        self._type_prompt(prompt_ref, task.prompt)

        submit_ref = self._resolve_submit_ref(self._snapshot())
        if submit_ref:
            self._browser("click", submit_ref)
        elif self._click_nearby_submit_button(prompt_ref):
            pass
        else:
            self._browser("press", "Enter")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"openclaw-{task.task_id}-{timestamp}"

    def wait_for_generation(
        self,
        job_id: str,
        timeout_seconds: int,
        poll_interval_seconds: int,
    ) -> Dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        last_snapshot = ""
        while time.monotonic() < deadline:
            last_snapshot = self._snapshot()
            if self._find_refs(last_snapshot, _DOWNLOAD_TEXTS, role_hints=_CLICKABLE_ROLE_HINTS):
                self.ready_result_urls = []
                return {"job_id": job_id, "status": "complete"}
            ready_urls = self._result_urls_ready(
                self._collect_result_image_urls(limit=self._result_probe_limit())
            )
            if ready_urls:
                self.ready_result_urls = ready_urls
                return {"job_id": job_id, "status": "complete"}
            if self._open_result_view(last_snapshot):
                self._wait_for_page_ready()
                ready_urls = self._result_urls_ready(
                    self._collect_result_image_urls(limit=self._result_probe_limit())
                )
                if ready_urls:
                    self.ready_result_urls = ready_urls
                    return {"job_id": job_id, "status": "complete"}
            if self._has_login_gate(last_snapshot):
                raise RuntimeError("OpenClaw 浏览器未登录即梦，或仍有登录/协议弹窗未处理")
            self.sleep_fn(poll_interval_seconds)

        raise TimeoutError("等待生成结果超时，页面未出现下载入口")

    def download_images(self, task: PromptTask, staging_dir: Path) -> List[Path]:
        result_urls = self.ready_result_urls or self._result_urls_ready(
            self._collect_result_image_urls(limit=self._result_probe_limit())
        )
        if result_urls:
            return self._download_images_from_urls(task, staging_dir, result_urls)

        snapshot = self._snapshot()
        download_refs = self._find_refs(snapshot, _DOWNLOAD_TEXTS, role_hints=_CLICKABLE_ROLE_HINTS)
        if not download_refs:
            raise RuntimeError("未找到下载按钮，无法下载图片")

        if self.config:
            download_refs = download_refs[: self.config.images_per_prompt]

        staging_dir.mkdir(parents=True, exist_ok=True)
        self.download_root.mkdir(parents=True, exist_ok=True)

        files: List[Path] = []
        for index, ref in enumerate(download_refs, start=1):
            temp_path = self.download_root / f"{task.task_id}-{index:03d}.png"
            if temp_path.exists():
                temp_path.unlink()
            output = self._browser("download", ref, str(temp_path), "--timeout-ms", "120000")
            downloaded_path = self._parse_download_path(output) or temp_path
            if not downloaded_path.exists():
                raise RuntimeError(f"下载命令执行后未找到文件: {downloaded_path}")
            final_path = staging_dir / downloaded_path.name
            shutil.move(str(downloaded_path), final_path)
            files.append(final_path)
        return files

    def _download_images_from_urls(
        self,
        task: PromptTask,
        staging_dir: Path,
        urls: Sequence[str],
    ) -> List[Path]:
        staging_dir.mkdir(parents=True, exist_ok=True)

        files: List[Path] = []
        for index, url in enumerate(urls[: self._expected_image_count()], start=1):
            extension = self._infer_extension_from_url(url)
            final_path = staging_dir / f"{task.task_id}-{index:03d}{extension}"
            self._download_image_from_url(url, final_path)
            files.append(final_path)
        return files

    def _selector_spec(self, name: str) -> Optional[Dict[str, Any]]:
        elements = self.selectors.get("elements", [])
        for element in elements:
            if element.get("name") == name:
                return element
        return None

    def _resolve_prompt_input_ref(self, snapshot: str) -> Optional[str]:
        rich_text_ref = self._find_rich_text_ref(snapshot)
        if rich_text_ref:
            return rich_text_ref

        spec = self._selector_spec("prompt_input")
        text_candidates = self._selector_text_candidates(spec) if spec else []
        text_candidates.extend(text for text in _GENERATION_READY_TEXTS if text not in text_candidates)
        return self._find_ref(snapshot, text_candidates, role_hints=_TEXT_INPUT_ROLE_HINTS)

    def _resolve_submit_ref(self, snapshot: str) -> Optional[str]:
        spec = self._selector_spec("generate_button")
        text_candidates = self._selector_text_candidates(spec) if spec else []
        text_candidates.extend(text for text in _SUBMIT_TEXTS if text not in text_candidates)
        direct_ref = self._find_direct_role_ref(snapshot, text_candidates, role="button")
        if direct_ref:
            return direct_ref
        return self._find_enabled_icon_submit_ref(snapshot)

    def _click_selector_spec(self, spec: Dict[str, Any]) -> bool:
        snapshot = self._snapshot()
        ref = self._find_ref(snapshot, self._selector_text_candidates(spec), role_hints=_CLICKABLE_ROLE_HINTS)
        if not ref:
            return False
        self._browser("click", ref)
        return True

    def _selector_text_candidates(self, spec: Dict[str, Any]) -> List[str]:
        if not spec:
            return []

        candidates: List[str] = []
        if spec.get("match_text"):
            candidates.append(str(spec["match_text"]))

        for key in ("primary_selector",):
            value = spec.get(key)
            if value:
                candidates.extend(self._extract_selector_text(str(value)))

        for selector in spec.get("fallback_selectors", []):
            candidates.extend(self._extract_selector_text(str(selector)))

        deduped: List[str] = []
        for candidate in candidates:
            normalized = candidate.strip()
            if normalized and normalized not in deduped:
                deduped.append(normalized)
        return deduped

    @staticmethod
    def _extract_selector_text(selector: str) -> List[str]:
        texts = re.findall(r"'([^']+)'|\"([^\"]+)\"", selector)
        generic_tokens = {"button", "textbox", "textarea", "input", "combobox", "link", "tab", "menuitem"}
        flattened = [
            value
            for left, right in texts
            for value in [left or right]
            if value and value.strip().lower() not in generic_tokens
        ]
        if flattened:
            return flattened
        if "textarea" in selector:
            return ["提示词", "输入文字", "创意无限可能"]
        if "button" in selector:
            return ["生成", "图片生成", "下载"]
        return []

    def _ensure_browser_started(self) -> None:
        self._browser("start")

    def _ensure_target(self, url: str) -> None:
        if self.target_id:
            if self._activate_existing_target(self.target_id):
                return
            self.target_id = None

        existing_target_id = self._find_existing_target(url)
        if existing_target_id:
            if self._activate_existing_target(existing_target_id):
                return

        output = self._browser("open", url)
        self.target_id = self._parse_target_id(output)
        if not self.target_id:
            raise RuntimeError(f"OpenClaw 未返回 target id: {output}")

    def _activate_existing_target(self, target_id: str) -> bool:
        try:
            self._browser("focus", target_id)
            self.target_id = target_id
            return True
        except Exception:
            return False

    def _find_existing_target(self, url: str) -> Optional[str]:
        output = self._browser("tabs")
        current_title: Optional[str] = None
        current_url: Optional[str] = None
        for raw_line in output.splitlines():
            line = raw_line.strip()
            if re.match(r"^\d+\.\s", line):
                current_title = re.sub(r"^\d+\.\s*", "", line)
                current_url = None
                continue
            if line.startswith("id: "):
                target_id = line.split("id: ", 1)[1].strip()
                if current_url and (url in current_url or "jimeng.jianying.com" in current_url):
                    return target_id
                if current_title and "即梦" in current_title:
                    return target_id
                continue
            if line and "://" in line:
                current_url = line
        return None

    def _wait_for_page_ready(self) -> None:
        self._browser("wait", "--load", "domcontentloaded", "--timeout-ms", "30000")

    def _snapshot(self) -> str:
        args = ["snapshot", "--limit", "300"]
        if self.target_id:
            args.extend(["--target-id", self.target_id])
        return self._browser(*args)

    def _current_url(self) -> str:
        output = self._evaluate("() => location.href")
        return output if isinstance(output, str) else str(output)

    def _clear_input(self, ref: str) -> None:
        js = (
            "(el) => {"
            "  if (!el) return false;"
            "  el.focus();"
            "  if (el.isContentEditable) {"
            "    const root = el;"
            "    root.innerHTML = '<p></p>';"
            "    const paragraph = root.querySelector('p') || root;"
            "    const selection = window.getSelection();"
            "    const range = document.createRange();"
            "    range.selectNodeContents(paragraph);"
            "    range.collapse(true);"
            "    selection?.removeAllRanges();"
            "    selection?.addRange(range);"
            "    root.dispatchEvent(new InputEvent('input', { bubbles: true, composed: true, inputType: 'deleteContentBackward', data: '' }));"
            "    root.dispatchEvent(new Event('change', { bubbles: true }));"
            "    return true;"
            "  }"
            "  if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {"
            "    const proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;"
            "    const descriptor = Object.getOwnPropertyDescriptor(proto, 'value');"
            "    if (descriptor && descriptor.set) {"
            "      descriptor.set.call(el, '');"
            "    } else {"
            "      el.value = '';"
            "    }"
            "    el.dispatchEvent(new Event('input', { bubbles: true, composed: true }));"
            "    el.dispatchEvent(new Event('change', { bubbles: true }));"
            "    return true;"
            "  }"
            "  el.textContent = '';"
            "  el.dispatchEvent(new InputEvent('input', { bubbles: true, composed: true, data: '' }));"
            "  el.dispatchEvent(new Event('change', { bubbles: true }));"
            "  return true;"
            "}"
        )
        args = ["evaluate", "--ref", ref, "--fn", js]
        if self.target_id:
            args.extend(["--target-id", self.target_id])
        self._browser(*args)

    def _type_prompt(self, ref: str, prompt: str) -> None:
        escaped_prompt = json.dumps(prompt, ensure_ascii=False)
        js = (
            "(el) => {"
            "  if (!el) return false;"
            "  el.focus();"
            "  const prompt = "
            f"{escaped_prompt};"
            "  if (el.isContentEditable) {"
            "    const root = el;"
            "    root.innerHTML = '';"
            "    const paragraph = document.createElement('p');"
            "    paragraph.textContent = prompt;"
            "    root.appendChild(paragraph);"
            "    const selection = window.getSelection();"
            "    const range = document.createRange();"
            "    range.selectNodeContents(paragraph);"
            "    range.collapse(false);"
            "    selection?.removeAllRanges();"
            "    selection?.addRange(range);"
            "    root.dispatchEvent(new InputEvent('input', { bubbles: true, composed: true, inputType: 'insertText', data: prompt }));"
            "    root.dispatchEvent(new Event('change', { bubbles: true }));"
            "    return true;"
            "  }"
            "  return false;"
            "}"
        )
        if self._evaluate(js, ref=ref) is True:
            return
        self._browser("type", ref, prompt)

    def _click_nearby_submit_button(self, ref: str) -> bool:
        js = (
            "(el) => {"
            "  if (!el) return false;"
            "  let node = el;"
            "  for (let depth = 0; depth < 6 && node; depth += 1, node = node.parentElement) {"
            "    const buttons = Array.from(node.querySelectorAll('button:not([disabled])'));"
            "    if (!buttons.length) continue;"
            "    const iconOnly = buttons.filter((button) => {"
            "      const rect = button.getBoundingClientRect();"
            "      return rect.width > 0 && rect.height > 0 && !(button.innerText || '').trim();"
            "    });"
            "    const candidates = iconOnly.length ? iconOnly : buttons;"
            "    const target = candidates[candidates.length - 1];"
            "    if (target) { target.click(); return true; }"
            "  }"
            "  return false;"
            "}"
        )
        output = self._evaluate(js, ref=ref)
        return output is True or output == "true"

    def _open_result_view(self, snapshot: str) -> bool:
        view_ref = self._find_ref(snapshot, _VIEW_RESULT_TEXTS, role_hints=("button",))
        if view_ref:
            self._browser("click", view_ref)
            return True

        js = (
            "() => {"
            "  const texts = ['去查看', '查看结果', '查看作品'];"
            "  const isVisible = (node) => {"
            "    if (!node) return false;"
            "    const rect = node.getBoundingClientRect();"
            "    return rect.width > 0 && rect.height > 0;"
            "  };"
            "  const primaryNodes = Array.from(document.querySelectorAll('button, [role=\"button\"], a'));"
            "  const target = primaryNodes.find((node) => {"
            "    const text = (node.innerText || node.textContent || '').trim();"
            "    return text && isVisible(node) && texts.some((item) => text.includes(item));"
            "  });"
            "  if (target) {"
            "    target.click();"
            "    return true;"
            "  }"
            "  const fallbackNodes = Array.from(document.querySelectorAll('div, span, p'));"
            "  const fallback = fallbackNodes.find((node) => {"
            "    const text = (node.innerText || node.textContent || '').trim();"
            "    return text && isVisible(node) && texts.some((item) => text.includes(item));"
            "  });"
            "  if (!fallback) return false;"
            "  const clickable = fallback.closest('button, [role=\"button\"], a');"
            "  if (clickable && isVisible(clickable)) {"
            "    clickable.click();"
            "    return true;"
            "  }"
            "  fallback.click();"
            "  return true;"
            "}"
        )
        output = self._evaluate(js)
        return output is True or output == "true"

    def _collect_result_image_urls(self, limit: int) -> List[str]:
        js = (
            "() => {"
            "  const hostPattern = /(dreamina-sign|heycan-hgt-sign|byteimg)/i;"
            "  const matches = [];"
            "  const seen = new Set();"
            "  for (const element of document.querySelectorAll('button, [role=\"button\"], a')) {"
            "    const img = element.querySelector('img');"
            "    if (!img) continue;"
            "    const src = img.currentSrc || img.src || '';"
            "    if (!hostPattern.test(src)) continue;"
            "    const rect = element.getBoundingClientRect();"
            "    const width = Math.max(rect.width, img.naturalWidth || 0);"
            "    const height = Math.max(rect.height, img.naturalHeight || 0);"
            "    if (width < 120 || height < 120) continue;"
            "    if (seen.has(src)) continue;"
            "    seen.add(src);"
            "    matches.push({ src, top: rect.top, left: rect.left });"
            "  }"
            "  matches.sort((left, right) => left.top - right.top || left.left - right.left);"
            f"  return matches.slice(0, {limit}).map((item) => item.src);"
            "}"
        )
        output = self._evaluate(js)
        if not isinstance(output, list):
            return []
        return [str(item) for item in output if isinstance(item, str) and item.strip()]

    def _result_urls_ready(self, urls: Sequence[str]) -> List[str]:
        if not urls:
            return []
        if not self.previous_result_urls:
            return list(urls[: self._expected_image_count()])

        ready_urls: List[str] = []
        seen: set[str] = set()
        for url in urls:
            normalized = self._normalize_result_url(url)
            if normalized in self.previous_result_urls or normalized in seen:
                continue
            seen.add(normalized)
            ready_urls.append(url)
            if len(ready_urls) >= self._expected_image_count():
                return ready_urls
        return []

    def _expected_image_count(self) -> int:
        if self.config:
            return max(1, self.config.images_per_prompt)
        return 1

    def _result_probe_limit(self) -> int:
        return max(8, self._expected_image_count() * 8)

    @staticmethod
    def _normalize_result_url(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def _normalized_result_url_set(self, urls: Sequence[str]) -> set[str]:
        return {self._normalize_result_url(url) for url in urls if url}

    def _evaluate(self, fn: str, *, ref: Optional[str] = None) -> Any:
        args = ["evaluate"]
        if ref:
            args.extend(["--ref", ref])
        args.extend(["--fn", fn])
        if self.target_id:
            args.extend(["--target-id", self.target_id])
        last_error: Optional[RuntimeError] = None
        for _ in range(3):
            try:
                output = self._browser(*args).strip()
                break
            except RuntimeError as exc:
                last_error = exc
                if "gateway timeout after 20000ms" not in str(exc):
                    raise
                self.sleep_fn(1)
        else:
            if last_error:
                raise last_error
            raise RuntimeError("OpenClaw evaluate failed without details")
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output.strip().strip('"')

    def _download_image_from_url(self, url: str, destination: Path) -> None:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=120) as response:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("wb") as handle:
                shutil.copyfileobj(response, handle)

    @staticmethod
    def _infer_extension_from_url(url: str) -> str:
        parsed = urlparse(url)
        suffix = Path(parsed.path).suffix.lower()
        if suffix:
            return suffix

        format_values = parse_qs(parsed.query).get("format", [])
        if format_values:
            format_value = format_values[0].strip().lower()
            if format_value.startswith("."):
                return format_value
            if format_value:
                return f".{format_value}"
        return ".png"

    def _find_ref(self, snapshot: str, texts: Sequence[str], *, role_hints: Sequence[str]) -> Optional[str]:
        refs = self._find_refs(snapshot, texts, role_hints=role_hints)
        return refs[0] if refs else None

    def _find_direct_role_ref(self, snapshot: str, texts: Sequence[str], *, role: str) -> Optional[str]:
        wanted = [text.lower() for text in texts if text]
        if not wanted:
            return None

        for raw_line in snapshot.splitlines():
            current_line = raw_line.lower()
            if role not in current_line:
                continue
            if not any(text in current_line for text in wanted):
                continue
            ref_match = re.search(r"\[ref=([^\]]+)\]", raw_line)
            if ref_match:
                return ref_match.group(1)
        return None

    @staticmethod
    def _find_rich_text_ref(snapshot: str) -> Optional[str]:
        matches: List[str] = []
        for raw_line in snapshot.splitlines():
            line = raw_line.lower()
            if 'textbox' not in line:
                continue
            if 'ref=' not in line:
                continue
            ref_match = re.search(r"\[ref=([^\]]+)\]", raw_line)
            if not ref_match:
                continue
            ref = ref_match.group(1)
            matches.append(ref)
        return matches[-1] if matches else None

    @staticmethod
    def _find_enabled_icon_submit_ref(snapshot: str) -> Optional[str]:
        candidates: List[str] = []
        for raw_line in snapshot.splitlines():
            line = raw_line.lower()
            if "button" not in line or "ref=" not in line:
                continue
            if "[disabled]" in line:
                continue
            if '"' in raw_line:
                continue
            ref_match = re.search(r"\[ref=([^\]]+)\]", raw_line)
            if not ref_match:
                continue
            candidates.append(ref_match.group(1))
        return candidates[-1] if candidates else None

    def _find_refs(self, snapshot: str, texts: Sequence[str], *, role_hints: Sequence[str]) -> List[str]:
        wanted = [text.lower() for text in texts if text]
        if not wanted:
            return []

        matches: List[str] = []
        ref_stack: List[tuple[int, str, str]] = []
        for raw_line in snapshot.splitlines():
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            while ref_stack and ref_stack[-1][0] >= indent:
                ref_stack.pop()

            current_line = raw_line.lower()
            ref_match = re.search(r"\[ref=([^\]]+)\]", raw_line)
            if ref_match:
                ref_stack.append((indent, ref_match.group(1), current_line))

            if not any(text in current_line for text in wanted):
                continue

            ref = self._pick_candidate_ref(ref_stack, role_hints)
            if ref and ref not in matches:
                matches.append(ref)
        return matches

    @staticmethod
    def _pick_candidate_ref(ref_stack: Sequence[tuple[int, str, str]], role_hints: Sequence[str]) -> Optional[str]:
        for _, ref, line in reversed(ref_stack):
            if any(role in line for role in role_hints):
                return ref
        if ref_stack and not role_hints:
            return ref_stack[-1][1]
        return None

    @staticmethod
    def _parse_target_id(output: str) -> Optional[str]:
        match = re.search(r"id:\s*([A-Z0-9]+)", output)
        return match.group(1) if match else None

    @staticmethod
    def _parse_download_path(output: str) -> Optional[Path]:
        match = re.search(r"(/tmp/openclaw/downloads/[^\s]+)", output)
        return Path(match.group(1)) if match else None

    @staticmethod
    def _has_login_gate(snapshot: str) -> bool:
        indicators = (
            'menuitem "登录"',
            'button "登录"',
            "前往登录",
            "同意协议后前往登录",
        )
        return any(indicator in snapshot for indicator in indicators)

    def _browser(self, *args: str) -> str:
        command = [str(self.openclaw_bin), "browser", "--browser-profile", self.browser_profile, *args]
        return self.command_runner(command)

    def _run_command(self, command: Sequence[str]) -> str:
        env = os.environ.copy()
        node_bin = str(self.openclaw_bin.parent)
        env["PATH"] = node_bin + os.pathsep + env.get("PATH", "")
        completed = subprocess.run(command, check=False, capture_output=True, text=True, env=env)
        if completed.returncode != 0:
            details = completed.stderr.strip() or completed.stdout.strip() or f"exit={completed.returncode}"
            raise RuntimeError(f"OpenClaw command failed: {' '.join(command)} :: {details}")
        return completed.stdout.strip()

    @staticmethod
    def _discover_openclaw_bin() -> Path:
        env_bin = os.environ.get("OPENCLAW_BIN")
        if env_bin:
            path = Path(env_bin).expanduser()
            if path.exists():
                return path

        discovered = shutil.which("openclaw")
        if discovered:
            return Path(discovered)

        candidates = sorted(Path.home().glob(".nvm/versions/node/v*/bin/openclaw"), reverse=True)
        if candidates:
            return candidates[0]

        raise FileNotFoundError("未找到 openclaw 可执行文件，请设置 OPENCLAW_BIN 或将其加入 PATH")
