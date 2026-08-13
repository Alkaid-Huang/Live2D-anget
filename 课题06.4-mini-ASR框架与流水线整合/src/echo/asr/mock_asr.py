"""
MockASR 假实现 —— 用于测试和开发
证明只要实现 ASRInterface，工厂就能创建它
"""
from .asr_interface import ASRInterface
from .asr_factory import register_asr


# TODO 1: 实现 MockASR
# 要求：
#   1. 继承 ASRInterface，并加 @register_asr("mock_asr") 装饰器
#   2. __init__ 接收任意参数（**kwargs），全部忽略
#   3. transcribe_np(audio) 直接返回固定文本 "你好世界"（模拟识别结果，不真听）
# 提示: 8-10 行代码
