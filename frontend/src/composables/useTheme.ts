import { ref, watch, onMounted } from 'vue'

export type Theme = 'dark' | 'light' | 'system'

const theme = ref<Theme>('dark')
const isDark = ref(true)

export function useTheme() {
  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme
    applyTheme()
  }

  const toggleTheme = () => {
    theme.value = isDark.value ? 'light' : 'dark'
    applyTheme()
  }

  const applyTheme = () => {
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
    localStorage.setItem('theme', theme.value)
  }

  const initTheme = () => {
    const saved = localStorage.getItem('theme') as Theme
    if (saved) {
      theme.value = saved
    }
    applyTheme()

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (theme.value === 'system') {
        applyTheme()
      }
    })
  }

  onMounted(() => {
    initTheme()
  })

  return {
    theme,
    isDark,
    setTheme,
    toggleTheme,
  }
}
