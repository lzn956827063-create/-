import json
from abc import ABC, abstractmethod
from typing import Optional

import requests
from flask import current_app


# ---------------------------------------------------------------------------
# Prompt templates for each AI action
# ---------------------------------------------------------------------------
ACTION_PROMPTS = {
    "polish": (
        "你是一位专业的文字编辑。请对以下文本进行润色，改善语法、清晰度和专业语气。"
        "保留所有事实性信息和原始含义。只返回润色后的文本，不要添加任何解释。"
    ),
    "tailor": (
        "请根据以下岗位要求重写这份简历内容："
        "{context}。使用有力的动词和行业关键词。"
        "保留所有事实性陈述。只返回重写后的文本，不要添加任何解释。"
    ),
    "expand": (
        "请将以下简短的项目描述扩展为 3-4 条详细且有影响力的要点，适用于简历。"
        "尽可能包含所用技术和可量化的成果。使用有力的动词。只返回扩展后的文本，"
        "以 '- ' 开头的要点形式，不要添加任何开头或结尾说明。"
    ),
    "proofread": (
        "请仔细校对以下文本。修正所有拼写、语法、标点和错别字。不要改变含义或语气。"
        "只返回修正后的文本，不要添加任何解释。"
    ),
}


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class AIProvider(ABC):
    """Abstract base class for AI model providers."""

    @abstractmethod
    def optimize(self, text: str, action: str, context: str = "") -> str:
        """Send text to the AI and return the optimized result."""
        ...


# ---------------------------------------------------------------------------
# Ollama (local)
# ---------------------------------------------------------------------------
class OllamaProvider(AIProvider):
    """Calls a local Ollama instance via its HTTP API."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def optimize(self, text: str, action: str, context: str = "") -> str:
        system_prompt = ACTION_PROMPTS.get(action, ACTION_PROMPTS["polish"])
        if "{context}" in system_prompt:
            system_prompt = system_prompt.format(context=context or "通用软件工程岗位")

        payload = {
            "model": self.model,
            "prompt": text,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.3, "top_p": 0.9},
        }
        url = f"{self.base_url}/api/generate"
        try:
            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", text).strip()
        except requests.RequestException as e:
            current_app.logger.error(f"Ollama request failed: {e}")
            raise AIProviderError(f"Ollama unavailable: {e}")

    def chat(self, messages: list) -> str:
        """Ollama 对话接口（使用 /api/chat 端点）。"""
        system_prompt = ""
        user_prompt = ""
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
            elif m["role"] == "user":
                user_prompt += m["content"] + "\n"
            elif m["role"] == "assistant":
                user_prompt += f"Assistant: {m['content']}\n"

        payload = {
            "model": self.model,
            "prompt": user_prompt.strip(),
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.7},
        }
        url = f"{self.base_url}/api/generate"
        try:
            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
        except requests.RequestException as e:
            current_app.logger.error(f"Ollama chat failed: {e}")
            raise AIProviderError(f"Ollama chat unavailable: {e}")


# ---------------------------------------------------------------------------
# DeepSeek (cloud, OpenAI-compatible)
# ---------------------------------------------------------------------------
class DeepSeekProvider(AIProvider):
    """Calls DeepSeek API via the OpenAI SDK."""

    def __init__(self, api_key: str, model: str, base_url: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def optimize(self, text: str, action: str, context: str = "") -> str:
        system_prompt = ACTION_PROMPTS.get(action, ACTION_PROMPTS["polish"])
        if "{context}" in system_prompt:
            system_prompt = system_prompt.format(context=context or "通用软件工程岗位")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.3,
                max_tokens=2000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            current_app.logger.error(f"DeepSeek request failed: {e}")
            raise AIProviderError(f"DeepSeek unavailable: {e}")

    def chat(self, messages: list) -> str:
        """DeepSeek 对话接口。"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            current_app.logger.error(f"DeepSeek chat failed: {e}")
            raise AIProviderError(f"DeepSeek chat unavailable: {e}")


# ---------------------------------------------------------------------------
# Alibaba Cloud Bailian (DashScope, OpenAI-compatible)
# ---------------------------------------------------------------------------
class AliyunProvider(AIProvider):
    """Calls Alibaba Cloud Bailian API via the OpenAI SDK (compatible mode)."""

    def __init__(self, api_key: str, model: str, base_url: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def optimize(self, text: str, action: str, context: str = "") -> str:
        system_prompt = ACTION_PROMPTS.get(action, ACTION_PROMPTS["polish"])
        if "{context}" in system_prompt:
            system_prompt = system_prompt.format(context=context or "通用软件工程岗位")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.3,
                max_tokens=2000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            current_app.logger.error(f"Aliyun Bailian request failed: {e}")
            raise AIProviderError(f"Aliyun Bailian unavailable: {e}")

    def chat(self, messages: list) -> str:
        """通用对话接口，接收完整的 messages 列表，返回 AI 回复。"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            current_app.logger.error(f"Aliyun Bailian chat failed: {e}")
            raise AIProviderError(f"Aliyun Bailian chat unavailable: {e}")


# ---------------------------------------------------------------------------
# Facade
# ---------------------------------------------------------------------------
class AIProviderError(Exception):
    """Raised when the AI provider call fails."""


class AIService:
    """Facade that selects the correct provider based on config."""

    def __init__(self, app=None):
        self._provider: Optional[AIProvider] = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        provider_name = app.config.get("AI_PROVIDER", "ollama")
        if provider_name == "ollama":
            self._provider = OllamaProvider(
                base_url=app.config["OLLAMA_BASE_URL"],
                model=app.config["OLLAMA_MODEL"],
            )
        elif provider_name == "deepseek":
            self._provider = DeepSeekProvider(
                api_key=app.config["DEEPSEEK_API_KEY"],
                model=app.config["DEEPSEEK_MODEL"],
                base_url=app.config["DEEPSEEK_BASE_URL"],
            )
        elif provider_name == "aliyun":
            self._provider = AliyunProvider(
                api_key=app.config["ALIYUN_API_KEY"],
                model=app.config["ALIYUN_MODEL"],
                base_url=app.config["ALIYUN_BASE_URL"],
            )
        else:
            raise ValueError(f"Unknown AI_PROVIDER: {provider_name}")

    @property
    def provider(self) -> AIProvider:
        if self._provider is None:
            raise RuntimeError("AIService not initialized. Call init_app() first.")
        return self._provider

    def optimize_text(self, text: str, action: str = "polish", context: str = "") -> str:
        """Optimize text using the configured AI provider."""
        return self.provider.optimize(text, action, context)


# Module-level singleton (lazy-init pattern)
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Return the singleton AIService, creating it if needed."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
        # If we have an app context, init now
        try:
            from flask import current_app

            _ai_service.init_app(current_app)
        except RuntimeError:
            pass  # No app context yet — will init on first request
    return _ai_service
