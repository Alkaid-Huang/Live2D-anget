"""
课题06.3 现象复现脚本
运行: python reproduce.py

本脚本不会告诉你 bug 在哪，只负责让"不对劲"变得可观察。
你的第一步：运行它，把三个异常现象记录到 01-核心内容.md 的作答区。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from echo.config import SileroVADConfig
from echo.vad.state_machine import StateMachine


def reproduce_bug_a():
    """现象 1：分贝值异常偏大"""
    print("=" * 55)
    print("现象 1：分贝计算")
    sm = StateMachine()
    loud = np.ones(512, dtype=np.float32) * 0.5
    db = sm.calculate_db(loud)
    expected = 20 * np.log10(np.sqrt(np.mean(loud ** 2)) + 1e-7)
    print(f"  幅度 0.5 的音频，当前实现算得分贝: {db:.3f} dB")
    print(f"  按 RMS=sqrt(mean(x^2)) 公式应得:   {expected:.3f} dB")
    same = abs(db - expected) < 0.01
    print(f"  >>> {'一致（正常）' if same else '不一致（异常：偏大非常多）'}")
    print()


def reproduce_bug_b():
    """现象 2：完整语音段的字节顺序倒置"""
    print("=" * 55)
    print("现象 2：完整语音段的字节顺序")
    sm = StateMachine(
        prob_threshold=0.5,
        db_threshold=-20.0,
        required_hits=2,
        required_misses=2,
        smoothing_window=1,
        pre_buffer_size=5,
    )
    loud = np.ones(512, dtype=np.float32) * 0.5
    silent = np.zeros(512, dtype=np.float32)

    # IDLE 2 帧（进 pre_buffer）→ 第 2 帧转 ACTIVE
    for i in range(2):
        sm.process(prob=0.9, audio_np=loud, chunk_bytes=f"P{i}".encode())
    # ACTIVE 2 帧正式语音
    for i in range(2):
        sm.process(prob=0.9, audio_np=loud, chunk_bytes=f"v{i}".encode())
    # 2 帧静音（ACTIVE 态累积，随后转 INACTIVE）+ 2 帧静音（INACTIVE 态，吐出完整段）
    result = None
    for _ in range(4):
        result = sm.process(prob=0.1, audio_np=silent, chunk_bytes=b"s")

    print(f"  实际输出: {result}")
    print(f"  期望输出: {b'P0P1v0v1ss'}")
    ok = result == b"P0P1v0v1ss"
    print(f"  >>> {'顺序正确（正常）' if ok else '异常：语音块顺序倒置，静音跑到了段首'}")
    print()


def reproduce_bug_c():
    """现象 3：非法配置没有被拦截"""
    print("=" * 55)
    print("现象 3：Pydantic 配置校验")
    try:
        cfg = SileroVADConfig(db_threshold=5)
        print(f"  db_threshold=5（正分贝）竟然通过了校验，当前值: {cfg.db_threshold}")
        print("  >>> 异常：分贝阈值应为负数，正数没有物理意义，校验契约被破坏")
    except Exception as e:
        print(f"  已拦截: {type(e).__name__}")
        print("  >>> 正常：非法配置被 Pydantic 拦住")
    print()


if __name__ == "__main__":
    reproduce_bug_a()
    reproduce_bug_b()
    reproduce_bug_c()
