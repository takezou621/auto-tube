import sys
from pathlib import Path

# プロジェクトの app モジュールを import 対象に含める
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from app.core.settings import get_settings
from app.services.project_repository import get_project_repository, reset_repository


@pytest.fixture(autouse=True)
def _isolate_projects_store(tmp_path, monkeypatch):
    db_path = tmp_path / "projects.json"
    monkeypatch.setenv("PROJECTS_STORE_PATH", str(db_path))
    get_settings.cache_clear()

    from app.services import projects_store

    get_project_repository.cache_clear()
    reset_repository(delete_file=True)
    yield
    reset_repository(delete_file=True)
    get_settings.cache_clear()
