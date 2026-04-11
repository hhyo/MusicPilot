import { createApp } from 'vue';
import { createPinia } from 'pinia';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';

import App from '@/App.vue';
import { createMusicPilotRouter } from '@/router';
import '@/styles/main.scss';

export function mountMusicPilotApp(
  target: Element,
  options?: { history?: 'web' | 'memory'; initialPath?: string },
) {
  const app = createApp(App);
  const router = createMusicPilotRouter(options?.history ?? 'web');

  app.use(createPinia());
  app.use(router);
  app.use(ElementPlus);
  app.mount(target);

  const initialPath = options?.initialPath?.trim();
  if (initialPath && router.currentRoute.value.fullPath !== initialPath) {
    void router.replace(initialPath);
  }

  return { app, router };
}
