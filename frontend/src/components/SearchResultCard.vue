<template>
  <VCard class="search-result-card panel-card">
    <VCardText class="stack">
      <div class="search-result-card__header">
        <div>
          <p class="eyebrow">{{ item.entity_type }}</p>
          <h3 class="search-result-card__title">{{ item.title }}</h3>
        </div>
        <VChip color="primary" variant="tonal">{{ item.provider }}</VChip>
      </div>

      <div class="meta-pairs">
        <div class="meta-pair">
          <span class="meta-pair__label">Artist</span>
          <span class="meta-pair__value">{{ item.artist_name || '-' }}</span>
        </div>
        <div class="meta-pair">
          <span class="meta-pair__label">Album</span>
          <span class="meta-pair__value">{{ item.album_title || '-' }}</span>
        </div>
        <div class="meta-pair">
          <span class="meta-pair__label">Year</span>
          <span class="meta-pair__value">{{ item.year || '-' }}</span>
        </div>
      </div>

      <p class="section-note">{{ item.note }}</p>

      <div class="search-result-card__actions">
        <VBtn color="primary" variant="flat" @click="$emit('view-detail', item)">
          查看详情
        </VBtn>
      </div>
    </VCardText>
  </VCard>
</template>

<script setup lang="ts">
import type { MetadataSummary } from '@/types/metadata';

defineProps<{
  item: MetadataSummary;
}>();

defineEmits<{
  (event: 'view-detail', item: MetadataSummary): void;
}>();
</script>

<style scoped lang="scss">
.search-result-card__header,
.search-result-card__actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.search-result-card__title {
  margin: 0.25rem 0 0;
  font-size: 1.15rem;
}
</style>
