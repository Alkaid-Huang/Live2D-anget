"""
VAD 工厂函数 —— 根据配置创建 VAD 实例
对照 Open-LLM-VTuber vad_factory.py（2026-08-03 检索）

改进点：
1. 用注册表替代 if-else 链（开闭原则）
2. 返回类型标注为 VADInterface（不是 Type[VADInterface]）
3. 加 CUDA→CPU 自动降级
"""
from typing import Dict, Type
from .vad_interface import VADInterface


# 注册表：后端名 → 类
_VAD_REGISTRY: Dict[str, Type[VADInterface]] = {}


def register_vad(name: str):
    """装饰器：注册 VAD 后端"""
    def decorator(cls):
        _VAD_REGISTRY[name] = cls
        return cls
    return decorator


def create_vad(vad_type: str, **kwargs) -> VADInterface:
    """
    工厂函数：根据类型字符串创建 VAD 实例

    参数:
        vad_type: 后端类型 ("silero_vad" | "mock_vad")
        **kwargs: 传给后端 __init__ 的参数
    返回:
        VADInterface 实例
    """
    # ═══════════════════════════════════════════════════════════
    # TODO 4: 实现工厂逻辑
    # ═══════════════════════════════════════════════════════════
    # 步骤:
    #   1. 检查 vad_type 是否在 _VAD_REGISTRY 中
    #   2. 不在 → raise ValueError(f"未知 VAD 类型: {vad_type}，可选: {list(_VAD_REGISTRY.keys())}")
    #   3. 在 → 取出类，调用类(**kwargs) 创建实例并返回
    # 提示: 4-5 行代码
    pass


# ═══════════════════════════════════════════════════════════
# TODO 6: CUDA 降级包装
# ═══════════════════════════════════════════════════════════
# 写一个 create_vad_with_fallback(vad_type, **kwargs) 函数：
#   1. 调用 create_vad(vad_type, **kwargs)
#   2. 如果是 silero_vad 且抛 RuntimeError 且错误信息含 "cuda"/"device":
#      - 打印降级警告（用 print 即可）
#      - 重新调用 create_vad(vad_type, **kwargs)（Silero 默认 CPU）
#   3. 其他错误不吞，直接 raise
# 提示: 8-10 行代码
