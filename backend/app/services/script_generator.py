"""動画スクリプト生成ロジック。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


Duration = Literal["short", "standard", "long"]
Tone = Literal["trust", "energetic", "premium"]
Audience = Literal["entry", "experienced", "investor"]


@dataclass(slots=True)
class ScriptSection:
    """スクリプトの1セクション。"""

    title: str
    body: str


@dataclass(slots=True)
class SceneOutline:
    """映像カットの簡易アウトライン。"""

    cue: str
    description: str


@dataclass(slots=True)
class ScriptResult:
    """生成結果。"""

    summary: str
    sections: list[ScriptSection]
    scenes: list[SceneOutline]


@dataclass(slots=True)
class ProjectContext:
    """入力値をまとめたコンテキスト。"""

    title: str
    location: str
    highlight: str
    audience: Audience
    duration: Duration
    call_to_action: str
    tone: Tone


_AUDIENCE_LABEL = {
    "entry": "不動産投資初心者",
    "experienced": "経験者",
    "investor": "富裕層投資家",
}

_TONE_PHRASES = {
    "trust": "落ち着いた信頼感のあるトーンで",
    "energetic": "明るくスピード感のある語り口で",
    "premium": "上質さと安心感を強調しながら",
}

_DURATION_SCENES: dict[Duration, list[tuple[str, str]]] = {
    "short": [
        ("オープニング", "冒頭のインパクト+物件名紹介"),
        ("魅力ポイント", "ロケーションと収益性を1ショットで訴求"),
        ("クロージング", "今すぐ問い合わせを促すCTA"),
    ],
    "standard": [
        ("イントロ", "ターゲットに問いかけ＋物件の立地"),
        ("資産価値", "利回りやキャッシュフロー"),
        ("生活利便性", "周辺環境と将来性"),
        ("クロージング", "信頼感ある締めとCTA"),
    ],
    "long": [
        ("導入", "トレンドや市場背景"),
        ("物件概要", "基本スペックと価格帯"),
        ("収益戦略", "利回りシミュレーション"),
        ("エリア評価", "交通・生活・再開発情報"),
        ("クロージング", "CTAと今後のサポート体制"),
    ],
}


def generate_script(context: ProjectContext) -> ScriptResult:
    """テンプレートベースで動画スクリプトを生成する。"""

    scenes: list[SceneOutline] = [
        SceneOutline(cue=name, description=description)
        for name, description in _DURATION_SCENES[context.duration]
    ]

    tone_phrase = _TONE_PHRASES[context.tone]
    audience_label = _AUDIENCE_LABEL[context.audience]
    today = datetime.now().strftime("%m/%d")

    sections: list[ScriptSection] = []
    for index, scene in enumerate(scenes):
        if index == 0:
            body = (
                f"{tone_phrase}{audience_label}の皆さんに向けて、{context.title} をご紹介します。"
                f"舞台は {context.location}。{context.highlight} が際立ちます。"
            )
        elif index == len(scenes) - 1:
            body = (
                f"{context.call_to_action}。{today} 時点の市場動向から見ても、"
                f"いま検討する価値があります。概要欄リンクから資料請求ください。"
            )
        else:
            body = _build_body(scene.cue, scene.description, context)

        body = f"{body}（シーン意図: {scene.description}）"
        sections.append(ScriptSection(title=scene.cue, body=body))

    summary = (
        f"{context.title}（{context.location}）の投資概要を{tone_phrase}"
        f"{len(sections)}パートで語る台本です。"
    )

    return ScriptResult(summary=summary, sections=sections, scenes=scenes)


def _build_body(section_name: str, description: str, context: ProjectContext) -> str:
    """セクションごとの本文を生成する。"""

    if section_name in {"魅力ポイント", "資産価値", "物件概要"}:
        body = f"{context.highlight} を軸に、数字で裏付ける魅力を解説します。"
    elif section_name in {"生活利便性", "エリア評価"}:
        body = f"{context.location} の利便性や将来の再開発計画を掘り下げ、暮らしやすさを伝えます。"
    elif section_name == "収益戦略":
        body = (
            f"家賃想定と運用シミュレーションから、{context.title} のキャッシュフローを具体的に提示します。"
        )
    else:
        body = f"{context.title} の価値を視覚的に伝えるカット構成を案内します。"

    return body
