"""
把学习仓库里的产品代码导出为独立的公开项目仓库。

用法（在仓库根目录执行）：
    .venv\\Scripts\\python.exe tools\\export_public_repo.py [目标目录]

默认目标目录：D:\\01_Work\\00_Todo\\echo-voice-assistant

脚本做三件事：
1. 只复制产品文件（不含课题目录、录音、模型、输出）
2. 做"产品化清理"：重命名课号测试文件、去掉过程标记、清理课号文案
3. 断言每处清理都精确命中，并检查是否还有残留
"""
import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(__file__).resolve().parent.parent
DEFAULT_DST = Path(r"D:\01_Work\00_Todo\echo-voice-assistant")
_FLAGS = {a for a in sys.argv[1:] if a.startswith("--")}
_POSITIONAL = [a for a in sys.argv[1:] if not a.startswith("--")]
DST = Path(_POSITIONAL[0]) if _POSITIONAL else DEFAULT_DST

# ── 要复制的文件 ──────────────────────────────────────────
FILES = [
    "main.py",
    "conf.yaml",
    "requirements.txt",
    "README.md",
    ".gitignore",
    ".env.example",
]
DIRS = ["src", "tests", "benchmarks"]
DOCS = ["需求文档.md", "架构设计.md", "接口文档.md", "真实Bug笔记.md", "理解补课清单.md"]

# ── 重命名（产品仓库里不出现课号） ─────────────────────────
RENAMES = {
    "tests/test_06_4.py": "tests/test_asr.py",
    "tests/test_06_2.py": "tests/test_vad.py",
}

# ── 精确文案替换：(文件, 原文, 新文) ───────────────────────
REPLACEMENTS = [
    (
        "conf.yaml",
        "db_threshold: -20.0       # float32 音频用负数（见课题06.1 坑7）",
        "db_threshold: -20.0       # float32 音频的能量值为负数",
    ),
    ("src/echo/asr/asr_factory.py", "改进点（相对 06.2 的 vad_factory）：", "设计说明："),
    (
        "src/echo/vad/silero_engine.py",
        "本课改动（相对 06.1）：加 @register_vad 装饰器，让工厂能创建它",
        "用 @register_vad 装饰器注册到工厂，使 create_vad 能按配置创建它",
    ),
    ("src/echo/vad/silero_engine.py", "  # 06.2 新增：导入注册装饰器", "  # 注册装饰器"),
    ("src/echo/vad/silero_engine.py", "  # 06.2 新增：注册到工厂", "  # 注册到工厂"),
    (
        "src/echo/service_context.py",
        "1. 简化版——只管 VAD + ASR（06.4 新增）",
        "1. 统一管理 VAD / ASR / LLM / TTS 四个组件",
    ),
    ("src/echo/service_context.py", "  # 06.4 新增", ""),
    ("src/echo/service_context.py", "  # 冲刺期新增", ""),
    ("tests/test_asr.py", "课题06.4 验收测试", "ASR 验收测试"),
    ("tests/test_asr.py", r"tests\test_06_4.py", "tests/test_asr.py"),
    ("tests/test_vad.py", "课题06.2 验收测试", "VAD 验收测试"),
    ("tests/test_vad.py", "tests/test_06_2.py", "tests/test_vad.py"),
    (
        "tests/test_llm_tts_pipeline.py",
        "冲刺期新增测试：LLM / TTS / 记忆 / 对话管线",
        "LLM / TTS / 记忆 / 对话管线测试",
    ),
    (
        "docs/理解补课清单.md",
        "冲刺期部分代码由 AI 助手生成，清单如下。",
        "本项目部分代码由 AI 助手生成，清单如下。",
    ),
    ("docs/理解补课清单.md", "# 理解补课清单（AI 代写模块）", "# 理解补课清单"),
    ("docs/真实Bug笔记.md", "**发现时间**：2026-09-10（冲刺第 4 天）", "**发现时间**：2026-09-10"),
]

MARKER = "AI 代写"
LEFTOVER_PATTERN = re.compile(r"课题|冲刺|06\.4|06\.2|06\.1")

