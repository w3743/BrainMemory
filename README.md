# BrainMemory — 类脑记忆 / Brain-Inspired Memory for LLM Agents

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue" alt="Python">
  <img src="https://img.shields.io/badge/License-GPL%20v3-green" alt="License">
  <br>
  <em>让本地 LLM Agent 在不同会话之间持续记住、检索和修正信息</em><br>
  <em>Persistent, searchable, and correctable memory for local LLM agents</em>
</p>

**中文** | [English](#english)

---

## 中文

### 这是什么

BrainMemory 是一个运行在本机的 LLM Agent 长期记忆系统。它位于 Agent 与模型之间：对话结束后提取值得长期保留的信息，在下一次回答前检索相关记忆，并根据记忆是否真正帮助了回答持续调整它。

它解决的不是“保存全部聊天记录”，而是让 Agent 维护一组可以长期演化的事实，例如：

- 用户是谁、喜欢怎样被称呼，以及稳定的回答偏好；
- 某个项目使用的技术栈、命令、规范和已经做出的决定；
- 可复用的操作流程与排障经验；
- 对旧信息的纠正，例如依赖工具从 pnpm 改为 bun。

数据保存在本地 SQLite 中。BrainMemory 可以作为独立 HTTP Sidecar 使用，也可以直接接入 pi Agent、OpenClaw 或 Hermes。它面向可信的本地单用户环境，不提供多租户用户隔离。

### 工作方式

```text
用户消息
   ↓
检索与当前问题相关的长期记忆
   ↓
以明确的 BrainMemory 来源标记注入 Agent
   ↓
Agent 回答
   ↓
判断哪些记忆被使用、忽略或纠正
   ↓
提取新事实、替换旧事实、更新记忆状态
```

BrainMemory 将记忆正文、检索索引、强度、可信度和反馈记录分开管理。记忆会随时间降低可检索性；真正被使用的记忆会得到强化，错误或被替代的信息会降权或删除。

### 一分钟开始

```bash
# 安装
pip install git+https://github.com/w3743/BrainMemory.git

# 启动 Sidecar；首次运行会下载约 1.3 GB 的 BGE 模型
python -m brainmemory.cli serve

# 打开管理控制台
# http://127.0.0.1:8765/admin
```

如果 `brainmemory` 命令不在 PATH 中，始终可以使用 `python -m brainmemory.cli`。

### 记忆模型

当前可回忆强度：

```text
R(t) = 2 / (1 + (2/s₀ - 1) · e^(2dt))
```

- `s₀`：上次访问后的记忆强度。
- 有效衰减率由稳定性 \(S\)、难度 \(D\) 和相似知识干扰 \(I\) 联合决定。
- 新记忆初始强度为 `0.6`。
- 默认归档阈值为 `0.2`。

成功使用后，即时强度向 1.0 移动：

```text
R' = R + 0.35 · (1 - R)
```

长期稳定性同时根据回忆难度增长：

```text
ΔS ∝ Puse · [0.15 + 1.85 · (1 - R)^1.25] · (0.5 + D) · (1 - S/730)
```

因此刚记住就频繁重复不会无限获得高收益；在已经有些模糊时成功回忆，会带来更大的长期稳定性提升。

### 检索与反馈

检索使用向量 Top-100、FTS5 Top-100 和高效用 Top-30 的候选并集，再执行非乘法评分：

```text
score = sigmoid(
  -2 + 3·semantic + 1.2·keyword + 1.2·R
  + 0.5·trust + 0.8·utility + 0.4·boost - 1.5·conflict
)
```

| 反馈 | 行为 |
|---|---|
| `used` | 强化强度与稳定性，`boost +0.05`，略微提高信任 |
| `ignored` | 不强化，仅轻微降低 boost，并略微加快衰减 |
| `corrected` | 降低 boost 和信任，加快衰减；需要主题匹配以避免误伤 |

`/pre_prompt` 返回的是本轮注入候选。`/post_run` 会检查 Agent 的实际回答，只有出现足够强的内容证据才将对应记忆判定为 `used`。

显式 `used_memory_ids` 的使用概率为 0.98；回退判断输出
`p_use / p_ignore / p_correct / confidence`。不确定反馈不奖不罚，并写入
`memory_feedback_events`。完整设计见
[`docs/easm_algorithm.md`](docs/easm_algorithm.md)。

### 60 日模拟

![60-day memory decay simulation](tools/sim_charts/decay_60d_curves.png)

| 使用频率 | 第 60 日强度 |
|---|---:|
| 从不使用 | 0.056 |
| 仅使用一次 | 0.146 |
| 每 30 天 | 0.351 |
| 每 14 天 | 0.755 |
| 每 7 天 | 0.900 |
| 每 3 天 | 0.974 |
| 每天 | 0.998 |

完整数据位于 [`tools/sim_charts/decay_60d.csv`](tools/sim_charts/decay_60d.csv)，模拟脚本为 [`tools/simulate_longterm.py`](tools/simulate_longterm.py)。

### 运行模式

BrainMemory 面向本地单用户环境：

- `project_id` / `workspace_id` 是唯一可选的记忆边界。
- `user_id` 仅作为旧接口兼容字段，不参与隔离。
- 未提供项目 ID 的记忆作为全局记忆，可被所有项目检索。
- 记忆内容按原文保存，不进行敏感信息识别或脱敏。

### 配置

| 环境变量 | 说明 | 默认值 |
|---|---|---|
| `BRAINMEMORY_DB` | SQLite 数据库路径 | `brainmemory.db` |
| `BRAINMEMORY_HOST` | Sidecar 监听地址 | `127.0.0.1` |
| `BRAINMEMORY_PORT` | Sidecar 端口 | `8765` |
| `BRAINMEMORY_API_KEY` | 可选 HTTP API Key | 空 |
| `BRAINMEMORY_EMBEDDING_MODEL` | 本地 BGE 模型目录 | 自动下载 HF 模型 |
| `BRAINMEMORY_DEEPSEEK_API_KEY` | DeepSeek API Key | 空 |
| `DEEPSEEK_API_KEY` | 通用 DeepSeek API Key | 空 |

### pi Agent

```bash
pip install git+https://github.com/w3743/BrainMemory.git
pi
```

扩展会自动启动 Sidecar。可用命令：

- `/remember <内容>`：手动保存记忆
- `/bm-health`：查看健康状态
- `/bm-search <查询>`：搜索记忆

卸载：`brainmemory uninstall --yes`

### CLI

```bash
python -m brainmemory.cli serve
python -m brainmemory.cli add "内容" --project demo
python -m brainmemory.cli search "查询" --project demo
python -m brainmemory.cli sleep
python -m brainmemory.cli health
python -m brainmemory.cli demo
python -m brainmemory.cli eval-all
python -m brainmemory.cli uninstall --yes
```

### HTTP API

| 端点 | 用途 |
|---|---|
| `POST /pre_prompt` | 回答前检索并生成记忆上下文 |
| `POST /post_run` | 回答后分析反馈并提取记忆 |
| `POST /remember` | 手动保存 |
| `POST /context` | 获取记忆上下文 |
| `POST /sleep` | 归档弱记忆并清理历史替换记录 |
| `POST /admin/feedback` | 查询概率反馈及其证据 |
| `GET /health` | 服务健康检查 |
| `GET /admin` | Web 控制台 |

### 从源码开发

```bash
git clone https://github.com/w3743/BrainMemory.git
cd BrainMemory
pip install -e .
python -m pytest -q
```

主要目录：

```text
src/brainmemory/       核心引擎、检索、演化、存储和 Sidecar
pi-extension/          pi Agent 扩展
tests/                 自动测试
eval/                  评测用例
tools/                 模拟与辅助脚本
docs/                  API 与集成文档
```

---

## English

### What is BrainMemory?

BrainMemory is a local long-term memory system for LLM agents. It sits between an agent and its model: after a conversation it extracts information worth retaining, before the next answer it retrieves relevant memories, and after the answer it learns whether those memories were actually useful.

It is not intended to preserve every chat message. It maintains an evolving set of reusable facts, including:

- who the user is, how they prefer to be addressed, and stable response preferences;
- project technologies, commands, conventions, and decisions;
- reusable procedures and troubleshooting knowledge;
- corrections to obsolete facts, such as a project moving from pnpm to bun.

All data is stored locally in SQLite. BrainMemory can run as an HTTP sidecar or integrate directly with pi Agent, OpenClaw, and Hermes. It targets a trusted local single-user environment rather than multi-tenant user isolation.

### How it works

```text
User message
    ↓
Retrieve relevant long-term memories
    ↓
Inject them with explicit BrainMemory provenance
    ↓
Agent answer
    ↓
Observe which memories were used, ignored, or corrected
    ↓
Extract new facts, replace obsolete facts, and update memory state
```

Memory content, retrieval indexes, strength, trust, and feedback evidence are managed separately. Memories become less retrievable over time; successful use reinforces them, while incorrect or superseded information is demoted or removed.

### Quick start

```bash
pip install git+https://github.com/w3743/BrainMemory.git
python -m brainmemory.cli serve

# Open http://127.0.0.1:8765/admin
```

The first run downloads `BAAI/bge-large-zh-v1.5` (about 1.3 GB). Set `BRAINMEMORY_EMBEDDING_MODEL` to a local model directory for offline use.


### Memory dynamics

Current retrievability is:

```text
R(t) = 2 / (1 + (2/s₀ - 1) · e^(2dt))
```

Each memory starts at strength `0.6` with its own decay rate `d=0.02`. A successful use moves activation toward 1:

```text
R' = R + 0.35 · (1 - R)
```

Long-term stability learns from retrieval effort:

```text
ΔS ∝ Puse · [0.15 + 1.85 · (1 - R)^1.25] · (0.5 + D) · (1 - S/730)
```

This models the spacing effect: immediate repetition has limited long-term value, while a successful recall after some forgetting produces a larger stability gain.

### Retrieval and feedback

Candidates are the union of dense top-100, FTS5 top-100, and utility top-30.
They are ranked by a sigmoid over semantic similarity, lexical match,
retrievability, Beta trust, utility, boost, and conflict risk. MMR removes
redundant memories before prompt injection.

| Feedback | Effect |
|---|---|
| `used` | Reinforce activation and stability, increase boost and trust |
| `ignored` | Do not reinforce; slightly reduce boost and increase decay |
| `corrected` | Reduce boost/trust and increase decay, with topic matching to avoid collateral penalties |

`/pre_prompt` returns memories injected for the current run. `/post_run` compares those exact IDs with the latest agent answer. A memory is reinforced only when the answer contains sufficient evidence that it was used.

Explicit `used_memory_ids` receive `P(use)=0.98`. Fallback evidence produces
`p_use`, `p_ignore`, `p_correct`, and confidence. Uncertain feedback does not
change the memory. Every observation is stored in `memory_feedback_events`.
See [`docs/easm_algorithm.md`](docs/easm_algorithm.md).

### 60-day simulation

![60-day memory decay simulation](tools/sim_charts/decay_60d_curves.png)

| Use frequency | Strength on day 60 |
|---|---:|
| Never | 0.056 |
| Once | 0.146 |
| Every 30 days | 0.351 |
| Every 14 days | 0.755 |
| Weekly | 0.900 |
| Every 3 days | 0.974 |
| Daily | 0.998 |

See [`tools/sim_charts/decay_60d.csv`](tools/sim_charts/decay_60d.csv) for the complete dataset.

### Runtime model

BrainMemory targets a trusted local single-user environment:

- `project_id` / `workspace_id` is the only optional memory boundary.
- `user_id` is accepted only for backward compatibility and does not isolate data.
- Memories without a project ID are global and can be retrieved from every project.
- Memory text is stored verbatim; no sensitive-data classification or redaction is performed.

### Configuration

| Environment variable | Description | Default |
|---|---|---|
| `BRAINMEMORY_DB` | SQLite database path | `brainmemory.db` |
| `BRAINMEMORY_HOST` | Sidecar bind address | `127.0.0.1` |
| `BRAINMEMORY_PORT` | Sidecar port | `8765` |
| `BRAINMEMORY_API_KEY` | Optional HTTP API key | empty |
| `BRAINMEMORY_EMBEDDING_MODEL` | Local BGE model directory | Hugging Face model |
| `BRAINMEMORY_DEEPSEEK_API_KEY` | DeepSeek API key | empty |
| `DEEPSEEK_API_KEY` | Generic DeepSeek API key | empty |

### pi Agent commands

- `/remember <text>` — save a memory manually
- `/bm-health` — show memory health
- `/bm-search <query>` — search memory

### CLI

```bash
python -m brainmemory.cli serve
python -m brainmemory.cli add "content" --project demo
python -m brainmemory.cli search "query" --project demo
python -m brainmemory.cli sleep
python -m brainmemory.cli health
python -m brainmemory.cli eval-all
```

### HTTP API

| Endpoint | Purpose |
|---|---|
| `POST /pre_prompt` | Retrieve context before an agent answer |
| `POST /post_run` | Analyze feedback and extract memory after a run |
| `POST /remember` | Save a memory manually |
| `POST /context` | Retrieve formatted memory context |
| `POST /sleep` | Archive weak memories and clean legacy superseded records |
| `POST /admin/feedback` | Inspect probabilistic feedback evidence |
| `GET /health` | Service health check |
| `GET /admin` | Web console |

### Development

```bash
git clone https://github.com/w3743/BrainMemory.git
cd BrainMemory
pip install -e .
python -m pytest -q
```

## License / 许可

GPL-3.0-only
