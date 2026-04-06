# 37. 插件中心页面入口 Vue Remote 运行态验证

## 目标

验证 MusicPilot 已经不再只是“宿主可加载插件 API”，而是可以在 MoviePilot 插件中心中通过宿主原生 `vue` 远程组件模式打开真实页面。

## 验证环境

- MusicPilot 工作树：
  - `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote`
- MoviePilot 宿主：
  - `/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot`
- MoviePilot 前端：
  - `/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot-Frontend`
- 宿主运行配置：
  - `CONFIG_DIR=/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev`

## 实现结果

### 1. 宿主插件入口切到 `vue` 远程组件模式

- `musicpilot.get_render_mode()` 返回：
  - `("vue", "static/assets")`
- `musicpilot.get_page()` 返回：
  - `None`

这意味着：

- 宿主 `/api/v1/plugin/page/musicpilot` 会返回 `render_mode=vue`
- 宿主 `/api/v1/plugin/remotes?token=moviepilot` 会把 MusicPilot 纳入远程组件列表
- 远程入口路径为：
  - `/api/v1/plugin/file/musicpilot/static/assets/remoteEntry.js`

### 2. 前端已导出宿主可加载的 `Page` 组件

- `frontend` 通过 Vite federation 暴露：
  - `./Page -> src/plugin/Page.vue`
- `Page.vue` 在宿主详情弹窗中挂载一个 MusicPilot 子应用：
  - `Pinia`
  - `Element Plus`
  - `memory router`

这样做的结果是：

- 保留当前 MusicPilot 前端结构
- 不污染宿主 URL
- 可以在插件中心详情弹窗内真实浏览 MusicPilot 页面

## API 与静态资源验证

### `/api/v1/plugin/remotes`

返回包含：

```json
[{"id":"musicpilot","url":"/plugin/file/musicpilot/static/assets/remoteEntry.js","name":"MusicPilot"}]
```

说明远程组件已被宿主识别。

### `remoteEntry.js`

实际可读内容中已包含：

- `./Page`
- `__federation_expose_Page`

说明 federation 产物已被正确打包进插件静态目录。

## 真实前端交互验证

### 访问步骤

1. 打开：
   - `http://127.0.0.1:5173/#/plugins`
2. 使用本地开发账号登录宿主前端
3. 在“我的插件”中点击 `MusicPilot`
4. 宿主弹出插件详情页
5. 弹窗内真实加载 MusicPilot 页面

### 观察结果

- 插件列表中 `MusicPilot` 条目可点击打开详情页
- 宿主弹窗内显示：
  - `MusicPilot`
  - 首页工作台
  - 模块入口
  - 当前边界说明
- 页面不是空白页，也不是 iframe 占位页
- 关闭按钮可正常关闭弹窗

## 截图证据

- 插件中心列表：
  - `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/.tmp/plugin-page-vue-remote/plugin-center-before-open.png`
- 宿主插件详情页内已加载 MusicPilot 页面：
  - `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/.tmp/plugin-page-vue-remote/plugin-center-remote-page-open.png`

## 已知边界

- 这轮只解决“宿主插件中心可打开 MusicPilot 页面”
- 这轮没有把 MusicPilot 做成宿主左侧一级菜单
- 当前远程页面里仍会出现一条 Vue runtime warning：
  - 与宿主页面现有 Vue/compiler 配置有关
  - 不影响远程页面真实加载和交互
- 这轮没有改写 MusicPilot 页面为宿主原生 Vuetify 页面，而是通过远程组件挂载 MusicPilot 子应用

## 结论

MusicPilot 现已完成从“宿主可加载插件 API”到“宿主插件中心可真实打开前端页面”的跨越。后续关于插件 UI 的工作，将在这个宿主原生 `vue` 远程组件入口之上继续演进，而不再回退到 iframe 或仅独立开发页访问的方案。
