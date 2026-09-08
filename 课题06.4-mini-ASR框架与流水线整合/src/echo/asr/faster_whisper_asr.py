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
        """同步转写：audio_np 必须是 float32 单声道 16kHz（接口契约）"""
        segments, _ = self.model.transcribe(
            audio_np,
            beam_size=5,
            language=self.language if self.language else None,
            condition_on_previous_text=False,
            initial_prompt=self.prompt,
        )
        return "".join(segment.text for segment in segments).strip()
    
