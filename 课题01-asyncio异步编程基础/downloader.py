import asyncio
import time


async def download_one(url: str, delay: float) -> tuple[str, float]:
    """
    模拟下载一个 URL。
    
    参数:
        url: 要下载的 URL
        delay: 下载耗时（秒），如果为 -1 表示下载失败
        
    返回:
        (url, 实际耗时)
    
    抛出:
        ValueError: 当 delay == -1 时
    """
    if delay == -1:
        raise ValueError(f"下载失败: {url}")
    start = time.monotonic()
    await asyncio.sleep(delay)
    end = time.monotonic()
    return (url, end - start)


async def run_downloads(urls: list[str], delays: list[float]) -> dict[str, float]:
    """
    并发下载多个 URL，返回按完成顺序排列的耗时字典。
    
    要求:
    1. 使用 asyncio.TaskGroup（Python 3.11+）或 asyncio.gather
    2. 如果某个下载失败（delay == -1），捕获异常，不影响其他下载
    3. 返回的字典按任务完成顺序排列（先完成的排前面）
    
    提示: 你可以用一个列表记录完成顺序
    """
    results = {}
    completed_order = []

    async def safe_download(url, delay):
        """包装 download_one，捕获异常"""
        try:
            result = await download_one(url, delay)
            results[url] = result[1]
            completed_order.append(url)
        except ValueError as e:
            print(e)

    async with asyncio.TaskGroup() as tg:
        for url, delay in zip(urls, delays):
            tg.create_task(safe_download(url, delay))

    ordered_results = {url: results[url] for url in completed_order}
    return ordered_results