<template>
  <VNavigationDrawer
    :model-value="modelValue"
    location="right"
    temporary
    width="560"
    class="metadata-drawer"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div class="metadata-drawer__inner">
      <div class="metadata-drawer__sticky">
        <p class="eyebrow">Metadata Detail</p>
        <h3 class="metadata-drawer__title">{{ detail?.title || '音乐实体详情' }}</h3>
        <p class="section-note">
          当前详情来自统一音乐媒体解析链，可直接基于该实体创建搜索任务或订阅。
        </p>
      </div>

      <VAlert
        v-if="errorMessage"
        type="error"
        variant="tonal"
        density="comfortable"
        :text="errorMessage"
      />

      <template v-else-if="loading">
        <VSkeletonLoader type="heading, article, article, article" />
      </template>

      <template v-else-if="detail">
        <VCard class="panel-card">
          <VCardText class="stack">
            <div>
              <p class="eyebrow">{{ detail.entity_type }}</p>
              <h4 class="metadata-drawer__headline">{{ detail.title }}</h4>
              <p class="section-note">{{ detail.note }}</p>
            </div>

            <div class="meta-pairs">
              <div class="meta-pair">
                <span class="meta-pair__label">Artist</span>
                <span class="meta-pair__value">{{ detail.artist_name || '-' }}</span>
              </div>
              <div class="meta-pair">
                <span class="meta-pair__label">Album</span>
                <span class="meta-pair__value">{{ detail.album_title || '-' }}</span>
              </div>
              <div class="meta-pair">
                <span class="meta-pair__label">Year</span>
                <span class="meta-pair__value">{{ detail.year || '-' }}</span>
              </div>
              <div class="meta-pair">
                <span class="meta-pair__label">Provider</span>
                <span class="meta-pair__value">{{ detail.provider }} / {{ detail.source_type }}</span>
              </div>
            </div>

            <div v-if="assessment || metaBase || mediaInfo" class="soft-block stack">
              <div v-if="assessment">
                <p class="eyebrow">Recognition</p>
                <div class="metadata-drawer__chips">
                  <VChip color="primary" variant="tonal">{{ assessment.state }}</VChip>
                  <VChip v-if="assessment.note" variant="outlined">{{ assessment.note }}</VChip>
                </div>
              </div>

              <div v-if="metaBase">
                <p class="eyebrow">Meta Base</p>
                <p class="section-note">
                  {{ metaBase.canonical_title || detail.title }}
                  <span v-if="metaBase.canonical_artist_names.length > 0">
                    · {{ metaBase.canonical_artist_names.join(' / ') }}
                  </span>
                </p>
              </div>

              <div v-if="mediaInfo">
                <p class="eyebrow">Media Info</p>
                <p class="section-note">
                  {{ mediaInfo.provider }} / {{ mediaInfo.provider_id }}
                  <span v-if="mediaInfo.match_strategy"> · {{ mediaInfo.match_strategy }}</span>
                </p>
              </div>
            </div>

            <div v-if="detail.related_artists.length > 0" class="stack">
              <p class="eyebrow">Related Artists</p>
              <div class="metadata-drawer__chips">
                <VChip
                  v-for="artist in detail.related_artists"
                  :key="artist.id"
                  color="success"
                  variant="tonal"
                >
                  {{ artist.title }}
                </VChip>
              </div>
            </div>

            <div v-if="detail.related_albums.length > 0" class="stack">
              <p class="eyebrow">Related Albums</p>
              <div class="metadata-drawer__chips">
                <VChip
                  v-for="album in detail.related_albums"
                  :key="album.id"
                  color="warning"
                  variant="tonal"
                >
                  {{ album.title }}
                </VChip>
              </div>
            </div>

            <div v-if="detail.tracks.length > 0" class="stack">
              <p class="eyebrow">Tracks</p>
              <div class="metadata-drawer__chips">
                <VChip v-for="track in detail.tracks" :key="track.id" variant="outlined">
                  {{ formatTrackLabel(track) }}
                </VChip>
              </div>
            </div>

            <div class="metadata-drawer__actions">
              <VBtn color="primary" variant="flat" @click="$emit('search-resources', detail)">
                创建搜索任务
              </VBtn>
              <VBtn color="secondary" variant="tonal" @click="$emit('create-subscription', detail)">
                创建订阅
              </VBtn>
            </div>
          </VCardText>
        </VCard>
      </template>
    </div>
  </VNavigationDrawer>
</template>

<script setup lang="ts">
import type { MetadataDetail, MetadataReference } from '@/types/metadata';
import type { MusicMediaInfo, MusicMetaBase, MusicRecognitionAssessment } from '@/types/music-media';

defineProps<{
  modelValue: boolean;
  loading: boolean;
  detail: MetadataDetail | null;
  errorMessage: string;
  metaBase?: MusicMetaBase | null;
  mediaInfo?: MusicMediaInfo | null;
  assessment?: MusicRecognitionAssessment | null;
}>();

defineEmits<{
  (event: 'update:modelValue', value: boolean): void;
  (event: 'search-resources', detail: MetadataDetail): void;
  (event: 'create-subscription', detail: MetadataDetail): void;
}>();

function formatTrackLabel(track: MetadataReference) {
  const prefixParts = [track.disc_number && `D${track.disc_number}`, track.track_number && `${track.track_number}`]
    .filter(Boolean)
    .join('-');
  return prefixParts ? `${prefixParts} ${track.title}` : track.title;
}
</script>

<style scoped lang="scss">
.metadata-drawer__inner {
  display: grid;
  gap: 1rem;
  padding: 1rem;
}

.metadata-drawer__sticky {
  position: sticky;
  top: 0;
  z-index: 1;
  padding-bottom: 0.5rem;
  background: rgb(var(--v-theme-surface));
}

.metadata-drawer__title,
.metadata-drawer__headline {
  margin: 0.3rem 0 0;
}

.metadata-drawer__headline {
  font-size: 1.25rem;
}

.metadata-drawer__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.metadata-drawer__actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}
</style>
