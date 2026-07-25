"""
Echo 模拟管线 —— 配置驱动的 4 阶段异步流水线

运行方式:
    python pipeline.py

测试方式:
    python -m pytest tests/test_04.py -v
"""

import asyncio
import os
import yaml
from dataclasses import dataclass


# ═══════════════════════════════════════════════════════════════
# ServiceContext —— 集中管理所有服务实例和队列（⚡设计2）
# ═══════════════════════════════════════════════════════════════
# 这就是 Open-LLM-VTuber ServiceContext 的简化版。
# 它是一个纯数据容器，持有配置和所有队列的引用。
# 所有阶段通过 ctx 访问队列，不需要全局变量。

@dataclass
class ServiceContext:
    """集中管理配置和队列 —— 分诊台"""
    config: dict = None
    input_queue: asyncio.Queue = None
    asr_queue: asyncio.Queue = None
    llm_queue: asyncio.Queue = None
    output_queue: asyncio.Queue = None


def load_config(config_path: str = None) -> dict:
    """从 YAML 文件加载配置（⚡设计1：配置驱动）"""
    if config_path is None:
        # 锚定到脚本所在目录，避免工作目录影响路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "conf.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_context(config: dict) -> ServiceContext:
    """根据配置创建 ServiceContext，初始化所有队列"""
    maxsize = config.get("pipeline", {}).get("queue_size", 10)
    return ServiceContext(
        config=config,
        input_queue=asyncio.Queue(maxsize=maxsize),
        asr_queue=asyncio.Queue(maxsize=maxsize),
        llm_queue=asyncio.Queue(maxsize=maxsize),
        output_queue=asyncio.Queue(maxsize=maxsize),
    )


# ═══════════════════════════════════════════════════════════════
# 阶段1：输入阶段 —— 产生模拟音频数据
# ═══════════════════════════════════════════════════════════════

async def input_stage(ctx: ServiceContext):
    """产生模拟音频数据，放入 input_queue"""
    items = ctx.config.get("pipeline", {}).get("input", {}).get("items", 5)
    delay = ctx.config.get("pipeline", {}).get("input", {}).get("delay", 0.1)

    for i in range(items):
        await asyncio.sleep(delay)  # 模拟采集音频的耗时
        # ═══════════════════════════════════════════════════════════
        # TODO 1: 把模拟音频数据放入 input_queue
        # ═══════════════════════════════════════════════════════════
        # 方法: await ctx.input_queue.put(item)
        # 作用: 往输入队列放一个数据，队列满了会自动等待
        # 参数: item —— 任意对象，这里放一个字典 {"audio": f"音频{i}"}
        # 返回值: None
        # 提示: 照着上面的注释写一行代码，替换下面的 pass
        await ctx.input_queue.put({"audio": f"音频{i}"})
        print(f"[输入] 产生: 音频{i}")

    # ═══════════════════════════════════════════════════════════
    # TODO 2: 放入哨兵值 None，通知下一个阶段"数据发完了"
    # ═══════════════════════════════════════════════════════════
    # 作用: None 是约定好的"结束信号"，ASR 阶段收到 None 就知道没有更多数据了
    # 提示: 和 TODO 1 类似，但放的是 None 而不是字典
    await ctx.input_queue.put(None)
    print("[输入] 所有数据已发送，发送结束信号")


# ═══════════════════════════════════════════════════════════════
# 阶段2：ASR阶段 —— 把"音频"转成"文字"
# ═══════════════════════════════════════════════════════════════

async def asr_stage(ctx: ServiceContext):
    """从 input_queue 取音频，转成文字，放入 asr_queue"""
    delay = ctx.config.get("pipeline", {}).get("asr", {}).get("delay", 0.2)

    while True:
        # ═══════════════════════════════════════════════════════════
        # TODO 3: 从 input_queue 取出数据
        # ═══════════════════════════════════════════════════════════
        # 方法: item = await ctx.input_queue.get()
        # 作用: 从输入队列取一个数据，队列空了会自动等待
        # 返回值: 队列中的数据（字典或 None）
        # 提示: 照着注释写一行代码，替换下面的 pass
        input_data = await ctx.input_queue.get()
        
        # ═══════════════════════════════════════════════════════════
        # TODO 4: 检查是否收到哨兵值 None
        # ═══════════════════════════════════════════════════════════
        # 作用: None 表示上一个阶段的数据已全部发完，需要退出循环
        # 退出前: 把 None 传给下一个阶段（让 LLM 阶段也知道该结束了）
        # 提示: 用 if 判断 item is None，如果是就 put(None) 到下一个队列并 break
        if input_data is None:
            await ctx.asr_queue.put(None)
            break



        # ═══════════════════════════════════════════════════════════
        # TODO 5: 标记任务完成 + 模拟 ASR 处理 + 放入下一个队列
        # ═══════════════════════════════════════════════════════════
        # 步骤1: ctx.input_queue.task_done()  —— 告诉队列"这个数据处理完了"
        # 步骤2: await asyncio.sleep(delay)   —— 模拟 ASR 转写耗时
        # 步骤3: 从 item["audio"] 提取音频名，构造文字: {"text": f"文字{N}"}
        #        提示: 音频名是 "音频N"，提取数字 N 可以用 item["audio"].replace("音频", "")
        # 步骤4: await ctx.asr_queue.put(text_data)  —— 放入下一个队列
        # 步骤5: print(f"[ASR] {item['audio']} → 文字{N}")
        ctx.input_queue.task_done()
        await asyncio.sleep(delay)
        text_data = {"text":f"文字{input_data['audio'].replace('音频', '')}"}
        await ctx.asr_queue.put(text_data)
        print(f"[ASR] {input_data['audio']} → 文字{input_data['audio'].replace('音频', '')}")





