<template>
  <n-layout-header class="header">
    <div class="header-left">
      <h1 class="title">{{ appTitle }}</h1>
    </div>
    <div class="header-right">
      <SearchBar />
      <n-button quaternary circle>
        <template #icon>
          <n-icon :size="20"><SettingsIcon /></n-icon>
        </template>
      </n-button>
    </div>
  </n-layout-header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NLayoutHeader, NButton, NIcon } from 'naive-ui'
import { SettingsOutline as SettingsIcon } from '@vicons/ionicons5'
import SearchBar from './SearchBar.vue'

const appTitle = computed(() => import.meta.env.VITE_APP_TITLE || 'MusicPilot')
</script>

<style scoped>
.header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid var(--n-border-color);
}

.header-left .title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>