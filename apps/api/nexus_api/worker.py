from celery import Celery
from celery.result import AsyncResult
from structlog import get_logger

from nexus_api.config import get_settings
from nexus_api.database import SessionLocal
from nexus_api.models import AgentRun
from nexus_api.services.agent_runtime import AgentRuntime

settings = get_settings()
logger = get_logger(__name__)

celery_app = Celery(
    "nexus",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    broker_connection_timeout=settings.queue_publish_timeout_seconds,
    broker_transport_options={
        "socket_connect_timeout": settings.queue_publish_timeout_seconds,
        "socket_timeout": settings.queue_publish_timeout_seconds,
    },
)


def enqueue_agent_workflow(run_id: str) -> AsyncResult | None:
    try:
        return run_agent_workflow.apply_async(args=[run_id], retry=False)
    except Exception as exc:  # pragma: no cover - broker failures vary by transport.
        logger.warning("agent_workflow.enqueue_failed", run_id=run_id, error=str(exc))
        return None


@celery_app.task(name="nexus.run_agent_workflow")
def run_agent_workflow(run_id: str) -> dict:
    with SessionLocal() as db:
        run = db.get(AgentRun, run_id)
        if run is None:
            return {"ok": False, "error": "run_not_found"}
        completed = AgentRuntime(db).run(run=run)
        return {
            "ok": True,
            "run_id": completed.id,
            "status": completed.status,
            "confidence": completed.confidence,
            "risk_score": completed.risk_score,
        }
