# RSS Settings Runtime Integration

Date: 2026-04-06

## Goal

把 RSS discovery 从“结构层 + 环境变量层”推进到“项目 settings 正式接入 + 真实运行态验证”。

## Tasks

1. 新增项目内 `app_settings` 存储，并让 `/settings/providers` 变成真实读写接口。
2. 实现最小 `/settings` 页面，支持 `chart_provider_mode` 与 `chart_rss_feeds` 的读取、编辑和保存。
3. 让 chart provider 运行时优先读取项目 settings，环境变量仅作为 fallback。
4. 用网易云热歌榜、YouTube TopSongs、YouTube TopArtists 三个 RSS 样本做真实运行态验证。
5. 同步 README、backend README、路线文档和运行态验证文档。

## Verification

- backend 全量测试通过
- frontend 单测通过
- frontend 构建通过
- `scripts/package_plugin.py` 通过
- `/openapi.json`、`/docs`、`/settings/providers`、`/charts` 运行态返回正常
- 截图证据覆盖：
  - settings 保存成功
  - RSS 榜单真实进入 discovery
