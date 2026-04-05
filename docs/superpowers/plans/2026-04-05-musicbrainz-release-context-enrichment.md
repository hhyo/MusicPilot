# MusicBrainz Release Context Enrichment Plan

1. 先补 red tests，覆盖：
   - album detail 暴露 status/barcode/label/media_format/track_count/disc_count/secondary_types
   - track detail 复用最佳 release / release-group 的关键上下文
2. 扩展 `MetadataDetail` schema 与前端类型
3. 在 `MusicBrainzMetadataProviderAdapter` 里补 release context helper 并接到 album/track detail
4. 更新 detail drawer 展示
5. 跑定向 metadata provider tests、backend 全量、frontend build、runtime 打包
