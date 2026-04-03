# 12. Phase 8 真实成功率验证矩阵

> 用途：把 Phase 7B 的“单条真实成功闭环”升级为“多样例、可复现、可回归”的稳定性基线。  
> 数据来源：`scripts/run_phase8_real_host_matrix.py --allow-side-effects` 导出的矩阵文件，默认落到 `backend/data/host_validation_matrix.latest.json`。  
> 约束：不记录真实 token；真实宿主 Base URL 与 token 通过本地环境变量注入。

> 当前说明：这份矩阵现在只保留为验证产物，用于回看哪些真实组合曾成功、哪些曾被阻断。当前运行时不再用它做 recommendation / strategy 决策，当前固定语义见 [docs/14_架构收缩与语义归一说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/14_架构收缩与语义归一说明.md)。

## 12.1 当前基线摘要

当前最新矩阵包含 9 条真实宿主样例，统计结果如下：

| 指标 | 数量 |
|---|---|
| sample_count | 9 |
| verified_count | 4 |
| unverified_count | 5 |
| stable_count | 3 |
| single_sample_count | 1 |
| blocked_count | 5 |
| flaky_count | 0 |

当前建议这样理解这些状态：

- `stable`：已至少有多条真实样例证明该类路径稳定成立。
- `single_sample`：已经真实成功，但目前只有单样例，不应过度外推。
- `blocked`：真实宿主确实接受了前置请求，但链路后段被明确业务语义阻断。
- `verified`：接口与当前样例链路已拿到真实正向依据。
- `unverified`：接口路径或局部语义可知，但当前组合尚未形成稳定正向结论。

## 12.2 当前样例矩阵

| sample_id | 类型 | dispatch 路径 | path handoff | transfer/name | transfer/manual | organize 结果 | verification_state | stability_state | 结论 |
|---|---|---|---|---|---|---|---|---|---|
| `ordinary_accident_media` | `search/media` | `download_media` | `resolved_from_history_download` | `preview_ready` | `failed` | `failed` | `unverified` | `blocked` | 宿主能搜索、下载、回读路径，但 `transfer/manual` 对该 history/download 文件样例拒绝整理。 |
| `snow_white_media` | `search/media` | `download_media` | `resolved_from_history_download` | `preview_ready` | `failed` | `failed` | `unverified` | `blocked` | 与上类似，说明 `download_media + history/download` 并不等价于稳定 organize 成功。 |
| `argentina_1985_media` | `search/media` | `download_media` | `N/A` | `N/A` | `N/A` | `N/A` | `unverified` | `blocked` | 该样例在 dispatch 阶段就被宿主返回 `任务添加失败`，尚未进入 handoff 与 organize。 |
| `ordinary_accident_title_add` | `search/title` | `download_add` | `resolved_from_history_download` | `preview_ready` | `applied` | `applied` | `verified` | `single_sample` | 当前唯一完整的 `search -> download/add -> history/download -> transfer/manual` 真实成功闭环。 |
| `snow_white_title_add` | `search/title` | `download_add` | `resolved_from_history_download` | `preview_ready` | `failed` | `failed` | `unverified` | `blocked` | `download_add` 并非对所有 title 样例都能稳定导出可整理输入。 |
| `argentina_1985_title_add` | `search/title` | `download_add` | `resolved_from_history_download` | `failed` | `failed` | `failed` | `unverified` | `blocked` | 宿主在该 title 样例上仍会给出明确业务拒绝。 |
| `transfer_history_fallback` | `history/transfer` | `N/A` | `resolved_from_history_transfer` | `N/A` | `N/A` | `N/A` | `verified` | `stable` | 证明 `history/transfer` 是可靠的 organize path fallback 来源。 |
| `transfer_replay_1` | `history/transfer-replay` | `N/A` | `resolved_from_history_transfer` | `preview_ready` | `applied` | `applied` | `verified` | `stable` | 真实宿主 replay 样例一，证明 `history/transfer` 回放可稳定形成 host organize success。 |
| `transfer_replay_2` | `history/transfer-replay` | `N/A` | `resolved_from_history_transfer` | `preview_ready` | `applied` | `applied` | `verified` | `stable` | 真实宿主 replay 样例二，进一步确认 `history/transfer` 路径回灌更稳。 |

## 12.3 Phase 8 的稳定性结论

### 已从 single-sample 升级到 multi-sample 的点

- `history/transfer -> path handoff -> organize preview/apply`
  - 已有 3 条真实依据：
    - `transfer_history_fallback`
    - `transfer_replay_1`
    - `transfer_replay_2`
