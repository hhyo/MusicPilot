# 09. Phase 6 Organize 联调说明

> 用途：说明 Phase 6 当前 organize 已收口到哪一步、如何在 `mock / prefer_host / strict_host` 之间切换、preview/apply 的现状，以及哪些点已经验证、哪些仍待真实 MoviePilot 宿主确认。

## 9.1 当前目标

Phase 6 的目标不是宣称“已经真实完成文件移动、硬链接、刮削入库或媒体库刷新”，而是把 organize boundary 升级为：

- `OrganizeAdapter = mock + host-backed selectable`
- `preview -> apply` 的最小状态流
- 基于 capability / settings / strategy 的集中 resolver
- 可记录 `organize_backend / organize_status / fallback_reason / verification_state`
- 在 API 与页面里能明确看见当前到底走的是 mock 还是 host-backed skeleton

## 9.2 当前 organize 接入状态总表

| 接入点 | 当前状态 | 说明 |
|---|---|---|
| Mock organize preview | verified | 已在本仓库内完成可重复验证。 |
| Mock organize apply | verified | 已在本仓库内完成可重复验证，但不会真实处理文件。 |
| Real organize preview skeleton | verified | 已对 `scripts/host_integration_stub.py` 完成请求构造与响应解析验证；对真实 MoviePilot 宿主仍是 `unverified`。 |
| Real organize apply skeleton | verified | 已对 `scripts/host_integration_stub.py` 完成请求构造与响应解析验证；对真实 MoviePilot 宿主仍是 `unverified`。 |
| Organize strategy mapping | verified | 已可通过 settings / env 配置库路径、命名模板与 conflict policy。 |
| 真实文件移动 / 硬链接 / 刮削 / 媒体库刷新 | placeholder | 仅保留 host-backed apply 骨架与结果记录，不宣称真实完成。 |
| 真实 MoviePilot organize 语义 | unverified | 需要后续人工联调、记录真实请求响应样例后再升级为 `verified`。 |

## 9.3 配置项

可通过 `.env` 或环境变量配置：

```env
MUSICPILOT_HOST_INTEGRATION_ENABLED=true
MUSICPILOT_HOST_BASE_URL=http://127.0.0.1:19090
MUSICPILOT_HOST_VERIFICATION_STATE=unverified
MUSICPILOT_HOST_ORGANIZE_PREVIEW_PATH=/organize/preview
MUSICPILOT_HOST_ORGANIZE_APPLY_PATH=/organize/apply
MUSICPILOT_HOST_ORGANIZE_STRATEGY=prefer_host
MUSICPILOT_HOST_FALLBACK_TO_MOCK=true

MUSICPILOT_ORGANIZE_LIBRARY_TYPE=music
MUSICPILOT_ORGANIZE_ROOT_PATH=/library/musicpilot/library
MUSICPILOT_ORGANIZE_ARTIST_DIR_TEMPLATE={artist_name}
MUSICPILOT_ORGANIZE_ALBUM_DIR_TEMPLATE={artist_name}/{year} - {album_title}
MUSICPILOT_ORGANIZE_TRACK_FILE_TEMPLATE={track_title}.{format_ext}
MUSICPILOT_ORGANIZE_CONFLICT_POLICY=skip_existing
```

策略说明：

- `mock`
  - 永远使用 mock organize adapter。
- `prefer_host`
  - organize capability 可用时优先走 host-backed preview/apply skeleton。
  - 若 capability 缺失、配置缺失或运行失败，且 `MUSICPILOT_HOST_FALLBACK_TO_MOCK=true`，则自动回退到 mock。
- `strict_host`
  - 要求必须使用 host-backed organize adapter。
  - 若 capability 缺失或配置不完整，接口会明确失败，不会静默回退。

## 9.4 preview / apply 现状

- `POST /api/v1/plugin/musicpilot/organize/preview`
  - 当前会根据 resolver 选择 mock 或 host-backed skeleton。
  - 返回中会明确展示：
    - `organize_backend`
    - `adapter_mode`
    - `organize_status`
    - `target_library_path`
    - `target_relative_path`
    - `strategy_snapshot`
    - `fallback_reason`
    - `verification_state`
