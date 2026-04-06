# MusicPilot Plugin Page Vue Remote Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 MusicPilot 在 MoviePilot 插件中心中通过宿主原生 `vue` 远程组件模式打开真实详情页面。

**Architecture:** 保留现有独立前端和插件 API，不重写宿主页面结构。通过 Vite federation 导出标准 `Page` 组件，在该组件内部挂载一个使用 `Element Plus + Pinia + Memory Router` 的 MusicPilot 子应用，并把插件入口改为 `get_render_mode() -> ('vue', 'static/assets')`。打包脚本继续把前端产物装配到 `plugin_runtime/plugins/musicpilot/static/assets/`，宿主通过 `/api/v1/plugin/remotes` 和 `/api/v1/plugin/file/musicpilot/static/assets/remoteEntry.js` 加载远程页面。

**Tech Stack:** Vue 3, TypeScript, Vite, @originjs/vite-plugin-federation, Element Plus, Pinia, FastAPI, Python packaging script.

---

### Task 1: 改造前端为“独立应用 + 远程 Page 组件”双入口

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/frontend/package.json`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/frontend/vite.config.ts`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/frontend/src/main.ts`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/frontend/src/router/index.ts`
- Create: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/frontend/src/app/createApp.ts`
- Create: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/frontend/src/plugin/Page.vue`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/frontend/src/plugin/__tests__/Page.spec.ts`

- [ ] **Step 1: 写前端红测，锁定远程 Page 能渲染并挂载 MusicPilot 子应用**

```ts
import { mount } from '@vue/test-utils'
import Page from '@/plugin/Page.vue'

it('mounts plugin page shell and shows discovery entry', async () => {
  const wrapper = mount(Page, {
    props: {
      api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
      show_switch: true,
    },
  })

  expect(wrapper.text()).toContain('MusicPilot')
  expect(wrapper.text()).toContain('榜单')
})
```

- [ ] **Step 2: 运行红测，确认当前缺少 `Page.vue` 和远程入口**

Run:
```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/frontend
pnpm test -- --run src/plugin/__tests__/Page.spec.ts
```
Expected:
- FAIL
- 找不到 `@/plugin/Page.vue` 或挂载内容为空

- [ ] **Step 3: 提炼可复用的子应用工厂，并让路由支持 `web` / `memory` 两种历史模式**

```ts
// frontend/src/app/createApp.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from '@/App.vue'
import { createMusicPilotRouter } from '@/router'
import '@/styles/main.scss'

export function mountMusicPilotApp(target: Element, options?: { history?: 'web' | 'memory' }) {
  const app = createApp(App)
  const router = createMusicPilotRouter(options?.history ?? 'web')
  app.use(createPinia())
  app.use(router)
  app.use(ElementPlus)
  app.mount(target)
  return { app, router }
}
```

```ts
// frontend/src/router/index.ts
import { createMemoryHistory, createRouter, createWebHistory } from 'vue-router'

export function createMusicPilotRouter(mode: 'web' | 'memory' = 'web') {
  return createRouter({
    history: mode === 'memory' ? createMemoryHistory() : createWebHistory(),
    routes,
    scrollBehavior() {
      return { top: 0 }
    },
  })
}

const router = createMusicPilotRouter('web')
export default router
```

- [ ] **Step 4: 实现远程 `Page.vue`，在宿主插件详情弹窗里挂载子应用**

```vue
<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { mountMusicPilotApp } from '@/app/createApp'

const emit = defineEmits(['action', 'switch', 'close'])
const rootEl = ref<HTMLElement | null>(null)
let mounted: ReturnType<typeof mountMusicPilotApp> | null = null

onMounted(() => {
  if (!rootEl.value) return
  mounted = mountMusicPilotApp(rootEl.value, { history: 'memory' })
})

onBeforeUnmount(() => {
  mounted?.app.unmount()
  mounted = null
})
</script>

<template>
  <div class="plugin-page-shell">
    <header class="plugin-page-shell__header">
      <div>
        <p class="plugin-page-shell__eyebrow">MoviePilot Plugin</p>
        <h2>MusicPilot</h2>
      </div>
      <button class="plugin-page-shell__close" type="button" @click="emit('close')">关闭</button>
    </header>
    <div ref="rootEl" class="plugin-page-shell__body"></div>
  </div>
</template>
```

```ts
// frontend/vite.config.ts
import federation from '@originjs/vite-plugin-federation'

plugins: [
  vue(),
  federation({
    name: 'musicpilot',
    filename: 'remoteEntry.js',
    exposes: {
      './Page': './src/plugin/Page.vue',
    },
    shared: {
      vue: { requiredVersion: false },
    },
    format: 'esm',
  }),
],
build: {
  target: 'esnext',
  cssCodeSplit: true,
},
```

- [ ] **Step 5: 安装 federation 依赖并运行前端测试验证转绿**

Run:
```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/frontend
pnpm add -D @originjs/vite-plugin-federation
pnpm test -- --run src/plugin/__tests__/Page.spec.ts
```
Expected:
- PASS
- `Page.vue` 能挂载出 `MusicPilot` 子应用壳

- [ ] **Step 6: 构建前端，确认生成 `remoteEntry.js`**

Run:
```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/frontend
pnpm build
find dist -maxdepth 2 \( -name 'remoteEntry.js' -o -name '*.css' -o -name '*.js' \) | sed -n '1,40p'
```
Expected:
- PASS
- `dist/assets/remoteEntry.js` 或等价 federation 产物存在

- [ ] **Step 7: 提交 Task 1**

```bash
git add frontend/package.json frontend/vite.config.ts frontend/src/main.ts frontend/src/router/index.ts frontend/src/app/createApp.ts frontend/src/plugin/Page.vue frontend/src/plugin/__tests__/Page.spec.ts pnpm-lock.yaml
git commit -m "feat: add vue remote plugin page shell"
```

### Task 2: 调整插件入口与打包，使宿主识别为 `vue` 远程组件插件

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/backend/app/__init__.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/plugin_runtime/plugins/musicpilot/__init__.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/scripts/package_plugin.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/backend/tests/test_moviepilot_semantics.py`

