import asyncio
import time


async def log_producer(name: str, queue: asyncio.Queue, count: int):
    """
    模拟一个模块不断产生日志。

    参数:
        name: 模块名（如 "语音识别"）
        queue: 共享的日志队列
        count: 要产生的日志条数
    """
    for i in range(count):
        log_sys = f"[{time.strftime('%H:%M:%S')}] [{name}] 日志-{i+1}"
        await queue.put(log_sys)
        print(f"生产 [{name}]: {log_sys}")
        await asyncio.sleep(1)


async def log_consumer(queue: asyncio.Queue, stop_event: asyncio.Event):
    """
    消费者：不断从队列取日志并处理，直到收到停止信号且队列为空。

    参数:
        queue: 共享的日志队列
        stop_event: 停止信号
    """
    processed = 0
    while True:
        if stop_event.is_set() and queue.empty():
            break
        try:
            log_sys = await asyncio.wait_for(queue.get(), timeout=0.5)
            processed += 1
            print(f"消费 [{processed}]: {log_sys}")
            await asyncio.sleep(0.3)
            queue.task_done()
        except asyncio.TimeoutError:
            continue

    print(f"\n消费者共处理了 {processed} 条日志")


async def run_log_system():
    """
    主函数：启动 3 个生产者 + 1 个消费者，协调启停。
    """
    queue = asyncio.Queue(maxsize=10)
    stop_event = asyncio.Event()

    print("=" * 50)
    print("日志系统启动")
    print("=" * 50)

    consumer_task = asyncio.create_task(log_consumer(queue, stop_event))

    await asyncio.gather(
        log_producer("语音识别", queue, 5),
        log_producer("LLM", queue, 3),
        log_producer("TTS", queue, 4)
    )

    print("\n所有生产者已完成")

    print("等待队列清空...")
    await queue.join()

    stop_event.set()

    await consumer_task

    print("\n日志系统已关闭")