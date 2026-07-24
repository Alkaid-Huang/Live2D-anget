"""
Echo 消息协议服务器

启动方式:
    uvicorn server:app --reload --port 8000

前端测试: 打开 client.html
"""

import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


# ═══════════════════════════════════════════════════════════════
# TODO 1: 注册 WebSocket 端点
# ═══════════════════════════════════════════════════════════════
# 方法: @app.websocket("/ws")
# 作用: 这是一个装饰器（decorator），放在函数定义上方，
#       告诉 FastAPI "当客户端连接 ws://xxx/ws 时，调用下面这个函数"
# 用法: 把下面这行注释去掉，放在 async def 的上一行
@app.websocket("/ws")
async def handle_ws(websocket: WebSocket):
    # websocket 参数: FastAPI 自动传入的 WebSocket 连接对象，
    # 你之后所有操作（接收、发送、关闭）都通过它完成

    # ═══════════════════════════════════════════════════════════
    # TODO 2: 接受连接
    # ═══════════════════════════════════════════════════════════
    # 方法: await websocket.accept()
    # 作用: 告诉客户端"我同意建立连接"。必须先调用这个方法，
    #       否则 receive_text() / send_text() 都会报 RuntimeError
    # 用法: 把下面这行注释去掉
    await websocket.accept()

    # ═══════════════════════════════════════════════════════════
    # TODO 3: 打印连接日志
    # ═══════════════════════════════════════════════════════════
    # 方法: print("客户端已连接")
    # 作用: 在服务端控制台输出一行日志，方便你知道有人连上了
    # 用法: 写一行 print 即可
    print("客户端已连接")
    try:
        while True:
            # ═══════════════════════════════════════════════════
            # TODO 4: 接收客户端消息
            # ═══════════════════════════════════════════════════
            # 方法: raw = await websocket.receive_text()
            # 作用: 等待客户端发来一条文本消息，收到后返回字符串。
            #       如果客户端一直不发，这里会一直等着（不占 CPU）
            # 返回值: str 类型，就是客户端发来的原始字符串
            # 用法: raw = await websocket.receive_text()
            raw = await websocket.receive_text()

            try:
                # ═══════════════════════════════════════════════
                # TODO 5: 解析 JSON
                # ═══════════════════════════════════════════════
                # 方法: msg = json.loads(raw)
                # 作用: 把 JSON 字符串转为 Python 字典。
                #       例如 '{"type":"text"}' → {"type": "text"}
                # 参数: raw — 上一步收到的字符串
                # 返回值: dict — 如果 JSON 合法；否则抛出 json.JSONDecodeError
                # 用法: msg = json.loads(raw)
                msg = json.loads(raw)

                # ═══════════════════════════════════════════════
                # TODO 6: 获取消息类型
                # ═══════════════════════════════════════════════
                # 方法: msg_type = msg.get("type", "unknown")
                # 作用: 从字典中取出 "type" 字段的值。
                #       如果字典里没有 "type" 这个键，返回 "unknown"
                # 参数: 第一个是键名，第二个是默认值
                # 返回值: str — 消息类型，或 "unknown"
                # 用法: msg_type = msg.get("type", "unknown")
                msg_type = msg.get("type", "unknown")

                # ═══════════════════════════════════════════════
                # TODO 7: 根据消息类型分发处理
                # ═══════════════════════════════════════════════
                # 你需要用 if/elif/else 判断 msg_type，然后做不同的事：
                #
                # if msg_type == "text":
                #     1. 用 msg.get("content", "") 取出文字内容
                #     2. 用 json.dumps() 构造回复字典 {"type":"text","content":"回声: xxx"}
                #     3. 用 await websocket.send_text() 发送
                #
                # elif msg_type == "control":
                #     1. 用 msg.get("action", "") 取出动作名称
                #     2. 构造回复 {"type":"control","action":action,"status":"done"}
                #     3. 发送
                #
                # elif msg_type == "ping":
                #     1. 构造回复 {"type":"pong"}
                #     2. 发送
                #
                # else:
                #     1. 构造回复 {"type":"error","message":"未知消息类型: xxx"}
                #     2. 发送
                if msg_type == "text":
                    content = msg.get("content", "")
                    reply = {"type": "text", "content": f"回声: {content}"}
                    await websocket.send_text(json.dumps(reply))
                elif msg_type == "control":
                    action = msg.get("action", "")
                    reply = {"type": "control", "action": action, "status": "done"}
                    await websocket.send_text(json.dumps(reply))
                elif msg_type == "ping":
                    reply = {"type": "pong"}
                    await websocket.send_text(json.dumps(reply))
                else:
                    reply = {"type": "error", "message": f"未知消息类型: {msg_type}"}
                    await websocket.send_text(json.dumps(reply))

            except json.JSONDecodeError:
                # ═══════════════════════════════════════════════
                # TODO 8: 处理非法 JSON
                # ═══════════════════════════════════════════════
                # 场景: 客户端发来了 "这不是JSON" 这种字符串
                #       json.loads() 抛出了 json.JSONDecodeError
                # 你要做的: 用 send_text 回复一个错误消息
                # 回复格式: {"type":"error","message":"消息格式错误，需要 JSON"}
                # 提示: json.dumps() 把字典转成字符串再发送
                error_reply = {"type": "error", "message": "消息格式错误，需要 JSON"}
                await websocket.send_text(json.dumps(error_reply))

    except WebSocketDisconnect:
        # ═══════════════════════════════════════════════════════
        # TODO 9: 处理客户端断开
        # ═══════════════════════════════════════════════════════
        # 场景: 用户关闭浏览器 / 断网 / 刷新页面
        #       FastAPI 自动抛出 WebSocketDisconnect 异常
        # 你要做的: 打印一行日志，然后函数结束（连接自动关闭）
        # 方法: print("客户端已断开")
        print("客户端已断开")