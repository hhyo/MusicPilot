import { ref } from 'vue'

export type Theme = 'dark' | 'light' | 'system'

const theme = ref<Theme>('dark')
const isDark = ref(true)

const applyTheme = () => {
  // Check if we're in browser environment
  if (typeof window === 'undefined') return
  
  const html = document.documentElement
  
  if (theme.value === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    isDark.value = prefersDark
  } else {
    isDark.value = theme.value === 'dark'
  }

  if (isDark.value) {
    html.classList.add('dark')
    html.classList.remove('light')
  } else {
    html.classList.add('light')
    html.classList.remove('dark')
  }

  // Save to localStorage
  try {
    localStorage.setItem('theme', theme.value)
  } catch (e) {
    // Ignore localStorage errors
  }
}

// Initialize theme - can be called before Vue app mounts
export const initTheme = () => {
  if (typeof window === 'undefined') return
  
  try {
    const saved = localStorage.getItem('theme') as Theme | null
    if (saved) {
      theme.value = saved
    }
  } catch (e) {
    // Ignore localStorage errors
  }
  applyTheme()

  // Listen for system theme changes
  try {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (theme.value === 'system') {
        applyTheme()
      }
    })
  } catch (e) {
    // Ignore matchMedia errors
  }
}

export function useTheme() {
  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme
    applyTheme()
  }

  const toggleTheme = () => {
    const newTheme = isDark.value ? 'light' : 'dark'
    theme.value = newTheme
    applyTheme()
  }

  return {
    theme,
    isDark,
    setTheme,
    toggleTheme,
  }
}
