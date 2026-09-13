# D_sakiko 架构研究：它怎么组织一个"数字生命"项目

> 研究日期：2026-09-13 ｜ 方法：GitHub API + raw 源码逐文件阅读（未整仓克隆）
> 许可：**GPL-3.0** —— 本文只提炼**架构与模块设计**，不复制任何代码。
> 规模：656 文件 / 306 个 .py / 47 个 Python 测试文件 / 14 篇 ADR

---

## 一、模块地图（按职责分层）

```
GPT_SoVITS/                      ← 应用主体（名字沿用第三方 TTS 项目，实际是完整应用）
├── chat/            (10)        对话编排：chat.py 编排 · tool_calling.py 工具 · rolling_summary.py 上下文压缩
│                                · reminder_manager.py 提醒 · attachments/image_upload 多模态输入 · model_token_usage 计费统计
├── runtime/         (5)         运行时与存储：conversation_storage · audio_files · runtime_lock（并发锁）· storage_ui
├── ui/              (18)        桌面界面：components / custom_widgets / interfaces / threads（GPU 检测、内存检测）
├── ui_main/         (17)        主窗口与向导
├── live2d_support/  (12)        【自有】Live2D 支持：布局、模型规范化、runtime 适配、表情策略、动作选择
├── live2d_download/ (7)         模型资产管理：bestdori_client · cache/asset_cache · downloader · service · models
├── update/ repair/ maintenance/ 产品生命周期：更新器、修复器、维护任务（均带回滚记录）
├── emotion_detect.py / emotion_enum.py / inference_emotion_detect.py   情绪识别（BERT 七分类）
├── character.py / character_creation.py                                 角色领域模型与创建流程
├── text/ (43) AR/ (32) ...      GPT-SoVITS 内部实现（第三方 vendored）
├── test/ (32)                   测试与实现同仓同层
└── docs/adr (14)                **架构决策记录**

dsakiko_webui/
├── backend/ (24)   app · main · ws · protocol · runtime · live2d_presentation · assets · auth · networking · pairing_ui · uploads + test/
└── frontend/ (59)  React + Cubism Core 5 + useAudioController（口型/音频）+ Avatar 组件 + 各自测试

docs-site/          VitePress 文档站（getting-started / live2d / llm / tts / settings / update）
AGENTS.md · CONTEXT.md（领域术语表）· pyproject.toml（uv 管理）
```

---

## 二、十个值得学的架构与模块设计

### 1. 契约优先的传输层（`backend/protocol.py`）

它把 WebSocket 协议写成一个**显式契约**：`PROTOCOL_VERSION = 1`、
Pydantic 请求模型（`SessionRequest`/`PairingRequest`/`SettingsUpdateRequest`）、
统一的命令信封 `CommandEnvelope{protocol_version, kind, type, request_id, payload}`、
以及带 `code / message / retryable / details` 的 `ProtocolError` 与 `command_result()` 响应构造器。

**为什么值得学**：版本号让前后端可以独立演进；`retryable` 让前端知道该不该重试；
统一信封让日志、追踪、错误处理都只需写一次。
**我们怎么落地**：Echo 现在的事件只是 `on_event(kind, payload)` 字符串约定，
应升级为带版本号与错误语义的契约（见产品仓库 `docs/架构对齐方案.md` 的 A1 阶段）。

### 2. 呈现契约独立成模块（`live2d_presentation.py`）

把"给渲染层看什么"建模为数据：`Live2DVersion(v2/v3)`、
`Live2DResolution(resolved/absent/configured_error)`、
`Live2DLayoutPresentation(scale/offset_x/offset_y)`、`Live2DCapabilities`、
`Live2DError(code/message/retryable)`，并统一 `to_dict()` 直接作为 WebSocket 契约。

**为什么**：渲染层与业务层解耦；模型缺失/配置错误都是**显式状态**而不是异常崩溃。
**我们怎么落地**：M3 的第一件事就是这层契约（动作组 id 见第 4、6 条）。

### 3. 自有支持模块与第三方 runtime 分离（`live2d_support/`，ADR 0001）

ADR 0001 写明了理由：应用依赖第三方包 `live2d`（`live2d.v2cpp` / `live2d.v3`），
若自有模块也叫 `live2d/` 会产生**导入遮蔽**，因此自有能力收拢到 `live2d_support/`，
并在入口做带 guard 的 `sys.path` 处理以兼容嵌入式 Python 发布环境。

**为什么**：命名冲突与打包环境差异是真实工程问题，写进 ADR 才不会反复踩。

### 4. 领域模型与可选能力解耦（ADR 0041）

