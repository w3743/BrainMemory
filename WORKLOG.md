# MemBrain / CSM 工作记录

> 本文件记录针对类脑连续强度记忆系统的测试、问题发现和修复。按时间倒序排列。

---

## 2026-06-22 · 严格本地 BGE 模型路径与测试入口补齐

### 背景

继续检查本地 BGE 约束时发现：文档已经声明“缺少依赖或模型时应修复环境，不会静默降级”，但 `embedding.py` 在默认模型目录不存在时仍会返回 `BAAI/bge-large-zh-v1.5` 远程模型 ID。严格按“全部使用 local bge-large-zh-v1.5”的要求，这会给运行时留下自动下载/远程解析的缝隙。

同时，`pytest` 中已有两个和 CSM 干扰控制强相关的回归测试没有纳入 `tests/run_tests.py`：无关查询不应注入记忆、搜索本身不应强化记忆。

### 修改

| 文件 | 改动 |
|------|------|
| `src/membrain/embedding.py` | 默认模型固定为项目本地 `models/bge-large-zh-v1.5`，不再在缺失时回退到远程模型 ID。 |
| `src/membrain/embedding.py` | `CSM_EMBEDDING_MODEL` 必须指向存在的本地目录；远程 ID 或不存在路径会直接报错。 |
| `tests/test_engine.py` | 默认 embedding 配置测试增加本地路径存在断言。 |
| `tests/test_engine.py` | 新增测试：`CSM_EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5` 会被拒绝，避免远程模型 ID 混入。 |
| `tests/run_tests.py` | 纳入“无关查询不注入”和“搜索不强化”两个已有回归测试，并加入远程模型 ID 拒绝测试，检查数更新为 79。 |

### 验证

```
pytest targeted(local BGE): 2 passed
embedding-info:
  model = C:\Users\wangj\Desktop\1\models\bge-large-zh-v1.5
pytest(local BGE): 79 passed
run_tests(local BGE): 79 checks passed
eval-all(local BGE):
  extraction accuracy = 1.0
  retrieval recall@k = 0.7368
  retrieval mrr = 0.6316
  retrieval ndcg = 0.6591
  e2e accuracy = 1.0
  e2e pollution_rate = 0.0
  embedding backend = local_bge_large_zh
```

### 设计结论

“本地 embedding”不能只靠约定和文档表达，入口本身必须拒绝远程模型 ID。否则外部 agent 部署时一旦模型目录缺失，就可能在用户无感知的情况下改变运行方式，后续检索质量和成本都不可控。

---

## 2026-06-22 · 管理端无项目检索边界与 LLM prompt 清理

### 背景

继续审查另一个 AI 的改动后，重点检查了管理 UI/API 与主 adapter 是否拥有同样的分区边界。主 adapter 已修复无 `workspace/project` 时的全库检索风险，但管理端也需要测试锁住这个行为，否则“检索实验/仲裁实验”可能在未来改动中重新把 `None` 当成全库搜索。

另外，DeepSeek 仲裁提示词中有一个拼写噪声：`SUPERSEDE` 说明句写成了 `SUPRESSEDE`。这不会让代码崩溃，但会降低模型理解操作语义的确定性。

### 修改

| 文件 | 改动 |
|------|------|
| `tests/test_server.py` | 新增 `/admin/retrieval/test` 无项目隐私边界测试：`u2` 不能检索到 `u1` 的 `user:u1` 私有姓名记忆。 |
| `tests/test_server.py` | 同一测试覆盖 `/admin/arbitration/dry-run`：写入仲裁候选也不能越界拿到其他用户私有记忆。 |
| `src/membrain/extractor.py` | 修正 schema prompt 中 `SUPERSEDE` 的拼写，减少 LLM 仲裁指令噪声。 |
| `tests/test_extractor.py` | 增加 prompt 守护断言，确保包含正确的 `SUPERSEDE creates a NEW memory`，且不再出现错误拼写。 |
| `tests/run_tests.py` | 将新增管理端分区测试纳入手写测试入口，检查数更新为 76。 |

### 验证

```
pytest targeted(local BGE): 2 passed
pytest(local BGE): 78 passed
run_tests(local BGE): 76 checks passed
eval-all(local BGE):
  extraction accuracy = 1.0
  retrieval recall@k = 0.7368
  retrieval mrr = 0.6316
  retrieval ndcg = 0.6591
  e2e accuracy = 1.0
  e2e pollution_rate = 0.0
  embedding backend = local_bge_large_zh
```

