import os
import certifi
import aiohttp

os.environ["SSL_CERT_FILE"] = certifi.where()

# Monkey-patch missing aiohttp attributes for compatibility with aiohttp 3.9.x
if not hasattr(aiohttp, "ClientConnectorDNSError"):
    aiohttp.ClientConnectorDNSError = aiohttp.ClientConnectorError
if not hasattr(aiohttp, "ClientProxyConnectionError"):
    aiohttp.ClientProxyConnectionError = aiohttp.ClientConnectorError

import asyncio
from datetime import date, datetime, time
from hindsight_client import Hindsight
from app.config import get_settings
from app.models import IncidentReport
from app.agent_core import report_incident

async def main():
    settings = get_settings()
    hindsight = Hindsight(
        base_url=settings.hindsight_base_url,
        api_key=settings.hindsight_api_key or None,
    )

    incidents = [
        IncidentReport(
            service="auth-service", severity="high",
            date=date(2024, 1, 5),
            root_cause="db migration failed on nullable column",
            resolution="rolled back migration, patched script",
            trigger="db-migration", downtime_minutes=45
        ),
        IncidentReport(
            service="auth-service", severity="high",
            date=date(2024, 1, 8),
            root_cause="connection pool exhausted after schema change",
            resolution="increased pool size, restarted service",
            trigger="db-migration", downtime_minutes=30
        ),
        IncidentReport(
            service="payment-service", severity="medium",
            date=date(2024, 1, 6),
            root_cause="memory leak in new billing module",
            resolution="hotfix deployed",
            trigger="code-deploy", downtime_minutes=15
        ),
        IncidentReport(
            service="auth-service", severity="low",
            date=date(2023, 12, 28),
            root_cause="cache invalidation bug after config change",
            resolution="cache cleared manually",
            trigger="config-change", downtime_minutes=5
        ),
        IncidentReport(
            service="api-gateway", severity="high",
            date=date(2024, 1, 10),
            root_cause="rate limiter misconfigured after Friday 5pm deploy",
            resolution="reverted config",
            trigger="code-deploy", downtime_minutes=60
        ),
        IncidentReport(
            service="api-gateway", severity="high",
            date=date(2024, 1, 3),
            root_cause="Friday deploy caused cascade failure in downstream",
            resolution="full rollback",
            trigger="code-deploy", downtime_minutes=90
        ),
    ]

    # All retains run concurrently
    await asyncio.gather(*[
        report_incident(i, hindsight, settings) for i in incidents
    ])

    hindsight.close()
    print(f"Seeded {len(incidents)} memories successfully")

if __name__ == "__main__":
    asyncio.run(main())
