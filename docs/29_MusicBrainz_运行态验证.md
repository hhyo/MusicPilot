# 29. MusicBrainz 运行态验证

## 结论

MusicPilot 当前已经支持 `MUSICPILOT_METADATA_PROVIDER_MODE=musicbrainz`，并在本地运行态下完成了真实搜索与详情 smoke check。

## 验证方式

- 使用 `TestClient`
- 设置：
  - `MUSICPILOT_METADATA_PROVIDER_MODE=musicbrainz`
  - `MUSICPILOT_METADATA_PROVIDER_USER_AGENT=MusicPilot/0.1.0 (runtime-smoke)`
- 请求：
  - `POST /api/v1/plugin/musicpilot/metadata/search`
  - `GET /api/v1/plugin/musicpilot/metadata/artists/{id}`

## 结果

- metadata search 返回 `200`
- 返回体 `provider=musicbrainz`
- 返回体 `source_type=musicbrainz_ws2`
- 返回体 `mock=false`
- artist detail 返回 `200`
- detail `integration_point=MusicBrainzMetadataProviderAdapter.get_artist_detail`

## 当前边界

- 当前只接入 Artist / Album / Track 的搜索与详情
- 当前没有 provider 缓存
- 当前没有 provider 配置持久化
- 当前没有多 provider 聚合
- 当前 organize 的本地 metadata 识别层仍独立存在，不依赖在线 provider
