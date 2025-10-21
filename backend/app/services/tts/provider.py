"""TTS プロバイダの抽象インターフェース。"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .types import TTSRequest, TTSResult


class TTSProviderError(RuntimeError):
    """TTS 呼び出しで発生したエラー。"""


class TTSProvider(ABC):
    """任意の TTS ベンダーを統一的に扱うための抽象クラス。"""

    @abstractmethod
    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """テキストを音声に変換する。"""

        raise NotImplementedError
