<template>
  <article class="module-card">
    <header class="module-card__header">
      <div>
        <p class="module-card__eyebrow">{{ module.status }}</p>
        <h3>{{ module.title }}</h3>
      </div>
      <el-tag type="primary" effect="plain">当前状态</el-tag>
    </header>

    <p class="module-card__description">{{ module.description }}</p>

    <RouterLink class="module-card__link" :to="module.route">
      进入模块
    </RouterLink>
  </article>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router';

import type { NavigationModule } from '@/types/module';

defineProps<{
  module: NavigationModule;
}>();
</script>

<style scoped lang="scss">
.module-card {
  display: grid;
  gap: 1rem;
  padding: 1.2rem;
  min-height: 220px;
  border: 1px solid var(--mp-line);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 18px 40px rgba(63, 43, 126, 0.08);
}

.module-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.module-card__header h3 {
  margin: 0.25rem 0 0;
  font-size: 1.15rem;
}

.module-card__eyebrow {
  margin: 0;
  color: var(--mp-accent);
  font-size: 0.8rem;
  font-weight: 700;
}

.module-card__description {
  margin: 0;
  color: var(--mp-muted);
  line-height: 1.7;
}

.module-card__link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  padding: 0.8rem 1rem;
  border-radius: 14px;
  background: rgba(126, 94, 248, 0.12);
  color: var(--mp-accent);
  font-weight: 700;
  text-decoration: none;
}
</style>
