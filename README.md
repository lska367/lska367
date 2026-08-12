# Hi there 👋 我是杨锴（lska367）

> 🎓 东北林业大学 数据科学与大数据技术 本科（2022–2026）
> 📍 已保研 → **华东师范大学 卓越工程师学院 · 人工智能 硕士**（2026.09 入学）
> 🔬 研究方向：**KV Cache / LLM 推理优化**

---

## 🔭 目前在做

- **KV Cache 方向研究**：LLM 推理优化，以测量为驱动的实验方法（从测量出发，而非文献 gap）
- **[vllm-sniffer](https://github.com/lska367/vllm-sniffer)**：非侵入式 vLLM 运行时 tracer —— 观测推理热路径（调度 / 前向 / 采样 / KV cache 压力），并定位生产排障中最棘手的"相同 prompt + temperature=0 却输出不同"的浮点不确定性，行为零侵入
- **分布式 LLM 推理 / 分布式训练**：Ray 生态（Ray Core / Ray Train / Ray Data）、vLLM 源码级调优

## 🌱 技术栈

| 方向 | 技术 |
|---|---|
| 深度学习 | PyTorch · Hugging Face Transformers · P-tuning / LoRA / QLoRA 微调 · RLHF / DPO |
| 分布式 | Ray Core / Train / Data · 分布式 LLM 推理 · vLLM |
| LLM 应用 | LangChain / LangGraph · Multi-Agent · RAG · 上下文工程 · LLM as Judge |
| 联邦学习 | 联邦标签噪声学习（FedCorr 复现与改进） |

## 💼 实习经历

**益普索（中国）咨询有限公司 · AI Lab · AI 算法实习生**（2025.12–2026.02）

- 主导 **DeepResearch Agent** 算法设计与迭代：基于 LangGraph + ReAct 构建"问题拆解 → 检索调用 → 结果验证 → 报告生成"多节点工作流，实现工具调用路由、上下文记忆压缩与异常重试机制
- 参与 **LLM as Judge** 评测与小模型对齐微调：搭建"数据清洗 → 自动标注 → 偏好构造 → LoRA 微调 → 离线评估"完整 Pipeline，资源受限场景下采用 QLoRA 与批量推理优化

## 🚀 项目

- **[vllm-sniffer](https://github.com/lska367/vllm-sniffer)** — 非侵入式 vLLM 运行时 tracer，观测推理热路径与浮点不确定性根因（当前主力项目）
- **[fnll](https://github.com/lska367/fnll) / [flwr4fnll](https://github.com/lska367/flwr4fnll)** — FedCorr 联邦标签噪声学习实验平台与联邦学习噪声标签处理框架（CVPR 2022 FedCorr 复现与多算法实现）
- **基于自我纠错机制的住建部 RAG 检索系统**（2025.05–2025.10）— 借鉴 ReAct 思想设计迭代式检索策略，多策略融合检索 + 交叉编码器重排序，系统召回率 **42% → 76%**，平均检索轮次 1.3 次

## 🏆 荣誉

- 东北林业大学 2025 年度国家励志奖学金

## 📫 联系我

- 📧 yangkamboy@outlook.com
- 🔭 常驻研究笔记：[kvcache_research](https://github.com/lska367/kvcache_research) · [llm-inference-paper-reading](https://github.com/lska367/llm-inference-paper-reading)

---

*🌟 从测量出发，用数据说话。*
