"""
Silero VAD 引擎 —— VADInterface 的具体实现
对照 Open-LLM-VTuber silero.py 的 VADEngine（2026-07-27 检索）

本课相对参考答案的改进：用 asyncio.to_thread 包装同步推理，不阻塞事件循环
"""
import asyncio
from typing import Generator

from .vad_interface import VADInterface
from .state_machine import StateMachine
from silero_vad import load_silero_vad, get_speech_timestamps
import numpy as np
import torch


class SileroVADEngine(VADInterface):
    """Silero VAD 流式引擎"""

    def __init__(
        self,
        prob_threshold: float = 0.5,
        db_threshold: float = -20.0,       # float32 音频用负数分贝（见坑7）
        required_hits: int = 3,
        required_misses: int = 24,
        smoothing_window: int = 5,
        pre_buffer_size: int = 20,
        window_size_samples: int = 512,   # silero-vad 每帧 512 采样点
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
        """
        流式检测语音段（同步生成器）。

        参数:
            audio_chunks: 可迭代对象，每项是 (audio_np, chunk_bytes)
                          audio_np: numpy 数组（一帧的音频，长度=window_size_samples）
                          chunk_bytes: 该帧的字节
        返回:
            生成器，每次 yield 一个完整语音段 (bytes)
        """
        # ═══════════════════════════════════════════════════════════
        # TODO 5: 流式检测主循环
        # ═══════════════════════════════════════════════════════════
        # 遍历 audio_chunks:
        #   1. 用模型算这一帧的语音概率:
        #      prob = self.model(audio_np, self.window_size_samples).item()
        #      （注意: model 返回的是 tensor，用 .item() 取标量）
        #   2. 把 (prob, audio_np, chunk_bytes) 喂给状态机:
        #      result = self.state_machine.process(prob, audio_np, chunk_bytes)
        #   3. 若 result 不是 None（状态机吐出完整语音段）:
        #      yield result
        # 提示: 5-6 行代码
        

    async def async_detect_speech(self, audio_chunks):
        """
        异步版检测（用 asyncio.to_thread 包装，不阻塞事件循环）。
        这是本课相对 Open-LLM-VTuber 参考答案的改进点。

        参数同 detect_speech，返回异步生成器。
        """
        # ═══════════════════════════════════════════════════════════
        # TODO 6: 异步包装同步生成器
        # ═══════════════════════════════════════════════════════════
        # 思路: 同步生成器 detect_speech 会阻塞（torch 推理），
        #       用 asyncio.to_thread 取下一个值，让事件循环有机会切换。
        # 步骤:
        #   1. sync_gen = self.detect_speech(audio_chunks)  # 拿到同步生成器
        #   2. while True:
        #        try:
        #            chunk = await asyncio.to_thread(next, sync_gen)  # 异步取下一个
        #        except StopIteration:
        #            break
        #        yield chunk
        # 提示: 注意 StopIteration 要捕获（生成器结束）
        pass