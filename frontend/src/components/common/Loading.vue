<template>
  <div class="loading-container">
    <n-spin :show="loading" :description="description">
      <slot v-if="!loading" />
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { NSpin } from 'naive-ui'

defineProps<{
  loading: boolean
  description?: string
}>()
</script>

<style scoped>
.loading-container {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>