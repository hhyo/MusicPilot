<template>
  <div
    :class="[
      'glass rounded-2xl transition-all duration-300',
      hoverable && 'glass-hover cursor-pointer hover:scale-[1.02] hover:shadow-xl',
      padding && 'p-6',
      className
    ]"
    @click="$emit('click')"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
interface Props {
  hoverable?: boolean
  padding?: boolean
  className?: string
}

withDefaults(defineProps<Props>(), {
  hoverable: false,
  padding: true,
  className: ''
})

defineEmits<{
  click: []
}>()
</script>
