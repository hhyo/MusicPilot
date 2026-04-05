<template>
  <el-drawer
    :model-value="modelValue"
    size="520px"
    title="Metadata Detail"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div class="detail-drawer">
      <el-alert
        title="当前可基于 metadata 创建订阅与搜索任务。search / dispatch 会直接展示当前 backend 与明确错误；音乐 organize 的 preview/apply 在订阅执行流中继续工作。真实 metadata provider、真实 discovery 与最小自动调度已接入，当前重点在真实命中率与自动闭环收口。"
        type="info"
        :closable="false"
        show-icon
      />

      <el-skeleton v-if="loading" animated :rows="8" />

      <el-alert
        v-else-if="errorMessage"
        :title="errorMessage"
        type="error"
        :closable="false"
        show-icon
      />

      <template v-else-if="detail">
        <section class="detail-section">
          <p class="detail-section__eyebrow">{{ detail.entity_type }}</p>
          <h3>{{ detail.title }}</h3>
          <p class="detail-section__note">{{ detail.note }}</p>
        </section>

        <el-descriptions :column="1" border>
          <el-descriptions-item label="Artist">{{ detail.artist_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Album">{{ detail.album_title || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Year">{{ detail.year || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Release Type">{{ detail.release_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Provider">
            {{ detail.provider }} / {{ detail.source_type }}
          </el-descriptions-item>
          <el-descriptions-item label="Country">{{ detail.country || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Disambiguation">
            {{ detail.disambiguation || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="Release Count">
            {{ detail.release_count ?? '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="Duration">
            {{ detail.duration_seconds ? `${detail.duration_seconds}s` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="Aliases">
            {{ detail.aliases.length > 0 ? detail.aliases.join(' / ') : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="Genres">
            {{ detail.genres.length > 0 ? detail.genres.join(' / ') : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="External IDs">
            <div v-if="externalIdEntries.length > 0" class="detail-badges">
              <el-tag
                v-for="[key, value] in externalIdEntries"
                :key="key"
                effect="plain"
                size="small"
              >
                {{ key }}: {{ value }}
              </el-tag>
            </div>
            <span v-else>-</span>
          </el-descriptions-item>
        </el-descriptions>

        <section class="detail-section">
          <h4>后续接入点</h4>
          <p class="detail-section__note">{{ detail.integration_point }}</p>
        </section>

        <section v-if="detail.related_artists.length > 0" class="detail-section">
          <h4>Related Artists</h4>
          <div class="detail-badges">
            <el-tag
              v-for="artist in detail.related_artists"
              :key="artist.id"
              effect="plain"
              type="success"
            >
              {{ artist.title }}
            </el-tag>
          </div>
        </section>

        <section v-if="detail.related_album" class="detail-section">
          <h4>Related Album</h4>
          <p class="detail-section__note">
            {{ detail.related_album.title }}
            <span v-if="detail.related_album.subtitle">· {{ detail.related_album.subtitle }}</span>
          </p>
        </section>

        <section v-if="detail.related_albums.length > 0" class="detail-section">
          <h4>Albums</h4>
          <div class="detail-badges">
            <el-tag
              v-for="album in detail.related_albums"
              :key="album.id"
              effect="plain"
              type="warning"
            >
              {{ album.title }}
            </el-tag>
          </div>
        </section>

        <section v-if="detail.tracks.length > 0" class="detail-section">
          <h4>Tracks</h4>
          <div class="detail-badges">
            <el-tag
              v-for="track in detail.tracks"
              :key="track.id"
              effect="plain"
            >
              {{ formatTrackLabel(track) }}
            </el-tag>
          </div>
        </section>

        <section class="detail-section">
          <h4>当前操作</h4>
          <div class="detail-actions">
            <el-button type="success" plain @click="$emit('create-subscription', detail)">
              创建订阅
            </el-button>
            <el-button type="primary" @click="$emit('search-resources', detail)">
              创建并执行搜索任务
            </el-button>
          </div>
          <ul class="detail-list">
            <li v-for="todo in detail.todo" :key="todo">{{ todo }}</li>
          </ul>
        </section>
      </template>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import type { MetadataDetail, MetadataReference } from '@/types/metadata';

const props = defineProps<{
  modelValue: boolean;
  loading: boolean;
  detail: MetadataDetail | null;
  errorMessage: string;
}>();

defineEmits<{
  (event: 'update:modelValue', value: boolean): void;
  (event: 'search-resources', detail: MetadataDetail): void;
  (event: 'create-subscription', detail: MetadataDetail): void;
}>();

const externalIdEntries = computed(() => Object.entries(props.detail?.external_ids ?? {}));

function formatTrackLabel(track: MetadataReference) {
  const prefixParts = [track.disc_number && `D${track.disc_number}`, track.track_number && `${track.track_number}`]
    .filter(Boolean)
    .join('-');
  return prefixParts ? `${prefixParts} ${track.title}` : track.title;
}
</script>

<style scoped lang="scss">
.detail-drawer {
  display: grid;
  gap: 1rem;
}

.detail-section {
  display: grid;
  gap: 0.6rem;
}

.detail-section h3,
.detail-section h4,
.detail-section__note,
.detail-section__eyebrow {
  margin: 0;
}

.detail-section__eyebrow {
  color: var(--mp-accent);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.detail-section__note {
  color: var(--mp-muted);
  line-height: 1.7;
}

.detail-badges {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.detail-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.detail-list {
  margin: 0;
  padding-left: 1.1rem;
  color: var(--mp-muted);
  line-height: 1.8;
}
</style>
