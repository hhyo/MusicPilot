<template>
  <div class="shell">
    <aside class="shell__sidebar">
      <div class="brand-card">
        <p class="brand-card__phase">{{ app.phaseLabel }}</p>
        <h1>{{ app.appName }}</h1>
        <p class="brand-card__description">
          独立音乐插件入口壳。当前已接通 metadata 搜索最小闭环，并保留后续扩展位。
        </p>
      </div>

      <AppNav :items="app.modules" />
    </aside>

    <main class="shell__content">
      <header class="topbar">
        <div>
          <p class="topbar__eyebrow">MoviePilot Plugin Metadata MVP</p>
          <h2>MusicPilot Metadata 最小闭环</h2>
        </div>
        <el-tag type="success" effect="plain">搜索链路可联调</el-tag>
      </header>

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
  padding: 1.5rem;
  border-radius: 28px;
  background: linear-gradient(145deg, #2b255d, #7e5ef8 62%, #d8cdfd);
  color: #fff;
  box-shadow: 0 22px 50px rgba(55, 37, 122, 0.24);
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

.shell__content {
  min-width: 0;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
  padding: 1.4rem 1.5rem;
  border: 1px solid var(--mp-line);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.76);
  box-shadow: 0 16px 40px rgba(52, 37, 122, 0.08);
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
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
