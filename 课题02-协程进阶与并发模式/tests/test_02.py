"""
课题02 验收测试：协程进阶与并发模式

运行方式：
    cd 课题02-协程进阶与并发模式
    python -m pytest tests/test_02.py -v

注意：你需要将你的作答代码保存为 log_system.py 放在本目录下（与 tests 文件夹同级）
"""

import sys
import os
import time
import asyncio
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# 测试 1：基本功能 —— 生产者产生日志
# ============================================================
def test_producer_basic():
    """测试生产者能正确产生日志"""
    from log_system import log_producer

    async def run():
        queue = asyncio.Queue(maxsize=10)
        await log_producer("测试模块", queue, 3)
        assert queue.qsize() == 3, f"应该有 3 条日志，实际 {queue.qsize()}"
        # 检查日志格式
        log = await queue.get()
        assert "[测试模块]" in log, f"日志应包含模块名，实际: {log}"
        assert "日志-" in log, f"日志应包含序号，实际: {log}"

    asyncio.run(run())


# ============================================================
# 测试 2：消费者处理所有日志
# ============================================================
def test_consumer_processes_all():
    """测试消费者处理完所有日志后才退出"""
    from log_system import log_producer, log_consumer

    async def run():
        queue = asyncio.Queue(maxsize=10)
        stop_event = asyncio.Event()

        # 先生产一些日志
        await log_producer("A", queue, 3)
        await log_producer("B", queue, 2)

        # 启动消费者
        consumer_task = asyncio.create_task(log_consumer(queue, stop_event))

        # 等待队列清空
        await queue.join()
        # 发停止信号
        stop_event.set()
        await consumer_task

        # 队列应该为空
        assert queue.qsize() == 0, f"队列应该为空，实际 {queue.qsize()}"

    asyncio.run(run())


# ============================================================
# 测试 3：并发执行 —— 总耗时验证
# ============================================================
def test_concurrent_execution():
    """测试 3 个生产者并发运行，总耗时合理"""
    from log_system import run_log_system

    async def run():
        start = time.monotonic()
        await run_log_system()
        elapsed = time.monotonic() - start

        # 最长生产者 5 条 × 1s = 5s，加上队列处理时间，应该在 8s 内
        assert elapsed < 8.0, (
            f"并发执行应在 8 秒内完成（最长生产者 5 条 × 1s），"
            f"实际 {elapsed:.1f} 秒。如果是 ~12 秒说明是串行执行。"
        )

    asyncio.run(run())


# ============================================================
# 测试 4：队列背压 —— 不超过 maxsize
# ============================================================
def test_backpressure():
    """测试队列大小不超过 maxsize"""
    from log_system import log_producer

    async def run():
        queue = asyncio.Queue(maxsize=3)

        # 快速生产者 + 满队列 = 背压
        async def fast_producer():
            for i in range(10):
                await queue.put(f"日志-{i}")
                # 不 sleep，生产者会很快填满队列

        async def slow_consumer():
            for _ in range(10):
                await asyncio.sleep(0.1)
                await queue.get()
                queue.task_done()

        prod = asyncio.create_task(fast_producer())
        cons = asyncio.create_task(slow_consumer())

        # 监控队列大小
        max_seen = 0
        async def monitor():
            nonlocal max_seen
            for _ in range(50):
                max_seen = max(max_seen, queue.qsize())
                await asyncio.sleep(0.02)

        mon = asyncio.create_task(monitor())
        await asyncio.gather(prod, cons)
        mon.cancel()

        assert max_seen <= 3, (
            f"队列大小不应超过 maxsize=3，实际观察到的最大值: {max_seen}"
        )

    asyncio.run(run())


# ============================================================
# 测试 5：消费者用 wait_for 不会永久阻塞
# ============================================================
def test_consumer_does_not_block_forever():
    """测试消费者在队列为空时不会永久阻塞"""
    from log_system import log_consumer

    async def run():
        queue = asyncio.Queue()
        stop_event = asyncio.Event()

        consumer_task = asyncio.create_task(log_consumer(queue, stop_event))

        # 队列一直为空，但 stop_event 还没设置
        # 消费者应该用 wait_for 定期检查，不会永久阻塞
        await asyncio.sleep(1.0)
        stop_event.set()

        try:
            await asyncio.wait_for(consumer_task, timeout=2.0)
        except asyncio.TimeoutError:
            consumer_task.cancel()
            pytest.fail("消费者在空队列上永久阻塞了，请检查是否用了 wait_for 超时")

    asyncio.run(run())


# ============================================================
# 测试 6：空队列立即停止
# ============================================================
def test_stop_on_empty_queue():
    """测试空队列 + 停止信号时消费者立即退出"""
    from log_system import log_consumer

    async def run():
        queue = asyncio.Queue()
        stop_event = asyncio.Event()

        # 队列为空，立即设置停止信号
        stop_event.set()
        consumer_task = asyncio.create_task(log_consumer(queue, stop_event))

        try:
            await asyncio.wait_for(consumer_task, timeout=2.0)
        except asyncio.TimeoutError:
            consumer_task.cancel()
            pytest.fail("消费者应该在空队列+停止信号时立即退出")

    asyncio.run(run())


# ============================================================
# 测试 7：日志格式正确
# ============================================================
def test_log_format():
    """测试日志格式包含时间戳、模块名、序号"""
    from log_system import log_producer

    async def run():
        queue = asyncio.Queue(maxsize=10)
        await log_producer("语音识别", queue, 1)
        log = await queue.get()

        # 格式: "[时间戳] [模块名] 日志-{序号}"
        assert "[" in log, f"日志应包含方括号，实际: {log}"
        assert "语音识别" in log, f"日志应包含模块名，实际: {log}"
        assert "日志-" in log, f"日志应包含'日志-'前缀，实际: {log}"

    asyncio.run(run())


# ============================================================
# 测试 8：完整流程 —— 集成测试
# ============================================================
def test_full_pipeline():
    """完整集成测试：3 个生产者 + 1 个消费者，全部正常完成"""
    from log_system import run_log_system

    async def run():
        await run_log_system()
        # 不抛异常就算通过

    asyncio.run(run())


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    sys.exit(exit_code)