# 32. 真实宿主 subscription 主链运行态验证

## 目标

验证 `MusicPilot` 在 **真实 MoviePilot 插件进程** 中，`subscription -> run` 这条主链是否已经跟上当前最新 runtime，而不是停留在旧的 `manual_pending` 行为。

本次验证重点不是“真实 PT 下载成功”，而是确认：

1. 插件已按最新 `plugin_runtime` 安装到宿主 `app/plugins/musicpilot`
2. 宿主真实插件 API 可以创建订阅并执行一次 run
3. 当前主链会推进到 `dispatched + preview_ready`
4. 结果 detail 与 summary 已反映最新自动 dispatch / binding preview 行为

## 验证环境

- 宿主源码路径：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot`
- 宿主运行态：`CONFIG_DIR=/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev`
- 宿主 Python：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/.venv/bin/python`
- 插件数据库：临时 `sqlite:////tmp/musicpilot-host-subscription-runtime-2.db`
- 鉴权：`X-API-KEY: moviepilot-dev-token`
- 元数据模式：`seed`
- 榜单模式：`mock`
- scheduler：关闭（只验证单次 run）

## 关键前置事实

### 1. live 3001 进程不能作为可靠验证对象

直接请求 `http://127.0.0.1:3001/api/v1/plugin/musicpilot/health` 与 `/openapi.json` 返回 `404`。

这说明：

- 当前 3001 上的进程并不能保证已加载最新本地插件代码
- 后续验证应以 **宿主进程内 `TestClient(app)`** 为准

### 2. 宿主已安装插件副本必须与当前 `plugin_runtime` 同步

验证前发现：

- `/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/app/plugins/musicpilot`
- 与
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot`

并不一致。

同步后重新验证，才得到当前最新主链行为。

## 验证步骤

1. 将当前 `plugin_runtime/plugins/musicpilot/` 同步到宿主 `app/plugins/musicpilot/`
2. 在宿主自己的 venv 中构建 `app.factory.app`
3. 用宿主 `TestClient` 调用真实插件 API：
   - `POST /api/v1/plugin/musicpilot/subscriptions`
   - `POST /api/v1/plugin/musicpilot/subscriptions/{id}/run`
   - `GET /api/v1/plugin/musicpilot/subscriptions/runs/{run_id}`

## 验证结果

### 1. 订阅创建成功

- `create_status = 200`

### 2. 主链已推进到 `dispatched`

- `run_status = 200`
- `execution_status = dispatched`
- `run_detail_execution_status = dispatched`

### 3. organize preview 已生成

- `organize_status = preview_ready`
- `run_detail_organize_status = preview_ready`

### 4. summary 已体现最新链路

`summary_json` 中出现：

- `dispatch_status = mock_submitted`
- `dispatch_backend = mock`
- `binding_id = ...`
- `last_dispatched_candidate_id = ...`
- `organize_preview_id = ...`

这说明当前真实宿主插件 API 下，run 已不是旧的“只搜索后停在 manual_pending”，而是：

`metadata -> search -> best candidate auto dispatch -> binding-based organize preview`

## 结论

结论已经比较明确：

1. **真实宿主插件 API 下，subscription 主链已跟上当前最新 runtime。**
2. 在默认 `seed + mock search/dispatch` 运行态中，真实 run 会稳定停在：
   - `execution_status=dispatched`
   - `organize_status=preview_ready`
3. 当前没有继续自动 `apply`，不是插件 API 没跑通，而是因为该运行态下没有真实本地源文件可供后续 organize apply 使用。

## 当前边界

这次验证确认的是：

- 主链推进逻辑真实生效
- 真实插件 API 已使用最新 runtime

这次没有验证的是：

- 真实 PT 搜索/下载能力
- 真实本地源文件下的自动 `apply`

这些属于下一阶段的 acquisition / dispatch 真实闭环问题，不属于本次验证范围。
