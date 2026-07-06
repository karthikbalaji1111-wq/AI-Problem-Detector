from celery import Celery

from nexus_api.config import get_settings
from nexus_api.database import SessionLocal
from nexus_api.models import AgentRun
from nexus_api.services.agent_runtime import AgentRuntime

settings = get_settings()

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
)


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

