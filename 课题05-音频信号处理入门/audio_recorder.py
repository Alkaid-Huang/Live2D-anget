"""
Echo 音频录制与 MFCC 提取

运行方式:
    python audio_recorder.py

依赖安装（在虚拟环境中）:
    pip install sounddevice soundfile librosa numpy
"""

import sounddevice as sd
import soundfile as sf
import librosa
import numpy as np


# ═══════════════════════════════════════════════════════════════
# 录音参数
# ═══════════════════════════════════════════════════════════════
SAMPLE_RATE = 16000      # 采样率 16000Hz（Whisper 标准）
DURATION = 5             # 录音时长 5 秒
CHANNELS = 1             # 单声道
OUTPUT_FILE = "recording.wav"   # 输出文件名


def record_audio(duration: int, sample_rate: int, channels: int) -> np.ndarray:
    """录制音频，返回 numpy 数组"""
    print(f"准备录音 {duration} 秒（采样率 {sample_rate}Hz）...")
    print("3秒后开始...")
    import time
    time.sleep(3)
    print("开始说话！")

    # ═══════════════════════════════════════════════════════════
    # TODO 1: 用 sd.rec 录音
    # ═══════════════════════════════════════════════════════════
    # 方法: recording = sd.rec(frames, samplerate, channels, dtype)
    # 作用: 从麦克风录制音频，返回 numpy 数组
    # 参数:
    #   frames —— 总采样点数 = duration * sample_rate
    #   samplerate —— 采样率
    #   channels —— 声道数
    #   dtype —— 数据类型，用 'float32'
    # 返回值: numpy 数组，形状 (frames, channels)
    # 提示: frames = int(duration * sample_rate)
    pass

    # ═══════════════════════════════════════════════════════════
    # TODO 2: 等待录音完成
    # ═══════════════════════════════════════════════════════════
    # 方法: sd.wait()
    # 作用: 阻塞当前线程，直到录音完成。不加这行，recording 可能是空的
    # 提示: 一行代码
    pass

    print("录音完成！")
    return recording


def save_wav(data: np.ndarray, file_path: str, sample_rate: int):
    """保存音频为 WAV 文件"""
    print(f"保存到 {file_path}...")

    # ═══════════════════════════════════════════════════════════
    # TODO 3: 用 sf.write 保存 WAV 文件
    # ═══════════════════════════════════════════════════════════
    # 方法: sf.write(file, data, samplerate, subtype)
    # 作用: 把 numpy 数组保存为 WAV 文件
    # 参数:
    #   file —— 文件路径
    #   data —— 音频数组
    #   samplerate —— 采样率
    #   subtype —— 位深格式，用 'PCM_16'（16位 PCM）
    # 提示: 一行代码
    pass

    print("保存完成！")


def extract_mfcc(file_path: str, n_mfcc: int = 13) -> np.ndarray:
    """读取音频文件并提取 MFCC 特征"""
    print(f"读取 {file_path} 并提取 MFCC...")

    # ═══════════════════════════════════════════════════════════
    # TODO 4: 用 librosa.load 读取音频文件
    # ═══════════════════════════════════════════════════════════
    # 方法: y, sr = librosa.load(path, sr)
    # 作用: 读取音频文件，返回音频数组和采样率
    # 参数:
    #   path —— 文件路径
    #   sr —— 目标采样率（会自动重采样），用 SAMPLE_RATE
    # 返回值: (y, sr) —— y 是 1D 数组，sr 是采样率
    # 提示: y, sr = librosa.load(file_path, sr=SAMPLE_RATE)
    pass

    # ═══════════════════════════════════════════════════════════
    # TODO 5: 用 librosa.feature.mfcc 提取 MFCC 特征
    # ═══════════════════════════════════════════════════════════
    # 方法: mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    # 作用: 从音频数组中提取 MFCC 特征矩阵
    # 参数:
    #   y —— 音频数组（TODO 4 的返回值）
    #   sr —— 采样率（TODO 4 的返回值）
    #   n_mfcc —— MFCC 系数个数，用参数 n_mfcc
    # 返回值: 2D 数组，形状 (n_mfcc, 帧数)
    # 提示: mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    pass

    return mfcc


def main():
    """主函数：录音 → 保存 → 提取 MFCC → 打印结果"""
    # 1. 录音
    recording = record_audio(DURATION, SAMPLE_RATE, CHANNELS)
    print(f"录音数组形状: {recording.shape}")

    # 2. 保存
    save_wav(recording, OUTPUT_FILE, SAMPLE_RATE)

    # 3. 提取 MFCC
    mfcc = extract_mfcc(OUTPUT_FILE, n_mfcc=13)

    # 4. 打印结果
    print(f"\n{'='*50}")
    print(f"MFCC 特征矩阵形状: {mfcc.shape}")
    print(f"  - {mfcc.shape[0]} 个系数")
    print(f"  - {mfcc.shape[1]} 帧")
    print(f"\n前 3 帧的 MFCC 值:")
    # mfcc[:, :3] 取前 3 列（前 3 帧），.T 转置让每行是一帧
    for i, frame in enumerate(mfcc[:, :3].T):
        print(f"  帧 {i}: {frame}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
