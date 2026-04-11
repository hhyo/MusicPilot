<script setup lang="ts">
import { computed } from 'vue';

type DashboardConfig = {
  id?: string;
  name?: string;
  key?: string;
  attrs?: {
    title?: string;
    subtitle?: string;
  };
};

const props = defineProps<{
  config?: DashboardConfig;
  allowRefresh?: boolean;
  api?: {
    get?: (...args: unknown[]) => unknown;
  };
}>();

const title = computed(() => props.config?.attrs?.title || props.config?.name || 'MusicPilot');
const subtitle = computed(
  () => props.config?.attrs?.subtitle || '音乐发现、元数据与整理工作台',
);

const summaryItems = [
  {
    label: 'Metadata',
    value: 'seed / MusicBrainz',
    note: '搜索与详情已接通',
  },
  {
    label: 'Discovery',
    value: 'RSS / ListenBrainz',
    note: '榜单入口已接入',
  },
  {
    label: 'Workspace',
    value: 'Preview / Apply 已接通',
    note: '可直接进入插件工作台',
  },
];

function openMusicPilot(): void {
  const openStandalone = () => {
    window.location.hash = '#/plugin-app/musicpilot/main';
  };
  const openDialog = () => {
    window.location.hash = '#/plugins?id=musicpilot';
  };

  const get = props.api?.get;
  if (!get) {
    openDialog();
    return;
  }

  Promise.resolve(get('plugin/sidebar_nav'))
    .then((result) => {
      if (Array.isArray(result)) {
        openStandalone();
        return;
      }
      openDialog();
    })
    .catch(() => {
      openDialog();
    });
}
</script>

<template>
  <VCard class="musicpilot-dashboard" rounded="xl" elevation="0">
    <VCardItem class="pb-1">
      <template #prepend>
        <div class="musicpilot-dashboard__icon">
          <VIcon icon="mdi-music-note-outline" size="22" />
        </div>
      </template>
      <VCardTitle class="text-h6">{{ title }}</VCardTitle>
      <VCardSubtitle>{{ subtitle }}</VCardSubtitle>
    </VCardItem>

    <VCardText class="pt-2">
      <div class="musicpilot-dashboard__grid">
        <article
          v-for="item in summaryItems"
          :key="item.label"
          class="musicpilot-dashboard__metric"
        >
          <p class="musicpilot-dashboard__metric-label">{{ item.label }}</p>
          <strong class="musicpilot-dashboard__metric-value">{{ item.value }}</strong>
          <p class="musicpilot-dashboard__metric-note">{{ item.note }}</p>
        </article>
      </div>

      <div class="musicpilot-dashboard__actions">
        <VBtn
          class="musicpilot-dashboard__open"
          color="primary"
          rounded="pill"
          variant="flat"
          @click="openMusicPilot"
        >
          打开 MusicPilot
        </VBtn>
      </div>
    </VCardText>
  </VCard>
</template>

<style scoped lang="scss">
.musicpilot-dashboard {
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 248, 250, 0.98));
}

.musicpilot-dashboard__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 999px;
  background: rgba(32, 115, 255, 0.12);
  color: rgb(32, 115, 255);
}

.musicpilot-dashboard__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.85rem;
}

.musicpilot-dashboard__metric {
  padding: 0.95rem 1rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
}

.musicpilot-dashboard__metric-label,
.musicpilot-dashboard__metric-note {
  margin: 0;
}

.musicpilot-dashboard__metric-label {
  color: rgb(102, 112, 133);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.musicpilot-dashboard__metric-value {
  display: block;
  margin-top: 0.45rem;
  color: rgb(16, 24, 40);
  font-size: 0.95rem;
  line-height: 1.4;
}

.musicpilot-dashboard__metric-note {
  margin-top: 0.35rem;
  color: rgb(102, 112, 133);
  font-size: 0.8rem;
}

.musicpilot-dashboard__actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
}

@media (max-width: 960px) {
  .musicpilot-dashboard__grid {
    grid-template-columns: 1fr;
  }
}
</style>