- [ ] **Step 1: 写后端红测，锁定插件远程页面元信息**

```python
def test_musicpilot_plugin_uses_vue_render_mode(self):
    from app import musicpilot

    plugin = musicpilot()
    assert plugin.get_render_mode() == ("vue", "static/assets")
    assert plugin.get_page() is None
```

- [ ] **Step 2: 运行红测，确认当前仍是默认 `vuetify` 模式**

Run:
```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/backend
.venv/bin/python -m unittest tests.test_moviepilot_semantics
```
Expected:
- FAIL
- `get_render_mode()` 不是 `('vue', 'static/assets')`

- [ ] **Step 3: 改插件入口为宿主原生 `vue` 远程组件模式**

```python
# backend/app/__init__.py and plugin_runtime/plugins/musicpilot/__init__.py
@staticmethod
def get_render_mode():
    return "vue", "static/assets"

def get_page(self):
    return None
```

- [ ] **Step 4: 调整打包脚本，确保 federation 构建产物完整进入 `static/assets/`**

```python
# scripts/package_plugin.py
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
STATIC_DIR = PLUGIN_DIR / "static"

# 保持 reset_directory(STATIC_DIR)
# 复制 dist 下的所有文件和 assets 目录
```

- [ ] **Step 5: 运行后端测试和打包验证转绿**

Run:
```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/backend
.venv/bin/python -m unittest tests.test_moviepilot_semantics
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote
python3 scripts/package_plugin.py
find plugin_runtime/plugins/musicpilot/static -maxdepth 2 \( -name 'remoteEntry.js' -o -name '*.css' -o -name '*.js' \) | sed -n '1,40p'
```
Expected:
- tests PASS
- `plugin_runtime/plugins/musicpilot/static/assets/remoteEntry.js` 存在

- [ ] **Step 6: 提交 Task 2**

```bash
git add backend/app/__init__.py plugin_runtime/plugins/musicpilot/__init__.py scripts/package_plugin.py backend/tests/test_moviepilot_semantics.py
git commit -m "feat: expose musicpilot plugin page as vue remote"
```

### Task 3: 宿主运行态联调与文档收口

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/README.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/backend/README.md`
- Create: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/docs/37_插件中心页面入口_vue_remote_运行态验证.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/docs/28_项目整体任务盘点与执行路线.md`

- [ ] **Step 1: 重新打包并同步到本地宿主插件目录**

Run:
```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote
python3 scripts/package_plugin.py
rsync -ac --delete plugin_runtime/plugins/musicpilot/ /Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/app/plugins/musicpilot/
```
Expected:
- 宿主目录中的 `musicpilot/static/assets/remoteEntry.js` 与本地打包结果一致

- [ ] **Step 2: 启动宿主并验证 remotes 接口**

Run:
```bash
cd /Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot
CONFIG_DIR="$PWD/config-dev" DEV=true ./.venv/bin/python -m app.main
```

Then verify:
```bash
curl -s -H 'X-API-KEY: moviepilot-dev-token' http://127.0.0.1:3001/api/v1/plugin/remotes?token=moviepilot
curl -I -s http://127.0.0.1:3001/api/v1/plugin/file/musicpilot/static/assets/remoteEntry.js
```
Expected:
- `plugin/remotes` 返回 `musicpilot`
- `remoteEntry.js` 返回 `200`

- [ ] **Step 3: 用宿主前端真实打开插件详情页并截图留证**

Run (example validation flow):
```bash
cd /Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot-Frontend
yarn dev --host
```

Manual verification:
1. 打开 `http://127.0.0.1:5173/plugins`
2. 点击 `MusicPilot`
3. 确认插件详情弹窗中加载了远程 `Page` 组件
4. 确认页面中至少一项真实功能可操作（推荐：Charts 或 Settings）
5. 保存两张截图：
   - 插件列表中可打开详情页
   - 详情页中远程页面加载成功

- [ ] **Step 4: 更新 README 和运行态验证文档**

```md
- README 增加：MusicPilot 前端已通过宿主 `vue` 远程组件模式接入插件中心详情页
- backend/README 增加：本地宿主验证步骤与 `/api/v1/plugin/remotes` / `remoteEntry.js` 验证点
- docs/37_插件中心页面入口_vue_remote_运行态验证.md 记录：
  - 宿主路径
  - 同步命令
  - remotes 返回
  - remoteEntry 可访问
  - 插件中心截图路径
```

- [ ] **Step 5: 跑最终验证**

Run:
```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/backend
.venv/bin/python -m unittest discover -s tests
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote/frontend
pnpm test -- --run
pnpm build
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/plugin-page-vue-remote
python3 scripts/package_plugin.py
```
Expected:
- backend 全量 PASS
- frontend 测试 PASS
- frontend build PASS
- packaging PASS

- [ ] **Step 6: 提交 Task 3**

```bash
git add README.md backend/README.md docs/28_项目整体任务盘点与执行路线.md docs/37_插件中心页面入口_vue_remote_运行态验证.md
git commit -m "docs: record vue remote plugin page validation"
```
