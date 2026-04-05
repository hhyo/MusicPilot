import { computed, ref } from 'vue';
import { defineStore } from 'pinia';

import { navigationModules } from '@/types/module';

export const useAppStore = defineStore('app', () => {
  const appName = ref('MusicPilot');
  const phaseLabel = ref('Current');

  const modules = computed(() => navigationModules);

  return {
    appName,
    phaseLabel,
    modules,
  };
});
