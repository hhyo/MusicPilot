# MusicPilot Backend

FastAPI 工程目录。当前已完成：

- 健康检查与统一响应结构
- 宿主能力探针 API 骨架
- metadata 搜索与详情最小闭环
- SQLite 最小落库与本地 seed 初始化
- QueryBuilder、SearchJob、候选评分与 mock dispatch 边界
- SubscriptionService、subscription run 与 mock chart discovery
- mock organize preview 与 organize 状态记录
- host-aware search / dispatch adapter resolver 与 fallback 机制

当前仍不包含：

- 真实第三方 metadata provider 接入
- 真实榜单抓取与增量监控
- 真实 PT 搜索与下载器派发
- 生产级订阅调度器与真实整理规则
- 真实 MoviePilot 宿主接口语义验证完成

手动初始化本地数据库：

```bash
cd backend
python -m app.db_init --reseed
```

当前执行模式说明：

- `subscriptions/{id}/run` 为同步最小执行骨架
- `charts/*` 为 local seed / mock chart source
- `organize/preview` 只生成 organize preview，不执行真实文件处理
- `jobs/*` 与 `downloads/dispatch` 会根据 host integration settings 在 mock 与 host-backed skeleton 间选择

启用 host integration 的最小配置示例：

```bash
export MUSICPILOT_HOST_INTEGRATION_ENABLED=true
export MUSICPILOT_HOST_BASE_URL=http://127.0.0.1:19090
export MUSICPILOT_HOST_HEALTH_PATH=/health
export MUSICPILOT_HOST_SITES_PATH=/sites
export MUSICPILOT_HOST_SEARCH_PATH=/search
export MUSICPILOT_HOST_DOWNLOADERS_PATH=/downloaders
export MUSICPILOT_HOST_DISPATCH_PATH=/dispatch
export MUSICPILOT_HOST_SEARCH_STRATEGY=prefer_host
export MUSICPILOT_HOST_DISPATCH_STRATEGY=prefer_host
```

若没有真实宿主，可运行：

```bash
python3 ../scripts/host_integration_stub.py
```

然后通过 `/health`、`/api/probe/health`、`/jobs/*` 与 `/downloads/dispatch` 查看当前 active adapter、dispatch backend 与 fallback 信息。更完整的联调说明见 [docs/08_Phase5_宿主接入联调说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/08_Phase5_宿主接入联调说明.md)。

启动方式见仓库根目录 [README.md](../README.md)。
