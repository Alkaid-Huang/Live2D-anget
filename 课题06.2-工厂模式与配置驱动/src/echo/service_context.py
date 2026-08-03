"""
ServiceContext —— 依赖注入容器
对照 Open-LLM-VTuber service_context.py（2026-08-03 检索）

改进点：
1. 简化版——只管 VAD（参考答案管十几个组件）
2. init_vad 用工厂而非直接 new
"""
from typing import Optional
from .config import EchoConfig
from .vad.vad_interface import VADInterface
from .vad.vad_factory import create_vad


class ServiceContext:
    """服务容器：统一管理 Echo 的所有组件"""

    def __init__(self, config: EchoConfig):
        self.config = config
        self.vad_engine: Optional[VADInterface] = None

    def init_vad(self) -> None:
        """根据配置创建 VAD 引擎"""
        # TODO 5: 实现 init_vad
        # 步骤:
        #   1. 从 config.vad_config 取 vad_type
        #   2. 若 vad_type == "none": self.vad_engine = None; return
        #   3. 否则取参数: params = self.config.vad_config.get_vad_params()
        #   4. 调用工厂: self.vad_engine = create_vad(vad_type, **params)
        # 提示: 5-6 行代码
        pass
