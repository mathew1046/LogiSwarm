# LogiSwarm - Geo-Aware Swarm Intelligence for Supply Chains
# Copyright (C) 2025 LogiSwarm Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from loguru import logger


def load_env() -> None:
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)
        logger.bind(event="env_loaded", env_file=str(env_file)).debug(
            f"Loaded environment from {env_file} (override=False)"
        )
    else:
        logger.bind(event="env_missing").warning(
            f"No .env file found at {env_file}, using system environment variables"
        )


load_env()


REQUIRED_ENV_VARS: dict[str, str] = {
    "DATABASE_URL": "PostgreSQL connection string (postgresql+asyncpg://user:pass@host:port/db)",
}

OPTIONAL_ENV_VARS: dict[str, tuple[Any, str]] = {
    "LLM_API_KEY": ("", "Anthropic/OpenRouter API key for LLM calls"),
    "LLM_BASE_URL": ("https://api.anthropic.com", "LLM API base URL"),
    "LLM_MODEL_NAME": ("claude-sonnet-4-6", "LLM model name"),
    "LLM_MAX_CONCURRENT": ("5", "Maximum concurrent LLM calls"),
    "LLM_MIN_CYCLE_INTERVAL": ("60", "Minimum seconds between agent reasoning cycles"),
    "LLM_DAILY_BUDGET_USD": ("10.0", "Daily budget threshold for LLM calls (USD)"),
    "LLM_FALLBACK_MODEL": (
        "claude-3-haiku-20240307",
        "Fallback model when budget exceeded",
    ),
    "ZEP_API_KEY": ("", "Zep Cloud API key for episodic memory"),
    "REDIS_URL": ("redis://localhost:6379", "Redis connection URL"),
    "TIMESCALE_URL": (
        "postgresql://logiswarm:logiswarm@localhost:5432/logiswarm",
        "TimescaleDB connection URL",
    ),
    "PORT_MOCK_ENABLED": ("true", "Enable port sensor mock mode"),
    "TMS_WEBHOOK_URL": ("", "TMS webhook URL for auto-reroute"),
    "TMS_WEBHOOK_SECRET": ("", "HMAC secret for TMS webhook"),
    "TMS_WEBHOOK_TIMEOUT_SECONDS": ("8", "TMS webhook timeout in seconds"),
    "TMS_WEBHOOK_MAX_RETRIES": ("3", "Maximum retries for TMS webhook"),
    "TMS_WEBHOOK_DLQ_KEY": (
        "dead_letter:tms:webhook",
        "Redis key for dead letter queue",
    ),
    "SLACK_WEBHOOK_URL": ("", "Slack webhook URL for notifications"),
    "SLACK_WEBHOOK_TIMEOUT_SECONDS": ("8", "Slack webhook timeout in seconds"),
    "SMTP_HOST": ("", "SMTP server hostname"),
    "SMTP_PORT": ("587", "SMTP server port"),
    "SMTP_USERNAME": ("", "SMTP authentication username"),
    "SMTP_PASSWORD": ("", "SMTP authentication password"),
    "SMTP_FROM_EMAIL": ("", "Email sender address"),
    "SMTP_USE_TLS": ("true", "Use TLS for SMTP"),
    "EMAIL_ALERT_THROTTLE_SECONDS": (
        "1800",
        "Email alert throttle duration in seconds",
    ),
    "EMAIL_DEFAULT_RECIPIENTS": ("", "Comma-separated default email recipients"),
    "EMAIL_RECIPIENTS_BY_PROJECT_JSON": (
        "{}",
        "JSON mapping of project IDs to recipient lists",
    ),
    "CARRIER_AVAILABILITY_API_URL": ("", "Carrier availability API URL"),
    "CARRIER_BOOKING_API_URL": ("", "Carrier booking API URL"),
    "CARRIER_API_TIMEOUT_SECONDS": ("8", "Carrier API timeout in seconds"),
    "CARRIER_DEFAULT_CANDIDATES": (
        "maersk,cma-cgm,msc,hapag-lloyd",
        "Default carrier candidates",
    ),
    "ENVIRONMENT": ("dev", "Environment (dev, staging, production)"),
    "CORS_ALLOW_ORIGINS": ("", "Comma-separated CORS allowed origins"),
    "LOG_LEVEL": ("INFO", "Logging level (DEBUG, INFO, WARNING, ERROR)"),
}


def validate_env() -> None:
    missing_vars = []

    for var_name, description in REQUIRED_ENV_VARS.items():
        value = os.getenv(var_name)
        if not value:
            missing_vars.append((var_name, description))

    if missing_vars:
        print("\n" + "=" * 80, file=sys.stderr)
        print("ERROR: Missing required environment variables", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        print(
            "\nThe following environment variables are required but not set:\n",
            file=sys.stderr,
        )
        for var_name, description in missing_vars:
            print(f"  {var_name:<30} {description}", file=sys.stderr)
        print(
            "\nPlease set these variables in your .env file or environment.",
            file=sys.stderr,
        )
        print("Example .env file:\n", file=sys.stderr)
        print(
            "  DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db\n",
            file=sys.stderr,
        )
        print("=" * 80 + "\n", file=sys.stderr)
        sys.exit(1)

    logger.bind(event="env_validated").info(
        "Environment variables validated successfully"
    )


def get_namespace() -> dict[str, str]:
    config: dict[str, str] = {}

    for var_name, (default_value, _) in OPTIONAL_ENV_VARS.items():
        config[var_name] = os.getenv(var_name, str(default_value))

    for var_name in REQUIRED_ENV_VARS.keys():
        value = os.getenv(var_name)
        if value:
            config[var_name] = value

    return config
