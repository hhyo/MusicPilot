<template>
  <button
    :class="buttonClasses"
    :disabled="disabled"
    @click="$emit('click')"
  >
    <span v-if="loading" class="mr-2">
      <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
          fill="none"
        />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </span>
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  block?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  disabled: false,
  loading: false,
  block: false
})

defineEmits<{
  click: []
}>()

const buttonClasses = computed(() => {
  const base = 'inline-flex items-center justify-center font-medium transition-all duration-200 rounded-full'
  
  const variants = {
    primary: 'bg-accent hover:bg-accent-hover text-white hover:shadow-lg hover:shadow-accent/25',
    secondary: 'glass glass-hover text-white',
    ghost: 'text-white/70 hover:text-white hover:bg-white/10'
  }
  
  const sizes = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg'
  }
  
  const states = [
    (props.disabled || props.loading) && 'opacity-50 cursor-not-allowed',
    props.block && 'w-full'
  ]
  
  return [
    base,
    variants[props.variant],
    sizes[props.size],
    ...states
  ].filter(Boolean).join(' ')
})
</script>
