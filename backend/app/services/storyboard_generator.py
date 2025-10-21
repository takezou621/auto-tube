"""ストーリーボード生成ロジック。"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.project_repository import Project
from app.services.script_generator import ProjectContext, SceneOutline


@dataclass(slots=True)
class StoryboardItem:
    scene: str
    shot_type: str
    broll_idea: str
    key_message: str
    overlay_text: str


@dataclass(slots=True)
class StoryboardResult:
    items: list[StoryboardItem]


def generate_storyboard(project: Project) -> StoryboardResult:
    """プロジェクトのシーン情報からストーリーボードを生成する。"""

    context = project.context
    total_scenes = len(project.script.scenes)
    items: list[StoryboardItem] = []

    for index, scene in enumerate(project.script.scenes):
        items.append(
            StoryboardItem(
                scene=f"{scene.cue} ({index + 1}/{total_scenes})",
                shot_type=_select_shot_type(scene),
                broll_idea=_suggest_broll(scene, context),
                key_message=_key_message(scene, context),
                overlay_text=_overlay_text(scene, context, index, total_scenes),
            )
        )

    return StoryboardResult(items=items)


def _select_shot_type(scene: SceneOutline) -> str:
    cue = scene.cue
    if cue in {"導入", "オープニング", "イントロ"}:
        return "タイトルアニメーション or シティライトのドローンショット"
    if cue in {"資産価値", "収益戦略"}:
        return "グラフアニメーション + 物件外観のトラックショット"
    if cue in {"生活利便性", "エリア評価"}:
        return "街歩きB-roll + 公園/商業施設のカット"
    if cue == "クロージング":
        return "MCが登場するミディアムショット"
    return "物件外観/内観の汎用B-roll"


def _suggest_broll(scene: SceneOutline, context: ProjectContext) -> str:
    cue = scene.cue
    highlight = context.highlight
    if cue in {"導入", "オープニング", "イントロ"}:
        return f"物件名テキストと {context.location} の夜景または空撮映像"
    if cue in {"資産価値", "収益戦略"}:
        return f"{highlight} を示すグラフやキャッシュフロー表をアニメーションで表示"
    if cue in {"生活利便性", "エリア評価"}:
        return f"{context.location} の周辺施設（駅・ショッピングモール・公園など）のB-roll"
    if cue == "クロージング":
        return "エージェントの挨拶カット + コールトゥアクションのテロップ"
    return "物件室内ツアーやラウンジ、共有設備のB-roll"


def _key_message(scene: SceneOutline, context: ProjectContext) -> str:
    cue = scene.cue
    if cue in {"導入", "オープニング", "イントロ"}:
        return f"{context.title} の魅力を視聴者に端的に伝える"
    if cue in {"資産価値", "収益戦略"}:
        return "投資判断の材料となる数値・収益戦略を明確化"
    if cue in {"生活利便性", "エリア評価"}:
        return "生活利便性・再開発情報で将来価値を訴求"
    if cue == "クロージング":
        return context.call_to_action
    return context.highlight


def _overlay_text(scene: SceneOutline, context: ProjectContext, index: int, total: int) -> str:
    cue = scene.cue
    if cue in {"導入", "オープニング", "イントロ"}:
        return f"{context.title} | {context.location}"
    if cue in {"資産価値", "収益戦略"}:
        return "利回り・キャッシュフロー / シミュレーション結果"
    if cue in {"生活利便性", "エリア評価"}:
        return "周辺施設ダイジェスト"
    if cue == "クロージング":
        return context.call_to_action
    return f"Scene {index + 1} / {total}: {scene.description}"
