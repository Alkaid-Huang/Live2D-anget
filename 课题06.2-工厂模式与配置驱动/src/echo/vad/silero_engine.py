"""
Silero VAD 引擎 —— VADInterface 的具体实现
对照 Open-LLM-VTuber silero.py 的 VADEngine（2026-08-03 检索）

本课改动（相对 06.1）：加 @register_vad 装饰器，让工厂能创建它
"""
import asyncio
from typing import Generator

from .vad_interface import VADInterface
from .vad_factory import register_vad  # 06.2 新增：导入注册装饰器
from .state_machine import StateMachine
from silero_vad import load_silero_vad


@register_vad("silero_vad")  # 06.2 新增：注册到工厂
class SileroVADEngine(VADInterface):
    """Silero VAD 流式引擎"""

    def __init__(
        self,
        prob_threshold: float = 0.5,
        db_threshold: float = -20.0,
        required_hits: int = 3,
        required_misses: int = 24,
        smoothing_window: int = 5,
        pre_buffer_size: int = 20,
        window_size_samples: int = 512,
    ):
        # 加载 silero 模型（只加载一次）
        self.model = load_silero_vad()
        self.window_size_samples = window_size_samples

        # 创建状态机
        self.state_machine = StateMachine(
            prob_threshold=prob_threshold,
            db_threshold=db_threshold,
            required_hits=required_hits,
            required_misses=required_misses,
            smoothing_window=smoothing_window,
            pre_buffer_size=pre_buffer_size,
        )

    def detect_speech(self, audio_chunks) -> Generator[bytes, None, None]:
        """流式检测语音段（同步生成器）"""
        for audio_chunk in audio_chunks:
            prob = self.model(audio_chunk[0], self.window_size_samples).item()
            result = self.state_machine.process(
                prob=prob, audio_np=audio_chunk[0], chunk_bytes=audio_chunk[1]
            )
            if result is not None:
                yield result

    async def async_detect_speech(self, audio_chunks):
        """异步版检测（用 asyncio.to_thread 包装，不阻塞事件循环）"""
        sync_gen = self.detect_speech(audio_chunks)
        while True:
            try:
                chunk = await asyncio.to_thread(next, sync_gen)
            except StopIteration:
                break
            yield chunk
