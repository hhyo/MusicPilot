# MusicPilot Backend

FastAPI 工程目录。当前已完成：

- 健康检查与统一响应结构
- 宿主能力探针 API 骨架
- metadata 搜索与详情最小闭环
- SQLite 最小落库与本地 seed 初始化

当前仍不包含：

- 真实第三方 metadata provider 接入
- 真实 PT 搜索与下载器派发
- 真实订阅执行与整理规则

手动初始化本地数据库：

```bash
cd backend
python -m app.db_init --reseed
```

启动方式见仓库根目录 [README.md](../README.md)。
