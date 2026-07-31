"""
课题06.1 验收测试
运行: python -m pytest tests/test_06_1.py -v

测试覆盖：
1. 抽象基类不可实例化
2. 状态机分贝计算
3. 三态状态转换
4. 双阈值检测
5. 预缓冲防切头
6. 生成器流式输出
7. MockVAD 假实现（证明接口可替换）
"""
import pytest
import numpy as np
import sys
import os

# 把 src 加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from echo.vad.vad_interface import VADInterface
from echo.vad.state_machine import StateMachine, State


# ═══════════════════════════════════════════════════════════════
# 测试 1: 抽象基类不可实例化
# ═══════════════════════════════════════════════════════════════
def test_abstract_cannot_instantiate():
    """VADInterface 是抽象类，不能直接 new"""
    with pytest.raises(TypeError):
        VADInterface()


# ═══════════════════════════════════════════════════════════════
# 测试 2: 分贝计算
# ═══════════════════════════════════════════════════════════════
def test_calculate_db():
    """静音分贝很低，大音量分贝高"""
    sm = StateMachine()
    silence = np.zeros(512, dtype=np.float32)
    loud = np.ones(512, dtype=np.float32) * 0.5
    db_silence = sm.calculate_db(silence)
    db_loud = sm.calculate_db(loud)
    assert db_silence < -50, f"静音分贝应很低，实际 {db_silence}"
    assert db_loud > -20, f"大音量分贝应较高，实际 {db_loud}"


# ═══════════════════════════════════════════════════════════════
# 测试 3: 三态状态转换
# ═══════════════════════════════════════════════════════════════
def test_state_transitions():
    """IDLE →(命中)→ ACTIVE →(未命中)→ INACTIVE →(未命中)→ IDLE"""
    sm = StateMachine(
        prob_threshold=0.5, db_threshold=-20,
        required_hits=2, required_misses=3,
        smoothing_window=1, pre_buffer_size=5,
    )
    assert sm.state == State.IDLE

    # 模拟高概率+高音量的帧（命中）
    loud_audio = np.ones(512, dtype=np.float32) * 0.5
    loud_bytes = b"\x01" * 100

    # 连续命中 2 次 → ACTIVE
    for _ in range(2):
        result = sm.process(prob=0.9, audio_np=loud_audio, chunk_bytes=loud_bytes)
    assert sm.state == State.ACTIVE, f"应转 ACTIVE，实际 {sm.state}"

    # 模拟低概率+低音量的帧（未命中）
    silence_audio = np.zeros(512, dtype=np.float32)
    silence_bytes = b"\x00" * 100

    # 连续未命中 3 次 → INACTIVE
    for _ in range(3):
        result = sm.process(prob=0.1, audio_np=silence_audio, chunk_bytes=silence_bytes)
    assert sm.state == State.INACTIVE, f"应转 INACTIVE，实际 {sm.state}"

    # 继续未命中 3 次 → IDLE，并输出语音段
    result = None
    for _ in range(3):
        result = sm.process(prob=0.1, audio_np=silence_audio, chunk_bytes=silence_bytes)
    assert sm.state == State.IDLE, f"应回 IDLE，实际 {sm.state}"
    assert result is not None, "INACTIVE→IDLE 时应输出完整语音段"
    assert len(result) > 0, "输出的语音段不应为空"


# ═══════════════════════════════════════════════════════════════
# 测试 4: 双阈值（高音量但低概率不算命中）
# ═══════════════════════════════════════════════════════════════
def test_dual_threshold():
    """高音量 + 低概率 = 不命中（双阈值拦截噪音）"""
    sm = StateMachine(
        prob_threshold=0.5, db_threshold=-20,
        required_hits=1, smoothing_window=1, pre_buffer_size=5,
    )
    # 高音量但 VAD 概率低（像装修噪音）
    loud_audio = np.ones(512, dtype=np.float32) * 0.5
    result = sm.process(prob=0.1, audio_np=loud_audio, chunk_bytes=b"x")
    assert sm.state == State.IDLE, "高音量低概率不应触发 ACTIVE（双阈值拦截）"


# ═══════════════════════════════════════════════════════════════
# 测试 5: 预缓冲防切头
# ═══════════════════════════════════════════════════════════════
def test_pre_buffer():
    """IDLE 态的帧应被 pre_buffer 捕获，转 ACTIVE 时拼到输出前面"""
    sm = StateMachine(
        prob_threshold=0.5, db_threshold=-20,
        required_hits=3, required_misses=2,
        smoothing_window=1, pre_buffer_size=5,
    )
    loud_audio = np.ones(512, dtype=np.float32) * 0.5

    # IDLE 态喂 2 帧（不够转 ACTIVE，这些应进 pre_buffer）
    for i in range(2):
        sm.process(prob=0.9, audio_np=loud_audio, chunk_bytes=f"P{i}".encode())

    # 此时还在 IDLE，pre_buffer 应有内容
    assert sm.state == State.IDLE, "2 帧 < required_hits=3，应还在 IDLE"
    assert len(sm.pre_buffer) == 2, "IDLE 态应缓存到 pre_buffer"

    # 第 3 帧命中：转 ACTIVE，pre_buffer 内容拼入 bytes_buffer
    sm.process(prob=0.9, audio_np=loud_audio, chunk_bytes=b"P2")
    assert sm.state == State.ACTIVE, "3 帧命中应转 ACTIVE"
    assert len(sm.pre_buffer) == 0, "转 ACTIVE 后 pre_buffer 应清空"
    assert sm.bytes_buffer == b"P0P1P2", "pre_buffer 内容应拼入 bytes_buffer（防切头）"


# ═══════════════════════════════════════════════════════════════
# 测试 6: MockVAD 假实现（证明接口可替换）
# ═══════════════════════════════════════════════════════════════
def test_mock_vad_implements_interface():
    """写一个假 VAD，证明只要实现接口就能用（为 06.2 工厂铺路）"""

    class MockVAD(VADInterface):
        """假 VAD：把所有输入原样吐出，用于测试"""
        def detect_speech(self, audio_chunks):
            for chunk in audio_chunks:
                yield chunk  # 假实现：直接吐出

    mock = MockVAD()  # 能实例化（实现了 detect_speech）
    results = list(mock.detect_speech([b"a", b"b", b"c"]))
    assert results == [b"a", b"b", b"c"], "MockVAD 应原样吐出"