# ═══════════════════════════════════════════════════════════════
# 阶段3：LLM阶段 —— 把"文字"转成"回复"
# ═══════════════════════════════════════════════════════════════

async def llm_stage(ctx: ServiceContext):
    """从 asr_queue 取文字，生成回复，放入 llm_queue"""
    delay = ctx.config.get("pipeline", {}).get("llm", {}).get("delay", 0.3)
    prefix = ctx.config.get("pipeline", {}).get("llm", {}).get("prefix", "Echo")

    while True:
        # ═══════════════════════════════════════════════════════════
        # TODO 6: 从 asr_queue 取出数据，处理哨兵值
        # ═══════════════════════════════════════════════════════════
        # 和 TODO 3、TODO 4 一样的模式，只是队列换成了 asr_queue：
        # 1. item = await ctx.asr_queue.get()
        # 2. if item is None: await ctx.llm_queue.put(None); break
        # 3. ctx.asr_queue.task_done()
        # 提示: 把 TODO 3-5 的模式套过来，改队列名即可
        asr_data =await ctx.asr_queue.get()

        if asr_data is None:
            await ctx.llm_queue.put(None)
            break

        ctx.asr_queue.task_done()



        # ═══════════════════════════════════════════════════════════
        # TODO 7: 模拟 LLM 生成回复，放入 llm_queue
        # ═══════════════════════════════════════════════════════════
        # 步骤1: await asyncio.sleep(delay)  —— 模拟 LLM 思考耗时
        # 步骤2: 从 item["text"] 提取文字名，构造回复: {"reply": f"{prefix}: 收到文字{N}"}
        #        提示: prefix 从配置读取，文字名是 "文字N"，提取数字用 .replace("文字", "")
        # 步骤3: await ctx.llm_queue.put(reply_data)
        # 步骤4: print(f"[LLM] {item['text']} → {prefix}: 收到文字{N}")
        await asyncio.sleep(delay)
        llm_data = {"reply":f"{prefix}:收到文字{asr_data['text'].replace('文字', '')}"}
        await ctx.llm_queue.put(llm_data)
        print(f"[LLM] {asr_data['text']} → {prefix}: 收到文字{asr_data['text'].replace('文字', '')}")


# ═══════════════════════════════════════════════════════════════
# 阶段4：输出阶段 —— 接收并打印结果
# ═══════════════════════════════════════════════════════════════

async def output_stage(ctx: ServiceContext) -> list:
    """从 llm_queue 取回复，打印并收集结果"""
    results = []

    while True:
        # ═══════════════════════════════════════════════════════════
        # TODO 8: 从 llm_queue 取出数据，处理哨兵值，收集结果
        # ═══════════════════════════════════════════════════════════
        # 和前面的模式一样，只是队列换成了 llm_queue：
        # 1. item = await ctx.llm_queue.get()
        # 2. if item is None: ctx.llm_queue.task_done(); break
        # 3. ctx.llm_queue.task_done()
        # 4. results.append(item["reply"])  —— 收集结果
        # 5. print(f"[输出] {item['reply']}")
        # 提示: 这是最后一个阶段，收到 None 时只需 task_done + break，不需要再传 None
        llm_data = await ctx.llm_queue.get()

        if llm_data is None:
            ctx.llm_queue.task_done()
            break

        results.append(llm_data["reply"])
        print(f"[输出] {llm_data['reply']}")
    
    return results


# ═══════════════════════════════════════════════════════════════
# 管线启动器 —— 用 TaskGroup 管理所有阶段
# ═══════════════════════════════════════════════════════════════

async def run_pipeline(config: dict = None) -> list:
    """启动 4 阶段管线，返回输出阶段收集的结果"""
    if config is None:
        config = load_config()

    ctx = create_context(config)
    results = []

    async with asyncio.TaskGroup() as tg:
        # ═══════════════════════════════════════════════════════════
        # TODO 9: 用 TaskGroup 创建 4 个阶段任务
        # ═══════════════════════════════════════════════════════════
        # 方法: tg.create_task(coro)
        # 作用: 在任务组中创建一个协程任务，所有任务并行运行
        # 参数: coro —— 协程对象，如 input_stage(ctx)
        # 返回值: Task 对象
        # 提示: 创建前 3 个阶段直接 tg.create_task(阶段名(ctx))
        #       但 output_stage 返回结果，需要把它的 Task 存到变量 output_task
        #       这样后面才能用 output_task.result() 拿到返回值
        tg.create_task(input_stage(ctx))
        tg.create_task(asr_stage(ctx))
        tg.create_task(llm_stage(ctx))
        output_task = tg.create_task(output_stage(ctx))

    # TaskGroup 退出后所有任务都完成了
    # TODO 10: 从 output_task 获取结果
    # 提示: results = output_task.result()
    results = output_task.result()
    print(f"\n[管线] 完成，共输出 {len(results)} 条结果")
    return results


if __name__ == "__main__":
    results = asyncio.run(run_pipeline())
    print("\n=== 最终结果 ===")
    for r in results:
        print(f"  {r}")