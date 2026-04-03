# 10. Phase 7A 真实宿主语义验证与差异收敛

> 用途：沉淀 MusicPilot 在 Phase 7A 对真实 MoviePilot 宿主完成的源码核对、运行时联调、字段映射修正和 stub 差异记录。  
> 约束：本文档不会写入真实 token；所有鉴权均通过本地环境变量注入。

> 更新说明：Phase 7B 已在真实宿主上拿到第一条成功下载与 organize 闭环样例。  
> 最新 verified 状态请同时参考 [docs/11_Phase7B_真实成功样例闭环.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/11_Phase7B_真实成功样例闭环.md)。

## 10.1 联调范围

- 主仓库：`./MusicPilot`
- 参考宿主源码：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot`
- 真实宿主 Base URL：通过本地环境变量注入，不写入仓库
- 推荐鉴权：`X-API-KEY: <TOKEN>`

## 10.2 推荐本地配置方式

推荐先把本机私有值放到本地未纳入版本控制的环境里，再映射给 MusicPilot：

```bash
export MUSICPILOT_HOST_INTEGRATION_ENABLED=true
export MUSICPILOT_HOST_BASE_URL="${URL}"
export MUSICPILOT_HOST_AUTH_TOKEN="${TOKEN}"
export MUSICPILOT_HOST_AUTH_MODE=x_api_key
export MUSICPILOT_HOST_API_KEY_HEADER_NAME=X-API-KEY