### 设计结论

管理界面的实验入口和外部 agent 的正式入口必须遵守同一套作用域规则。否则 UI 上测出来的“能搜到”，可能来自越界候选，而不是系统真实的记忆智能。

---

## 2026-06-22 · 修复无 workspace 检索越界与项目信号误判

### 背景

继续分析“CSM 会干扰无关对话”时发现两个问题：

1. 当外部 agent 没有传 `project_id/workspace_id` 时，adapter 会同时查个人分区和共享项目分区；共享项目分区为 `None` 时，底层检索会退化成“查全部活跃记忆”，导致其他用户的 `user:*` 私有记忆也可能被注入。
2. `_looks_like_project_memory()` 把“命令、流程、代码、规范”等弱词直接当项目信号。像“本机默认 Python 命令是 py -3.11”这种环境事实可能被误分到用户/项目空间，影响跨项目检索。

### 修改

| 文件 | 改动 |
|------|------|
| `src/membrain/adapters.py` | `retrieve()` 和写入仲裁只在存在 `shared_project_id` 时查询共享项目分区，避免 `None` 触发全库检索。 |
| `src/membrain/adapters.py` | `filter_scoped_results()` 拦截其他用户的 `user:*` 与 `*:user:*` 私有记忆，作为检索候选放大的防线。 |
| `src/membrain/adapters.py` | 将项目信号拆成强信号与锚定弱信号；“命令/流程/代码/规范”等弱词必须和项目/workspace/repo 锚点一起出现才判为项目记忆。 |
| `tests/test_adapters.py` | 新增无 workspace 姓名记忆私有测试，验证 `user:u1` 不会泄漏给 `u2`。 |
| `tests/test_adapters.py` | 新增无 workspace 项目式记忆测试，验证“这个项目依赖...”在没有 workspace 边界时不会变成全局。 |
| `tests/test_adapters.py` | 新增环境事实全局测试，验证“本机默认 Python 命令...”可跨用户/项目检索。 |
| `tests/run_tests.py` | 将 3 个分区边界测试纳入手写测试入口，检查数更新为 75。 |

### 验证

```
pytest tests/test_adapters.py(local BGE): 24 passed
pytest(local BGE): 77 passed
run_tests(local BGE): 75 checks passed
eval-all(local BGE):
  extraction accuracy = 1.0
  retrieval recall@k = 0.7368
  retrieval mrr = 0.6316
  retrieval ndcg = 0.6591
  e2e accuracy = 1.0
  e2e pollution_rate = 0.0
  embedding backend = local_bge_large_zh
```

### 设计结论

外部 agent 接入时，`None` 不能含糊地同时表示“全局事实”和“无项目上下文”。写入端可以把真正的环境事实存成全局，但检索端不能因为缺少 workspace 就查询全库；否则 CSM 会把无关记忆带进普通对话，形成你指出的干扰。

---

## 2026-06-22 · PiAgent state 兼容 workspace_id 与旧 memory_ids

### 背景

继续压测真实 pi 接入状态字段时发现两个兼容缝隙：

1. HTTP/OpenClaw payload 支持 `workspace_id`，但 `PiAgentMemoryHook` 的 state 只读取 `project_id`。如果 pi 扩展或其他 hook 使用 `workspace_id`，写入会落到 `user:<id>` 或全局，而不是 workspace 分区。
2. 包名迁移后 hook 已写入 `membrain_memory_ids`，但一些旧接入可能只保留 `csm_memory_ids`。`agent_end()` 若不 fallback，就不会强化本轮实际使用过的记忆。

### 修改

| 文件 | 改动 |
|------|------|
| `src/membrain/adapters.py` | `_scope_from_state()` 支持 `project_id` 或 `workspace_id`，与 HTTP payload 行为一致。 |
| `src/membrain/adapters.py` | `PiAgentMemoryHook.agent_end()` 的 `used_memory_ids` 支持 `membrain_memory_ids`，并 fallback 到旧 `csm_memory_ids`。 |
| `tests/test_adapters.py` | 新增测试：只传 `workspace_id` 的 PiAgent state 会把项目记忆写入 workspace 共享分区。 |
| `tests/test_adapters.py` | 新增测试：只传旧 `csm_memory_ids` 时仍会生成 UPDATE 并强化记忆。 |
| `tests/run_tests.py` | 将两个 PiAgent 兼容测试纳入手写测试入口，检查数更新为 72。 |

### 验证

