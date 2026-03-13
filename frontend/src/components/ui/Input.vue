<template>
  <div class="w-full">
    <label v-if="label" class="block text-sm font-medium text-white/70 mb-2">
      {{ label }}
    </label>
    <div class="relative">
      <input
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        class="w-full input-glass"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        @keyup.enter="$emit('enter')"
      />
      <div v-if="$slots.suffix" class="absolute right-3 top-1/2 -translate-y-1/2">
        <slot name="suffix" />
      </div>
    </div>
    <p v-if="error" class="mt-1 text-sm text-red-400">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  modelValue: string
  type?: string
  label?: string
  placeholder?: string
  disabled?: boolean
  error?: string
}

withDefaults(defineProps<Props>(), {
  type: 'text',
  label: '',
  placeholder: '',
  disabled: false,
  error: ''
})

defineEmits<{
  'update:modelValue': [value: string]
  enter: []
}>()
</script>