export MUSICPILOT_HOST_SEARCH_STRATEGY=prefer_host
export MUSICPILOT_HOST_DISPATCH_STRATEGY=prefer_host
export MUSICPILOT_HOST_ORGANIZE_STRATEGY=prefer_host
export MUSICPILOT_HOST_FALLBACK_TO_MOCK=true
```

真实 MoviePilot 宿主的推荐路径：

```env
MUSICPILOT_HOST_HEALTH_PATH=/api/v1/search/last
MUSICPILOT_HOST_SITES_PATH=/api/v1/site
MUSICPILOT_HOST_SEARCH_TITLE_PATH=/api/v1/search/title
MUSICPILOT_HOST_SEARCH_MEDIA_PATH=/api/v1/search/media
MUSICPILOT_HOST_SEARCH_LAST_PATH=/api/v1/search/last
MUSICPILOT_HOST_DOWNLOADERS_PATH=/api/v1/download/clients
MUSICPILOT_HOST_DOWNLOAD_ADD_PATH=/api/v1/download/add
MUSICPILOT_HOST_DOWNLOAD_MEDIA_PATH=/api/v1/download/
MUSICPILOT_HOST_TRANSFER_NAME_PATH=/api/v1/transfer/name
MUSICPILOT_HOST_TRANSFER_QUEUE_PATH=/api/v1/transfer/queue
MUSICPILOT_HOST_TRANSFER_MANUAL_PATH=/api/v1/transfer/manual
MUSICPILOT_HOST_TRANSFER_NOW_PATH=/api/v1/transfer/now
```

## 10.3 宿主接口映射与当前结论

| 域 | 宿主接口 | 宿主鉴权 | 当前 verification_state | 结论 |
|---|---|---|---|---|
| API 主前缀 | `/api/v1` | 源码确认 | `verified` | 由 `app/api/apiv1.py` 与真实宿主运行结果共同确认。 |
| Plugin 动态路由 | `/api/v1/plugin/{plugin_id}` | 源码确认 | `verified` | 由 `plugin.py`、`routers_initializer.py`、`plugins_initializer.py` 确认。 |
| Search title | `GET /api/v1/search/title` | `X-API-KEY` | `verified` | 已拿到真实宿主正向样例，返回 `Response{success,data:[Context]}`。 |
| Search media | `GET /api/v1/search/media/{mediaid}` | `X-API-KEY` | `unverified` | 已确认路径、参数和“未搜索到任何资源”负向返回；正向候选样例仍缺失。 |
| Search last | `GET /api/v1/search/last` | `X-API-KEY` | `verified` | 已拿到真实宿主样例，返回 `List[Context]`，用于低风险连通性与最近搜索读取。 |
| Download clients | `GET /api/v1/download/clients` | `X-API-KEY` | `verified` | 已拿到真实宿主列表样例，返回裸 `List[DownloaderInfo]`。 |
| Download add | `POST /api/v1/download/add` | `X-API-KEY` | `unverified` | 已确认 payload 兼容性和负向语义；真实音乐资源成功创建下载任务仍待样例。 |
| Download media | `POST /api/v1/download/` | `X-API-KEY` | `placeholder` | 宿主源码已确认入口，但本轮未拿到真实成功/失败样例。 |
| Transfer name | `GET /api/v1/transfer/name` | `X-API-KEY` | `unverified` | 已确认 `path + filetype` 请求契约和负向返回；正向命名样例仍待真实本地媒体路径。 |
| Transfer queue | `GET /api/v1/transfer/queue` | `X-API-KEY` | `verified` | 已确认返回为裸列表，可作辅助状态读取。 |
| Transfer manual | `POST /api/v1/transfer/manual` | `X-API-KEY` / 超级用户语义 | `unverified` | 已确认 `ManualTransferItem` 结构和负向返回；真实成功整理样例仍缺失。 |
| Transfer now | `GET /api/v1/transfer/now` | `?token=` | `verified` | 已确认它不接受单独 `X-API-KEY`，必须走 query token。当前未接入 MusicPilot 主链路。 |

## 10.4 真实宿主运行时样例摘要

本轮对真实宿主拿到的关键结论：

- `GET /api/v1/search/last`
  - `200`
  - 返回形态是 `List[Context]`
  - 样例顶层字段：`meta_info`、`media_info`、`torrent_info`
- `GET /api/v1/search/title?keyword=Taylor Swift&page=0`
  - `200`
  - 返回形态是 `Response{success,data:[Context]}`
  - 样例字段：`meta_info`、`torrent_info`、`media_info`、`media_recognize_fail_count`
- `GET /api/v1/search/media/tmdb:550?area=title`
  - `200`
  - `success=false`
  - `message=未搜索到任何资源`
- `GET /api/v1/download/clients`
  - `200`
  - 返回裸列表
  - 样例字段：`name=QB`、`type=qbittorrent`
- `POST /api/v1/download/add`
  - `200`
  - 以最小安全测试 payload 验证后，宿主返回 `success=false`
  - 失败信息：`无法识别媒体信息`
- `GET /api/v1/transfer/name?path=...&filetype=file`
  - `200`
  - 负向样例：`success=false`、`message=未识别到媒体信息`
- `POST /api/v1/transfer/manual`
  - `200`
  - 负向样例：`success=false`
  - 失败信息形态：`<filename> 没有找到可整理的媒体文件`
- `GET /api/v1/transfer/now`
  - 仅用 `X-API-KEY`：`401`、`detail=token 校验不通过`
  - 改为 `?token=`：`200`、`success=true`

## 10.5 MusicPilot 适配收敛结果

### Search

- `RealHostSearchAdapter`
  - 已改为对齐 `GET /api/v1/search/title`
  - 不再假设通用 POST 搜索接口
  - 已按 `Context -> torrent_info` 结构解析标题、站点、体积、做种等字段
- `SearchJob`
  - `prefer_host` + 真实宿主下已跑通一次
  - 结果可见：
    - `adapter_mode=host`
    - `capability_source=moviepilot.runtime.search.title`
    - `verification_state=verified`

### Dispatch

- `RealDownloadDispatchAdapter`
  - 已先对齐 `GET /api/v1/download/clients`
  - 再按有无 `media_info` 在 `/api/v1/download/add` 与 `/api/v1/download/` 之间选择
  - 当前真实宿主已验证到“payload 被宿主接受并给出业务拒绝信息”
- 当前结论
  - `dispatch_backend=host`
  - `verification_state=unverified`
  - 失败语义可见：`failure_reason=无法识别媒体信息`

### Organize / Transfer

- `RealOrganizeAdapter.preview`
  - 已映射到 `GET /api/v1/transfer/name`
  - 必须提供本地已下载文件路径和 `filetype`
- `RealOrganizeAdapter.apply`
  - 已映射到 `POST /api/v1/transfer/manual`
  - 当前仍是手动整理语义映射，不等价于 MusicPilot 自己拥有独立 organize 引擎
- 当前结论
  - 请求契约与负向返回已确认
  - 由于 SearchJob 候选只有远端 torrent context、尚无真实本地下载文件路径，所以 `prefer_host` 模式下 organize 会安全回退到 mock
  - `verification_state` 保持 `unverified`

## 10.6 与本地 host stub 的差异

| 项目 | 本地 stub | 真实 MoviePilot |
|---|---|---|
| search/title | 返回静态 `Context` 集合 | 返回真实 `Response{success,data:[Context]}` |
| search/media | 默认固定“未搜索到任何资源” | 真实宿主同样可能返回该业务失败，但正向样例仍待补充 |
| download/clients | 返回简化列表 | 真实宿主返回裸列表，字段 `name/type` |
| download/add | 可直接返回 stub 成功 | 真实宿主对音乐 payload 更严格，当前实测为业务拒绝 |
| transfer/name | stub 现在要求 `path + filetype` | 真实宿主同样要求 `path + filetype` |
| transfer/manual | stub 只做最小失败/成功模拟 | 真实宿主要求 `ManualTransferItem` 语义，并带超级用户权限路径 |
| transfer/now | stub 允许 `?token=` | 真实宿主必须 `?token=`，`X-API-KEY` 单独无效 |

## 10.7 mock / prefer_host / strict_host 行为验证

| 模式 | Search | Dispatch | Organize |
|---|---|---|---|
| `mock` | 固定使用 `mock_host_search` | 固定使用 `mock_download_dispatch` | 固定使用 `mock_organize` |
| `prefer_host` | 能力存在时走真实宿主；失败可回退 | 能力存在时走真实宿主；业务拒绝不伪装为 mock | 当前因缺少本地文件路径，真实 organize 会回退到 mock |
| `strict_host` | 宿主能力不可用时直接 `503` | 宿主能力不可用时直接 `503` | 宿主能力不可用时直接 `503` |

## 10.8 后续仍需补充的真实样例

- `search/media` 的真实正向候选样例
- `/api/v1/download/add` 或 `/api/v1/download/` 的真实成功样例
- `transfer/name` 的真实正向命名样例
- `transfer/manual` 的真实成功整理样例
- 真实下载完成后，如何把本地文件路径回灌到 MusicPilot organize 链路

## 10.9 结论

Phase 7A 的收口重点是“让 stub 假设服从真实宿主语义”，而不是宣称“全部真实可用”。  
当前状态可概括为：

- search title：`verified`
- search media：`unverified`
- download clients：`verified`
- download add：`unverified`
- transfer name/manual：`unverified`
- transfer now：`verified`，但不在主链路中使用

更细的逐项记录，请继续补到 [docs/07_宿主能力验证记录模板.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/07_宿主能力验证记录模板.md)。
