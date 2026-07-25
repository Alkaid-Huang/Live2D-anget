"""
课题06 VAD 测试文件
生成模拟音频（含语音+静音段）测试 VAD 检测逻辑
"""

import os
import sys
import pytest
import numpy as np
import soundfile as sf
import tempfile

# 添加课题06目录到路径（tests/ 的上一级）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def model():
    """加载 VAD 模型（所有测试共用）"""
    from vad_detector import load_model
    return load_model()


@pytest.fixture
def test_audio_file():
    """生成测试音频文件：3段语音 + 2段静音交替"""
    sr = 16000
    # 生成 5 秒音频：1秒语音 + 1秒静音 + 1秒语音 + 1秒静音 + 1秒语音
    t = np.linspace(0, 1, sr, endpoint=False)

    # 语音段：440Hz 正弦波（模拟人声）
    speech = (0.3 * np.sin(2 * np.pi * 440 * t)).astype('float32')
    # 静音段：低振幅噪声
    silence = (0.001 * np.random.randn(sr)).astype('float32')

    # 拼接：语音-静音-语音-静音-语音
    audio = np.concatenate([speech, silence, speech, silence, speech])

    # 保存到临时文件
    tmpdir = tempfile.mkdtemp()
    wav_path = os.path.join(tmpdir, "test_audio.wav")
    sf.write(wav_path, audio, sr)

    yield wav_path

    # 清理
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


class TestVadModel:
    """测试模型加载"""

    def test_model_loaded(self, model):
        """模型应该成功加载"""
        assert model is not None

    def test_model_callable(self, model):
        """模型应该是可调用的"""
        assert hasattr(model, '__call__') or hasattr(model, 'forward')


class TestReadAudio:
    """测试音频读取"""

    def test_read_audio_returns_tensor(self, test_audio_file):
        """read_audio_sf 应该返回 torch.Tensor"""
        import torch
        from vad_detector import read_audio_sf

        wav = read_audio_sf(test_audio_file)

        assert isinstance(wav, torch.Tensor)
        assert wav.dim() == 1  # 1D
        assert len(wav) > 0


class TestDetectSpeech:
    """测试语音检测"""

    def test_detect_returns_list(self, test_audio_file, model):
        """detect_speech 应该返回列表和音频张量"""
        from vad_detector import detect_speech

        speech_ts, wav = detect_speech(test_audio_file, model)

        assert isinstance(speech_ts, list)
        assert len(speech_ts) > 0  # 应该检测到至少 1 个语音段

    def test_each_timestamp_has_start_end(self, test_audio_file, model):
        """每个时间戳应该有 start 和 end 键"""
        from vad_detector import detect_speech

        speech_ts, _ = detect_speech(test_audio_file, model)

        for ts in speech_ts:
            assert 'start' in ts
            assert 'end' in ts
            assert ts['start'] < ts['end']  # start 必须小于 end

    def test_speech_segments_not_overlapping(self, test_audio_file, model):
        """语音段之间不应该重叠"""
        from vad_detector import detect_speech

        speech_ts, _ = detect_speech(test_audio_file, model)

        for i in range(len(speech_ts) - 1):
            assert speech_ts[i]['end'] <= speech_ts[i + 1]['start']


class TestSplitAndSave:
    """测试切分保存"""

    def test_split_creates_files(self, test_audio_file, model, tmp_path):
        """split_and_save 应该创建 WAV 文件"""
        from vad_detector import detect_speech, split_and_save

        speech_ts, wav = detect_speech(test_audio_file, model)
        output_dir = str(tmp_path / "chunks")

        split_and_save(speech_ts, wav, output_dir)

        # 检查文件是否创建
        files = [f for f in os.listdir(output_dir) if f.endswith('.wav')]
        assert len(files) == len(speech_ts)

    def test_split_files_are_valid_wav(self, test_audio_file, model, tmp_path):
        """切分后的文件应该是有效的 WAV"""
        from vad_detector import detect_speech, split_and_save

        speech_ts, wav = detect_speech(test_audio_file, model)
        output_dir = str(tmp_path / "chunks")

        split_and_save(speech_ts, wav, output_dir)

        # 读取每个文件验证
        files = sorted([f for f in os.listdir(output_dir) if f.endswith('.wav')])
        for f in files:
            data, sr = sf.read(os.path.join(output_dir, f))
            assert sr == 16000
            assert len(data) > 0  # 不为空

    def test_total_speech_duration_reasonable(self, test_audio_file, model, tmp_path):
        """切分后的语音总时长应该合理（不超过原始音频）"""
        from vad_detector import detect_speech, split_and_save, SAMPLE_RATE

        speech_ts, wav = detect_speech(test_audio_file, model)

        total_speech = sum(ts['end'] - ts['start'] for ts in speech_ts) / SAMPLE_RATE
        original_duration = len(wav) / SAMPLE_RATE

        # 语音总时长应该小于原始音频时长
        assert total_speech < original_duration
        # 应该检测到至少 1 秒的语音（我们生成了 3 秒语音）
        assert total_speech > 1.0


class TestParameters:
    """测试参数调优"""

    def test_high_threshold_fewer_segments(self, test_audio_file, model):
        """高阈值应该检测到更少或相等的语音段"""
        from vad_detector import read_audio_sf
        from silero_vad import get_speech_timestamps

        wav = read_audio_sf(test_audio_file)

        # 低阈值
        ts_low = get_speech_timestamps(wav, model, threshold=0.3, return_seconds=False)
        # 高阈值
        ts_high = get_speech_timestamps(wav, model, threshold=0.9, return_seconds=False)

        # 高阈值检测到的段数应该 <= 低阈值
        assert len(ts_high) <= len(ts_low)
