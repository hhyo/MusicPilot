<template>
  <div class="pagination">
    <n-pagination
      v-model:page="currentPage"
      :page-count="pageCount"
      :page-size="pageSize"
      :item-count="totalItems"
      show-size-picker
      :page-sizes="[10, 20, 50, 100]"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NPagination } from 'naive-ui'

const props = defineProps<{
  page: number
  pageSize: number
  totalItems: number
}>()

const emit = defineEmits<{
  'update:page': [page: number]
  'update:pageSize': [pageSize: number]
}>()

const currentPage = computed({
  get: () => props.page,
  set: (val: number) => emit('update:page', val)
})

const pageCount = computed(() => Math.ceil(props.totalItems / props.pageSize))

function handlePageChange(page: number) {
  emit('update:page', page)
}

function handlePageSizeChange(pageSize: number) {
  emit('update:pageSize', pageSize)
  emit('update:page', 1)
}
</script>

<style scoped>
.pagination {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}
</style>