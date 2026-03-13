# MusicPilot Design System

## 色彩系统

### 深色主题 (默认)
- Primary Background: #0f0f0f
- Secondary Background: #1a1a1a
- Card Background: #252525
- Glass Background: rgba(255,255,255,0.05)
- Accent: #1db954 (音乐绿)
- Accent Hover: #1ed760
- Text Primary: #ffffff
- Text Secondary: #b3b3b3
- Border: rgba(255,255,255,0.1)

### 浅色主题
- Primary Background: #ffffff
- Secondary Background: #f5f5f5
- Card Background: #ffffff
- Accent: #1db954
- Text Primary: #191414
- Text Secondary: #6a6a6a

## 玻璃拟态
```css
.glass {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

## 动画
- Transition: 200ms ease
- Page Transition: 300ms ease-out
- Micro-interaction: 150ms ease-in-out

## 响应式断点
- sm: 640px
- md: 768px
- lg: 1024px
- xl: 1280px
- 2xl: 1536px

## 组件规范

### 按钮
- Primary: bg-accent, rounded-full, px-6 py-3
- Secondary: glass effect, rounded-full
- Ghost: transparent, hover:bg-white/10

### 卡片
- Background: bg-card or glass
- Border Radius: rounded-2xl (16px)
- Padding: p-6
- Shadow: shadow-lg on hover

### 输入框
- Background: bg-white/5
- Border: border border-white/10
- Border Radius: rounded-xl
- Focus: ring-2 ring-accent
