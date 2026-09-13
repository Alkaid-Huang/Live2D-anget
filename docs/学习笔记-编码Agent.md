# 学习笔记：编码 Agent（边学边写）

> 每完成一个阶段写一篇，格式固定五段：**概念 → 参照系统怎么做 → 我们的实现 → 实测数据 → 遗留问题**。
> 代码与设计在产品仓库 `echo-voice-assistant`（见 `docs/编码Agent集成设计.md`），本文件只记学习与验证结论。

---

## P1 · ACI：工具与沙箱（待写）

**要理解的问题**

1. 为什么工具要"少而正交"？（对比：给模型几十个碎工具会发生什么）
2. 编辑格式怎么选：整文件重写 / 统一 diff / 带上下文锚点的搜索-替换，各自风险是什么？
3. 为什么要在**每次编辑后**做语法检查，而不是等测试阶段？
4. 权限与沙箱的边界画在哪：路径、命令、网络分别怎么限制？

**参照系统**：[SWE-agent](https://github.com/SWE-agent/SWE-agent)（ACI 原始实现）、
[aider](https://github.com/Aider-AI/aider)（编辑格式与自动提交）

**实现落点**：`src/echo/agent/tools/coding.py` + `src/echo/agent/sandbox.py`

**实测数据**：（待填：工具调用成功率、编辑应用率、被拦截的危险命令数）

**遗留问题**：（待填）

---

## P2 · 仓库检索与上下文预算（待写）

**要理解的问题**

1. 按行、按文件、按符号（函数/类）切片，检索效果差在哪？
2. BM25 与向量检索各自的强项，RRF 融合为什么有效？
3. 上下文不是越多越好：token 预算怎么分配，什么该摘要、什么该保留原文？

**参照系统**：[LLMLingua](https://github.com/microsoft/LLMLingua)（压缩）、
SWE-agent/OpenHands 的检索与上下文构造

**实现落点**：`src/echo/index/`

**实测数据**：（待填：recall@k 对比、上下文 token 消耗）

---

## P3 · 反思修复与长任务状态（待写）

**要理解的问题**

1. 失败信息怎么回灌才有效？（完整输出 vs 摘要 vs 只给断言差异）
2. 什么时候该"换策略"而不是重试？（同错两次、工具反复失败、预算将尽）
3. 长任务怎么不迷失：状态机、变更日志（diff + 理由）、检查点各解决什么？

**参照系统**：Reflexion 思路、Agentless 的 localize→repair→validate 三段式

**实现落点**：`src/echo/agent/agent.py` + `task_state.py` + `journal.py`

**实测数据**：（待填：平均轮次、pass@1、回归引入率）

---

## P4 · 评测 harness（待写）

**要理解的问题**

1. 为什么"修好了"必须由测试判定，而不能让模型自称修好了？
2. pass@1 与 pass^k 的区别，为什么可靠性比单次最好成绩更重要？
3. 怎么测"有没有引入漏洞"与"有没有越权"？

**参照系统**：[SWE-bench](https://github.com/princeton-nlp/SWE-bench) 的评测协议、
[Terminal-Bench](https://github.com/laude-institute/terminal-bench) 的任务构造

**实现落点**：`src/echo/eval/`，报表写入 `benchmarks/codeagent_results.md`

**实测数据**：（待填：13 个任务的通过率与成本）

---

## P5 · 进阶（待写）

混合检索（向量 + RRF + rerank）、上下文压缩消融、Docker 沙箱、Semgrep 安全扫描。
