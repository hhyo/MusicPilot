<template>
  <VList class="app-nav" bg-color="transparent" density="comfortable" nav>
    <VListItem
      v-for="item in items"
      :key="item.key"
      :to="item.route"
      rounded="xl"
      color="primary"
    >
      <template #prepend>
        <VIcon :icon="item.icon" size="20" />
      </template>
      <VListItemTitle class="nav-title">{{ item.title }}</VListItemTitle>
      <VListItemSubtitle class="nav-description">{{ item.description }}</VListItemSubtitle>
      <template #append>
        <VChip size="x-small" variant="flat" color="secondary">{{ item.status }}</VChip>
      </template>
    </VListItem>
  </VList>
</template>

<script setup lang="ts">
import type { NavigationModule } from '@/types/module';

defineProps<{
  items: NavigationModule[];
}>();
</script>

<style scoped lang="scss">
.app-nav {
  padding: 0;
  border-radius: 24px;
  border: 1px solid var(--mp-line);
  background: var(--mp-panel);
  box-shadow: var(--mp-shadow);
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
