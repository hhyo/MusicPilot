<template>
  <nav class="app-nav">
    <RouterLink
      v-for="item in items"
      :key="item.key"
      :to="item.route"
      class="nav-link"
      active-class="is-active"
    >
      <span class="nav-title">{{ item.title }}</span>
      <span class="nav-description">{{ item.description }}</span>
    </RouterLink>
  </nav>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router';

import type { NavigationModule } from '@/types/module';

defineProps<{
  items: NavigationModule[];
}>();
</script>

<style scoped lang="scss">
.app-nav {
  display: grid;
  gap: 0.75rem;
}

.nav-link {
  display: grid;
  gap: 0.25rem;
  padding: 1rem;
  border-radius: 18px;
  border: 1px solid var(--mp-line);
  background: rgba(255, 255, 255, 0.72);
  color: var(--mp-text);
  text-decoration: none;
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.nav-link:hover,
.nav-link.is-active {
  transform: translateY(-1px);
  border-color: rgba(126, 94, 248, 0.35);
  box-shadow: 0 16px 36px rgba(63, 43, 126, 0.08);
}

.nav-title {
  font-size: 0.98rem;
  font-weight: 700;
}

.nav-description {
  color: var(--mp-muted);
  font-size: 0.84rem;
}
</style>

