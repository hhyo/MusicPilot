<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';

import { mountMusicPilotApp } from '@/app/createApp';

const props = defineProps<{
  api?: {
    get?: (...args: unknown[]) => unknown;
  };
  pluginId?: string;
  navKey?: string;
}>();

const rootEl = ref<HTMLElement | null>(null);
let mounted: ReturnType<typeof mountMusicPilotApp> | null = null;

function resolveInitialPath(navKey?: string): string {
  const normalized = (navKey || 'main').trim().toLowerCase();
  switch (normalized) {
    case 'charts':
      return '/charts';
    case 'search':
      return '/search';
    case 'subscriptions':
      return '/subscriptions';
    case 'downloads':
      return '/downloads';
    case 'organize':
      return '/organize';
    case 'settings':
      return '/settings';
    case 'home':
    case 'main':
    default:
      return '/';
  }
}

onMounted(async () => {
  if (!rootEl.value) return;
  mounted = mountMusicPilotApp(rootEl.value, {
    history: 'memory',
    initialPath: resolveInitialPath(props.navKey),
  });
  await mounted.router.isReady();
});

onBeforeUnmount(() => {
  mounted?.app.unmount();
  mounted = null;
});
</script>

<template>
  <section class="plugin-app-shell">
    <div ref="rootEl" class="plugin-app-shell__body"></div>
  </section>
</template>

<style scoped lang="scss">
.plugin-app-shell {
  min-height: calc(100vh - 2rem);
  padding: 0.75rem 0;
}

.plugin-app-shell__body {
  min-height: calc(100vh - 3rem);
}
</style>
