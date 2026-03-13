<template>
  <n-layout-footer class="footer">
    <span class="copyright">© {{ year }} MusicPilot</span>
  </n-layout-footer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NLayoutFooter } from 'naive-ui'

const year = computed(() => new Date().getFullYear())
</script>

<style scoped>
.footer {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-top: 1px solid var(--n-border-color);
}

.copyright {
  font-size: 12px;
  color: var(--n-text-color-2);
}
</style>