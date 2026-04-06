# 36. RSS settings runtime integration 运行态验证

## 目标

验证本轮 RSS settings runtime integration 是否已经进入真实运行态，而不是停留在 placeholder、环境变量拼接或本地假数据阶段。

本次只确认四件事：

1. `/settings` 已从 placeholder 变成最小可用设置页。
2. `/settings/providers` 已从 placeholder 变成真实读写接口。
3. chart provider 运行时优先读取项目 settings，环境变量仅作为 fallback。
4. RSS feed 已能通过 settings 配置后真实进入 discovery。

## 验证样本

本次验证的 RSS 样本至少包括：

- 网易云热歌榜 playlist RSS
- YouTube TopSongs RSS
- YouTube TopArtists RSS

## 已知运行态证据

settings API 返回结果中：

- `chart_provider_mode=rss_feed`
- 保存后的 `chart_rss_feeds` 包含 3 个 feed

charts API 返回结果中：

- `/charts` 返回 3 个真实 RSS charts
- chart id 分别为：
  - `rss-feed-netease-hot-tracks`
  - `rss-feed-youtube-top-songs-global`
  - `rss-feed-youtube-top-artists-global`
- `item_count` 分别可写为：
  - `200`
  - `100`
  - `100`

## 运行态结论

当前可以确认：

1. RSS discovery 已经不是 placeholder，而是通过 settings 进入了真实运行态。
2. charts 的 RSS provider 配置以 settings 为主，环境变量只作为 fallback。
3. discovery 条目点击会进入 metadata drawer。
4. 在当前 `metadata provider mode=seed` 的运行态下，示例 lookup 可能返回“未匹配到 metadata”，这说明当前 metadata lookup 没有命中，不代表 discovery 接口缺失。
5. 本轮没有做复杂 RSS 可视化 CRUD，这部分仍然保留为后续扩展项。

## 截图证据

![settings saved](/Users/lihuanhuan/PycharmProjects/MusicPilot/.tmp/rss-settings-runtime/settings-saved.png)

![charts rss discovery](/Users/lihuanhuan/PycharmProjects/MusicPilot/.tmp/rss-settings-runtime/charts-rss-discovery.png)

## 当前边界

- 这次验证只覆盖 RSS settings 读写、charts discovery 和 discovery -> metadata drawer 的真实运行态。
- 这次验证不包含复杂 RSS 可视化 CRUD。
- 这次验证不把 metadata lookup 的“未匹配到 metadata”写成接口缺失。
