from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field


SlackSeverity = Literal["MEDIUM", "HIGH", "CRITICAL"]


class SlackAlertPayload(BaseModel):
    """Structured disruption alert payload for Slack notifications."""

    project_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    severity: SlackSeverity
    affected_routes: list[str] = Field(default_factory=list)
    top_recommendation: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    triggered_by: str = Field(min_length=1)


class SlackNotifyResult(BaseModel):
    """Delivery result for a Slack webhook alert operation."""

    model_config = ConfigDict(extra="allow")

    ok: bool
    status_code: int | None = None
    response_body: str | None = None
    sent_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SlackNotifier:
    """Send rich disruption notifications to Slack via incoming webhooks."""

    def __init__(self, webhook_url: str | None = None, timeout_seconds: float = 8.0) -> None:
        self.webhook_url = (webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")).strip()
        self.timeout_seconds = float(os.getenv("SLACK_WEBHOOK_TIMEOUT_SECONDS", str(timeout_seconds)))

    async def send_alert(self, payload: SlackAlertPayload) -> SlackNotifyResult:
        """Post Block Kit alert payload to Slack webhook."""
        if not self.webhook_url:
            return SlackNotifyResult(ok=False, response_body="SLACK_WEBHOOK_URL is not configured")

        message_payload = self._build_webhook_payload(payload)
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(self.webhook_url, json=message_payload)

        return SlackNotifyResult(
            ok=200 <= response.status_code < 300,
            status_code=response.status_code,
            response_body=response.text,
        )

    def _build_webhook_payload(self, payload: SlackAlertPayload) -> dict[str, object]:
        severity_badge = self._severity_badge(payload.severity)
        confidence_pct = round(payload.confidence * 100, 1)
        mention_prefix = "@channel " if payload.severity == "CRITICAL" else ""
        routes_text = ", ".join(payload.affected_routes) if payload.affected_routes else "No explicit route list"
        button_value = json.dumps(
            {
                "project_id": payload.project_id,
                "region_id": payload.region_id,
                "top_recommendation": payload.top_recommendation,
                "triggered_by": payload.triggered_by,
            }
        )

        text = (
            f"{mention_prefix}{severity_badge} Disruption alert in {payload.region_id} · "
            f"confidence {confidence_pct}%"
        )

        return {
            "text": text,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"{severity_badge} Disruption Alert", "emoji": True},
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Region:*\n{payload.region_id}"},
                        {"type": "mrkdwn", "text": f"*Confidence:*\n{confidence_pct}%"},
                        {"type": "mrkdwn", "text": f"*Affected Routes:*\n{routes_text}"},
                        {"type": "mrkdwn", "text": f"*Triggered By:*\n{payload.triggered_by}"},
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*Top Recommendation:*\n{payload.top_recommendation}\n\n"
                            f"*Reason:*\n{payload.reason}"
                        ),
                    },
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "style": "primary",
                            "action_id": "accept_recommendation",
                            "text": {"type": "plain_text", "text": "Accept Recommendation", "emoji": True},
                            "value": button_value,
                        }
                    ],
                },
            ],
        }

    @staticmethod
    def _severity_badge(severity: SlackSeverity) -> str:
        mapping = {
            "MEDIUM": "🟡 MEDIUM",
            "HIGH": "🟠 HIGH",
            "CRITICAL": "🔴 CRITICAL",
        }
        return mapping[severity]


slack_notifier = SlackNotifier()
