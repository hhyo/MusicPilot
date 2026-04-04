# 08. Phase 5 宿主接入联调说明

> 用途：说明 Phase 5 当前已经收口到哪一步、如何在 `mock / prefer_host / strict_host` 之间切换、哪些接口已经验证、哪些仍待真实 MoviePilot 宿主确认。

> Phase 8 更新：真实宿主联调已经从“单条成功样例”推进到“多样例验证矩阵”。  
> 最新稳定性结论请同时参考 [docs/12_Phase8_真实成功率验证矩阵.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/12_Phase8_真实成功率验证矩阵.md)。

## 8.1 当前目标

Phase 5 的目标不是宣称“已经真实接通宿主全部能力”，而是把关键边界升级为：

- `HostSearchAdapter = mock + host-backed selectable`
- `DownloadDispatchAdapter = mock + host-backed selectable`
- 能基于 probe / capability / settings 做集中 adapter 选择
- mock 仅作为开发与显式 mock 模式下的边界
- 在 API 返回与页面里能看到 `adapter_mode / dispatch_backend / fallback_reason`

## 8.2 当前接入状态总表

| 接入点 | 当前状态 | 说明 |
|---|---|---|
| Host probe mock adapter | verified | 已在本仓库内运行验证，通过 `/api/probe/*` 可见统一结构。 |
| Host probe real adapter skeleton | verified | 已对真实 MoviePilot 宿主完成 API 前缀、鉴权与低风险连通性验证。 |
| Host search mock adapter | verified | 已在 SearchJob 链路中跑通。 |
| Host search real adapter skeleton | verified | `search/title`、`search/last` 与 `search/media` 已拿到真实正向样例；但不同样例的后续 organize 成功率仍需结合 Phase 8 矩阵判断。 |
| Download dispatch mock adapter | verified | 已在 `/downloads/dispatch` 路由中跑通。 |
| Download dispatch real adapter skeleton | verified | `/api/v1/download/` 已有多条真实成功样例；`download/add` 已补到 1 条真实成功样例，但稳定性仍未达到多样例级别。 |
| Notify real adapter | placeholder | 仅保留 endpoint 骨架与配置入口。 |
| Config real adapter | placeholder | 仅保留 endpoint 骨架与配置入口。 |
| 真实 MoviePilot 宿主接口语义 | unverified | Phase 7A 已完成首轮真实宿主差异收敛，详见 `docs/10_Phase7A_真实宿主语义验证与差异收敛.md`。 |

## 8.3 配置项

可通过 `.env` 或环境变量配置：

```env
MUSICPILOT_HOST_INTEGRATION_ENABLED=true
MUSICPILOT_HOST_BASE_URL=http://127.0.0.1:3000
MUSICPILOT_HOST_AUTH_TOKEN=<local env only>
MUSICPILOT_HOST_AUTH_MODE=x_api_key
MUSICPILOT_HOST_API_KEY_HEADER_NAME=X-API-KEY
MUSICPILOT_HOST_VERIFICATION_STATE=unverified
MUSICPILOT_HOST_HEALTH_PATH=/api/v1/search/last
MUSICPILOT_HOST_SITES_PATH=/api/v1/site
MUSICPILOT_HOST_SEARCH_TITLE_PATH=/api/v1/search/title
MUSICPILOT_HOST_SEARCH_MEDIA_PATH=/api/v1/search/media
MUSICPILOT_HOST_SEARCH_LAST_PATH=/api/v1/search/last
MUSICPILOT_HOST_DOWNLOADERS_PATH=/api/v1/download/clients
MUSICPILOT_HOST_DOWNLOAD_ADD_PATH=/api/v1/download/add
MUSICPILOT_HOST_DOWNLOAD_MEDIA_PATH=/api/v1/download/
MUSICPILOT_HOST_HISTORY_DOWNLOAD_PATH=/api/v1/history/download
MUSICPILOT_HOST_HISTORY_TRANSFER_PATH=/api/v1/history/transfer
MUSICPILOT_HOST_SEARCH_STRATEGY=prefer_host
MUSICPILOT_HOST_DISPATCH_STRATEGY=prefer_host
```

策略说明：

- `mock`
  - 永远使用 mock adapter，适合本地默认开发。
- `prefer_host`
  - 能力存在时优先走 host-backed adapter skeleton。
  - 当前已不再把它当成业务失败时的自动 mock 回退开关；host 运行失败会直接暴露错误。
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

### B. 真实 MoviePilot 宿主 + prefer_host

1. 配置 `prefer_host`、`X-API-KEY` 和真实 `HOST_BASE_URL`
2. 启动 backend
3. 预期：
   - `/health` 与 `/api/probe/health` 中出现 `real_host_search / real_download_dispatch`
   - SearchJob candidates 中 `adapter_mode=host`
   - dispatch result 中 `dispatch_backend=host`
   - 若宿主返回 `success=true`，还能看到 `path_handoff`
   - 若宿主拒绝 payload，仍会保留 `dispatch_backend=host`，并给出真实 `failure_reason`

### C. 本地 host stub + prefer_host

1. 启动 stub：

```bash
python3 scripts/host_integration_stub.py
```

2. 配置 `prefer_host` 并启动 backend
3. 预期：
   - 行为与真实宿主保持同一套 resolver 与错误暴露逻辑
   - 但返回语义仍然只是本地 stub，不能替代真实宿主验证

### D. strict_host 失败验证

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
  - 查看 `data.path_handoff` 与 `data.host_response_summary`

## 8.6 与真实 MoviePilot 宿主的边界声明

- `verified`
  - 仅表示本仓库已经对 mock 或本地 stub 进行了可重复验证。
- `unverified`
  - 表示代码骨架已就位，但尚未拿真实 MoviePilot 宿主完成接口语义确认。
- `placeholder`
  - 表示只保留接口边界、配置入口或探针骨架，尚未具备有效联调样本。

当前仓库**没有**宣称“已真实接通宿主全部能力”。  
真实 MoviePilot 宿主联调结果，请继续记录到 [docs/07_宿主能力验证记录模板.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/07_宿主能力验证记录模板.md)。

Phase 7A 的真实宿主差异与验证结论，见 [docs/10_Phase7A_真实宿主语义验证与差异收敛.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/10_Phase7A_真实宿主语义验证与差异收敛.md)。  
Phase 7B 的真实成功样例闭环，见 [docs/11_Phase7B_真实成功样例闭环.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/11_Phase7B_真实成功样例闭环.md)。
