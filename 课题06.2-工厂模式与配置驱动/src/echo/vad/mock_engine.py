"""
MockVAD 假实现 —— 用于测试和开发
证明只要实现 VADInterface，工厂就能创建它
"""
from typing import Generator
from .vad_interface import VADInterface
from .vad_factory import register_vad


# TODO 3: 实现 MockVAD
# 要求：
#   1. 继承 VADInterface
#   2. __init__ 接收任意参数（用 **kwargs），全部忽略
#   3. detect_speech 是生成器：遍历 audio_chunks，每次 yield chunk[1]（chunk_bytes）
#      （因为 MockVAD 不做真正检测，直接把字节吐出）
# 提示: 6-8 行代码
