import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// Tailwind CSS
import './styles/tailwind.css'

// Initialize theme before creating app
import { initTheme } from './composables/useTheme'
initTheme()

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')