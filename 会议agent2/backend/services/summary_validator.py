from __future__ import annotations

import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from backend.core.config import load_prompt_config
from backend.core.paths import get_abs_path
from backend.models.factory import get_chat_model


class SummaryValidatorService:
    def __init__(self) -> None:
        self._chat_model = get_chat_model()
        self._prompt_config = load_prompt_config()

    def _load_prompt_text(self, config_key: str) -> str:
        prompt_path = Path(get_abs_path(self._prompt_config[config_key]))
        return prompt_path.read_text(encoding="utf-8").strip()

    def validate_summary(self, clean_transcript_text: str, summary_json: dict, recent_meetings_context: str = "") -> dict:
        system_prompt = self._load_prompt_text("summary_validate_system_prompt_path")
        user_prompt_template = self._load_prompt_text("summary_validate_user_prompt_path")
        user_prompt = user_prompt_template.format(
            clean_transcript_text=clean_transcript_text,
            summary_json=json.dumps(summary_json, ensure_ascii=False, indent=2),
            recent_meetings_context=recent_meetings_context or "无",
        )
        response = self._chat_model.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        content = str(response.content).strip()
        result = self._parse_json(content)
        return self._normalize_validation_result(clean_transcript_text, summary_json, result)

    def _parse_json(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end < start:
                raise ValueError("Validator did not return valid JSON")
            return json.loads(content[start : end + 1])

    def _normalize_validation_result(self, clean_transcript_text: str, summary_json: dict, result: dict) -> dict:
        issues = result.get("issues", [])
        if not isinstance(issues, list):
            issues = []

        normalized_issues = []
        for item in issues:
            if not isinstance(item, dict):
                continue
            issue_type = str(item.get("type", "")).strip() or "unknown_issue"
            message = str(item.get("message", "")).strip() or "Unknown issue"
            normalized_issues.append({"type": issue_type, "message": message})

        repair_instructions = result.get("repair_instructions", [])
        if not isinstance(repair_instructions, list):
            repair_instructions = []
        normalized_repair_instructions = [
            str(item).strip() for item in repair_instructions if str(item).strip()
        ]

        rule_issues = self._run_rule_checks(clean_transcript_text, summary_json)
        normalized_issues.extend(rule_issues)

        passed = bool(result.get("passed", True)) and not normalized_issues
        raw_score = result.get("score", 0.0)
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = 0.0

        if rule_issues and not normalized_repair_instructions:
            normalized_repair_instructions = [issue["message"] for issue in rule_issues]

        return {
            "passed": passed,
            "score": max(0.0, min(score, 1.0)),
            "issues": normalized_issues,
            "repair_instructions": normalized_repair_instructions,
        }

    def _run_rule_checks(self, clean_transcript_text: str, summary_json: dict) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []

        meeting_topic = str(summary_json.get("meeting_topic", "")).strip()
        summary = str(summary_json.get("summary", "")).strip()
        key_points = summary_json.get("key_points", [])
        action_items = summary_json.get("action_items", [])

        if not clean_transcript_text.strip():
            issues.append({"type": "empty_transcript", "message": "会议文本为空，无法完成总结。"})
        if not meeting_topic:
            issues.append({"type": "missing_topic", "message": "meeting_topic 为空，请重新提取会议主题。"})
        if not summary:
            issues.append({"type": "missing_summary", "message": "summary 为空，请补充一句话总结。"})
        if not isinstance(key_points, list) or len([item for item in key_points if str(item).strip()]) < 2:
            issues.append({"type": "weak_key_points", "message": "key_points 信息不足，至少补充两条关键讨论点。"})
        if not isinstance(action_items, list):
            issues.append({"type": "invalid_action_items", "message": "action_items 结构错误，请返回数组。"})
        else:
            for index, item in enumerate(action_items, start=1):
                if not isinstance(item, dict):
                    issues.append({"type": "invalid_action_item", "message": f"第 {index} 条 action_item 不是对象。"})
                    continue
                if not str(item.get("task", "")).strip():
                    issues.append({"type": "missing_task", "message": f"第 {index} 条 action_item 缺少 task。"})
        return issues


summary_validator_service = SummaryValidatorService()
