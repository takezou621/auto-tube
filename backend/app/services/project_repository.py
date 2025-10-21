"""プロジェクト永続化リポジトリ。"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Protocol
from uuid import UUID, uuid4

from app.core.settings import get_settings
from app.services.script_generator import ProjectContext, ScriptResult, SceneOutline, ScriptSection, generate_script


@dataclass(slots=True)
class Project:
    """生成済み動画プロジェクト。"""

    id: UUID
    created_at: datetime
    context: ProjectContext
    script: ScriptResult


class ProjectRepository(Protocol):
    """プロジェクト永続化のための抽象インターフェース。"""

    def create(self, context: ProjectContext) -> Project: ...

    def get(self, project_id: UUID) -> Project | None: ...

    def list(self) -> list[Project]: ...

    def reset(self, *, delete_persisted: bool = False) -> None: ...


class JsonProjectRepository(ProjectRepository):
    """JSONファイルで永続化するシンプルな実装。"""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._projects: dict[UUID, Project] = {}
        self._lock = Lock()

    def create(self, context: ProjectContext) -> Project:
        project_id = uuid4()
        project = Project(
            id=project_id,
            created_at=datetime.now(tz=timezone.utc),
            context=context,
            script=generate_script(context),
        )

        with self._lock:
            self._ensure_loaded()
            self._projects[project_id] = project
            self._persist()
        return project

    def get(self, project_id: UUID) -> Project | None:
        with self._lock:
            self._ensure_loaded()
            return self._projects.get(project_id)

    def list(self) -> list[Project]:
        with self._lock:
            self._ensure_loaded()
            return sorted(self._projects.values(), key=lambda project: project.created_at, reverse=True)

    def reset(self, *, delete_persisted: bool = False) -> None:
        with self._lock:
            self._projects.clear()
            if delete_persisted and self._path.exists():
                self._path.unlink()

    def _ensure_loaded(self) -> None:
        if self._projects:
            return
        if not self._path.exists():
            return
        try:
            records = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        for record in records:
            project = _record_to_project(record)
            self._projects[project.id] = project

    def _persist(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        records = [_project_to_record(project) for project in self._projects.values()]
        self._path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def _project_to_record(project: Project) -> dict[str, object]:
    return {
        "id": str(project.id),
        "created_at": project.created_at.isoformat(),
        "context": {
            "title": project.context.title,
            "location": project.context.location,
            "highlight": project.context.highlight,
            "audience": project.context.audience,
            "duration": project.context.duration,
            "call_to_action": project.context.call_to_action,
            "tone": project.context.tone,
        },
        "script": {
            "summary": project.script.summary,
            "sections": [asdict(section) for section in project.script.sections],
            "scenes": [asdict(scene) for scene in project.script.scenes],
        },
    }


def _record_to_project(record: dict[str, object]) -> Project:
    context_data = record["context"]
    script_data = record["script"]

    context = ProjectContext(**context_data)
    sections = [ScriptSection(**section) for section in script_data.get("sections", [])]
    scenes = [SceneOutline(**scene) for scene in script_data.get("scenes", [])]
    script = ScriptResult(summary=script_data["summary"], sections=sections, scenes=scenes)

    created_at = datetime.fromisoformat(record["created_at"])
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    return Project(id=UUID(record["id"]), created_at=created_at, context=context, script=script)


@lru_cache
def get_project_repository() -> ProjectRepository:
    settings = get_settings()
    return JsonProjectRepository(Path(settings.projects_store_path))


def create_project(context: ProjectContext) -> Project:
    return get_project_repository().create(context)


def get_project(project_id: UUID) -> Project | None:
    return get_project_repository().get(project_id)


def list_projects() -> list[Project]:
    return get_project_repository().list()


def reset_repository(*, delete_file: bool = False) -> None:
    get_project_repository().reset(delete_persisted=delete_file)
