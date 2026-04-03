# 13. Phase 9 策略收敛与交付说明

> 用途：把 Phase 8 的真实宿主验证矩阵收敛成默认更稳、更适合演示与交付的运行策略。  
> 范围：只处理 `search -> dispatch -> path handoff -> organize` 这条既有链路，不扩展新业务域。  
> 约束：所有结论都以真实宿主矩阵与已验证样例为准，不用 mock/stub 推断真实稳定性。

> 当前说明：本文保留 Phase 9 的历史收敛结论，但从当前轮开始，MusicPilot 不再继续扩展或依赖通用 strategy / matrix / recommendation 运行时体系。当前实现以固定接口语义、固定场景调用规则和单一权威数据来源为准，见 [docs/14_架构收缩与语义归一说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/14_架构收缩与语义归一说明.md)。

## 13.1 当前策略收敛结论

当前 MusicPilot 已不再只是“知道有哪些组合曾经成功过”，而是把这些结果收敛成了三类策略：

### 推荐路径

- `history/transfer -> organize replay/apply`
  - 当前矩阵结论：`stable`
  - 适合用于演示、联调回归与交付验收。
- `prefer_host + matrix-aware strategy`
  - 当前会优先读取真实宿主能力，同时根据矩阵结果解释当前路径的风险等级。

### 保留但不默认的路径

- `search/title -> download_add -> history/download -> transfer/manual -> organize`
  - 当前矩阵结论：`single_sample`
  - 可保留用于受控演示或追加验证，但不应对外宣称为“稳定默认路径”。

### 显式阻断的路径

- `download_media + resolved_from_history_download -> organize apply`
  - 当前矩阵结论：`blocked`
  - 已有多条真实样例证明这条链路更容易命中宿主业务拒绝。
  - Phase 9 开始，系统会在 organize apply 前显式给出阻断决策，而不是默默走到失败。

## 13.2 Phase 9 默认策略

### 搜索输入优先级

1. 已有可回放 organize 样例时，优先走 `history/transfer` replay。
2. 需要新建 dispatch 时，允许继续使用 `search/title` 和 `search/media` 获取候选，但仅作为“候选来源”，不直接代表 organize 稳定性。

### dispatch endpoint 选择

1. 当候选中存在可用 `media_reference` 时，优先选择 `download_add`。
2. `download_media` 保留，但不作为默认演示路径。
3. 若矩阵已证明某组合是 `blocked`，不会再伪装成“可放心自动尝试”。

### path handoff 优先级

1. dispatch 成功后仍先读取 `history/download`。
2. 但在 organize 侧，`history/transfer` 已被提升为更稳的 replay / fallback 来源。
3. 当 `history/download` 只证明“下载成功”，但不代表 organize 可成功时，策略结果会明确标成 `blocked` 或 `single_sample`。

### organize apply 触发条件

- `stable`：允许直接作为推荐路径展示。
- `single_sample`：允许继续执行，但必须显示风险说明。
- `blocked`：默认阻断，返回明确 reason 与推荐替代路径。

## 13.3 推荐运行模式

### 推荐交付模式

```bash
export MUSICPILOT_HOST_INTEGRATION_ENABLED=true
export MUSICPILOT_HOST_SEARCH_STRATEGY=prefer_host
export MUSICPILOT_HOST_DISPATCH_STRATEGY=prefer_host
export MUSICPILOT_HOST_ORGANIZE_STRATEGY=prefer_host
export MUSICPILOT_HOST_FALLBACK_TO_MOCK=true
export MUSICPILOT_HOST_VALIDATION_MATRIX_PATH=/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/data/host_validation_matrix.latest.json
```

说明：

- `prefer_host` 仍保留 mock 安全回退。
- 但 Phase 9 下的 `prefer_host` 已不是“能试就试”，而是会结合矩阵给出稳定性决策。

### 不推荐的演示方式

- 直接把 `download_media` 当成默认 organize 主路径。
- 把 `single_sample` 组合当成稳定成功路径对外演示。
- 在未查看 matrix summary 的情况下盲目复跑真实副作用样例。

## 13.4 演示路径建议

### 推荐演示路径

1. 先展示 `/health` 与 `/api/probe/validation-matrix`
   - 让验收方看到当前 active adapter、matrix summary 与推荐策略。
2. 展示 `history/transfer` replay 样例
   - 这是当前最稳的真实 host organize 成功路径。
3. 如需展示从搜索到派发：
   - 仅演示 `search/title -> download_add` 单样例路径，并明确标注 `single_sample`。

### 不建议在演示中使用的路径

- `download_media + history/download -> organize apply`
- 任何当前矩阵已标为 `blocked` 的组合

## 13.5 MVP 验收清单

交付时建议至少逐项确认：

- `/health` 可返回 active adapter、matrix summary、strategy summary
- `/api/probe/health` 可返回 runtime wiring 与 strategy summary
- `/api/probe/validation-matrix` 可返回样例矩阵摘要
- `jobs/{id}/results` 中可看到 candidate 的 `strategy_decision`
- `downloads/dispatch` 中可看到 `dispatch_backend`、`path_handoff`、`strategy_decision`
- `organize/preview` 与 `organize/apply` 中可看到 `organize_backend`、`path_handoff`、`strategy_decision`
- `blocked` 组合会被显式提示，而不是无声失败
- 前端 SearchJobPanel / SubscriptionsView 能看到 `backend / verification / fallback / matrix status / strategy`

## 13.6 当前 verified / single_sample / blocked 边界

### verified 且 stable

- `history/transfer` 作为 organize replay / fallback 来源
- `transfer replay -> organize apply`

### verified 但 only single-sample

- `search/title -> download_add -> history/download -> transfer/manual -> organize`

### blocked

- `download_media + resolved_from_history_download -> organize apply`

### 仍需人工判断

- `download_add` 何时能从 `single_sample` 升级为 `stable`
- 某些 `search/media` 候选是否只适合 dispatch，不适合 organize

## 13.7 交付说明

推荐把当前仓库作为“可试运行、可演示、可继续联调”的版本交付，而不是“所有真实组合都已完全稳定”的版本交付。

交付时应明确说明：

- 当前系统已具备真实宿主矩阵驱动的策略收敛能力
- 当前默认行为会优先稳态路径，而不是盲目尝试所有 host-backed 路径
- 当前仍保留 mock 作为安全回退
- 当前仍存在 `single_sample` 与 `blocked` 边界，已经在接口和页面中透明暴露
