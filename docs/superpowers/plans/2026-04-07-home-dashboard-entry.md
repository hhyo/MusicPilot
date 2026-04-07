# MusicPilot 首页仪表盘入口实现计划

1. 补插件 dashboard 契约
- 在插件入口实现 `get_dashboard_meta()` 和 `get_dashboard()`。
- 返回一个轻量 dashboard 项目，render mode 保持 `vue`。

2. 新增远程 Dashboard 组件
- 在 `frontend/src/plugin/` 下新增 `Dashboard.vue`。
- 组件风格贴近宿主 dashboard 卡片。
- 提供“打开 MusicPilot”按钮，点击跳转到 `/#/plugins?id=musicpilot`。

3. 扩展 federation 暴露
- 在 `frontend/vite.config.ts` 中新增 `./Dashboard` 暴露。

4. 同步 runtime
- 构建前端
- 运行 `python3 scripts/package_plugin.py`
- 同步到本地宿主插件目录

5. 验证
- 后端全量测试
- 前端测试与构建
- 真实打开宿主首页 dashboard
- 校验卡片展示
- 校验点击后进入插件页并自动打开 MusicPilot 弹窗
- 记录截图
