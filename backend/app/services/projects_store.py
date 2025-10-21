"""互換レイヤー。旧 projects_store API をラップする。"""
from __future__ import annotations

from uuid import UUID

from app.services.project_repository import (
    Project,
    create_project as _create_project,
    get_project as _get_project,
    list_projects as _list_projects,
    reset_repository as _reset_repository,
)
from app.services.script_generator import ProjectContext


def create_project(context: ProjectContext) -> Project:
    return _create_project(context)


def get_project(project_id: UUID) -> Project | None:
    return _get_project(project_id)


def list_projects() -> list[Project]:
    return _list_projects()


def reset_store(*, delete_file: bool = False) -> None:
    _reset_repository(delete_file=delete_file)
