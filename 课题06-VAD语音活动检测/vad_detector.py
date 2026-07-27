"""
Echo VAD 语音活动检测 —— 检测并切分语音段

运行方式:
    python vad_detector.py

依赖安装（在虚拟环境中）:
    pip install silero-vad soundfile numpy torch

注意: silero-vad 自带的 read_audio 依赖 torchaudio I/O，在 Python 3.14 + torchaudio 2.9+
环境下需要 torchcodec+FFmpeg。本脚本用 soundfile 替代读取，绕过这个限制。
"""

import os
import soundfile as sf
import numpy as np
import torch
from silero_vad import load_silero_vad, get_speech_timestamps


# ═══════════════════════════════════════════════════════════════
# VAD 参数
# ═══════════════════════════════════════════════════════════════
SAMPLE_RATE = 16000          # silero-vad 只支持 8000 和 16000
THRESHOLD = 0.5              # 语音概率阈值
MIN_SILENCE_MS = 500         # 最小静音时长（判断"说完了"）
OUTPUT_DIR = "speech_chunks" # 切分后保存目录


def read_audio_sf(path: str, target_sr: int = SAMPLE_RATE) -> torch.Tensor:
    """
    用 soundfile 读取音频，转成 torch.Tensor（替代 silero-vad 的 read_audio）。
    自动重采样到 target_sr，自动转单声道。
    """
    # 用 soundfile 读取（返回 numpy 数组和采样率）
    data, sr = sf.read(path, dtype='float32')

    # 如果是多声道，取平均值转单声道
    if data.ndim > 1:
        data = data.mean(axis=1)

    # 如果采样率不匹配，用 librosa 重采样
    if sr != target_sr:
        import librosa
        data = librosa.resample(data, orig_sr=sr, target_sr=target_sr)

    # numpy 转 torch.Tensor
    return torch.from_numpy(data).float()


def load_model():
    """加载 silero-vad 模型"""
    print("正在加载 VAD 模型...")

    # ═══════════════════════════════════════════════════════════
    # TODO 1: 加载 silero-vad 模型
    # ═══════════════════════════════════════════════════════════
    # 方法: model = load_silero_vad()
    # 作用: 加载预训练的 VAD 神经网络模型，用于判断音频中哪里有人说话
    # 参数: 无
    # 返回值: 模型对象，后续传给 get_speech_timestamps 使用
    # 提示: 一行代码，赋值给 model
    model = load_silero_vad()
    
    print("模型加载完成！")
    return model


def detect_speech(wav_path: str, model) -> tuple:
    """检测音频中的语音段，返回时间戳列表和音频张量"""
    print(f"读取音频: {wav_path}")

    # ═══════════════════════════════════════════════════════════
    # TODO 2: 读取音频文件
    # ═══════════════════════════════════════════════════════════
    # 方法: wav = read_audio_sf(path)
    # 作用: 用 soundfile 读取音频，自动重采样到 16kHz 单声道，返回 torch.Tensor
    # 参数: path —— 音频文件路径，用参数 wav_path
    # 返回值: torch.Tensor，1D，值域 -1.0 到 1.0
    # 提示: wav = read_audio_sf(wav_path)
    wav = read_audio_sf(wav_path)

    print(f"音频长度: {len(wav)} 个采样点（{len(wav) / SAMPLE_RATE:.1f} 秒）")

    # ═══════════════════════════════════════════════════════════
    # TODO 3: 检测语音段
    # ═══════════════════════════════════════════════════════════
    # 方法: speech_ts = get_speech_timestamps(wav, model, threshold=, min_silence_duration_ms=, return_seconds=)
    # 作用: 用 VAD 模型检测音频中哪些片段是语音，返回时间戳列表
    # 参数:
    #   wav —— 音频张量（TODO 2 的返回值）
    #   model —— VAD 模型（传入参数 model）
    #   threshold —— 语音概率阈值，用常量 THRESHOLD
    #   min_silence_duration_ms —— 最小静音时长，用常量 MIN_SILENCE_MS
    #   return_seconds —— 设为 False（返回采样点，方便后续切片）
    # 返回值: list[dict]，每个 dict 含 'start' 和 'end' 键（采样点索引）
    # 提示: 注意 return_seconds=False，这样 start/end 是采样点索引，可以直接用于切片
    speech_ts = get_speech_timestamps(wav,model, threshold=THRESHOLD, min_silence_duration_ms=MIN_SILENCE_MS, return_seconds=False)

    print(f"检测到 {len(speech_ts)} 个语音段")
    for i, ts in enumerate(speech_ts):
        start_sec = ts['start'] / SAMPLE_RATE
        end_sec = ts['end'] / SAMPLE_RATE
        print(f"  段{i}: {start_sec:.2f}s - {end_sec:.2f}s（时长 {end_sec - start_sec:.2f}s）")

    return speech_ts, wav


