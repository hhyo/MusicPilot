<template>
  <div class="search-bar">
    <n-input
      v-model:value="searchQuery"
      placeholder="搜索音乐..."
      clearable
      @input="handleSearch"
    >
      <template #prefix>
        <n-icon><SearchIcon /></n-icon>
      </template>
    </n-input>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NInput, NIcon } from 'naive-ui'
import { SearchOutline as SearchIcon } from '@vicons/ionicons5'

const searchQuery = ref('')

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    console.log('搜索:', searchQuery.value)
    // TODO: 实现搜索功能
  }
}
</script>

<style scoped>
.search-bar {
  width: 300px;
}
</style>