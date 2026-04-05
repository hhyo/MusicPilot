# MusicBrainz Search & Lookup Best Practices

## Goal

继续围绕 MusicBrainz 官方 WS/2 文档和 Search 文档，把当前 metadata provider 再收紧一轮，但不扩新源、不改对外 API。

## Why

当前 `MusicBrainzMetadataProviderAdapter` 已经可用，但还有两处可以更贴近官方建议：

1. `metadata search` 面向的是普通用户 keyword 输入，适合按官方文档使用 `dismax=true`，避免把用户输入当成高级 Lucene 语法处理。
2. `recording detail` 当前虽然已经能对齐 release-group 语义，但还没有把 `release-groups` 作为官方支持的 `inc` 一起请求，导致部分场景仍要额外 release lookup。

## Scope

本轮只做：

- 对 plain keyword search 启用 `dismax=true`
- 对显式高级 query 保持兼容，不强行转成 dismax
- `recording detail` 请求增加 `release-groups`
- 优先消费 recording response 里已携带的 nested `release-group`

不做：

- 新 provider
- 新 API 字段
- 新前端交互
- 更大范围 search query 重写

## Official References

- MusicBrainz API / Search：plain indexed search 可通过 `dismax=true` 使用更适合普通 keyword 的解析方式
- MusicBrainz API：`/ws/2/recording` lookup 支持 `inc=releases+release-groups`

## Success Criteria

- 普通 keyword metadata search 请求会带 `dismax=true`
- 显式高级 query 不会被强制 dismax 化
- recording detail 请求会带 `release-groups`
- 当 recording response 已带 `release-group` 时，不再额外请求 release detail
