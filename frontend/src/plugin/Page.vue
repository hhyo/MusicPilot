<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';

import { mountMusicPilotApp } from '@/app/createApp';

defineProps<{
  show_switch?: boolean;
}>();

const emit = defineEmits(['action', 'switch', 'close']);

const rootEl = ref<HTMLElement | null>(null);
let mounted: ReturnType<typeof mountMusicPilotApp> | null = null;

onMounted(async () => {
  if (!rootEl.value) return;
  mounted = mountMusicPilotApp(rootEl.value, { history: 'memory' });
  await mounted.router.isReady();
});

onBeforeUnmount(() => {
  mounted?.app.unmount();
  mounted = null;
});
</script>

<template>
  <section class="plugin-page-shell">
    <VCard class="plugin-page-shell__header" rounded="xl">
      <VCardText class="plugin-page-shell__header-inner">
        <div>
          <p class="plugin-page-shell__eyebrow">MoviePilot Plugin</p>
          <h2>MusicPilot</h2>
        </div>
        <div class="plugin-page-shell__actions">
          <VBtn
            v-if="show_switch"
            color="primary"
            variant="tonal"
            @click="emit('switch')"
          >
            插件设置
          </VBtn>
          <VBtn color="secondary" variant="flat" @click="emit('close')">关闭</VBtn>
        </div>
      </VCardText>
    </VCard>

    <div ref="rootEl" class="plugin-page-shell__body"></div>
  </section>
</template>

<style scoped lang="scss">
.plugin-page-shell {
  display: grid;
  gap: 1rem;
  padding: 1rem;
}

.plugin-page-shell__header {
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: linear-gradient(140deg, #ffffff, #f7fbff 62%, #eef4ff);
}

.plugin-page-shell__header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.25rem;
}

.plugin-page-shell__eyebrow {
  margin: 0;
  color: #667085;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.plugin-page-shell__header h2 {
  margin: 0.35rem 0 0;
  font-size: 1.4rem;
}

.plugin-page-shell__actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.plugin-page-shell__body {
  min-height: min(78vh, 920px);
  overflow: auto;
  border-radius: 24px;
}
</style>
