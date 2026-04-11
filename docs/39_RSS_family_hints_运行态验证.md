# RSS family hints 运行态验证

## 目标

验证 `rss_feed` discovery 在真实宿主运行态下是否已经：

1. 将 family-specific candidate hints 写入 discovery target。
2. 通过 `search_lookup` 将这些 hints 传入 metadata lookup。
3. 在 `seed` metadata provider 模式下，用 candidate arrays 提升 lookup 命中能力。

## 验证环境

- 宿主仓库：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot`
- 宿主解释器：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/.venv/bin/python`
- 插件来源：`/Users/lihuanhuan/PycharmProjects/MoviePilot/.worktrees/rss-hint-quality/plugin_runtime/plugins/musicpilot`
- 宿主插件目录：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/app/plugins/musicpilot`
- 宿主配置：复制 `config-dev/` 到隔离目录后，通过 `CONFIG_DIR` 指向隔离副本运行 `TestClient(app)`

## 临时设置

运行态脚本通过 `/api/v1/plugin/musicpilot/settings/providers` 将 `chart_provider_mode` 临时切换为 `rss_feed`，并写入 3 个 feed：

- `netease-hot-tracks`
- `youtube-top-songs-global`
- `youtube-top-artists-global`

## 关键结果

### 1. RSS charts 在真实宿主中加载成功

宿主真实返回 3 个 RSS charts：

- `rss-feed-netease-hot-tracks`
- `rss-feed-youtube-top-songs-global`
- `rss-feed-youtube-top-artists-global`

`item_count` 分别为：

- `200`
- `100`
- `100`

### 2. YouTube TopSongs 的 hero/group target 已带 candidate hints

验证 `rss-feed-youtube-top-songs-global` 的 `hero_entry.target` 和 `entry_groups[0].items[0].target`，结果一致，均为：

- `resolution_mode = search_lookup`
- `conversion_ready = true`
- `resolution_hints.family = youtube_top_songs`
- `resolution_hints.title = SWIM`
- `resolution_hints.artist_name = BTS`
- `resolution_hints.title_candidates = ["SWIM", "BTS"]`
- `resolution_hints.artist_name_candidates = ["BTS", "SWIM"]`

这说明 family-specific candidate hints 已经真正进入 discovery 下钻层，而不只是停留在 parser 内部。

### 3. metadata lookup 已消费 candidate arrays

在宿主真实运行态下调用：

- `POST /api/v1/plugin/musicpilot/metadata/lookup`

请求使用 noisy title：

- `title = Hello (Official Video)`
- `title_candidates = ["Hello (Official Video)", "Hello"]`
- `artist_name = Adele`
- `album_title = 25`

返回：

- `code = METADATA_LOOKUP_OK`
- `entity_id = track-hello`
- `title = Hello`
- `artist_name = Adele`
- `mock = true`

说明在当前 `metadata_provider_mode = seed` 的前提下，candidate arrays 已经在真实宿主运行态里生效，帮助 lookup 命中了本地 seed catalog 的正确歌曲。

## 结论

本轮改动已经在真实宿主运行态下验证通过：

- RSS family-specific candidate hints 已进入 discovery target。
- `search_lookup` 路径已经能携带这些 hints。
- metadata lookup 已能利用 candidate arrays 提升带噪声标题的命中率。

## 当前边界

- 当前宿主验证仍是 `metadata_provider_mode = seed`。
- 因此本轮验证的是：
  - candidate hints 是否真正进入真实运行态
  - lookup 是否真正消费 candidate arrays
- 还不是对真实 MusicBrainz provider 命中率的最终结论。
