"""
课题03 验收测试：FastAPI + WebSocket 消息协议

运行方式:
    cd 课题03-FastAPI与WebSocket消息协议
    python -m pytest tests/test_03.py -v

注意：需要将你的 server.py 放在本目录下（与 tests 文件夹同级）
      需要安装: pip install fastapi uvicorn websockets pytest pytest-asyncio
"""

import sys
import os
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# 测试方案：启动服务器子进程，用 websockets 库连接
# ============================================================
import subprocess
import time
import asyncio


def get_server_url():
    """获取服务器地址"""
    return "ws://localhost:18765/ws"


@pytest.fixture(scope="module")
def server_process():
    """启动服务器进程"""
    server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--port", "18765", "--host", "127.0.0.1"],
        cwd=server_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)  # 等待服务器启动
    yield proc
    proc.terminate()
    proc.wait(timeout=5)


# ============================================================
# 测试 1：文字消息回声
# ============================================================
@pytest.mark.asyncio
async def test_text_message(server_process):
    """测试发送文字消息，收到回声"""
    import websockets

    uri = get_server_url()
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "text", "content": "你好"}))
        response = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(response)

        assert data["type"] == "text", f"消息类型应为 text，实际: {data.get('type')}"
        assert "你好" in data.get("content", ""), f"回声应包含'你好'，实际: {data}"


# ============================================================
# 测试 2：控制指令
# ============================================================
@pytest.mark.asyncio
async def test_control_message(server_process):
    """测试发送控制指令"""
    import websockets

    uri = get_server_url()
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "control", "action": "start"}))
        response = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(response)

        assert data["type"] == "control", f"消息类型应为 control，实际: {data.get('type')}"
        assert data["action"] == "start", f"action 应为 start，实际: {data.get('action')}"
        assert data["status"] == "done", f"status 应为 done，实际: {data.get('status')}"


# ============================================================
# 测试 3：心跳
# ============================================================
@pytest.mark.asyncio
async def test_ping_pong(server_process):
    """测试心跳 ping/pong"""
    import websockets

    uri = get_server_url()
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "ping"}))
        response = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(response)

        assert data["type"] == "pong", f"消息类型应为 pong，实际: {data.get('type')}"


# ============================================================
# 测试 4：非法 JSON
# ============================================================
@pytest.mark.asyncio
async def test_invalid_json(server_process):
    """测试发送非法 JSON，收到错误消息"""
    import websockets

    uri = get_server_url()
    async with websockets.connect(uri) as ws:
        await ws.send("这不是JSON")
        response = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(response)

        assert data["type"] == "error", f"消息类型应为 error，实际: {data.get('type')}"
        assert "格式错误" in data.get("message", "") or "JSON" in data.get("message", ""), \
            f"错误消息应提及格式问题，实际: {data.get('message')}"


# ============================================================
# 测试 5：未知消息类型
# ============================================================
@pytest.mark.asyncio
async def test_unknown_type(server_process):
    """测试发送未知消息类型，收到错误消息"""
    import websockets

    uri = get_server_url()
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "unknown_type_xyz"}))
        response = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(response)

        assert data["type"] == "error", f"消息类型应为 error，实际: {data.get('type')}"
        assert "未知" in data.get("message", ""), f"错误消息应提及'未知'，实际: {data.get('message')}"


# ============================================================
# 测试 6：多个消息连续发送
# ============================================================
@pytest.mark.asyncio
async def test_multiple_messages(server_process):
    """测试连续发送多条不同类型的消息"""
    import websockets

    uri = get_server_url()
    async with websockets.connect(uri) as ws:
        messages = [
            {"type": "text", "content": "第一条"},
            {"type": "ping"},
            {"type": "control", "action": "stop"},
            {"type": "text", "content": "第二条"},
        ]

        for msg in messages:
            await ws.send(json.dumps(msg))

        responses = []
        for _ in range(4):
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            responses.append(json.loads(response))

        types = [r["type"] for r in responses]
        assert types == ["text", "pong", "control", "text"], \
            f"消息类型顺序应为 [text, pong, control, text]，实际: {types}"


# ============================================================
# 测试 7：连接建立后立即断开
# ============================================================
@pytest.mark.asyncio
async def test_connect_and_disconnect(server_process):
    """测试连接后立即断开，服务端不崩溃"""
    import websockets

    uri = get_server_url()
    # 连接后不做任何操作就关闭
    async with websockets.connect(uri) as ws:
        pass  # 自动关闭

    # 再连一次确认服务器还在
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "ping"}))
        response = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(response)
        assert data["type"] == "pong", "断开后重连应该正常工作"


# ============================================================
# 测试 8：空内容 text 消息
# ============================================================
@pytest.mark.asyncio
async def test_empty_content(server_process):
    """测试空内容消息"""
    import websockets

    uri = get_server_url()
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "text", "content": ""}))
        response = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(response)

        assert data["type"] == "text", f"空消息也应正常回复，实际: {data.get('type')}"


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    sys.exit(exit_code)