```
pytest targeted(local BGE): 2 passed
pytest tests/test_adapters.py(local BGE): 21 passed
pytest tests/test_server.py(local BGE): 4 passed
pytest(local BGE): 74 passed
run_tests(local BGE): 72 checks passed
eval-all(local BGE):
  extraction accuracy = 1.0
  retrieval recall@k = 0.7368
  retrieval mrr = 0.6316
  retrieval ndcg = 0.6591
  e2e accuracy = 1.0
  e2e pollution_rate = 0.0
  embedding backend = local_bge_large_zh
```

### 设计结论

外部 agent 接入不应依赖单一字段命名。`project_id`、`workspace_id`、`membrain_*`、旧 `csm_*` 需要在 adapter 边界统一归一，否则迁移包名或接入不同 agent 时会产生难查的分区错误和强化丢失。

---

## 2026-06-22 · 清理陈旧发布产物并验证 wheel 依赖元数据

### 背景

继续检查发布/安装链路时发现：虽然 `pyproject.toml` 已改为正式依赖 `sentence-transformers`，但另一个 AI 留下的 `dist/` 和 `src/*.egg-info` 仍是旧元数据：

- `src/membrain.egg-info/PKG-INFO` 仍声明 `Provides-Extra: local-embedding`
- `Requires-Dist: sentence-transformers>=3.0.0; extra == "local-embedding"`
- README 描述仍是“sentence-transformers 可选，不装也能用关键词检索”

如果用户或 pi 扩展误用这些旧构建产物，实际安装结果会和源码要求不一致。

### 修改

| 文件 | 改动 |
|------|------|
| `.gitignore` | 增加 `dist/`，避免陈旧 wheel/sdist 留在工作树中。 |
| `.gitignore` | 增加 `build/`，避免 `pip wheel` 生成目录污染工作树。 |
| 根目录 / `src/` | 删除未跟踪的旧 `dist/`、`build/`、`src/membrain.egg-info`、`src/csm_agent.egg-info` 生成产物。 |
| `tests/test_packaging.py` | 增加 wheel metadata 检查：若存在 `.tmp/packaging_check/membrain-*.whl`，必须包含正式 `Requires-Dist: sentence-transformers`，且不能包含 `extra == "local-embedding"`。 |
| `tests/run_tests.py` | 将 wheel metadata 检查纳入手写测试入口，检查数更新为 70。 |

### 验证

```
pip wheel --no-deps --wheel-dir .tmp/packaging_check .
wheel METADATA:
  Name: membrain
  Version: 1.0.0
  Requires-Dist: sentence-transformers>=3.0.0

pytest tests/test_packaging.py(local BGE env): 3 passed
pytest(local BGE): 72 passed
run_tests(local BGE): 70 checks passed
eval-all(local BGE):
  extraction accuracy = 1.0
  retrieval recall@k = 0.7368
  retrieval mrr = 0.6316
  retrieval ndcg = 0.6591
  e2e accuracy = 1.0
  e2e pollution_rate = 0.0
  embedding backend = local_bge_large_zh
```

### 设计结论

源码正确不等于安装链路正确。对 agent sidecar 这种需要被 pi/OpenClaw/Hermes 调起的组件，wheel 元数据也是运行时契约的一部分，必须和本地 BGE-only 约束一致。

---

## 2026-06-22 · 文档一致性与 Windows nul 残留清理

### 背景

继续复测另一 AI 改动后的状态，发现两类非核心代码但会影响真实使用的问题：

1. `INTEGRATION.md` 仍把 `sentence-transformers` 描述成“向量后端升级”，并在文件清单中声称 `src/membrain` 未修改；这与当前本地 BGE-only 运行约束和实际代码状态不一致。
2. 根目录存在未跟踪的 `nul` 文件。它是 Windows 设备名冲突文件，会导致 `rg .` 报 `函数不正确`，影响后续代码审查和测试定位。

### 修改

| 文件 | 改动 |
|------|------|
| `INTEGRATION.md` | 将本地语义向量说明改为“安装项目依赖会安装 sentence-transformers，手动运行时显式指定本地模型”。 |
| `INTEGRATION.md` | 更新文件清单，移除 `src/membrain` 未修改的错误描述。 |
| `INTEGRATION.md` | 将后续建议中的“向量后端升级”改为“检索质量评测”，保持本地 BGE-only 约束。 |
| `tests/test_packaging.py` | 新增文档守护测试，禁止 README、INTEGRATION、pi 扩展继续宣传 optional/fallback embedding。 |
| `tests/run_tests.py` | 将文档守护测试纳入手写测试入口，检查数更新为 69。 |
| 根目录 | 删除异常未跟踪文件 `nul`，恢复 `rg` 全仓搜索可用性。 |