LICENSE_TEXT = """MIT License

Copyright (c) 2026 Alkaid Huang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def guard_destination() -> None:
    """目标目录必须是我们约定的导出位置，避免误删"""
    if DST.name != "echo-voice-assistant" or DST.parent != Path(r"D:\01_Work\00_Todo"):
        raise SystemExit(f"目标目录不符合约定，拒绝操作：{DST}")


def copy_files() -> None:
    for name in FILES:
        shutil.copy2(SRC / name, DST / name)
    for name in DIRS:
        shutil.copytree(
            SRC / name,
            DST / name,
            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "test_06_*.py"),
        )
    (DST / "docs").mkdir(parents=True, exist_ok=True)
    for name in DOCS:
        shutil.copy2(SRC / "docs" / name, DST / "docs" / name)


def copy_files_over() -> None:
    """增量更新：覆盖目标仓库里的产品文件，保留 .git 与提交历史"""
    for name in FILES:
        shutil.copy2(SRC / name, DST / name)
    for name in DIRS:
        shutil.copytree(
            SRC / name,
            DST / name,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "test_06_*.py"),
        )
    (DST / "docs").mkdir(parents=True, exist_ok=True)
    for name in DOCS:
        shutil.copy2(SRC / "docs" / name, DST / "docs" / name)


def strip_markers(text: str) -> str:
    """删掉 '# ⚠️ AI 代写…' 行（含可能的第二行说明）"""
    out = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if MARKER in lines[i]:
            if i + 1 < len(lines) and lines[i + 1].lstrip().startswith("#    ——"):
                i += 2
            else:
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out) + "\n"


def rename_tests() -> None:
    """把带课号的测试文件名改成产品化命名"""
    for old, new in RENAMES.items():
        if (DST / old).exists():
            (DST / old).rename(DST / new)


def apply_text_cleanup(strict: bool = True) -> None:
    """strict=True 用于全新导出（漏了要报错）；False 用于增量更新（已清理过的就跳过）"""
    for rel, old, new in REPLACEMENTS:
        path = DST / rel
        text = path.read_text(encoding="utf-8")
        if old not in text:
            if strict:
                raise SystemExit(f"替换未命中（请检查原文）：{rel} → {old[:40]}")
            continue
        path.write_text(text.replace(old, new), encoding="utf-8")

    # 清理 Python 文件里的过程标记
    for path in DST.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if MARKER in text:
            path.write_text(strip_markers(text), encoding="utf-8")

    (DST / "LICENSE").write_text(LICENSE_TEXT, encoding="utf-8")


def check_leftovers() -> None:
    leftovers = []
    for path in DST.rglob("*"):
        if path.suffix not in {".py", ".md", ".yaml", ".txt"}:
            continue
        for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if LEFTOVER_PATTERN.search(line) or MARKER in line:
                leftovers.append(f"{path.relative_to(DST)}:{no}: {line.strip()}")
    if leftovers:
        print("[!] 仍有残留，请检查：")
        for item in leftovers:
            print("   " + item)
    else:
        print("[OK] 无课号/过程标记残留")


def main() -> None:
    guard_destination()
    args = _FLAGS
    update_mode = "--update" in args

    if update_mode:
        if not (DST / ".git").exists():
            raise SystemExit(f"更新模式要求目标已是 git 仓库：{DST}")
        copy_files_over()
        rename_tests()
        apply_text_cleanup(strict=False)
    else:
        if (DST / ".git").exists() and "--force" not in args:
            raise SystemExit(
                f"目标已是 git 仓库，为避免删掉历史，拒绝全新导出：{DST}\n"
                f"如确认要重建，请加 --force；只想同步内容，请用 --update"
            )
        if DST.exists():
            shutil.rmtree(DST)
        DST.mkdir(parents=True)
        copy_files()
        rename_tests()
        apply_text_cleanup(strict=True)
    check_leftovers()
    print(f"[OK] 已{'更新' if update_mode else '导出'}到 {DST}")


if __name__ == "__main__":
    main()
