"""echo.audio 包 —— 麦克风采集与扬声器播放"""
# ⚠️ AI 代写（2026-09-10）：尚未经学习者理解验收
from .io import MicStream, load_audio_mono, play_audio, play_file, resample_linear

__all__ = [
    "MicStream",
    "load_audio_mono",
    "play_audio",
    "play_file",
    "resample_linear",
]