- `search/media` 正向搜索语义
  - 已有多条真实 `search/media` 正向返回，不再只是 Phase 7A 的路径/负向语义确认。

### 仍然只是 single-sample 的点

- `search/title -> download_add -> history/download -> transfer/manual -> organize`
  - 当前只有 `ordinary_accident_title_add` 一条真实完整成功样例。

### 当前明确被真实宿主阻断的组合

- `download_media + history/download + transfer/manual`
  - 已有多条样例命中 `没有找到可整理的媒体文件`。
  - 说明宿主 download 成功不自动等价于 organize 输入可被 transfer/manual 接受。
- `download_media` 的部分媒体样例
  - 可能在 dispatch 阶段就被真实宿主业务语义拒绝为 `任务添加失败`。
  - 这类样例应保持 `blocked`，不要误判为 handoff 或 organize 层故障。
- 部分 `download_add` title 样例
  - 宿主能接受请求，但后续 organize 仍可能失败。

## 12.3A Phase 9 策略提炼

Phase 9 不再只“记录这些差异”，而是把它们转成默认行为：

- 默认推荐路径：
  - `history/transfer -> organize replay/apply`
- 保留但不默认：
  - `search/title -> download_add -> history/download -> transfer/manual -> organize`
- 显式阻断：
  - `download_media + resolved_from_history_download -> organize apply`

也就是说，当前矩阵的用途已经从“回看历史”升级成“解释运行时策略决策”：

- `stable`：作为推荐路径
- `single_sample`：允许继续尝试，但必须显示风险
- `blocked`：默认阻断或明确提示，不再默默尝试

## 12.4 path handoff 稳定性结论

当前 MusicPilot 对真实宿主 path handoff 的优先级与结论如下：

1. `resolved_from_history_download`
   - 仍是 dispatch 成功后的第一优先来源。
   - 优点：离下载结果最近，可直接附在 dispatch result、candidate raw payload 与 organize record 中。
   - 风险：不是所有 `history/download` 路径都能被 `transfer/manual` 稳定接受。
2. `resolved_from_history_transfer`
   - 是当前更稳定的 organize fallback 来源。
   - 当 `history/download` 命中但后续 transfer 语义失败时，优先尝试 `history/transfer` replay 更符合真实宿主行为。
3. `pending_history_sync`
   - 表示下载成功，但宿主 history 尚未完成同步。
   - MusicPilot 现在会按 `MUSICPILOT_HOST_HISTORY_SYNC_RETRY_ATTEMPTS` 和 `MUSICPILOT_HOST_HISTORY_SYNC_RETRY_INTERVAL_SECONDS` 做最小重试。
4. `handoff_unresolved`
   - 表示 `history/download` 与 `history/transfer` 都未能给出可用来源。
   - 这类结果应保持 `unverified`，不要伪装成可整理。

## 12.5 如何复跑 Phase 8 矩阵

推荐先在本机私有环境准备：

```bash
export MUSICPILOT_REAL_HOST_BASE_URL="${REAL_MOVIEPILOT_BASE_URL}"
export MUSICPILOT_REAL_HOST_API_TOKEN="${REAL_MOVIEPILOT_TOKEN}"
```

然后执行：

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot
backend/.venv/bin/python scripts/run_phase8_real_host_matrix.py --allow-side-effects
```

常用可选参数：

```bash
backend/.venv/bin/python scripts/run_phase8_real_host_matrix.py \
  --allow-side-effects \
  --output backend/data/host_validation_matrix.latest.json \
  --handoff-attempts 3 \
  --handoff-interval 1.0 \
  --organize-root-path /downloads/media/movie
```

回归后可通过以下位置查看结果：

- `backend/data/host_validation_matrix.latest.json`
- `/health`
- `/api/probe/health`
- `/api/probe/validation-matrix`
- `jobs/{id}`、`jobs/{id}/results`
- `downloads/dispatch`
- `organize/preview`、`organize/apply`、`organize/jobs/{id}`

## 12.6 当前仍需继续补的点

- `download_add` 的多样例稳定成功，还没有从 `single_sample` 升级到 `stable`。
- `download_media` 目前能稳定拿到真实搜索、真实下载和真实 path handoff，但 organize apply 仍有多条真实阻断。
- `search/media + download_media + organize` 还不能标为 `verified`。
- 生产级自动回调、自动整理、刮削和媒体库刷新不在本轮范围内。
