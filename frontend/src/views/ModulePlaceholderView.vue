<template>
  <div class="page-shell">
    <VCard class="hero-card">
      <VCardText class="pa-6 stack">
        <div class="subscriptions-view__header">
          <div>
            <p class="eyebrow">Planned Module</p>
            <h2 class="section-title">{{ title }}</h2>
          </div>
          <VChip color="warning" variant="tonal">待后续接入</VChip>
        </div>
        <p class="section-note">{{ description }}</p>
      </VCardText>
    </VCard>

    <div class="stats-grid">
      <VCard v-for="item in notes" :key="item.title" class="panel-card">
        <VCardText class="pa-5">
          <p class="eyebrow">{{ item.title }}</p>
          <p class="section-note">{{ item.note }}</p>
        </VCardText>
      </VCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

const title = computed(() => String(route.meta.title ?? '占位页'));
const description = computed(() => String(route.meta.description ?? ''));

const notes = [
  {
    title: '当前状态',
    note: '入口已保留，模块边界已明确，但当前页面不承载真实业务流。',
  },
  {
    title: '后续接入点',
    note: '后续会优先从服务层、类型层和后端契约补齐，不在页面内堆临时逻辑。',
  },
  {
    title: '本轮约束',
    note: '本轮前端重构先聚焦 discovery、metadata、subscriptions 和 settings 主链页面。',
  },
];
</script>
