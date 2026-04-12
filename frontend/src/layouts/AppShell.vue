<template>
  <div class="shell">
    <aside class="shell__sidebar">
      <VCard class="brand-card" rounded="xl">
        <VCardText class="pa-6">
          <p class="brand-card__phase">{{ app.phaseLabel }}</p>
          <h1>{{ app.appName }}</h1>
          <p class="brand-card__description">
            统一围绕音乐媒体解析链组织 discovery、metadata、subscription 和 acquisition，
            作为 MoviePilot 的音乐工作台入口。
          </p>
          <div class="brand-card__chips">
            <VChip color="primary" variant="flat">Music Media Chain</VChip>
            <VChip color="success" variant="flat">Plugin Runtime</VChip>
          </div>
        </VCardText>
      </VCard>

      <AppNav :items="app.modules" />
    </aside>

    <main class="shell__content">
      <VCard class="topbar" rounded="xl">
        <VCardText class="topbar__inner">
          <div>
            <p class="topbar__eyebrow">MoviePilot Music Plugin</p>
            <h2>MusicPilot 工作台</h2>
          </div>
          <VChip color="success" variant="flat">统一音乐媒体解析链已接入后端主线</VChip>
        </VCardText>
      </VCard>

      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router';

import AppNav from '@/components/AppNav.vue';
import { useAppStore } from '@/stores/app';

const app = useAppStore();
</script>

<style scoped lang="scss">
.shell {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 1.5rem;
  min-height: 100vh;
  padding: 1.5rem;
}

.shell__sidebar {
  display: grid;
  gap: 1rem;
  align-content: start;
}

.brand-card {
  border: 1px solid rgba(255, 255, 255, 0.2);
  background:
    linear-gradient(145deg, rgba(17, 24, 39, 0.96), rgba(31, 111, 235, 0.92) 68%, rgba(14, 165, 233, 0.82));
  color: #fff;
  box-shadow: 0 24px 54px rgba(15, 23, 42, 0.24);
}

.brand-card h1 {
  margin: 0.2rem 0 0.6rem;
  font-size: 1.9rem;
}

.brand-card__phase {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.84;
}

.brand-card__description {
  margin: 0;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.88);
}

.brand-card__chips {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 1.1rem;
}

.shell__content {
  min-width: 0;
}

.topbar {
  margin-bottom: 1.25rem;
  border: 1px solid var(--mp-line);
  background: var(--mp-panel);
  box-shadow: var(--mp-shadow);
}

.topbar__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.2rem 1.4rem;
}

.topbar h2 {
  margin: 0.35rem 0 0;
  font-size: 1.5rem;
}

.topbar__eyebrow {
  margin: 0;
  color: var(--mp-muted);
  font-size: 0.84rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

@media (max-width: 1080px) {
  .shell {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .shell {
    padding: 1rem;
  }

  .topbar {
    .topbar__inner {
      align-items: flex-start;
      flex-direction: column;
    }
  }
}
</style>
