from uuid import uuid4
from fastapi import APIRouter, HTTPException
from app.agents.concept_agents import AGENTS
from app.models.schemas import ProjectCreate, Project, RunCreate, DesignRun
from app.services import storage
from app.services.orchestrator import run_project
from app.agents.llm_client import LLMConfigurationError, LLMProviderError

router = APIRouter()

@router.get("/agents")
def list_agents():
    return [agent.info.model_dump() for agent in AGENTS.values()]

@router.post("/projects", response_model=Project, status_code=201)
def create_project(payload: ProjectCreate):
    project = Project(id=str(uuid4()), **payload.model_dump())
    storage.save_project(project)
    return project

@router.get("/projects/{project_id}", response_model=Project)
def read_project(project_id: str):
    payload = storage.get_project(project_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Project not found")
    return Project.model_validate(payload)

@router.post("/projects/{project_id}/runs", response_model=DesignRun, status_code=201)
def start_run(project_id: str, payload: RunCreate):
    stored = storage.get_project(project_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Project not found")
    project = Project.model_validate(stored)
    try:
        run = run_project(project, payload.agents)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    storage.save_run(run)
    return run

@router.get("/runs/{run_id}", response_model=DesignRun)
def read_run(run_id: str):
    payload = storage.get_run(run_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Run not found")
    return DesignRun.model_validate(payload)
