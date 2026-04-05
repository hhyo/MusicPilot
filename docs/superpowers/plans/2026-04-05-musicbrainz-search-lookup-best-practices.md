# MusicBrainz Search & Lookup Best Practices Plan

1. 先补 provider red tests：
   - plain keyword search 带 `dismax=true`
   - 高级 query 不带 `dismax`
   - recording detail 请求包含 `release-groups`
2. 实现 provider search/lookup 最小改动
3. 跑定向 metadata provider tests
4. 跑 backend 全量、frontend build、plugin runtime 打包
5. 同步 README / backend README 当前 metadata 描述
