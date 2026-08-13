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

from echo.config import VADConfig, SileroVADConfig
from echo.vad.state_machine import StateMachine


def reproduce_bug_a():
    """现象 1：分贝值异常"""
    print("=" * 55)
    print("现象 1：分贝计算")
    sm = StateMachine()
    loud = np.ones(512, dtype=np.float32) * 0.5
    db = sm.calculate_db(loud)
    expected = 20 * np.log10(0.5 + 1e-7)
    print(f"  幅度 0.5 的音频，当前实现算得分贝: {db:.3f} dB")
    print(f"  按 20*log10(RMS) 公式应得:        {expected:.3f} dB")
    same = abs(db - expected) < 0.01
    print(f"  >>> {'一致（正常）' if same else '不一致（异常：偏小一半）'}")
    print()


def reproduce_bug_b():
    """现象 2：配置参数不生效"""
    print("=" * 55)
    print("现象 2：配置驱动是否生效")
    cfg = VADConfig(
        vad_type="silero_vad",
        silero=SileroVADConfig(prob_threshold=0.9, required_hits=10),
    )
    params = cfg.get_vad_params()
    got_prob = params.get("prob_threshold")
    got_hits = params.get("required_hits")
    print(f"  配置里写的:   prob_threshold=0.9, required_hits=10")
    print(f"  工厂拿到的:   prob_threshold={got_prob}, required_hits={got_hits}")
    ok = got_prob == 0.9 and got_hits == 10
    print(f"  >>> {'透传成功（正常）' if ok else '配置被静默忽略（异常：回落默认值）'}")
    print()


def reproduce_bug_c():
    """现象 3：INACTIVE 恢复 ACTIVE 的帧数"""
    print("=" * 55)
    print("现象 3：停顿后重新开口，多少帧能恢复 ACTIVE")
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

    # IDLE → 2 帧命中 → ACTIVE
    for _ in range(2):
        sm.process(prob=0.9, audio_np=loud, chunk_bytes=b"v")
    print(f"  2 帧命中后状态:           {sm.state.name}（应为 ACTIVE）")

    # ACTIVE → 2 帧未命中 → INACTIVE
    for _ in range(2):
        sm.process(prob=0.1, audio_np=silent, chunk_bytes=b"s")
    print(f"  2 帧静音后状态:           {sm.state.name}（应为 INACTIVE）")

    # INACTIVE → 再 2 帧命中（required_hits=2，恰好应该恢复）
    for _ in range(2):
        sm.process(prob=0.9, audio_np=loud, chunk_bytes=b"v")
    print(f"  再 2 帧命中后状态:        {sm.state.name}（应为 ACTIVE）")

    # 如果还没恢复，多喂 1 帧观察
    sm.process(prob=0.9, audio_np=loud, chunk_bytes=b"v")
    print(f"  再补 1 帧后状态:          {sm.state.name}（若此时才 ACTIVE，说明多要了一帧）")
    print(f"  >>> 配置说 2 帧就该恢复。实际需要几帧？")
    print()


if __name__ == "__main__":
    reproduce_bug_a()
    reproduce_bug_b()
    reproduce_bug_c()