ADR 0041：「把角色与可选能力解耦」——角色由**稳定 ID + 显示名 + 非空描述**构成，
Live2D、语音、头像都是**可选能力**；CONTEXT.md 里还专门定义了"无模型展示"（没有模型也要能正常展示背景与字幕）。

**为什么**：让"角色"这个概念不被某一项能力绑架；新增能力不需要改角色模型。
**我们怎么落地**：Echo 的"角色"目前还散落在 persona 配置里，可以抽成独立领域模型。

### 5. 稳定 ID 用资源目录名（ADR 0042）

角色 ID 就是资源文件夹名，显示名变化不影响 ID。

**为什么**：ID 一旦漂移，配置引用、存档、备份全都会断。

### 6. 不静默回退显式目标（ADR 0045 / 0046）

ADR 0045：**不要**把"显式指定的模型加载失败"悄悄回退到别的模型；
ADR 0046：Live2D 目标用**可空路径**表达"未配置"与"配置了但失效"的区别。

**为什么**：静默回退会掩盖配置错误，让人以为"系统正常工作"。
**注意对照**：Echo 的 ASR 有"CUDA 不可用自动降级 CPU"——那是**运行时资源**降级，与"用户显式配置错了"是两回事，两者都要保留但语义要分清。

### 7. 对话编排拆分（`chat/`，10 个模块）

`chat.py`（主编排）、`tool_calling.py`（工具定义与执行，含沙箱与错误回灌）、
`rolling_summary.py`（**上下文滚动摘要**）、`reminder_manager.py`（提醒）、
`attachments.py` / `image_upload.py` / `remote_attachments.py`（多模态输入）、
`model_token_usage.py`（用量统计）、`chat_meta.py`（会话元数据）。

**为什么**：编排只做编排；上下文压缩、工具、多模态输入各自独立可测。
**我们的差距**：Echo 的 `chat_history.py` 只做按轮裁剪，没有滚动摘要；工具与编排混在 `agent.py`。

### 8. 运行时与存储独立（`runtime/`）

`conversation_storage.py`（会话持久化）、`audio_files.py`（音频文件管理）、
`runtime_lock.py`（**并发/多实例锁**）、`storage_ui.py`（存储相关界面）。

**为什么**：存储是长期演进的关注点；`runtime_lock` 说明他们真的被"多开/并发"坑过。

### 9. 产品生命周期模块（`update/`、`repair/`、`maintenance/`、`tools/release/`）

更新器、修复器、维护任务与发布工具独立成模块，并有 ADR 0006（更新结果记录）、
ADR 0007（按版本精确修复程序资源）、ADR 0008（对话备份的资源引用）。

**为什么**：能给别人用的软件，一半工作量在"更新与修复"；这些能力必须有**机器可读的结果记录**。

### 10. ADR + 术语表 + 测试同位

| 实践 | 它的做法 | 我们能立刻学的 |
|------|---------|---------------|
| ADR | `docs/adr/0001-...md`，格式就两段：**做了什么决定 + 为什么/约束**（样例仅 628 字节） | 立即可用，成本极低，面试极加分 |
| 术语表 | `CONTEXT.md` 定义"角色/角色 ID/无模型展示/标准动作组"，并写明"不该叫什么" | 做精简版（角色/动作组/情绪/事件/双工模式） |
| 测试同位 | `GPT_SoVITS/test/`、`backend/test/`、前端 `*.test.jsx` | 我们已有 tests/，可增设"契约测试"层 |

---

## 三、它做得不好 / 我们不必学的地方

1. **单文件过大**：`chat.py` 111 KB、`tool_calling.py` 82 KB——模块划分清晰但文件粒度失控；
   我们的规范是"单文件超过 300 行考虑拆分"，这条要坚持。
2. **重桌面技术栈**：PyQt5 + 自维护的 Live2D runtime 分叉（`live2d-py==0.7.0.4+d_sakiko.4` + CI 自编译）；
   功能强但可移植性差、Python 锁 3.11。
3. **GPL-3.0**：直接抄代码会让 Echo 也必须 GPL；只学设计。
4. **依赖体积大**：内置 GPT-SoVITS、funasr、gradio 等，安装门槛高（他们靠一键包解决）。

---

## 四、结论

**学它的"分层与契约"，不学它的"体量与堆叠"。**

它真正优秀的地方是：把"一个复杂桌面 Agent 应用"拆成了**可解释的模块边界**
（契约层 / 呈现层 / 编排层 / 运行时 / UI / 资产生命周期），
并用 ADR 与术语表把决策与词汇固定下来，让多人（和多 AI）协作不失控。

这两件事我们都能做，而且成本很低——见产品仓库的 `docs/架构对齐方案.md`。
