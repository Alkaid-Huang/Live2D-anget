"""
VAD 抽象接口 —— 所有 VAD 后端的统一契约
对照 Open-LLM-VTuber 的 vad_interface.py（2026-08-03 检索）
"""
from abc import ABC, abstractmethod
from typing import Generator


class VADInterface(ABC):
    """VAD 抽象基类：定义所有 VAD 后端必须实现的契约"""

    @abstractmethod
    def detect_speech(self, audio_chunks) -> Generator[bytes, None, None]:
        """
        流式检测语音段。

        参数:
            audio_chunks: 可迭代的音频块，每块是 (audio_np, chunk_bytes)
                          audio_np: numpy 数组 (用于算分贝和概率)
                          chunk_bytes: 该块的原始字节 (用于输出)

        返回:
            生成器，每次 yield 一个完整的语音段 (bytes)
            没有完整语音段时不 yield（等状态机累积到输出条件）
        """
        pass
