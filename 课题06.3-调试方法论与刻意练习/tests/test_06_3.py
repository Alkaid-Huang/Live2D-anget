"""
课题06.3 防回归测试区 —— 你的任务：填完 3 个测试

每个测试的验收标准：
- 修复前（bug 还在）：测试失败
- 修复后（bug 已修）：测试通过
- 也就是说：测试必须能"拦住"对应 bug，而不是永远通过

运行: python -m pytest tests\test_06_3.py -v
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pydantic import ValidationError

from echo.config import SileroVADConfig
from echo.vad.state_machine import StateMachine, State


# ═══════════════════════════════════════════════════════════
# 测试 1: Bug A 防回归 —— RMS 必须是"均方根"（先平方、再平均、再开方）
# ═══════════════════════════════════════════════════════════
def test_calculate_db_uses_rms_mean():
    """
    幅度 0.5、长度 512 的音频，正确 RMS = sqrt(mean(x^2)) = 0.5，分贝 ≈ -6.02。
    提示:
      - 期望值用公式 20 * np.log10(np.sqrt(np.mean(loud ** 2)) + 1e-7) 算出来，不硬编码
      - 用 pytest.approx(..., abs=0.01) 做浮点断言
    """
    sm = StateMachine()
    loud = np.ones(512, dtype=np.float32) * 0.5
    db = sm.calculate_db(loud)
    expected = 20 * np.log10(np.sqrt(np.mean(loud ** 2)) + 1e-7)
    # TODO: 断言 db 接近 expected
    raise NotImplementedError("请填写断言")


# ═══════════════════════════════════════════════════════════
# 测试 2: Bug B 防回归 —— ACTIVE 态必须按到达顺序追加字节
# ═══════════════════════════════════════════════════════════
def test_active_appends_chunks_in_order():
    """
    语音块必须按到达顺序拼进 bytes_buffer，不能倒置。
    提示:
      - required_hits=2, required_misses=2, smoothing_window=1
      - 2 帧 (b"P0", b"P1") → ACTIVE（预缓冲拼入）
      - 2 帧 (b"v0", b"v1") 在 ACTIVE 态累积
      - 4 帧静音 → 吐出完整段（ACTIVE 期间的前 2 帧静音也会进段）
      - 期望输出 == b"P0P1v0v1ss"
    """
    # TODO: 构造状态机序列，断言输出的完整段
    raise NotImplementedError("请填写断言")


# ═══════════════════════════════════════════════════════════
# 测试 3: Bug C 防回归 —— 正分贝阈值必须被 Pydantic 拒绝
# ═══════════════════════════════════════════════════════════
def test_db_threshold_rejects_positive():
    """
    db_threshold 只允许负数（float32 音频的分贝不可能为正）。
    提示:
      - with pytest.raises(ValidationError): SileroVADConfig(db_threshold=5)
    """
    # TODO: 断言正分贝配置会抛 ValidationError
    raise NotImplementedError("请填写断言")
