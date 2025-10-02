"""動画レンダリングAPIモック。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/render", tags=["render"])


@router.post("/{project_id}", status_code=status.HTTP_202_ACCEPTED)
async def request_render(project_id: str) -> dict[str, str]:
    if len(project_id) != 36:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid project id")
    return {"job_id": f"mock-job-{project_id}"}


@router.get("/jobs/{job_id}")
async def get_render_job(job_id: str) -> dict[str, str]:
    return {"job_id": job_id, "status": "queued"}
