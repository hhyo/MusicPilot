# MusicPilot 插件中心页面入口（Vue Remote）设计

## 目标

将 MusicPilot 前端真正接入 MoviePilot 插件中心，使用户可以在宿主插件列表中点击 `MusicPilot` 后，直接打开由宿主前端加载的插件详情页面，而不是依赖独立开发服务器页面或仅访问插件 API。

当前目标仅覆盖“插件详情页面入口”这一件事：
- 在 MoviePilot 插件中心中，`MusicPilot` 具备可打开的详情页
- 详情页由宿主支持的 `vue` 远程组件模式加载
- 页面展示 MusicPilot 已有前端能力的最小可用入口
- 不改宿主仓库，不引入新的宿主页面路由，不改变现有插件 API 命名空间

## 现状分析

### 宿主能力

MoviePilot 宿主前后端已经支持插件详情页的两种渲染模式：
- `vuetify`
- `vue` 远程组件

关键契约：
- 后端插件基类 `get_render_mode()` 可返回 `(render_mode, dist_path)`
- 宿主通过 `/api/v1/plugin/remotes` 读取所有 `render_mode == vue` 的插件远程入口
- 宿主前端 `PluginDataDialog` 在 `vue` 模式下通过 `loadRemoteComponent(pluginId, 'Page')` 动态加载 `Page` 组件

这说明，要“真正接成 MoviePilot 插件中心页面入口”，技术上应走宿主已有的 module federation 远程组件模式，而不是自定义 iframe 方案。

### MusicPilot 当前缺口

MusicPilot 当前虽然已经具备：
- 插件 API
- 插件静态资源打包
- 独立 Vue 前端页面

但仍缺这几件事：
1. 前端没有 module federation 远程组件构建
2. 没有导出标准 `Page` 组件
3. 插件入口 `get_render_mode()` 仍默认 `vuetify`
4. `get_page()` 返回空数组，虽然宿主会认为“有详情页”，但弹窗中没有真实内容

因此，当前缺的不是“地址”，而是“宿主原生远程组件接入层”。

## 方案比较

### 方案 A：继续 `vuetify` 模式，返回 iframe 容器

优点：
- 改动较小
- 可快速把现有前端嵌进插件详情弹窗

缺点：
- 不符合宿主对插件前端的原生接入方式
- 页面通信、尺寸、鉴权和资源路径处理都会更脆弱
- 后续如果切到原生 `vue` 模式，会再次重构

### 方案 B：切到宿主原生 `vue` 远程组件模式（推荐）

优点：
- 完全对齐 MoviePilot 官方插件前端机制
- 详情页由宿主前端原生加载，体验更一致
- 后续可继续扩 `Config` / `Dashboard` 远程组件，不需要推翻结构

缺点：
- 需要补 MusicPilot 前端的 module federation 构建与 `Page` 组件导出
- 第一轮改动会同时触及前端构建、打包脚本和插件入口

### 方案 C：不接插件中心，只保留独立开发页

优点：
- 没有额外工程成本

缺点：
- 不满足“在 MoviePilot 插件中心可打开”的目标
- 不能视为真正插件化 UI 集成

本次采用：**方案 B**。

## 设计

## 1. 总体架构

新增一个“插件远程页面入口层”，结构如下：

- MusicPilot 前端继续保留现有独立开发模式
- 在现有前端工程中增加 module federation 构建配置
- 暴露标准远程组件：`Page`
- 插件 runtime 打包时，把远程组件产物装配到 `plugin_runtime/plugins/musicpilot/static/assets/` 下
- 插件入口改为：
  - `get_render_mode() -> ('vue', 'static/assets')`
  - `get_page() -> None`

这样宿主打开 `PluginDataDialog` 时，会：
1. 调 `/api/v1/plugin/page/musicpilot`
2. 看到 `render_mode = vue`
3. 再通过 `/api/v1/plugin/remotes` 获取 remoteEntry
4. 动态加载 `musicpilot` 的 `Page` 组件

## 2. 前端页面策略

第一轮不把整个 MusicPilot SPA 直接塞进远程组件，而是新增一个**宿主插件详情页壳组件**，例如：
- `frontend/src/plugin/Page.vue`

职责：
- 作为宿主插件中心里的 `Page` 远程组件
- 使用现有 MusicPilot 页面能力作为内部内容来源
- 提供最小可用导航或切换入口
- 兼容宿主传入的：
  - `api`
  - `close`
  - `switch`
  - `action`

