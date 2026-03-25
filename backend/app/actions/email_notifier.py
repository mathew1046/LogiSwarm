from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from email.message import EmailMessage
from typing import Literal

import aiosmtplib
from pydantic import BaseModel, ConfigDict, Field

from app.bus.connection import get_redis_client


EmailSeverity = Literal["MEDIUM", "HIGH", "CRITICAL"]


class EmailAlertPayload(BaseModel):
    """Structured disruption alert payload rendered into an HTML email."""

    project_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    severity: EmailSeverity
    affected_regions: list[str] = Field(default_factory=list)
    route_recommendations: list[str] = Field(default_factory=list)
    propagation_forecast: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    recipients: list[str] = Field(default_factory=list)


class EmailNotifyResult(BaseModel):
    """Delivery result for an email alert operation."""

    model_config = ConfigDict(extra="allow")

    ok: bool
    throttled: bool = False
    recipients: list[str] = Field(default_factory=list)
    sent_at: datetime | None = None
    error: str | None = None


class EmailNotifier:
    """Dispatch HTML disruption emails with per-region anti-spam throttling."""

    def __init__(self) -> None:
        self.smtp_host = os.getenv("SMTP_HOST", "").strip()
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "").strip()
        self.smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
        self.smtp_from_email = os.getenv("SMTP_FROM_EMAIL", "").strip()
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"}
        self.throttle_seconds = int(os.getenv("EMAIL_ALERT_THROTTLE_SECONDS", "1800"))
        self.default_recipients = [
            item.strip()
            for item in os.getenv("EMAIL_DEFAULT_RECIPIENTS", "").split(",")
            if item.strip()
        ]
        recipients_map_raw = os.getenv("EMAIL_RECIPIENTS_BY_PROJECT_JSON", "{}")
        try:
            parsed_map = json.loads(recipients_map_raw)
        except json.JSONDecodeError:
            parsed_map = {}
        self.project_recipients_map: dict[str, list[str]] = {
            str(key): [str(item) for item in value if isinstance(item, str)]
            for key, value in parsed_map.items()
            if isinstance(value, list)
        }

    async def send_alert(self, payload: EmailAlertPayload) -> EmailNotifyResult:
        """Send throttled HTML email alert for a disruption event."""
        recipients = self._resolve_recipients(payload)
        if not recipients:
            return EmailNotifyResult(ok=False, error="No recipients configured")

        if not self.smtp_host or not self.smtp_from_email:
            return EmailNotifyResult(ok=False, recipients=recipients, error="SMTP_HOST or SMTP_FROM_EMAIL missing")

        throttle_key = f"throttle:email:{payload.project_id}:{payload.region_id}"
        redis = get_redis_client()
        try:
            throttled = await redis.get(throttle_key)
            if throttled:
                return EmailNotifyResult(ok=False, throttled=True, recipients=recipients)

            message = self._build_message(payload=payload, recipients=recipients)
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username or None,
                password=self.smtp_password or None,
                start_tls=self.smtp_use_tls,
            )

            await redis.set(throttle_key, "1", ex=self.throttle_seconds)
            return EmailNotifyResult(
                ok=True,
                throttled=False,
                recipients=recipients,
                sent_at=datetime.now(UTC),
            )
        except Exception as exc:  # noqa: BLE001
            return EmailNotifyResult(ok=False, recipients=recipients, error=str(exc))
        finally:
            await redis.aclose()

    def _resolve_recipients(self, payload: EmailAlertPayload) -> list[str]:
        if payload.recipients:
            return payload.recipients
        if payload.project_id in self.project_recipients_map:
            return self.project_recipients_map[payload.project_id]
        return self.default_recipients

    def _build_message(self, *, payload: EmailAlertPayload, recipients: list[str]) -> EmailMessage:
        severity_badge = {
            "MEDIUM": "🟡 MEDIUM",
            "HIGH": "🟠 HIGH",
            "CRITICAL": "🔴 CRITICAL",
        }[payload.severity]
        confidence_pct = round(payload.confidence * 100, 1)
        affected_regions = ", ".join(payload.affected_regions) if payload.affected_regions else "N/A"
        recommendations = "".join(f"<li>{item}</li>" for item in payload.route_recommendations) or "<li>N/A</li>"

        html = f"""
        <html>
          <body style=\"font-family: Arial, sans-serif; color: #222;\"> 
            <h2>{severity_badge} Disruption Alert</h2>
            <p><strong>Project:</strong> {payload.project_id}</p>
            <p><strong>Region:</strong> {payload.region_id}</p>
            <p><strong>Confidence:</strong> {confidence_pct}%</p>
            <p><strong>Affected Regions:</strong> {affected_regions}</p>
            <p><strong>Reason:</strong> {payload.reason}</p>
            <h3>Route Recommendations</h3>
            <ul>{recommendations}</ul>
            <h3>Propagation Forecast</h3>
            <p>{payload.propagation_forecast}</p>
          </body>
        </html>
        """.strip()

        message = EmailMessage()
        message["From"] = self.smtp_from_email
        message["To"] = ", ".join(recipients)
        message["Subject"] = f"[{payload.severity}] LogiSwarm disruption alert · {payload.region_id}"
        message.set_content("This alert requires an HTML-capable email client.")
        message.add_alternative(html, subtype="html")
        return message


email_notifier = EmailNotifier()
