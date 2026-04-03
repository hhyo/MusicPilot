# 11. Phase 7B 真实成功样例闭环

> 用途：记录 MusicPilot 在 Phase 7B 针对真实 MoviePilot 宿主拿到的第一条“成功下载 -> 路径回灌 -> transfer/name -> transfer/manual”闭环样例。  
> 约束：不写入真实 token；所有宿主配置均通过本地环境变量注入。

> Phase 8 更新：当前这条闭环已不再是唯一成功依据。  
> Phase 8 已补出真实样例矩阵，用于区分 `stable / single_sample / blocked`。最新结论请同时参考 [docs/12_Phase8_真实成功率验证矩阵.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/12_Phase8_真实成功率验证矩阵.md)。

## 11.1 本轮目标

Phase 7B 的重点不是继续扩大接口面，而是把 Phase 7A 里仍是 `unverified` 的关键主链路推进到至少一条真实成功样例：

- 真实下载成功样例
- 下载后本地路径回灌样例
- 真实 `transfer/name` 正向样例
- 真实 `transfer/manual` 成功样例
- MusicPilot organize host 路径中的一条 `verification_state=verified` 记录

## 11.2 本轮成功样例概览

本轮选择的真实闭环样例是一条电影资源，用于验证宿主 download / history / transfer 语义：

1. 通过真实宿主 `GET /api/v1/search/title` 获取候选。
2. 对真实宿主 `POST /api/v1/download/` 发送 `media_in + torrent_in` 最小 payload。
3. 宿主返回 `success=true` 和真实 `download_id`。
4. MusicPilot 通过 `GET /api/v1/history/download` 回读该 `download_id` 对应的本地路径。
5. `GET /api/v1/transfer/name` 基于该路径返回正向命名结果。
6. `POST /api/v1/transfer/manual` 基于真实 `fileitem` 成功返回 `success=true`。
7. MusicPilot 的 organize preview / apply / record 都记录为：
   - `organize_backend=host`
   - `verification_state=verified`
   - `path_handoff.handoff_status=resolved_from_history_download`

## 11.3 推荐本地配置

```bash
export MUSICPILOT_HOST_INTEGRATION_ENABLED=true
export MUSICPILOT_HOST_BASE_URL="${REAL_MOVIEPILOT_BASE_URL}"
export MUSICPILOT_HOST_AUTH_TOKEN="${REAL_MOVIEPILOT_TOKEN}"
export MUSICPILOT_HOST_AUTH_MODE=x_api_key
export MUSICPILOT_HOST_API_KEY_HEADER_NAME=X-API-KEY
export MUSICPILOT_HOST_VERIFY_TLS=false

export MUSICPILOT_HOST_SEARCH_STRATEGY=prefer_host
export MUSICPILOT_HOST_DISPATCH_STRATEGY=prefer_host
export MUSICPILOT_HOST_ORGANIZE_STRATEGY=prefer_host
export MUSICPILOT_HOST_FALLBACK_TO_MOCK=true

export MUSICPILOT_HOST_SEARCH_TITLE_PATH=/api/v1/search/title
export MUSICPILOT_HOST_SEARCH_LAST_PATH=/api/v1/search/last
export MUSICPILOT_HOST_DOWNLOADERS_PATH=/api/v1/download/clients
export MUSICPILOT_HOST_DOWNLOAD_ADD_PATH=/api/v1/download/add
export MUSICPILOT_HOST_DOWNLOAD_MEDIA_PATH=/api/v1/download/
export MUSICPILOT_HOST_HISTORY_DOWNLOAD_PATH=/api/v1/history/download
export MUSICPILOT_HOST_HISTORY_TRANSFER_PATH=/api/v1/history/transfer
export MUSICPILOT_HOST_TRANSFER_NAME_PATH=/api/v1/transfer/name
export MUSICPILOT_HOST_TRANSFER_MANUAL_PATH=/api/v1/transfer/manual
```

推荐把真实值保存在本机私有环境或 `/Users/lihuanhuan/.env`，不要写入仓库文件。

## 11.4 成功样例的最小 payload 形态

### 下载成功 payload

真实成功样例走的是 `POST /api/v1/download/`，不是 `download/add`。

最小形态如下：

```json
{
  "media_in": {
    "type": "电影",
    "title": "普通事故",
    "year": 2025,
    "tmdb_id": 1456349,
    "title_year": "普通事故 (2025)"
  },
  "torrent_in": {
    "site": 0,
    "title": "<真实搜索结果标题>",
    "description": "<真实搜索结果副标题>",
    "enclosure": "<真实下载链接>",
    "size": 0,
    "seeders": 0,
    "peers": 0
  },
  "downloader": "QB"
}
```

注意：

- `media_in` 是 Phase 7B 成功样例的关键。只有 `torrent_in` 时，宿主更可能走 `download/add` 的媒体识别路径，并返回业务拒绝。
- `torrent_in` 直接来自真实 `search/title` 返回的 `torrent_info` 映射，不建议在 MusicPilot 内再随意猜测字段。

### path handoff 形态

MusicPilot 现在会优先从 `/api/v1/history/download` 回读：

