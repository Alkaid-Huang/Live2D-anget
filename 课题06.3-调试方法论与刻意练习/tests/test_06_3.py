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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from echo.config import VADConfig, SileroVADConfig
from echo.vad.state_machine import StateMachine, State


# ═══════════════════════════════════════════════════════════
# 测试 1: Bug A 防回归 —— 分贝公式的系数
# ═══════════════════════════════════════════════════════════
def test_calculate_db_uses_20_factor():
    """
    幅度分贝公式是 20*log10(RMS)，不是 10*log10(RMS)。
    提示:
      - 用公式 20 * np.log10(0.5 + 1e-7) 算出期望值，不硬编码数字
      - 用 pytest.approx(..., abs=0.01) 做浮点断言
    """
    sm = StateMachine()
    loud = np.ones(512, dtype=np.float32) * 0.5
    db = sm.calculate_db(loud)
    expected = 20 * np.log10(0.5 + 1e-7)
    # TODO: 断言 db 接近 expected
    raise NotImplementedError("请填写断言")


# ═══════════════════════════════════════════════════════════
# 测试 2: Bug B 防回归 —— 配置参数必须原样透传
# ═══════════════════════════════════════════════════════════
def test_get_vad_params_passthrough():
    """
    配置里写什么，工厂就该拿到什么，不能静默回落默认值。
    提示:
      - 构造 VADConfig(vad_type="silero_vad", silero=SileroVADConfig(prob_threshold=0.9, required_hits=10))
      - 调用 get_vad_params()，断言 prob_threshold == 0.9、required_hits == 10
    """
    # TODO: 构造配置并断言参数透传
    raise NotImplementedError("请填写断言")


# ═══════════════════════════════════════════════════════════
# 测试 3: Bug C 防回归 —— INACTIVE 恢复 ACTIVE 的帧数精确匹配
# ═══════════════════════════════════════════════════════════
def test_inactive_reacts_at_exact_required_hits():
    """
    required_hits=2 时，INACTIVE 态命中第 2 帧必须立刻回 ACTIVE，不能多要 1 帧。
    提示:
      - required_hits=2, required_misses=2, smoothing_window=1
      - 2 帧 loud → ACTIVE；2 帧 silent → INACTIVE；再 2 帧 loud → 断言状态 == State.ACTIVE
    """
    # TODO: 构造状态机序列并断言
    raise NotImplementedError("请填写断言")
