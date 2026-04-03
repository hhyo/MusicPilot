# 08. Phase 5 宿主接入联调说明

> 用途：说明 Phase 5 当前已经收口到哪一步、如何在 `mock / prefer_host / strict_host` 之间切换、哪些接口已经验证、哪些仍待真实 MoviePilot 宿主确认。

## 8.1 当前目标

Phase 5 的目标不是宣称“已经真实接通宿主全部能力”，而是把关键边界升级为：

- `HostSearchAdapter = mock + host-backed selectable`
- `DownloadDispatchAdapter = mock + host-backed selectable`
- 能基于 probe / capability / settings 做集中决策
- 当宿主能力缺失、配置缺失或运行失败时可安全降级回 mock
- 在 API 返回与页面里能看到 `adapter_mode / dispatch_backend / fallback_reason`

## 8.2 当前接入状态总表

| 接入点 | 当前状态 | 说明 |
|---|---|---|
| Host probe mock adapter | verified | 已在本仓库内运行验证，通过 `/api/probe/*` 可见统一结构。 |
| Host probe real adapter skeleton | verified | 已对“本地 host stub”完成请求构造与响应解析验证；对真实 MoviePilot 宿主仍是 `unverified`。 |
| Host search mock adapter | verified | 已在 SearchJob 链路中跑通。 |
| Host search real adapter skeleton | verified | 已对 `scripts/host_integration_stub.py` 完成联调；对真实 MoviePilot 宿主仍是 `unverified`。 |
| Download dispatch mock adapter | verified | 已在 `/downloads/dispatch` 路由中跑通。 |
| Download dispatch real adapter skeleton | verified | 已对 `scripts/host_integration_stub.py` 完成联调；对真实 MoviePilot 宿主仍是 `unverified`。 |
| Notify real adapter | placeholder | 仅保留 endpoint 骨架与配置入口。 |
| Config real adapter | placeholder | 仅保留 endpoint 骨架与配置入口。 |
| 真实 MoviePilot 宿主接口语义 | unverified | 需要后续人工联调、记录真实请求响应样例后再升级为 `verified`。 |

## 8.3 配置项

可通过 `.env` 或环境变量配置：

```env
MUSICPILOT_HOST_INTEGRATION_ENABLED=true
MUSICPILOT_HOST_BASE_URL=http://127.0.0.1:19090
MUSICPILOT_HOST_VERIFICATION_STATE=unverified
MUSICPILOT_HOST_HEALTH_PATH=/health
MUSICPILOT_HOST_SITES_PATH=/sites
MUSICPILOT_HOST_SEARCH_PATH=/search
MUSICPILOT_HOST_DOWNLOADERS_PATH=/downloaders
MUSICPILOT_HOST_DISPATCH_PATH=/dispatch
MUSICPILOT_HOST_SEARCH_STRATEGY=prefer_host
MUSICPILOT_HOST_DISPATCH_STRATEGY=prefer_host
MUSICPILOT_HOST_FALLBACK_TO_MOCK=true
```

策略说明：

- `mock`
  - 永远使用 mock adapter，适合本地默认开发。
- `prefer_host`
  - 能力存在时优先走 host-backed adapter skeleton。
  - 若能力缺失、配置缺失或运行失败，且 `MUSICPILOT_HOST_FALLBACK_TO_MOCK=true`，则自动回退到 mock。
- `strict_host`
  - 要求必须使用 host-backed adapter。
  - 若能力缺失或配置不完整，接口会返回失败，不会静默回退。

## 8.4 如何验证

### A. 默认 mock 模式

1. 不配置 `MUSICPILOT_HOST_INTEGRATION_ENABLED` 或保持为 `false`
2. 启动 backend
3. 查看：
   - `/health`
   - `/api/probe/health`
   - `POST /api/v1/plugin/musicpilot/jobs/{id}/run`
   - `POST /api/v1/plugin/musicpilot/downloads/dispatch`
4. 预期：
   - `active_search_adapter=mock_host_search`
   - `active_dispatch_adapter=mock_download_dispatch`

### B. 本地 host stub + prefer_host

1. 启动 stub：

```bash
python3 scripts/host_integration_stub.py
```

2. 配置 `prefer_host` 并启动 backend
3. 预期：
   - `/health` 与 `/api/probe/health` 中出现 `real_host_search / real_download_dispatch`
   - SearchJob candidates 中 `adapter_mode=host`
   - dispatch result 中 `dispatch_backend=host`

### C. strict_host 失败验证

1. 开启 `MUSICPILOT_HOST_INTEGRATION_ENABLED=true`
2. 设置：
   - `MUSICPILOT_HOST_SEARCH_STRATEGY=strict_host`
   - `MUSICPILOT_HOST_DISPATCH_STRATEGY=strict_host`
3. 不启动 stub 或不提供合法 `HOST_BASE_URL`
4. 预期：
   - `/health` 仍可查看 wiring 状态
   - SearchJob 执行与 dispatch 调用会报错
   - 错误原因中能看到 capability / fallback 相关信息

## 8.5 如何查看当前 active adapter

- `GET /health`
  - 查看 `data.host_integration.active_search_adapter`
  - 查看 `data.host_integration.active_dispatch_adapter`
- `GET /api/probe/health`
  - 查看 `data.runtime_state`
- `GET /api/v1/plugin/musicpilot/jobs/{id}`
  - 查看 `data.adapter_resolution`
- `GET /api/v1/plugin/musicpilot/jobs/{id}/results`
  - 查看 `data.adapter_resolution` 与每个 candidate 的 `adapter_resolution`
- `POST /api/v1/plugin/musicpilot/downloads/dispatch`
  - 查看 `data.dispatch_backend`、`data.fallback_reason`、`data.adapter_resolution`

## 8.6 与真实 MoviePilot 宿主的边界声明

- `verified`
  - 仅表示本仓库已经对 mock 或本地 stub 进行了可重复验证。
- `unverified`
  - 表示代码骨架已就位，但尚未拿真实 MoviePilot 宿主完成接口语义确认。
- `placeholder`
  - 表示只保留接口边界、配置入口或探针骨架，尚未具备有效联调样本。

当前仓库**没有**宣称“已真实接通宿主全部能力”。  
真实 MoviePilot 宿主联调结果，请继续记录到 [docs/07_宿主能力验证记录模板.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/07_宿主能力验证记录模板.md)。
