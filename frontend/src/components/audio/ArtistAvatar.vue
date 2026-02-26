<template>
  <div class="artist-avatar" :style="{ width: size, height: size }">
    <img v-if="avatarUrl" :src="avatarUrl" :alt="name" @error="handleError" />
    <div v-else class="avatar-placeholder">
      {{ name.charAt(0).toUpperCase() }}
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  avatarUrl?: string
  name: string
  size?: string
}>()

function handleError() {
  console.warn('头像加载失败')
}
</script>

<style scoped>
.artist-avatar {
  border-radius: 50%;
  overflow: hidden;
  background: var(--n-color);
  flex-shrink: 0;
}

.artist-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: var(--n-text-color-3);
  background: linear-gradient(135deg, var(--n-primary-color), var(--n-primary-color-hover));
}
</style>