"""
Slack notification service for health checks and alerts.
"""
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Sends notifications to Slack via webhook URL."""

    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize Slack notifier with webhook URL."""
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")

        if not self.webhook_url:
            logger.warning(
                "No Slack webhook URL provided. Notifications will be logged only."
            )
        else:
            logger.info("Slack notifier initialized with webhook URL")

    async def send_notification(
        self,
        message: str,
        title: str = "Aslan Drive Notification",
        color: str = "good",
        fields: Optional[list] = None,
    ) -> bool:
        """Send a notification to Slack."""
        if not self.webhook_url or not HTTPX_AVAILABLE:
            logger.info(f"[SLACK NOTIFICATION] {title}: {message}")
            if fields:
                for field in fields:
                    logger.info(f"  {field.get('title', '')}: {field.get('value', '')}")
            return True

        # Prepare Slack payload
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": message,
                    "ts": int(datetime.now().timestamp()),
                }
            ]
        }

        if fields:
            payload["attachments"][0]["fields"] = fields

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url, json=payload, timeout=10.0
                )

                if response.status_code == 200:
                    logger.info("Slack notification sent successfully")
                    return True
                else:
                    logger.error(
                        f"Slack notification failed: HTTP {response.status_code}"
                    )
                    logger.error(f"Response: {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    async def send_health_check_success(
        self,
        check_date: str,
        records_found: int,
        symbols: list,
        database_stats: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send a health check success notification."""
        message = f"✅ Health check passed for {check_date}"

        fields = [
            {"title": "Date Checked", "value": check_date, "short": True},
            {"title": "Records Found", "value": str(records_found), "short": True},
            {
                "title": "Symbols",
                "value": ", ".join(symbols[:10]) + ("..." if len(symbols) > 10 else ""),
                "short": False,
            },
        ]

        if database_stats:
            fields.extend(
                [
                    {
                        "title": "Total Records",
                        "value": str(database_stats.get("total_records", "N/A")),
                        "short": True,
                    },
                    {
                        "title": "Total Symbols",
                        "value": str(database_stats.get("total_symbols", "N/A")),
                        "short": True,
                    },
                ]
            )

        return await self.send_notification(
            message=message,
            title="🏦 Aslan Drive Health Check",
            color="good",
            fields=fields,
        )

    async def send_health_check_failure(
        self, check_date: str, error_message: str, database_connected: bool = False
    ) -> bool:
        """Send a health check failure notification."""
        message = f"❌ Health check failed for {check_date}"

        fields = [
            {"title": "Date Checked", "value": check_date, "short": True},
            {
                "title": "Database Connected",
                "value": "✅ Yes" if database_connected else "❌ No",
                "short": True,
            },
            {"title": "Error", "value": error_message, "short": False},
        ]

        return await self.send_notification(
            message=message,
            title="🚨 Aslan Drive Health Check FAILED",
            color="danger",
            fields=fields,
        )

    async def send_data_ingestion_complete(
        self, records_processed: int, processing_time: float, date_range: str
    ) -> bool:
        """Send a data ingestion completion notification."""
        message = f"✅ Data ingestion completed successfully"

        fields = [
            {
                "title": "Records Processed",
                "value": str(records_processed),
                "short": True,
            },
            {
                "title": "Processing Time",
                "value": f"{processing_time:.2f} seconds",
                "short": True,
            },
            {"title": "Date Range", "value": date_range, "short": False},
        ]

        return await self.send_notification(
            message=message,
            title="📊 Aslan Drive Data Ingestion",
            color="good",
            fields=fields,
        )

    async def send_system_startup(
        self, service_name: str, version: str = "0.1.0"
    ) -> bool:
        """Send a system startup notification."""
        message = f"🚀 {service_name} has started successfully"

        fields = [
            {"title": "Service", "value": service_name, "short": True},
            {"title": "Version", "value": version, "short": True},
            {
                "title": "Timestamp",
                "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "short": False,
            },
        ]

        return await self.send_notification(
            message=message,
            title="⚡ Aslan Drive System Startup",
            color="good",
            fields=fields,
        )

    def send_notification_sync(
        self, message: str, title: str = "Aslan Drive Notification", color: str = "good"
    ) -> bool:
        """Synchronous version for simple use cases."""
        import asyncio

        try:
            return asyncio.run(self.send_notification(message, title, color))
        except Exception as e:
            logger.error(f"Failed to send sync notification: {e}")
            return False
