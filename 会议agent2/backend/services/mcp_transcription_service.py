from __future__ import annotations

import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from backend.core.config import load_mcp_config


class MCPTranscriptionService:
    """Speech-to-text client backed by an MCP tool call."""

    def __init__(self) -> None:
        self._config = load_mcp_config()["speech_to_text"]

    async def _transcribe_async(self, file_url: str) -> str:
        """Call the remote MCP speech-to-text tool."""
        headers = {"Authorization": f"Bearer {self._get_api_key()}"}
        async with streamablehttp_client(self._config["base_url"], headers=headers, timeout=300) as (
            read_stream,
            write_stream,
            _,
        ):
            session = ClientSession(read_stream, write_stream)
            async with session:
                await session.initialize()
                result = await session.call_tool(
                    self._config["tool_name"],
                    {
                        "file_urls": [file_url],
                        "language_hints": self._config.get("language_hints", ["zh"]),
                    },
                )
        return self._extract_text(result)

    def _extract_text(self, result) -> str:
        """Normalize tool output into a plain transcript string."""
        content = getattr(result, "content", None)
        if isinstance(content, list):
            text_parts = []
            for item in content:
                text = getattr(item, "text", None)
                if isinstance(text, str) and text.strip():
                    normalized = self._extract_text_from_string(text)
                    if normalized:
                        text_parts.append(normalized)
            if text_parts:
                return "\n".join(text_parts)
        structured = getattr(result, "structuredContent", None)
        if isinstance(structured, dict):
            normalized = self._extract_text_from_payload(structured)
            if normalized:
                return normalized
            for key in ("text", "result", "transcript"):
                value = structured.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return self._extract_text_from_string(str(result).strip())

    def _extract_text_from_string(self, value: str) -> str:
        """Try to parse plain or JSON-encoded transcription output."""
        value = value.strip()
        if not value:
            return ""
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return value
        normalized = self._extract_text_from_payload(payload)
        return normalized or value

    def _extract_text_from_payload(self, payload) -> str:
        """Recursively extract transcript text from nested payloads."""
        if isinstance(payload, dict):
            results = payload.get("results")
            if isinstance(results, list):
                parts = [str(item).strip() for item in results if str(item).strip()]
                if parts:
                    return "\n".join(parts)
            for key in ("text", "result", "transcript"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            data = payload.get("data")
            if data is not None:
                return self._extract_text_from_payload(data)
        if isinstance(payload, list):
            parts = [self._extract_text_from_payload(item) for item in payload]
            parts = [item for item in parts if item]
            if parts:
                return "\n".join(parts)
        return ""

    def _get_api_key(self) -> str:
        """Read the required MCP API key from the environment."""
        api_key = os.getenv("MCP_API_KEY", "").strip()
        if not api_key:
            raise ValueError("Missing MCP_API_KEY in .env")
        return api_key

    def transcribe_audio(self, file_url: str) -> str:
        """Synchronously transcribe one remote audio file."""
        return asyncio.run(self._transcribe_async(file_url))


transcription_service = MCPTranscriptionService()
