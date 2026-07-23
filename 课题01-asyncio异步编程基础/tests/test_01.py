"""
课题01 验收测试：asyncio 异步编程基础

运行方式：
    cd 课题01-asyncio异步编程基础
    python -m pytest tests/test_01.py -v

或者直接运行：
    python tests/test_01.py

注意：你需要将你的作答代码保存为 downloader.py 放在本目录下（与 tests 文件夹同级）
"""

import sys
import os
import time
import asyncio
import pytest

# 将上级目录加入 path，以导入你的 downloader 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# 测试 1：基本功能 —— 单文件下载
# ============================================================
def test_single_download():
    """测试下载单个 URL 是否正常工作"""
    from downloader import download_one

    async def run():
        url, elapsed = await download_one("http://test.com", 0.1)
        assert url == "http://test.com"
        assert 0.05 <= elapsed <= 0.2, f"耗时应在 0.1s 左右，实际 {elapsed:.3f}s"

    asyncio.run(run())


# ============================================================
# 测试 2：异常处理 —— delay=-1 时抛出 ValueError
# ============================================================
def test_download_failure():
    """测试 delay=-1 时抛出 ValueError"""
    from downloader import download_one

    async def run():
        with pytest.raises(ValueError, match="下载失败"):
            await download_one("http://fail.com", -1)

    asyncio.run(run())


# ============================================================
# 测试 3：并发执行 —— 总耗时验证
# ============================================================
def test_concurrent_execution():
    """测试并发执行：总耗时应该接近最长的单个任务（~2s），而非串行总和（~3.5s）"""
    from downloader import run_downloads

    urls = ["http://a.com", "http://b.com", "http://c.com", "http://d.com"]
    delays = [2.0, 0.5, 1.0, 1.5]

    async def run():
        start = time.monotonic()
        result = await run_downloads(urls, delays)
        elapsed = time.monotonic() - start

        # 串行需要 2.0+0.5+1.0+1.5 = 5.0s
        # 并发只需要 max(2.0, 0.5, 1.0, 1.5) ≈ 2.0s + 开销
        assert elapsed < 2.5, (
            f"并发执行应在 2.5s 内完成，实际 {elapsed:.2f}s。"
            f"如果结果是 ~5s，说明你是串行执行的，请检查是否用了 asyncio.create_task 或 TaskGroup。"
        )
        assert len(result) == 4, f"应该有 4 个结果，实际 {len(result)}"

    asyncio.run(run())


# ============================================================
# 测试 4：异常隔离 —— 一个失败不影响其他
# ============================================================
def test_exception_isolation():
    """测试异常隔离：失败的下载不影响成功的下载"""
    from downloader import run_downloads

    urls = ["http://good1.com", "http://bad.com", "http://good2.com"]
    delays = [0.5, -1, 0.3]

    async def run():
        result = await run_downloads(urls, delays)
        assert len(result) == 2, f"应该有 2 个成功下载，实际 {len(result)}"
        assert "http://good1.com" in result
        assert "http://good2.com" in result
        assert "http://bad.com" not in result

    asyncio.run(run())


# ============================================================
# 测试 5：完成顺序 —— 先完成的排前面
# ============================================================
def test_completion_order():
    """测试返回字典按完成顺序排列"""
    from downloader import run_downloads

    urls = ["http://slow.com", "http://fast.com", "http://mid.com"]
    delays = [1.0, 0.1, 0.5]

    async def run():
        result = await run_downloads(urls, delays)
        keys = list(result.keys())

        assert keys[0] == "http://fast.com", (
            f"最快的应该第一个出现，实际: {keys[0]}"
        )
        assert keys[1] == "http://mid.com", (
            f"中速的应该第二个出现，实际: {keys[1]}"
        )
        assert keys[2] == "http://slow.com", (
            f"最慢的应该最后出现，实际: {keys[2]}"
        )

    asyncio.run(run())


# ============================================================
# 测试 6：全部失败的情况
# ============================================================
def test_all_failures():
    """测试全部下载失败时返回空字典"""
    from downloader import run_downloads

    urls = ["http://fail1.com", "http://fail2.com"]
    delays = [-1, -1]

    async def run():
        result = await run_downloads(urls, delays)
        assert result == {}, f"全部失败时应该返回空字典，实际: {result}"

    asyncio.run(run())


# ============================================================
# 测试 7：空列表
# ============================================================
def test_empty_input():
    """测试空列表返回空字典"""
    from downloader import run_downloads

    async def run():
        result = await run_downloads([], [])
        assert result == {}

    asyncio.run(run())


# ============================================================
# 测试 8：大量并发 —— 压力测试
# ============================================================
def test_high_concurrency():
    """测试大量并发任务（20 个），验证不会崩溃"""
    from downloader import run_downloads

    urls = [f"http://site{i}.com" for i in range(20)]
    delays = [0.01 * (i % 5 + 1) for i in range(20)]  # 0.01~0.05s

    async def run():
        start = time.monotonic()
        result = await run_downloads(urls, delays)
        elapsed = time.monotonic() - start

        assert len(result) == 20, f"应该有 20 个结果，实际 {len(result)}"
        # 并发执行应该在 0.1s 内（最长 0.05s + 开销）
        assert elapsed < 0.3, f"20 个并发任务应在 0.3s 内完成，实际 {elapsed:.2f}s"

    asyncio.run(run())


# ============================================================
# 直接运行入口
# ============================================================
if __name__ == "__main__":
    # 用 pytest 运行所有测试
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    sys.exit(exit_code)