# Backend Data

本目录用于承载 Phase 2 的本地 SQLite 数据文件。

- 默认数据库路径：`backend/data/musicpilot.db`
- 当前只保存元数据搜索最小闭环所需的本地 seed 与搜索历史
- 不代表真实数据库方案已经冻结
- 后续若接入迁移体系或真实外部 provider，需要在保持字段兼容的前提下再扩展
