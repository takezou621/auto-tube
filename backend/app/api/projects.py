"""動画プロジェクト関連API。"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.project_repository import Project, create_project, get_project, list_projects
from app.services.storyboard_generator import StoryboardItem, generate_storyboard
from app.services.tts.provider import TTSProviderError
from app.services.tts.usecase import TTSUnavailableError, synthesize_project_audio
from app.services.script_generator import Audience, Duration, ProjectContext, Tone

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ScriptRequest(BaseModel):
    """プロジェクト生成のリクエスト。"""

    title: str = Field(min_length=2, max_length=80, description="動画で紹介する物件名")
    location: str = Field(min_length=2, max_length=80)
    highlight: str = Field(min_length=10, max_length=200, description="投資家に伝えたい魅力の要約")
    audience: Audience = Field(description="想定視聴者")
    duration: Duration = Field(description="動画尺カテゴリ")
    call_to_action: str = Field(min_length=5, max_length=120, description="クロージングで伝えるCTA")
    tone: Tone = Field(description="ナレーションの雰囲気")


class ScriptSectionResponse(BaseModel):
    title: str
    body: str


class SceneOutlineResponse(BaseModel):
    cue: str
    description: str


class ProjectResponse(BaseModel):
    id: UUID
    title: str
    location: str
    highlight: str
    audience: Audience
    duration: Duration
    tone: Tone
    call_to_action: str
    summary: str
    sections: list[ScriptSectionResponse]
    scenes: list[SceneOutlineResponse]
    created_at: datetime

    @classmethod
    def from_project(cls, project: Project) -> "ProjectResponse":
        return cls(
            id=project.id,
            title=project.context.title,
            location=project.context.location,
            highlight=project.context.highlight,
            audience=project.context.audience,
            duration=project.context.duration,
            tone=project.context.tone,
            call_to_action=project.context.call_to_action,
            summary=project.script.summary,
            sections=[
                ScriptSectionResponse(title=section.title, body=section.body)
                for section in project.script.sections
            ],
            scenes=[
                SceneOutlineResponse(cue=scene.cue, description=scene.description)
                for scene in project.script.scenes
            ],
            created_at=project.created_at,
        )


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project_endpoint(request: ScriptRequest) -> ProjectResponse:
    """動画プロジェクトを生成する。"""

    context = ProjectContext(
        title=request.title,
        location=request.location,
        highlight=request.highlight,
        audience=request.audience,
        duration=request.duration,
        call_to_action=request.call_to_action,
        tone=request.tone,
    )
    project = create_project(context)
    return ProjectResponse.from_project(project)


@router.get("/", response_model=list[ProjectResponse])
async def list_projects_endpoint() -> list[ProjectResponse]:
    """生成済みプロジェクトの一覧を返す。"""

    return [ProjectResponse.from_project(project) for project in list_projects()]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_endpoint(project_id: UUID) -> ProjectResponse:
    """生成済みプロジェクトを取得する。"""

    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectResponse.from_project(project)


@router.post("/{project_id}/tts", response_class=StreamingResponse, status_code=status.HTTP_200_OK)
async def synthesize_project_tts(project_id: UUID) -> StreamingResponse:
    """生成済みプロジェクトの台本を音声化する。"""

    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    try:
        result = await synthesize_project_audio(project)
    except TTSUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except TTSProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    headers = {}
    if result.request_id:
        headers["x-request-id"] = result.request_id
    headers["Content-Disposition"] = f"attachment; filename={project.id}.mp3"
    media_type = result.content_type or "audio/mpeg"

    return StreamingResponse(iter([result.audio]), media_type=media_type, headers=headers)


class StoryboardItemResponse(BaseModel):
    scene: str
    shot_type: str
    broll_idea: str
    key_message: str
    overlay_text: str


class StoryboardResponse(BaseModel):
    items: list[StoryboardItemResponse]

    @classmethod
    def from_items(cls, items: list[StoryboardItem]) -> "StoryboardResponse":
        return cls(
            items=[
                StoryboardItemResponse(
                    scene=item.scene,
                    shot_type=item.shot_type,
                    broll_idea=item.broll_idea,
                    key_message=item.key_message,
                    overlay_text=item.overlay_text,
                )
                for item in items
            ]
        )


@router.get("/{project_id}/storyboard", response_model=StoryboardResponse)
async def get_storyboard(project_id: UUID) -> StoryboardResponse:
    """プロジェクトのストーリーボードを生成する。"""

    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    storyboard = generate_storyboard(project)
    return StoryboardResponse.from_items(storyboard.items)