```json
{
  "download_hash": "<download_id>",
  "source_path": "/downloads/movie/<目录或文件>",
  "source_filetype": "dir|file",
  "handoff_source": "moviepilot.runtime.history.download",
  "handoff_status": "resolved_from_history_download",
  "verification_state": "verified"
}
```

当 download history 尚未同步时，会暂存为：

```json
{
  "handoff_status": "pending_history_sync",
  "verification_state": "unverified"
}
```

## 11.5 真实宿主成功样例的验证结果

| 能力 | 接口 | 当前状态 | 说明 |
|---|---|---|---|
| Search title | `GET /api/v1/search/title` | `verified` | 已作为真实成功下载样例的候选来源。 |
| Download clients | `GET /api/v1/download/clients` | `verified` | 已用于下载器选择与 remap。 |
| Download media | `POST /api/v1/download/` | `verified` | 已拿到真实 `success=true` 与 `download_id`。 |
| Download add | `POST /api/v1/download/add` | `verified` | Phase 8 已补到 1 条真实成功样例，但当前仍只是 `single_sample`。 |
| History download | `GET /api/v1/history/download` | `verified` | 已回读成功样例的真实本地路径。 |
| History transfer | `GET /api/v1/history/transfer` | `verified` | 已验证结构，可作为兼容回灌来源。 |
| Transfer name | `GET /api/v1/transfer/name` | `verified` | 已拿到真实正向命名样例。 |
| Transfer manual | `POST /api/v1/transfer/manual` | `verified` | 已拿到真实 `success=true` 的最小整理样例。 |
| Organize host preview/apply | MusicPilot `organize/*` | `verified` | 已完成一条 `backend=host`、`status=applied` 的真实记录。 |

## 11.6 MusicPilot 代码侧收口结果

### download dispatch

- `RealDownloadDispatchAdapter`
  - 成功后会读取宿主 `download_id`
  - 再通过 `HostPathHandoffService` 调用 `/api/v1/history/download`
  - 把 `path_handoff` 写入 dispatch result、binding raw payload 和 candidate raw payload
- API 中可见：
  - `dispatch_backend`
  - `verification_state`
  - `host_response_summary`
  - `path_handoff`

### organize

- `RealOrganizeAdapter.preview`
  - 继续映射到 `GET /api/v1/transfer/name`
  - 但输入路径现在优先来自 `path_handoff`
- `RealOrganizeAdapter.apply`
  - 继续映射到 `POST /api/v1/transfer/manual`
  - 若 dispatch / history 已回读到真实路径，则可以走真实 host apply
- `OrganizeService`
  - 会在 preview/apply 前优先解析 candidate / binding 中的 `path_handoff`
  - 若路径缺失，会尝试按 `download_hash` 二次从宿主 history API 回读

## 11.7 与本地 stub 的差异

Phase 7B 已把本地 stub 升级到更接近真实宿主的语义：

- 新增 `/api/v1/history/download`
- 新增 `/api/v1/history/transfer`
- `download/add` / `download/` 成功后会写入 history
- `transfer/manual` 成功后会写入 transfer history

但仍要明确：

- stub 只是本地回归工具，不是 `verified` 依据
- `verified` 只能来自真实宿主运行结果

## 11.8 Phase 8 后的补充结论

- `GET /api/v1/search/media/{mediaid}` 已在 Phase 8 拿到多条正向样例。
- `POST /api/v1/download/add` 已在 Phase 8 拿到 1 条真实成功样例，但稳定性尚不足以升级为多样例成功。
- `history/transfer` 现在已经被证明是更稳定的 organize fallback / replay 来源。
- “下载完成后自动进入整理”的生产级调度仍未实现；Phase 8 关注的是稳定性收敛，而不是自动化扩面。

## 11.9 如何回看当前状态

- `/health`
  - 查看 `active_search_adapter`、`active_dispatch_adapter`、`active_organize_adapter`
- `/api/probe/health`
  - 查看 capability summary
- `/api/v1/plugin/musicpilot/jobs/{id}/results`
  - 查看 candidate 的 `path_handoff`
- `/api/v1/plugin/musicpilot/downloads/dispatch`
  - 查看 `host_response_summary`、`path_handoff`
- `/api/v1/plugin/musicpilot/organize/preview`
  - 查看 `target_relative_path`、`path_handoff`
- `/api/v1/plugin/musicpilot/organize/apply`
  - 查看 `organize_backend`、`organize_status`、`verification_state`

## 11.10 结论

Phase 7B 已把 MusicPilot 从“真实宿主语义已核对”推进到“至少一条真实成功闭环已跑通”：

- 真实 download 成功：已验证
- 下载后 path handoff：已验证
- 真实 transfer/name 成功：已验证
- 真实 transfer/manual 成功：已验证
- organize host applied record：已验证

这不等价于“所有下载、整理、媒体库刷新语义都已完整验证”，但已经把最关键的真实成功样例链路沉淀下来。  
Phase 8 又在此基础上补出了多样例验证矩阵，用来区分“已稳定”“仅单样例成功”和“真实宿主已阻断”这三类状态。
