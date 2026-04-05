# MusicBrainz Metadata Provider Plan

1. 写 failing tests，锁定 live provider 契约和 MusicBrainz 基本映射。
2. 扩展 metadata provider adapter 与 settings/dependencies。
3. 让 MetadataService 在 live mode 下走 adapter search/detail。
4. 跑定向测试，再跑后端全量与前端构建。
5. 更新 README / backend README / docs/28，记录真实 metadata provider 已开始接入。
