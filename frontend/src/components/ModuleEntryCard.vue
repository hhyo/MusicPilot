<template>
  <VCard class="module-entry-card panel-card" :to="module.route" rounded="xl" hover>
    <VCardText class="stack">
      <div class="module-entry-card__head">
        <VAvatar color="primary" variant="tonal" size="42">
          <VIcon :icon="module.icon" />
        </VAvatar>
        <VChip color="secondary" variant="tonal">{{ module.status }}</VChip>
      </div>
      <div>
        <h3 class="module-entry-card__title">{{ module.title }}</h3>
        <p class="section-note">{{ module.description }}</p>
      </div>
    </VCardText>
  </VCard>
</template>

<script setup lang="ts">
import type { NavigationModule } from '@/types/module';

defineProps<{
  module: NavigationModule;
}>();
</script>

<style scoped lang="scss">
.module-entry-card {
  text-decoration: none;
  color: inherit;
}

.module-entry-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.module-entry-card__title {
  margin: 0;
  font-size: 1.1rem;
}
</style>