def split_and_save(speech_ts: list, wav, output_dir: str = OUTPUT_DIR):
    """把每个语音段切分出来，保存为独立的 WAV 文件"""
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n切分并保存到 {output_dir}/")

    for i, ts in enumerate(speech_ts):
        # ═══════════════════════════════════════════════════════════
        # TODO 4: 从音频中切出这一段
        # ═══════════════════════════════════════════════════════════
        # 方法: chunk = wav[start:end]
        # 作用: 用 torch.Tensor 的切片功能，取出 start 到 end 之间的音频片段
        # 参数:
        #   start —— ts['start']（这一段的起始采样点）
        #   end —— ts['end']（这一段的结束采样点）
        # 返回值: torch.Tensor 子集
        # 提示: chunk = wav[ts['start']:ts['end']]
        chunk = wav[ts['start']:ts['end']]

        # ═══════════════════════════════════════════════════════════
        # TODO 5: 转换为 numpy 数组并保存为 WAV
        # ═══════════════════════════════════════════════════════════
        # 步骤1: chunk_np = chunk.numpy()
        #        作用: torch.Tensor 转 numpy 数组（soundfile 需要 numpy）
        # 步骤2: file_path = os.path.join(output_dir, f"chunk_{i:03d}.wav")
        #        作用: 拼接输出文件路径，如 "speech_chunks/chunk_000.wav"
        # 步骤3: sf.write(file_path, chunk_np, SAMPLE_RATE)
        #        作用: 保存为 WAV 文件
        # 提示: 三行代码
        chunk_np = chunk.numpy()
        file_path = os.path.join(output_dir, f"chunk_{i:03d}.wav")
        sf.write(file_path, chunk_np, SAMPLE_RATE)

        duration = len(chunk) / SAMPLE_RATE
        print(f"  chunk_{i:03d}.wav（{duration:.2f}s）")

    print(f"\n共保存 {len(speech_ts)} 个语音片段到 {output_dir}/")


def main():
    """主函数：加载模型 → 检测语音 → 切分保存"""
    print("=" * 50)
    print("Echo VAD 语音活动检测")
    print("=" * 50)

    # 1. 加载模型
    model = load_model()

    # 2. 检测语音段（用课题05录制的音频，或自己提供的音频）
    wav_path = input("请输入音频文件路径（直接回车用课题05的 recording.wav）: ").strip()
    if not wav_path:
        wav_path = os.path.join(os.path.dirname(__file__), "..", "课题05-音频信号处理入门", "recording.wav")
        if not os.path.exists(wav_path):
            print(f"找不到默认音频文件: {wav_path}")
            print("请先运行课题05录制音频，或提供自己的 WAV 文件路径")
            return

    speech_ts, wav = detect_speech(wav_path, model)

    if not speech_ts:
        print("未检测到语音段！可能是音频太短或全是静音。")
        return

    # 3. 切分并保存
    split_and_save(speech_ts, wav)

    print("\n" + "=" * 50)
    print("VAD 检测完成！")
    print(f"原始音频: {len(wav) / SAMPLE_RATE:.1f} 秒")
    total_speech = sum(ts['end'] - ts['start'] for ts in speech_ts) / SAMPLE_RATE
    print(f"语音总长: {total_speech:.1f} 秒")
    print(f"切分片段: {len(speech_ts)} 个")
    print("=" * 50)


if __name__ == "__main__":
    main()
