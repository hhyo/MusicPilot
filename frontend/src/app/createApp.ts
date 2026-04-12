import { createApp } from 'vue';
import { createPinia } from 'pinia';

import App from '@/App.vue';
import { vuetify } from '@/plugins/vuetify';
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
  app.use(vuetify);
  app.mount(target);

  const initialPath = options?.initialPath?.trim();
  if (initialPath && router.currentRoute.value.fullPath !== initialPath) {
    void router.replace(initialPath);
  }

  return { app, router };
}
