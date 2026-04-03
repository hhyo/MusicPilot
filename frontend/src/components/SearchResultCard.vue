<template>
  <article class="result-card">
    <header class="result-card__header">
      <div>
        <p class="result-card__type">{{ typeLabel }}</p>
        <h3>{{ item.title }}</h3>
      </div>
      <el-tag size="small" type="info" effect="plain">{{ item.provider }}</el-tag>
    </header>

    <p class="result-card__meta">
      {{ primaryMeta }}
    </p>

    <div class="result-card__tags">
      <el-tag v-if="item.year" size="small" effect="plain">{{ item.year }}</el-tag>
      <el-tag v-if="item.release_type" size="small" effect="plain">{{ item.release_type }}</el-tag>
      <el-tag size="small" effect="plain">{{ item.source_type }}</el-tag>
      <el-tag v-for="genre in item.genres.slice(0, 2)" :key="genre" size="small" type="success" effect="plain">
        {{ genre }}
      </el-tag>
    </div>

    <p class="result-card__note">{{ item.note }}</p>

    <footer class="result-card__footer">
      <span>{{ aliasText }}</span>
      <el-button type="primary" plain @click="$emit('view-detail', item)">
        查看详情
      </el-button>
    </footer>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import type { MetadataSummary } from '@/types/metadata';

const props = defineProps<{
  item: MetadataSummary;
}>();

defineEmits<{
  (event: 'view-detail', item: MetadataSummary): void;
}>();

const typeMap = {
  artist: 'Artist',
  album: 'Album',
  track: 'Track',
} as const;

const typeLabel = computed(() => typeMap[props.item.entity_type]);

const primaryMeta = computed(() => {
  if (props.item.entity_type === 'artist') {
    return props.item.artist_name ?? '本地 seed 艺人';
  }

  if (props.item.entity_type === 'album') {
    return props.item.artist_name ? `${props.item.artist_name} · 专辑元数据` : '专辑元数据';
  }

  const segments = [props.item.artist_name, props.item.album_title].filter(Boolean);
  return segments.join(' · ') || '歌曲元数据';
});

const aliasText = computed(() =>
  props.item.aliases.length > 0 ? `别名：${props.item.aliases.join(' / ')}` : '暂无额外别名',
);
</script>

<style scoped lang="scss">
.result-card {
  display: grid;
  gap: 0.9rem;
  padding: 1.1rem;
  border: 1px solid var(--mp-line);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 16px 30px rgba(52, 37, 122, 0.06);
}

.result-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.8rem;
}

.result-card__header h3,
.result-card__meta,
.result-card__note {
  margin: 0;
}

.result-card__type {
  margin: 0 0 0.25rem;
  color: var(--mp-accent);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.result-card__meta {
  color: var(--mp-text);
  font-weight: 600;
}

.result-card__tags {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.result-card__note {
  color: var(--mp-muted);
  line-height: 1.7;
}

.result-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  color: var(--mp-muted);
  font-size: 0.9rem;
}

@media (max-width: 640px) {
  .result-card__footer {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
