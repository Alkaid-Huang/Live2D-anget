# 与 D_sakiko 对照：同类项目里的"完成度天花板"

> 参考项目：[MacchaPafe/D_sakiko](https://github.com/MacchaPafe/D_sakiko)（数字小祥）
> 元信息（2026-09-13 检索）：93 ★ / 15 fork / Python / **GPL-3.0** / 创建 2025-05-26 / 最后推送 2026-09-12 /
> 656 个文件（306 个 .py）/ 仓库约 37MB / 有官网与 VitePress 文档站
> 定位自述：**"基于多模态与 ReAct 框架的桌面数字生命 Agent"**

---

## 一、它做了什么（比我们多出来的部分）

| 能力 | 它的实现 | Echo 现状 |
|------|---------|----------|
| 编排 | 自研 **ReAct 引擎 + ToolRegistry 抽象层 + 工具执行沙盒**，异常 traceback 自动转成 prompt 反馈，让模型自纠错 | 有工具注册表与循环，但只是把错误文本回给模型，**没有反思重试策略** |
| 知识 | **RAG**：Qdrant 向量 + BM25 稀疏双路召回 → RRF 融合 → Reranker 精排；用 BangDream 时间线构建"世界书"防止角色 OOC | 只有关键词检索的 `FactStore` |
| 记忆 | 短期滑动窗口 + **异步反思（Reflection）** 抽取关键事件并向量化落盘，按阈值触发召回 | 短期按轮裁剪 + 长期事实条目，无反思、无向量 |
| 情绪 | 独立模块 `emotion_detect.py` / `emotion_enum.py`：**BERT-base-Chinese 微调 7 分类**（happiness/sadness/anger/disgust/like/surprise/fear） | 让 LLM 在 JSON 里自评情绪 + 关键词兜底 |
| 语音 | **GPT-SoVITS 语音克隆**，角色用自己的声线说话；安装脚本 + 模型预加载 | edge-tts 通用音色 |
| Live2D | 桌面端 `live2d-py + PyQt5`；另有 `dsakiko_webui`（React + **Cubism Core 5**）走 WebSocket；后端有专门的**呈现契约模块** `live2d_presentation.py` | **未接入**（M3 待做） |
| LLM 接入 | LiteLLM 路由，Windows/macOS 几乎支持所有 provider | 自研 OpenAI 兼容 + Ollama 两个后端 |
| 产品化 | 一键包（Win/macOS）、网盘分发、**更新器/修复器（带回滚记录）**、对话备份包、对话分叉、角色管理、Live2D 模型下载器（Bestdori）、动作组编辑器 | 只有本地源码运行 |
| 文档 | VitePress 文档站（getting-started / live2d / llm / tts / settings / update） | Markdown 文档齐全但无站点 |
| 工程 | 前后端各自带测试；`AGENTS.md` + **`CONTEXT.md` 领域术语表**；uv 管理依赖 | 54 源码文件 + 52 个测试；有 AGENTS.md，无术语表 |

---

## 二、最值得抄的五个"思路"（不是代码）

### 1. Live2D 呈现契约（直接服务我们的 M3）

它的 `live2d_presentation.py` 把"给前端看什么"建模成数据结构：

- `Live2DVersion`（v2/v3）、`Live2DResolution`（`resolved` / `absent` / `configured_error`）
- `Live2DLayoutPresentation`（scale / offset_x / offset_y）
- `Live2DCapabilities`（该模型能做哪些动作与表情）
- `Live2DError`（code / message / retryable，直接作为 WebSocket 契约）

并且定义了**项目标准动作组 id**：`IDLE`、`happiness`、`text_generating`、`idle_motion`，
方向动作用 `{group}_L` / `{group}_R`，缺失时回退基础动作组。

**为什么要学**：这正是"后端事件流 → 前端呈现"的稳定契约；
我们已有 `thinking / tool_call / speech / emotion` 事件，缺的正是"模型布局 + 能力 + 错误码 + 动作组命名"这一层。

### 2. 情绪识别独立成模块

它不在 prompt 里让大模型自评，而是训练/加载 **BERT 7 分类**模型，再用 `EmotionEnum` 统一不同数据集的标签表示。

**为什么要学**：我们现在 `emotion` 来自 LLM 自评，主观且不稳定；
独立模块可替换、可评测（准确率）、可离线。**面试里"情绪怎么来的"这题立刻高一档。**

### 3. 领域术语表（`CONTEXT.md`）

它把"角色 / 角色 ID / 待启用角色 / 无模型展示 / 动作编辑器预览 / 默认 Live2D 模型"等词严格定义，
并写明"不该叫什么"（Avoid: ...）。

**为什么要学**：术语不清是多人/AI 协作最大的隐性成本。我们可以做一份精简版术语表（角色、动作组、情绪、事件、双工模式）。

### 4. 工具沙箱 + 错误反思

它把工具执行放进沙盒，捕获 Traceback 后**转成 prompt 让模型自己修**（而不是只回一句"工具错误"）。

**为什么要学**：我们的 `ToolRegistry.call()` 已经做到"异常转可读文本"，
只要再加一步"引导模型换参数重试"，就从"不崩"升级为"自愈"。

### 5. 产品化外壳

一键安装包、网盘分发、更新器/修复器（带回滚）、对话备份与分叉、角色管理界面。

**为什么要学**：这是"能给别人用"与"只能自己跑"的分界线；
我们短期不必做全套，但**打包成"双击可运行 + 说明文档"**是面试演示的加分项。

---

## 三、不能碰的地方

1. **License 是 GPL-3.0**：代码不可复制进 Echo（否则 Echo 也必须以 GPL 开源）。
   只能学习思路、独立实现。这一条要写进自己的开发规范。
2. **Live2D 模型与角色 IP 有版权**：它从 Bestdori 下载的是 BanG Dream 的模型资源，
   非商业同人使用；若要公开演示，注意素材授权，最好换成官方示例模型或自制模型。
3. **体量差距是真实的**：它 306 个 .py（还不含前端），我们 54 个；
   对方是"产品级"，我们是"工程内核 + 可演示闭环"，**不要试图在两周内追平功能面**。

---

## 四、对 Echo 的直接启示

### 4.1 M3（Live2D 身体）走哪条路

| 方案 | 优点 | 缺点 | 参考 |
|------|------|------|------|
| 桌面：PyQt5 + live2d-py | 真·桌面伴侣（透明/置顶窗口）、无需前端栈 | 需要 Qt 与 asyncio 事件循环整合；打包更重 | D_sakiko 主程序 |
| 网页：WS + Cubism Core 5 + React | 演示与录屏容易、可远程、便于我用浏览器验证 | 要写前端与协议；不算"桌面" | 它的 `dsakiko_webui` |

**建议**：M3 先做**网页渲染**（把"呈现契约"打牢，容易验证与录屏），
把桌面渲染当作该契约的第二个实现放到 M4——这也正是 D_sakiko 自己走过的路。

### 4.2 立刻可落地的三处小改造

1. 情绪层抽成独立模块：`emotion/`（枚举 + 规则/模型实现 + 映射到动作组），LLM 自评降级为兜底
2. 定义标准动作组 id：`IDLE` / `text_generating` / `happiness` / `sadness` / `angry` / `surprised` / `shy`，
   并规定缺失时的回退顺序
3. 在工具循环里加"错误反思"：连续两次工具失败时，把失败原因作为 system 提醒再试一轮

---

## 五、面试话术

> "我研究过两个参照系：工业级框架 Pipecat 和同类开源项目 D_sakiko。
> Pipecat 让我看清编排层的差距——帧驱动管线、可插拔轮次策略、输入音频滤波；
> D_sakiko 让我看清能力面的差距——RAG 知识库、专用情绪模型、语音克隆和产品化分发。
> 我的项目定位是'把内核做扎实'：四组件接口化 + 配置驱动 + Agent 工具调用 + 事件流，
> 现在按三条线收敛：先做 Live2D 呈现契约与情绪映射，再做流式与记忆升级，最后才是打包。
> 我知道自己离产品级还差什么，也知道下一步先补哪块。"