### 验证

```
pytest targeted(local BGE): 3 passed
pytest(local BGE): 71 passed
run_tests(local BGE): 69 checks passed
eval-all(local BGE):
  extraction accuracy = 1.0
  retrieval recall@k = 0.7368
  retrieval mrr = 0.6316
  retrieval ndcg = 0.6591
  e2e accuracy = 1.0
  e2e pollution_rate = 0.0
  e2e stale_rate = 0.0
  strength accuracy = 1.0
  embedding backend = local_bge_large_zh
```

### 设计结论

文档和发布入口也是接入链路的一部分。只要文档继续暗示“可不装 embedding / 可降级关键词”，外部 agent 接入时就可能以错误环境运行。现在 README、INTEGRATION、pi 扩展和 pyproject 对本地 BGE-only 约束保持一致。

---

## 2026-06-22 · 复测另一 AI 改动后的接入兼容与本地 BGE 依赖

### 背景

另一 AI 对项目做了较大调整：包名从 `csm_agent` 改为 `membrain`，并新增发布/README/扩展相关文件。复测发现核心测试可以通过，但存在两个真实接入风险：

1. Pi Agent hook 状态字段半新半旧：提问前写入 `membrain_memory_context` / `membrain_memory_ids`，结束后仍只输出 `csm_write_plan` / `csm_committed_ids`，且显式记忆只读取 `csm_explicit_memories`。
2. README 和打包元数据把 `sentence-transformers` 描述成 optional，和“运行时全部使用本地 bge-large-zh-v1.5，不允许静默降级”的项目要求冲突。

### 修改

| 文件 | 改动 |
|------|------|
| `src/membrain/adapters.py` | `PiAgentMemoryHook.before_agent_start()` 双写 `membrain_*` 与兼容的 `csm_*` 上下文字段。 |
| `src/membrain/adapters.py` | `PiAgentMemoryHook.agent_end()` 同时读取 `membrain_explicit_memories` 与旧 `csm_explicit_memories`。 |
| `src/membrain/adapters.py` | `agent_end()` 双写 `membrain_write_plan` / `membrain_committed_ids` 与旧 `csm_write_plan` / `csm_committed_ids`。 |
| `tests/test_adapters.py` | 扩展 PiAgent hook 测试，验证新旧字段兼容、`membrain_explicit_memories` 可触发 ADD。 |
| `pyproject.toml` | 将 `sentence-transformers>=3.0.0` 提升为运行时正式依赖，移除空的 optional extra。 |
| `tests/test_packaging.py` | 新增打包测试，确保 `sentence-transformers` 不会再次从正式依赖中消失。 |
| `README.md` | 移除“sentence-transformers 可选 / 不装也能用关键词检索”的说法，改为明确本地 BGE 是运行时要求。 |
| `pi-extension/mb-memory.ts` | 安装提示改为强调本地 BGE embedding 是运行时要求。 |
| `WORKLOG.md` | 恢复被删除的工作记录文件，并记录本轮修复。 |

### 验证

```
pytest targeted(local BGE): 2 passed
pytest(local BGE): 70 passed
run_tests(local BGE): 68 checks passed
eval-all(local BGE):
  extraction accuracy = 1.0
  retrieval recall@k = 0.7368
  retrieval mrr = 0.6316
  retrieval ndcg = 0.6591
  e2e accuracy = 1.0
  e2e pollution_rate = 0.0
  e2e stale_rate = 0.0
  strength accuracy = 1.0
  embedding backend = local_bge_large_zh
  embedding synonym/paraphrase/cross_lang recall = 1.0 / 1.0 / 1.0
```

### 设计结论

包名迁移可以接受，但外部接入字段不能半迁移。当前策略是新字段 `membrain_*` 为主，同时保留旧 `csm_*` 字段，避免 pi / OpenClaw / Hermes 现有接入突然断裂。本地 BGE 是运行时核心能力，不再作为 optional extra 表达。

### 后续关注

- 根目录存在一个未跟踪的 `nul` 文件，会导致 `rg .` 报 Windows 设备名错误；本轮未删除，后续可确认来源后清理。
- `eval-all` 的 MRR/NDCG 低于早前记录，但 recall/e2e/pollution 仍稳定；后续应继续围绕排序质量做细测。

---
