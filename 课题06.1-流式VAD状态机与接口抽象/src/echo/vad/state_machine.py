"""
流式 VAD 状态机
对照 Open-LLM-VTuber silero.py 的 StateMachine（2026-07-27 检索）

三态：IDLE → ACTIVE → INACTIVE → (输出) → IDLE
双阈值：概率阈值 + 分贝阈值（滑动窗口平滑后比较）
预缓冲：IDLE 态缓存最近 pre_buffer_size 帧，防止开口第一个字被切掉
"""
from enum import Enum
from collections import deque
import numpy as np


class State(Enum):
    """VAD 三态"""
    IDLE = 1       # 空闲，等待语音
    ACTIVE = 2     # 检测到语音
    INACTIVE = 3   # 语音暂停（可能说完）


class StateMachine:
    """流式 VAD 状态机"""

    def __init__(
        self,
        prob_threshold: float = 0.5,      # 语音概率阈值
        db_threshold: float = -20.0,       # 分贝阈值（float32 用负数，见坑7）
        required_hits: int = 3,           # 连续命中几次确认"开始说话"
        required_misses: int = 24,        # 连续未命中几次确认"说完了"
        smoothing_window: int = 5,        # 滑动窗口大小（平滑概率和分贝）
        pre_buffer_size: int = 20,       # 预缓冲帧数（防切头）
    ):
        self.state = State.IDLE

        # 阈值参数
        self.prob_threshold = prob_threshold
        self.db_threshold = db_threshold
        self.required_hits = required_hits
        self.required_misses = required_misses

        # 滑动窗口（deque 满了自动挤掉最老的）
        self.probs = deque(maxlen=smoothing_window)
        self.dbs = deque(maxlen=smoothing_window)

        # 预缓冲（IDLE 态悄悄存，转 ACTIVE 时拼到前面）
        self.pre_buffer = deque(maxlen=pre_buffer_size)

        # 正式音频累积（ACTIVE/INACTIVE 态存）
        self.bytes_buffer = b""

        # 计数器
        self.hit_count = 0    # 连续命中次数
        self.miss_count = 0   # 连续未命中次数

    @staticmethod
    def calculate_db(audio_np: np.ndarray) -> float:
        """计算音频分贝（RMS 法），对照 silero.py 的 calculate_db"""
        # TODO 1: 实现分贝计算
        # 步骤:
        #   1. rms = np.sqrt(np.mean(audio_np ** 2))  —— 均方根
        #   2. return 20 * np.log10(rms + 1e-7)       —— 转分贝，+1e-7 防 log(0)
        # 提示: 两行代码
        rms = np.sqrt(np.mean(audio_np ** 2))
        return 20 * np.log10(rms + 1e-7)

    def _is_hit(self, prob: float, db: float) -> bool:
        """判断是否命中（双阈值，用平滑后的值）"""
        self.probs.append(prob)
        self.dbs.append(db)
        smoothed_prob = sum(self.probs) / len(self.probs)
        smoothed_db = sum(self.dbs) / len(self.dbs)
        return smoothed_prob >= self.prob_threshold and smoothed_db >= self.db_threshold

    def process(self, prob: float, audio_np: np.ndarray, chunk_bytes: bytes):
        """
        处理一帧，返回完整语音段（bytes）或 None。

        这是状态机核心：根据当前状态 + 是否命中，更新状态并决定是否输出。
        返回 bytes 表示"这段语音完整了，吐出去"；返回 None 表示"继续累积"。

        参数:
            prob: 该帧是语音的概率 (0.0~1.0)
            audio_np: 该帧的 numpy 数组（算分贝用）
            chunk_bytes: 该帧的原始字节（输出用）
        """
        db = self.calculate_db(audio_np)
        is_hit = self._is_hit(prob, db)

        # ═══════════════════════════════════════════════════════════
        # TODO 2: IDLE 态处理（等待语音开始）
        # ═══════════════════════════════════════════════════════════
        if self.state == State.IDLE:
            # 1. 把 chunk_bytes 加入 pre_buffer（防切头，deque 会自动挤掉最老的）
            # 2. 若 is_hit: hit_count += 1; miss_count = 0
            #      若 hit_count >= required_hits:
            #         - 状态转 ACTIVE
            #         - 把 pre_buffer 的内容拼到 bytes_buffer 前面:
            #           self.bytes_buffer = b"".join(self.pre_buffer)
            #         - 清空 pre_buffer: self.pre_buffer.clear()
            #         - hit_count = 0
            # 3. 若未命中: hit_count = 0（连续命中被打断）
            # 4. IDLE 态不输出，return None
            self.pre_buffer.append(chunk_bytes)

            if is_hit:
                self.hit_count += 1
                self.miss_count = 0
                if self.hit_count > self.required_hits:
                    self.state = State.ACTIVE
                    self.bytes_buffer = b"".join(self.pre_buffer) + self.bytes_buffer
                    self.pre_buffer.clear()
                    self.hit_count = 0
            elif not is_hit:
                self.hit_count = 0
            return None


        # ═══════════════════════════════════════════════════════════
        # TODO 3: ACTIVE 态处理（正在说话）
        # ═══════════════════════════════════════════════════════════
        elif self.state == State.ACTIVE:
            # 1. 把 chunk_bytes 累积到 bytes_buffer: self.bytes_buffer += chunk_bytes
            # 2. 若 is_hit: miss_count = 0
            # 3. 若未命中: miss_count += 1
            #      若 miss_count >= required_misses:
            #         - 状态转 INACTIVE
            #         - miss_count = 0
            # 4. ACTIVE 态不立即输出（要等 INACTIVE→IDLE 才输出完整段），return None
            self.bytes_buffer += chunk_bytes
            if is_hit:
                self.miss_count = 0
            elif not is_hit:
                self.miss_count += 1
                if self.miss_count >= self.required_misses:
                    self.state = State.INACTIVE
                    self.miss_count = 0
            return None

        

        # ═══════════════════════════════════════════════════════════
        # TODO 4: INACTIVE 态处理（暂停，可能说完）
        # ═══════════════════════════════════════════════════════════
        elif self.state == State.INACTIVE:
            # 1. 若 is_hit: hit_count += 1; miss_count = 0
            #      若 hit_count >= required_hits:  # 又开始说话了
            #         - 状态转 ACTIVE
            #         - hit_count = 0
            #         - return None（继续累积，不打断）
            # 2. 若未命中: miss_count += 1
            #      若 miss_count >= required_misses:  # 确实说完了
            #         - 准备输出: result = self.bytes_buffer
            #         - 状态转 IDLE
            #         - 清空: self.bytes_buffer = b""
            #         - miss_count = 0
            #         - return result  ← 吐出完整语音段！
            # 3. INACTIVE 态若未达输出条件，return None
            if is_hit:
                self.hit_count += 1
                self.miss_count = 0
                self.state = State.ACTIVE
                return None
            elif not is_hit:
                self.miss_count += 1
                if self.miss_count > self.required_misses:
                    result = self.bytes_buffer
                    self.state = State.IDLE
                    self.bytes_buffer = b""
                    self.miss_count = 0
                    return result
                
        return None