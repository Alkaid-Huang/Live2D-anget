"""
Pydantic 配置模型 —— 用类型校验拦截非法配置
对照 Open-LLM-VTuber config_manager/vad.py（2026-08-03 检索）

改进点：
1. 加 Field(ge=, le=) 值域约束（参考答案没有）
2. db_threshold 用 float 不用 int（参考答案用 int 但实际是浮点）
"""
from pydantic import BaseModel, Field
from typing import Optional


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
    pass


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


class EchoConfig(BaseModel):
    """Echo 全局配置"""
    # TODO 2: 定义顶层配置
    # 要求：
    #   - vad_config: VADConfig 类型，默认 VADConfig()
    # 提示: 一行代码
    pass
