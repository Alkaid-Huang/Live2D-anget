"""
Pydantic 配置模型 —— 用类型校验拦截非法配置（06.4 新增 ASR 部分）
对照 Open-LLM-VTuber config_manager/vad.py 与 config_manager/asr.py
（2026-08-03 / 2026-08-13 检索）

改进点：
1. 加 Field(ge=, le=) 值域约束（参考答案没有）
2. db_threshold 用 float 不用 int（参考答案用 int 但实际是浮点）
3. ASR 配置字段名对齐真实源码：model_path / tokens / provider / prompt
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional


class SileroVADConfig(BaseModel):
    """Silero VAD 参数配置（带校验）"""
    # TODO 1: 定义 Silero VAD 的配置字段
    # 要求：
    #   - prob_threshold: float, 默认 0.5, 约束 0.0~1.0
    #   - db_threshold: float, 默认 -20.0（float32 用负数，见课题06.1 坑7）
    #   - required_hits: int, 默认 3, 必须 > 0
    #   - required_misses: int, 默认 24, 必须 > 0
    #   - smoothing_window: int, 默认 5, 必须 > 0
    #   - pre_buffer_size: int, 默认 20, 必须 > 0
    #   - window_size_samples: int, 默认 512, 必须 > 0
    # 提示: 每行用 Field(default=..., ge=... 或 gt=...)
    prob_threshold: float = Field(default = 0.5,ge = 0.0,le = 1.0)
    db_threshold: float = Field(default= -20.0,le = 0)
    required_hits: int = Field(default=3, gt=0)
    required_misses: int = Field(default=24, gt=0)
    smoothing_window: int = Field(default=5, gt=0)
    pre_buffer_size: int = Field(default=20, gt=0)
    window_size_samples: int = Field(default=512, gt=0)


class VADConfig(BaseModel):
    """VAD 顶层配置：选择哪个后端 + 对应参数"""
    vad_type: str = Field(default="silero_vad")  # "silero_vad" | "mock_vad" | "none"
    silero: Optional[SileroVADConfig] = Field(default=None)

    def get_vad_params(self) -> dict:
        """根据 vad_type 取对应后端的参数字典"""
        if self.vad_type == "silero_vad":
            if self.silero is None:
                return SileroVADConfig().model_dump()
            return self.silero.model_dump()
        return {}


class SherpaOnnxASRConfig(BaseModel):
    """SenseVoice 后端参数（带校验，字段名对齐真实源码 config_manager/asr.py）"""
    # SenseVoice 是单模型文件：model.onnx + tokens.txt（对照真实源码 sense_voice 参数）
    model_path: str = Field(
        default="models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/model.int8.onnx"
    )
    tokens: str = Field(
        default="models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/tokens.txt"
    )
    num_threads: int = Field(default=4, gt=0)
    use_itn: bool = Field(default=True)
    provider: Literal["cpu", "cuda"] = Field(default="cpu")


class FasterWhisperASRConfig(BaseModel):
    """faster-whisper 后端参数（带校验，字段名对齐真实源码 config_manager/asr.py）"""
    model_path: str = Field(default="small")  # 模型名（如 small）或本地路径
    download_root: str = Field(default="models/whisper")
    language: Optional[str] = Field(default="zh")
    device: Literal["cpu", "cuda", "auto"] = Field(default="auto")
    compute_type: Literal["int8", "float16", "float32"] = Field(default="int8")
    prompt: Optional[str] = Field(default=None)  # initial_prompt，引导识别


class ASRConfig(BaseModel):
    """ASR 顶层配置：选择哪个后端 + 对应参数"""
    # TODO 3: 定义 ASR 顶层配置（对照上面的 VADConfig）
    # 要求：
    #   - asr_type: str, 默认 "mock_asr"
    #     （可选: "sherpa_onnx" | "faster_whisper" | "mock_asr" | "none"）
    #   - sherpa_onnx: Optional[SherpaOnnxASRConfig] = Field(default=None)
    #   - faster_whisper: Optional[FasterWhisperASRConfig] = Field(default=None)
    #   - get_asr_params(self) 方法：
    #     asr_type == "sherpa_onnx" 时返回 sherpa_onnx 的 model_dump()
    #     asr_type == "faster_whisper" 时返回 faster_whisper 的 model_dump()
    #     否则返回 {}（对照 VADConfig.get_vad_params 的写法）
    pass


class EchoConfig(BaseModel):
    """Echo 全局配置"""
    # TODO 2: 定义顶层配置
    # 要求：
    #   - vad_config: VADConfig 类型，默认 VADConfig()
    # 提示: 一行代码
    vad_config: VADConfig = Field(default_factory=VADConfig)
    # TODO 5: 加 ASR 顶层配置字段（对照上一行）
    # 要求: asr_config: ASRConfig = Field(default_factory=ASRConfig)