- `POST /api/v1/plugin/musicpilot/organize/apply`
  - 当前可能走 mock apply，也可能走 host-backed apply skeleton。
  - 即使返回 `applied`，也只表示“状态记录已更新”或“host stub 已返回 applied”，并不等价于真实 MoviePilot 已完成文件处理。
- `GET /api/v1/plugin/musicpilot/organize/jobs`
  - 可回看 organize records 列表。
- `GET /api/v1/plugin/musicpilot/organize/jobs/{id}`
  - 可查看单条 organize record detail、失败原因和 fallback 信息。

## 9.5 如何验证

### A. 默认 mock 模式

1. 不配置 `MUSICPILOT_HOST_INTEGRATION_ENABLED` 或保持为 `false`
2. 启动 backend
3. 调用：
   - `POST /api/v1/plugin/musicpilot/organize/preview`
   - `POST /api/v1/plugin/musicpilot/organize/apply`
   - `GET /api/v1/plugin/musicpilot/organize/jobs`
4. 预期：
   - `organize_backend=mock`
   - preview 为 `preview_ready`
   - apply 为 `applied`

### B. prefer_host 但 capability 不足

1. 开启：
   - `MUSICPILOT_HOST_INTEGRATION_ENABLED=true`
   - `MUSICPILOT_HOST_ORGANIZE_STRATEGY=prefer_host`
2. 不配置合法 `HOST_BASE_URL` 或 organize path
3. 预期：
   - organize 会自动回退到 mock
   - 返回中出现 `fallback_reason=host_capability_unavailable` 或同类原因

### C. 本地 host stub + prefer_host

1. 启动 stub：

```bash
python3 scripts/host_integration_stub.py
```

2. 配置：
   - `MUSICPILOT_HOST_INTEGRATION_ENABLED=true`
   - `MUSICPILOT_HOST_BASE_URL=http://127.0.0.1:19090`
   - `MUSICPILOT_HOST_ORGANIZE_PREVIEW_PATH=/organize/preview`
   - `MUSICPILOT_HOST_ORGANIZE_APPLY_PATH=/organize/apply`
   - `MUSICPILOT_HOST_ORGANIZE_STRATEGY=prefer_host`
3. 预期：
   - `/health` 中 `active_organize_adapter=real_organize`
   - preview/apply 返回 `organize_backend=host`
   - `verification_state` 仍为 `unverified` 或 `placeholder`，除非你已拿真实宿主完成验证

### D. strict_host 失败验证

1. 开启：
   - `MUSICPILOT_HOST_INTEGRATION_ENABLED=true`
   - `MUSICPILOT_HOST_ORGANIZE_STRATEGY=strict_host`
2. 不启动 stub 或不提供合法 organize endpoint
3. 预期：
   - `/health` 仍可查看 wiring 状态
   - organize preview/apply 会返回失败
   - 错误原因中能看到 capability / fallback 相关信息

## 9.6 如何查看当前 organize backend

- `GET /health`
  - 查看 `data.host_integration.active_organize_adapter`
- `GET /api/probe/health`
  - 查看 `data.runtime_state.organize_capability` 与 `organize_fallback_reason`
- `POST /api/v1/plugin/musicpilot/organize/preview`
  - 查看 `data.organize_backend`、`data.organize_status`、`data.fallback_reason`
- `POST /api/v1/plugin/musicpilot/organize/apply`
  - 查看 `data.organize_backend`、`data.organize_status`、`data.failure_reason`
- `GET /api/v1/plugin/musicpilot/organize/jobs/{id}`
  - 查看持久化后的 organize record detail

## 9.7 与真实 MoviePilot organize 的边界声明

- `verified`
  - 仅表示本仓库已经对 mock 或本地 stub 进行了可重复验证。
- `unverified`
  - 表示代码骨架已就位，但尚未拿真实 MoviePilot 宿主完成 organize 语义确认。
- `placeholder`
  - 表示只保留接口边界、配置入口或状态结构，尚未具备有效联调样本。

当前仓库**没有**宣称“已真实完成文件移动、硬链接、刮削入库或媒体库刷新”。  
真实 organize 联调结果，请继续记录到 [docs/07_宿主能力验证记录模板.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/07_宿主能力验证记录模板.md)。
