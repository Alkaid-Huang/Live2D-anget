"""echo.tts 包 —— 文字转语音（TTS）后端"""
# ⚠️ AI 代写（2026-09-10）：本包由助手生成，尚未经学习者理解验收
from .tts_interface import TTSInterface
from .tts_factory import create_tts, register_tts, _TTS_REGISTRY

from .mock_tts import MockTTS

try:
    from .edge_tts_engine import EdgeTTSEngine
except ImportError:
    pass

__all__ = [
    "TTSInterface",
    "create_tts",
    "register_tts",
    "MockTTS",
]
