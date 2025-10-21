"""TTSユースケース: プロジェクト台本を音声化する。"""
from __future__ import annotations

from app.core.settings import get_settings
from app.services.projects_store import Project
from app.services.tts.factory import get_tts_provider
from app.services.tts.types import TTSRequest, TTSResult


class TTSUnavailableError(RuntimeError):
    """TTSプロバイダが利用できない状態。"""


async def synthesize_project_audio(project: Project) -> TTSResult:
    """プロジェクトの台本全体を音声化する。"""

    script_text = _render_script(project)
    settings = get_settings()

    if settings.enable_tts_mock:
        return TTSResult(audio=_build_mock_audio(script_text), content_type="audio/mpeg", request_id=None)

    try:
        provider = get_tts_provider()
    except RuntimeError as exc:
        raise TTSUnavailableError("TTSプロバイダが未設定です") from exc

    return await provider.synthesize(TTSRequest(text=script_text))


def _render_script(project: Project) -> str:
    """セクションとCTAをまとめて1つの台本に整形する。"""

    lines: list[str] = [project.script.summary]
    for section in project.script.sections:
        lines.append(f"【{section.title}】")
        lines.append(section.body)
    return '\n'.join(lines)


def _build_mock_audio(text: str) -> bytes:
    """モック用にテキストをバイト列へ変換する。"""

    placeholder = f"MOCK_AUDIO::{len(text)}"
    return placeholder.encode("utf-8")
