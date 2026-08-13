"""
ASR 工厂函数 —— 根据配置创建 ASR 实例
对照 Open-LLM-VTuber asr_factory.py（2026-08-13 检索）

改进点（相对 06.2 的 vad_factory）：
1. 真实后端用延迟导入：未安装依赖时，mock 后端仍可正常使用
2. 保持注册表 + 装饰器模式（开闭原则）
"""
import importlib
from typing import Dict, Type

from .asr_interface import ASRInterface


# 注册表：后端名 → 类
_ASR_REGISTRY: Dict[str, Type[ASRInterface]] = {}

# 后端名 → (模块路径, 依赖包名)，用于延迟导入
_BACKEND_MODULES = {
    "sherpa_onnx": ("echo.asr.sherpa_onnx_asr", "sherpa-onnx"),
    "faster_whisper": ("echo.asr.faster_whisper_asr", "faster-whisper"),
}


def register_asr(name: str):
    """装饰器：注册 ASR 后端"""
    def decorator(cls):
        _ASR_REGISTRY[name] = cls
        return cls
    return decorator


def _ensure_backend_loaded(asr_type: str) -> None:
    """延迟导入真实后端：第一次用到时才 import，缺依赖抛清晰错误"""
    if asr_type not in _BACKEND_MODULES:
        return
    if asr_type in _ASR_REGISTRY:
        return
    module_path, package = _BACKEND_MODULES[asr_type]
    try:
        importlib.import_module(module_path)
    except ImportError as e:
        raise ImportError(
            f"ASR 后端 {asr_type} 加载失败: {e}\n"
            f"请先安装依赖: pip install {package}"
        ) from e


def create_asr(asr_type: str, **kwargs) -> ASRInterface:
    """
    工厂函数：根据类型字符串创建 ASR 实例

    参数:
        asr_type: 后端类型 ("sherpa_onnx" | "faster_whisper" | "mock_asr")
        **kwargs: 传给后端 __init__ 的参数
    返回:
        ASRInterface 实例
    """
    # ═══════════════════════════════════════════════════════════
    # TODO 2: 实现工厂逻辑（对照 06.2 的 create_vad，多一步延迟导入）
    # 步骤:
    #   1. _ensure_backend_loaded(asr_type)   # 先确保后端已注册
    #   2. 检查 asr_type 是否在 _ASR_REGISTRY 中
    #   3. 不在 → raise ValueError(f"未知 ASR 类型: {asr_type}，可选: {list(_ASR_REGISTRY.keys())}")
    #   4. 在 → 返回 _ASR_REGISTRY[asr_type](**kwargs)
    # 提示: 5-7 行代码
    pass


# ═══════════════════════════════════════════════════════════
# TODO 4: CUDA/设备降级包装（对照 06.2 的 create_vad_with_fallback）
# ═══════════════════════════════════════════════════════════
# 写 create_asr_with_fallback(asr_type, **kwargs) 函数：
#   1. 调用 create_asr(asr_type, **kwargs)
#   2. 捕获 RuntimeError，若错误信息含 "cuda"/"device"/"gpu":
#      - 打印降级警告（用 print 即可）
#      - 用 device="cpu" 覆盖 kwargs 后重试（faster-whisper 支持）
#   3. 其他错误不吞，直接 raise
# 提示: 8-10 行代码
