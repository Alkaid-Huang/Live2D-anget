"""
课题04 验收测试：管线编排与配置系统

运行方式:
    cd 课题04-管线编排与配置系统
    python -m pytest tests/test_04.py -v

注意：需要将你的 pipeline.py 和 conf.yaml 放在本目录下（与 tests 文件夹同级）
      需要安装: pip install pyyaml pytest pytest-asyncio
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# 测试 1：配置加载
# ============================================================
def test_load_config():
    """测试 load_config 能正确读取 conf.yaml"""
    from pipeline import load_config

    config = load_config()
    assert config is not None, "配置不应为 None"
    assert "pipeline" in config, "配置应包含 'pipeline' 键"

    pipeline = config["pipeline"]
    assert "input" in pipeline, "配置应包含 input 阶段"
    assert "asr" in pipeline, "配置应包含 asr 阶段"
    assert "llm" in pipeline, "配置应包含 llm 阶段"


def test_load_config_values():
    """测试配置值正确读取"""
    from pipeline import load_config

    config = load_config()
    pipeline = config["pipeline"]

    assert pipeline["input"]["items"] == 5, f"input.items 应为 5，实际: {pipeline['input']['items']}"
    assert pipeline["llm"]["prefix"] == "Echo", f"llm.prefix 应为 Echo，实际: {pipeline['llm']['prefix']}"
    assert pipeline["queue_size"] == 10, f"queue_size 应为 10，实际: {pipeline['queue_size']}"


# ============================================================
# 测试 2：ServiceContext 创建
# ============================================================
def test_create_context():
    """测试 create_context 创建的 ServiceContext 包含 4 个 Queue"""
    import asyncio
    from pipeline import create_context, ServiceContext

    config = {
        "pipeline": {
            "queue_size": 5,
            "input": {"items": 3, "delay": 0.01},
            "asr": {"delay": 0.01},
            "llm": {"delay": 0.01, "prefix": "Test"},
        }
    }

    ctx = create_context(config)

    assert isinstance(ctx, ServiceContext), "ctx 应为 ServiceContext 实例"
    assert ctx.config == config, "ctx.config 应为传入的配置"
    assert ctx.input_queue is not None, "input_queue 不应为 None"
    assert ctx.asr_queue is not None, "asr_queue 不应为 None"
    assert ctx.llm_queue is not None, "llm_queue 不应为 None"
    assert ctx.output_queue is not None, "output_queue 不应为 None"


def test_create_context_queue_maxsize():
    """测试队列的 maxsize 正确设置"""
    from pipeline import create_context

    config = {"pipeline": {"queue_size": 3}}
    ctx = create_context(config)

    assert ctx.input_queue.maxsize == 3, f"input_queue.maxsize 应为 3，实际: {ctx.input_queue.maxsize}"
    assert ctx.asr_queue.maxsize == 3, f"asr_queue.maxsize 应为 3，实际: {ctx.asr_queue.maxsize}"


# ============================================================
# 测试 3：管线运行（5 条数据）
# ============================================================
@pytest.mark.asyncio
async def test_pipeline_5_items():
    """测试默认配置（5 条）管线运行"""
    from pipeline import run_pipeline

    config = {
        "pipeline": {
            "queue_size": 10,
            "input": {"items": 5, "delay": 0.01},
            "asr": {"delay": 0.01},
            "llm": {"delay": 0.01, "prefix": "Echo"},
            "output": {"delay": 0.01},
        }
    }

    results = await run_pipeline(config)

    assert len(results) == 5, f"应输出 5 条结果，实际: {len(results)}"
    assert "Echo" in results[0], f"回复应包含 'Echo' 前缀，实际: {results[0]}"
    assert "文字0" in results[0], f"回复应包含 '文字0'，实际: {results[0]}"
    assert "文字4" in results[4], f"最后一条应包含 '文字4'，实际: {results[4]}"


# ============================================================
# 测试 4：配置驱动——修改 items 数量
# ============================================================
@pytest.mark.asyncio
async def test_pipeline_3_items():
    """测试修改 items 从 5 改成 3，输出结果变为 3 条"""
    from pipeline import run_pipeline

    config = {
        "pipeline": {
            "queue_size": 10,
            "input": {"items": 3, "delay": 0.01},
            "asr": {"delay": 0.01},
            "llm": {"delay": 0.01, "prefix": "Echo"},
            "output": {"delay": 0.01},
        }
    }

    results = await run_pipeline(config)

    assert len(results) == 3, f"应输出 3 条结果，实际: {len(results)}"


# ============================================================
# 测试 5：配置驱动——修改 prefix
# ============================================================
@pytest.mark.asyncio
async def test_pipeline_custom_prefix():
    """测试修改 prefix 从 'Echo' 改成 'AI'"""
    from pipeline import run_pipeline

    config = {
        "pipeline": {
            "queue_size": 10,
            "input": {"items": 2, "delay": 0.01},
            "asr": {"delay": 0.01},
            "llm": {"delay": 0.01, "prefix": "AI"},
            "output": {"delay": 0.01},
        }
    }

    results = await run_pipeline(config)

    assert len(results) == 2, f"应输出 2 条结果，实际: {len(results)}"
    assert "AI" in results[0], f"回复应包含 'AI' 前缀，实际: {results[0]}"
    assert "Echo" not in results[0], f"回复不应包含 'Echo'，实际: {results[0]}"


# ============================================================
# 测试 6：管线不卡死（哨兵值正确传递）
# ============================================================
@pytest.mark.asyncio
async def test_pipeline_terminates():
    """测试管线能正常结束，不卡死"""
    import asyncio
    from pipeline import run_pipeline

    config = {
        "pipeline": {
            "queue_size": 10,
            "input": {"items": 10, "delay": 0.001},
            "asr": {"delay": 0.001},
            "llm": {"delay": 0.001, "prefix": "Echo"},
            "output": {"delay": 0.001},
        }
    }

    try:
        results = await asyncio.wait_for(run_pipeline(config), timeout=10)
        assert len(results) == 10, f"应输出 10 条结果，实际: {len(results)}"
    except asyncio.TimeoutError:
        pytest.fail("管线在 10 秒内未完成，可能哨兵值未正确传递，管线卡死")


# ============================================================
# 测试 7：从 conf.yaml 文件加载并运行
# ============================================================
@pytest.mark.asyncio
async def test_pipeline_from_yaml():
    """测试从 conf.yaml 文件加载配置并运行"""
    from pipeline import load_config, run_pipeline

    config = load_config()
    results = await run_pipeline(config)

    expected_items = config["pipeline"]["input"]["items"]
    expected_prefix = config["pipeline"]["llm"]["prefix"]

    assert len(results) == expected_items, \
        f"应输出 {expected_items} 条结果，实际: {len(results)}"
    assert expected_prefix in results[0], \
        f"回复应包含 '{expected_prefix}'，实际: {results[0]}"


# ============================================================
# 测试 8：数据流转顺序正确
# ============================================================
@pytest.mark.asyncio
async def test_pipeline_order():
    """测试数据流转顺序正确：音频0→文字0→回复0，音频1→文字1→回复1..."""
    from pipeline import run_pipeline

    config = {
        "pipeline": {
            "queue_size": 10,
            "input": {"items": 4, "delay": 0.01},
            "asr": {"delay": 0.01},
            "llm": {"delay": 0.01, "prefix": "Echo"},
            "output": {"delay": 0.01},
        }
    }

    results = await run_pipeline(config)

    assert len(results) == 4, f"应输出 4 条结果，实际: {len(results)}"

    for i in range(4):
        assert f"文字{i}" in results[i], \
            f"第 {i} 条结果应包含 '文字{i}'，实际: {results[i]}"


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    sys.exit(exit_code)