第一轮建议在 `Page.vue` 中直接承接 MusicPilot 现有最有价值的入口：
- Dashboard / 概览
- Discovery / Charts
- Metadata Search
- Settings

但只做**插件详情页内的最小导航壳**，不重写整套应用路由系统。

## 3. 构建策略

前端构建改成双目标兼容：
- 本地开发：继续 `vite dev` 作为独立前端
- 生产打包：输出宿主可加载的 module federation 产物

第一轮建议：
- 保留当前 `build` 为插件远程组件构建
- 增加 federation 配置：
  - `name = 'musicpilot'`
  - `filename = 'remoteEntry.js'`
  - `exposes['./Page'] = './src/plugin/Page.vue'`
- `shared` 对齐宿主推荐：
  - `vue`
  - `vuetify`
  - `vuetify/styles`
- `build.target = 'esnext'`

如果 MusicPilot 当前前端尚未依赖 Vuetify，则第一轮 `Page.vue` 本身可以尽量采用宿主可兼容的简单 Vue 组件实现，但为了和宿主主应用风格统一，建议在远程组件层适度兼容 Vuetify 组件使用方式。

## 4. 打包与 runtime 装配

现有 `scripts/package_plugin.py` 需要调整：
- 不再只假设 `frontend/dist` 是普通 SPA 静态资源
- 要确保 federation 构建产物完整进入：
  - `plugin_runtime/plugins/musicpilot/static/assets/`
  - 包含 `remoteEntry.js` 及其依赖文件

同时需要确认：
- 产物路径与 `get_render_mode()` 返回的 `dist_path` 保持一致
- 宿主生成 remote entry URL 后可以正确访问：
  - `/api/v1/plugin/file/musicpilot/static/assets/remoteEntry.js`

## 5. 插件入口改造

在：
- `backend/app/__init__.py`
- `plugin_runtime/plugins/musicpilot/__init__.py`

增加或覆写：
- `get_render_mode()` 返回 `('vue', 'static/assets')`
- `get_page()` 在 `vue` 模式下返回 `None`

说明：
- 宿主在 `vue` 模式下不依赖 `get_page()` 的页面配置内容
- 但仍需要 `get_page()` 方法存在，满足宿主“有详情页”的判断逻辑

## 6. 第一轮交互边界

第一轮只完成：
- 在插件中心中打开 MusicPilot 详情页
- 详情页真实加载远程 `Page` 组件
- 页面里展示最小可用的 MusicPilot 前端入口
- 页面可正常调用插件 API
- 关闭、切换配置等宿主交互信号保持可用

第一轮明确不做：
- 远程 `Config` 组件
- 远程 `Dashboard` 组件
- 把整个现有 SPA 原样搬进宿主对话框
- 改宿主前端路由或主导航
- 重做插件市场 manifest 体系

## 7. 验证要求

### 本地工程验证
- frontend 构建成功
- backend 测试通过
- plugin_runtime 打包成功

### 宿主运行态验证
- `PluginManager` 能正常加载 `musicpilot`
- `/api/v1/plugin/remotes` 中出现 `musicpilot`
- remote entry 可访问
- 在 MoviePilot 插件页点击 `MusicPilot` 时，弹出 `PluginDataDialog`
- `PluginDataDialog` 成功加载 `Page` 远程组件
- 页面内至少有一项真实功能可操作（例如 charts 或 settings）

### 交付证据
- 至少提供：
  - 插件列表里 `MusicPilot` 可打开详情页的截图
  - 宿主插件详情页加载 MusicPilot 页面成功的截图

## 8. 风险与后续

### 当前风险
- MusicPilot 当前前端并非为 module federation 设计，改造时可能涉及：
  - 入口拆分
  - 共享依赖
  - 构建产物路径
- 如果远程组件直接依赖当前整套 SPA 路由和全局应用初始化，第一轮复杂度会明显上升

### 控制策略
- 第一轮只导出单一 `Page.vue`
- `Page.vue` 只承接最小页面壳和少量核心入口
- 避免直接把现有独立前端整站嵌入远程组件

### 后续扩展
- 第二轮可继续补：
  - `Config.vue`
  - `Dashboard.vue`
- 后续如需更深整合，再评估是否把更多现有视图抽成宿主可加载的远程模块
