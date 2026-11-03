from datetime import datetime, timezone
from uuid import uuid4
from collections import deque
from threading import Lock
from app.agents.concept_agents import AGENTS, DISCLAIMER
from app.models.schemas import Project, DesignRun

_events=deque(maxlen=100)
_status={agent_id:"idle" for agent_id in AGENTS}
_lock=Lock()
def record(agent_id: str, status: str, message: str):
    with _lock:
        _status[agent_id]=status
        _events.appendleft({"time":datetime.now(timezone.utc).isoformat(),"agent_id":agent_id,"status":status,"message":message[:250]})
def workflow_snapshot():
    with _lock:
        return {"agents":[{"id":aid,"name":agent.info.name,"discipline":agent.info.discipline,"status":_status.get(aid,"idle")} for aid,agent in AGENTS.items()],"events":list(_events)}

def run_project(project: Project, requested: list[str] | None = None) -> DesignRun:
    selected = requested or list(AGENTS.keys())
    unknown = sorted(set(selected) - set(AGENTS))
    if unknown:
        raise ValueError("Unknown agent ids: " + ", ".join(unknown))
    results=[]
    record("orchestrator","running",f"شروع تحلیل پروژه: {project.name}")
    try:
        for agent_id in selected:
            agent=AGENTS[agent_id]
            record(agent_id,"running",f"داده به {agent.info.name} ارسال شد")
            try:
                result=agent.run(project); results.append(result)
                record(agent_id,"done",f"{agent.info.name}: خروجی مفهومی آماده شد")
            except Exception:
                record(agent_id,"error",f"{agent.info.name}: اجرای ماژول ناموفق بود")
                raise
        record("orchestrator","done","هماهنگی خروجی‌های ایجنت‌ها انجام شد")
    except Exception:
        record("orchestrator","error","اجرای گردش‌کار با خطا متوقف شد")
        raise
    return DesignRun(id=str(uuid4()),project_id=project.id,status="completed",created_at=datetime.now(timezone.utc),agents=results,coordination_notes=["خروجی‌های رشته‌ها باید توسط معمار هماهنگ‌کننده تلفیق شوند.","تعارض‌ها، ابعاد و الزامات قانونی در این نسخه به‌صورت خودکار اعتبارسنجی نمی‌شوند."],disclaimer=DISCLAIMER)
