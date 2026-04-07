# MusicPilot 首页仪表盘入口设计

## 目标
在 MoviePilot 首页 dashboard 中为 MusicPilot 提供一个轻量入口卡片，让用户不用先进入插件页深层查找，也能直接进入 MusicPilot 插件详情页。

## 设计原则
- 保持与 MoviePilot 现有 dashboard 卡片风格一致。
- 只做轻量摘要，不在首页重复承载完整 MusicPilot 页面。
- 点击后复用宿主既有插件详情弹窗路径，而不是自定义新的宿主交互。
- 改动范围限定在 MusicPilot 插件自身；不修改宿主 MoviePilot 仓库。

## 方案选择
采用“轻量摘要卡片 + 深链接打开插件详情页”的方案。

### 不采用的方案
- 首页直接嵌入完整 MusicPilot 页面：过重，与插件详情页重复。
- 首页自定义控制宿主 PluginDataDialog：需要耦合宿主前端内部状态，不稳。
- 只放一个裸链接：入口可用，但缺少 dashboard 感。

## 用户体验
首页出现一个 MusicPilot 卡片：
- 标题：MusicPilot
- 副标题：音乐发现、元数据与整理工作台
- 展示三组简短状态：
  - Metadata：当前 provider 状态摘要
  - Discovery：当前榜单/源状态摘要
  - Workspace：preview/apply 接通状态摘要
- 主按钮：打开 MusicPilot

点击主按钮后跳转到：
- `/#/plugins?id=musicpilot`

宿主插件页会自动打开 MusicPilot 插件详情弹窗。

## 技术方案

### 插件后端入口
在插件入口中新增：
- `get_dashboard_meta()`：声明一个 dashboard 项目
- `get_dashboard()`：返回 dashboard 配置

继续使用 `vue` 渲染模式。

### 前端远程组件
新增并暴露：
- `Dashboard.vue`

职责：
- 读取 dashboard 传入的简短配置
- 渲染轻量卡片摘要
- 点击按钮后跳转到 `/#/plugins?id=musicpilot`

### Federation 暴露
在前端 federation 配置里新增：
- `./Dashboard`

### dashboard 数据
第一轮不接复杂实时聚合，只返回稳定静态摘要文案，避免把首页入口扩成新的聚合系统。

摘要文案按当前项目真实状态组织，例如：
- Metadata：seed / MusicBrainz
- Discovery：RSS / ListenBrainz
- Workspace：Preview / Apply 已接通

## 边界
这轮不做：
- 首页内嵌完整 MusicPilot 页面
- 首页 dashboard 实时统计
- 宿主 dashboard 交互增强
- 额外次按钮或复杂配置入口

## 验证
- backend 测试通过
- frontend 测试/构建通过
- 重新打包并同步插件到本地宿主
- 真实打开 MoviePilot 首页，确认出现 MusicPilot dashboard 卡片
- 点击“打开 MusicPilot”后，确认跳转并自动打开插件详情页
- 保留真实截图
