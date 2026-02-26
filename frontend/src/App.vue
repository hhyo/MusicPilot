<template>
  <n-config-provider :theme="theme">
    <n-layout class="layout">
      <LayoutHeader />
      <n-layout has-sider class="content-layout">
        <LayoutSidebar />
        <n-layout-content>
          <router-view />
        </n-layout-content>
      </n-layout>
      <PlayerBar />
      <LayoutFooter />
    </n-layout>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { darkTheme, NConfigProvider, NLayout, NLayoutContent } from 'naive-ui'
import LayoutHeader from '@/components/common/LayoutHeader.vue'
import LayoutSidebar from '@/components/common/LayoutSidebar.vue'
import LayoutFooter from '@/components/common/LayoutFooter.vue'
import PlayerBar from '@/components/player/PlayerBar.vue'

const theme = computed(() => darkTheme)
</script>

<style scoped>
.layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.content-layout {
  flex: 1;
  overflow: hidden;
}

.n-layout-content {
  padding: 20px;
  overflow-y: auto;
}
</style>