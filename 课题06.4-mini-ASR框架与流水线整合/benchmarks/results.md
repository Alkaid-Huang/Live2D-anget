# 延迟记录（冲刺期临时基准）

> 目的：先有数字，再谈优化——正式基准在冲刺 D8 / 课题06.5 扩展。

## 2026-09-08 第一次真实转写

**环境**：Windows / Python 3.14.6 / faster-whisper 1.2.1 / ctranslate2 4.8.2 / CPU int8
**模型**：Systran/faster-whisper-small（已下载到 `models/whisper` 本地缓存）
**输入**：`recording.wav`（16kHz 单声道 16bit，5.0 秒人声）

| 指标 | 数值 |
|------|------|
| 首次模型加载 | 1.87 s |
| 5 秒音频转写（CPU small/int8） | 1.5 s |

**识别结果**：`字幕by索兰娅`

**备注**：Windows 控制台可能把中文结果显示成乱码——写入 UTF-8 文件再读即可，不是识别错误。

**结论**：5s 音频 CPU 转写约 1.5s，单句延迟预算乐观；模型常驻后首次加载时间不再计入链路。
