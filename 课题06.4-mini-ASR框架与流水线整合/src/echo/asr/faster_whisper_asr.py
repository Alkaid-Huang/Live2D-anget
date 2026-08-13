"""
FasterWhisperASR —— faster-whisper 后端（CTranslate2 加速）
对照 Open-LLM-VTuber src/open_llm_vtuber/asr/faster_whisper_asr.py（2026-08-13 检索）

对齐真实源码的 3 个细节：
1. 参数名：model_path / download_root / language / device / compute_type / prompt
2. prompt 会作为 initial_prompt 传入——给识别提供上下文（语言应与音频一致）
3. numpy 输入必须是 16k float32（接口契约），transcribe 不传采样率

依赖: pip install faster-whisper
"""
from typing import Optional

import numpy as np

from .asr_interface import ASRInterface
from .asr_factory import register_asr


@register_asr("faster_whisper")
class FasterWhisperASR(ASRInterface):
    """faster-whisper 转写器"""

    def __init__(
        self,
        model_path: str = "small",
        download_root: str = "models/whisper",
        language: Optional[str] = "zh",
        device: str = "auto",  # "cpu" | "cuda" | "auto"
        compute_type: str = "int8",
        prompt: Optional[str] = None,
    ):
        from faster_whisper import WhisperModel

        self.model = WhisperModel(
            model_size_or_path=model_path,
            download_root=download_root,
            device=device,
            compute_type=compute_type,
        )
        self.language = language
        self.prompt = prompt

    def transcribe_np(self, audio_np: np.ndarray) -> str:
        # ═══════════════════════════════════════════════════════════
        # TODO 7: 调用 faster-whisper 转写 numpy 音频
        # ═══════════════════════════════════════════════════════════
        # ⚠️ 演化知识：参数名请以官方 README / 真实源码为准（检索后填写）。
        # 对照真实源码 faster_whisper_asr.py（2026-08-13 检索）:
        #   1. segments, info = self.model.transcribe(
        #        audio_np,
        #        beam_size=5,
        #        language=self.language if self.language else None,
        #        condition_on_previous_text=False,
        #        initial_prompt=self.prompt,   # prompt 为 None 时就是不加提示
        #      )
        #   2. 拼接所有 segment.text（list comprehension + join），strip 后返回
        # 提示: numpy 输入必须是 16k float32（接口契约），不需要传采样率
        raise NotImplementedError("请检索官方文档后实现")
