<template>
  <div class="library-view">
    <n-page-header title="音乐库" />
    <n-spin :show="loading">
      <n-empty v-if="!loading && !libraries.length" description="暂无音乐库" />
      <n-list v-else>
        <n-list-item v-for="library in libraries" :key="library.id">
          <div class="library-item">
            <div class="library-info">
              <div class="library-name">{{ library.name }}</div>
              <div class="library-path">{{ library.path }}</div>
            </div>
            <div class="library-stats">
              <n-tag>{{ library.trackCount || 0 }} 首曲目</n-tag>
              <n-tag>{{ library.albumCount || 0 }} 张专辑</n-tag>
            </div>
          </div>
        </n-list-item>
      </n-list>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NPageHeader, NSpin, NEmpty, NList, NListItem, NTag } from 'naive-ui'
import { useLibraryStore, type Library } from '@/store/library'

const libraryStore = useLibraryStore()
const loading = ref(false)
const libraries = ref<Library[]>([])

onMounted(async () => {
  loading.value = true
  // TODO: 调用 API 获取音乐库列表
  loading.value = false
})
</script>

<style scoped>
.library-view {
  padding: 20px;
}

.library-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.library-info {
  flex: 1;
}

.library-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}

.library-path {
  font-size: 12px;
  color: var(--n-text-color-2);
}

.library-stats {
  display: flex;
  gap: 8px;
}
</style>