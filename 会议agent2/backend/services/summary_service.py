from __future__ import annotations

import json
import re
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from backend.core.config import load_prompt_config
from backend.core.paths import get_abs_path
from backend.models.factory import get_chat_model


class SummaryService:
    def __init__(self) -> None:
        self._chat_model = get_chat_model()
        self._prompt_config = load_prompt_config()

    def _load_prompt_text(self, config_key: str) -> str:
        prompt_path = Path(get_abs_path(self._prompt_config[config_key]))
        return prompt_path.read_text(encoding="utf-8").strip()

    def clean_transcript(self, transcript_text: str) -> str:
        text = transcript_text.replace("\r\n", "\n").replace("\r", "\n").strip()
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{2,}", "\n", text)
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        deduped_lines: list[str] = []
        for line in lines:
            if deduped_lines and deduped_lines[-1] == line:
                continue
            deduped_lines.append(line)

        text = "\n".join(deduped_lines)
        text = re.sub(r"[。]{2,}", "。", text)
        text = re.sub(r"[，]{2,}", "，", text)
        text = re.sub(r"[！]{2,}", "！", text)
        text = re.sub(r"[？]{2,}", "？", text)
        return text.strip()

    def extract_summary(self, clean_transcript_text: str, recent_meetings_context: str = "") -> dict:
        system_prompt = self._load_prompt_text("summary_extract_system_prompt_path")
        user_prompt_template = self._load_prompt_text("summary_extract_user_prompt_path")
        user_prompt = user_prompt_template.format(
            clean_transcript_text=clean_transcript_text,
            recent_meetings_context=recent_meetings_context or "无",
        )
        response = self._chat_model.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        content = str(response.content).strip()
        summary_json = self._parse_json(content)
        return self._normalize_summary_json(summary_json)

    def repair_summary(self, clean_transcript_text: str, summary_json: dict, validation_result: dict) -> dict:
        system_prompt = self._load_prompt_text("summary_repair_system_prompt_path")
        user_prompt_template = self._load_prompt_text("summary_repair_user_prompt_path")
        user_prompt = user_prompt_template.format(
            clean_transcript_text=clean_transcript_text,
            summary_json=json.dumps(summary_json, ensure_ascii=False, indent=2),
            validation_result=json.dumps(validation_result, ensure_ascii=False, indent=2),
        )
        response = self._chat_model.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        content = str(response.content).strip()
        repaired_summary_json = self._parse_json(content)
        return self._normalize_summary_json(repaired_summary_json)

    def render_summary(self, summary_json: dict) -> str:
        system_prompt = self._load_prompt_text("summary_system_prompt_path")
        user_prompt_template = self._load_prompt_text("summary_user_prompt_path")
        user_prompt = user_prompt_template.format(
            summary_json=json.dumps(summary_json, ensure_ascii=False, indent=2)
        )
        response = self._chat_model.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        return str(response.content).strip()

    def _parse_json(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.S)
            if not match:
                raise ValueError("Model did not return valid JSON")
            return json.loads(match.group(0))

    def _normalize_summary_json(self, summary_json: dict) -> dict:
        action_items = summary_json.get("action_items", [])
        if not isinstance(action_items, list):
            action_items = []

        normalized_actions = []
        for item in action_items:
            if not isinstance(item, dict):
                continue
            normalized_actions.append(
                {
                    "task": str(item.get("task", "")).strip(),
                    "owner": str(item.get("owner", "")).strip(),
                    "deadline": str(item.get("deadline", "")).strip(),
                    "status": str(item.get("status", "pending")).strip() or "pending",
                }
            )

        return {
            "meeting_topic": str(summary_json.get("meeting_topic", "")).strip(),
            "summary": str(summary_json.get("summary", "")).strip(),
            "key_points": self._normalize_string_list(summary_json.get("key_points", [])),
            "decisions": self._normalize_string_list(summary_json.get("decisions", [])),
            "action_items": normalized_actions,
            "risks": self._normalize_string_list(summary_json.get("risks", [])),
            "open_questions": self._normalize_string_list(summary_json.get("open_questions", [])),
        }

    def _normalize_string_list(self, value) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]


summary_service = SummaryService()
