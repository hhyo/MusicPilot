<template>
  <div class="visualizer-container" ref="containerRef">
    <canvas
      ref="canvasRef"
      :width="width"
      :height="height"
      :class="['visualizer', `effect-${effectType}`]"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

interface Props {
  width?: number
  height?: number
  effectType?: 'bars' | 'wave' | 'circle' | 'dots'
  barCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  width: 300,
  height: 150,
  effectType: 'bars',
  barCount: 64,
})

const containerRef = ref<HTMLDivElement>()
const canvasRef = ref<HTMLCanvasElement>()

let audioContext: AudioContext | null = null
let analyser: AnalyserNode | null = null
let source: MediaElementAudioSourceNode | null = null
let animationId: number | null = null
let dataArray: Uint8Array | null = null

/**
 * 初始化 AudioContext
 */
const initAudioContext = () => {
  if (audioContext) return

  audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
  analyser = audioContext.createAnalyser()
  analyser.fftSize = props.barCount * 2
  dataArray = new Uint8Array(analyser.frequencyBinCount)

  // 获取当前播放的 audio 元素
  const audioElement = document.querySelector('audio')
  if (audioElement) {
    source = audioContext.createMediaElementSource(audioElement)
    source.connect(analyser)
    analyser.connect(audioContext.destination)
  }
}

/**
 * 绘制柱状图效果
 */
const drawBars = (ctx: CanvasRenderingContext2D) => {
  if (!analyser || !dataArray) return

  analyser.getByteFrequencyData(dataArray)

  const barWidth = ctx.canvas.width / dataArray.length
  let x = 0

  dataArray.forEach((value, index) => {
    const barHeight = (value / 255) * ctx.canvas.height

    // 创建渐变色
    const gradient = ctx.createLinearGradient(0, ctx.canvas.height, 0, 0)
    gradient.addColorStop(0, '#18a058')
    gradient.addColorStop(0.5, '#2080f0')
    gradient.addColorStop(1, '#f0a020')

    ctx.fillStyle = gradient
    ctx.fillRect(x, ctx.canvas.height - barHeight, barWidth - 1, barHeight)

    x += barWidth
  })
}

/**
 * 绘制波形效果
 */
const drawWave = (ctx: CanvasRenderingContext2D) => {
  if (!analyser || !dataArray) return

  analyser.getByteTimeDomainData(dataArray)

  ctx.lineWidth = 2
  ctx.strokeStyle = '#2080f0'
  ctx.beginPath()

  const sliceWidth = ctx.canvas.width / dataArray.length
  let x = 0

  dataArray.forEach((value) => {
    const y = (value / 255.0) * ctx.canvas.height

    if (x === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }

    x += sliceWidth
  })

  ctx.lineTo(ctx.canvas.width, ctx.canvas.height / 2)
  ctx.stroke()
}

/**
 * 绘制圆形效果
 */
const drawCircle = (ctx: CanvasRenderingContext2D) => {
  if (!analyser || !dataArray) return

  analyser.getByteFrequencyData(dataArray)

  const centerX = ctx.canvas.width / 2
  const centerY = ctx.canvas.height / 2
  const radius = Math.min(centerX, centerY) - 10

  dataArray.forEach((value, index) => {
    const angle = (index / dataArray.length) * Math.PI * 2
    const barHeight = (value / 255) * 50

    const x1 = centerX + Math.cos(angle) * radius
    const y1 = centerY + Math.sin(angle) * radius
    const x2 = centerX + Math.cos(angle) * (radius + barHeight)
    const y2 = centerY + Math.sin(angle) * (radius + barHeight)

    // 彩虹色
    const hue = (index / dataArray.length) * 360
    ctx.strokeStyle = `hsl(${hue}, 70%, 50%)`
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(x1, y1)
    ctx.lineTo(x2, y2)
    ctx.stroke()
  })
}

/**
 * 绘制点阵效果
 */
const drawDots = (ctx: CanvasRenderingContext2D) => {
  if (!analyser || !dataArray) return

  analyser.getByteFrequencyData(dataArray)

  const cols = Math.floor(Math.sqrt(dataArray.length))
  const rows = Math.ceil(dataArray.length / cols)
  const dotWidth = ctx.canvas.width / cols
  const dotHeight = ctx.canvas.height / rows

  dataArray.forEach((value, index) => {
    const x = (index % cols) * dotWidth + dotWidth / 2
    const y = Math.floor(index / cols) * dotHeight + dotHeight / 2
    const radius = (value / 255) * (Math.min(dotWidth, dotHeight) / 2 - 2)

    ctx.beginPath()
    ctx.arc(x, y, Math.max(0, radius), 0, Math.PI * 2)
    ctx.fillStyle = `hsl(${(value / 255) * 240}, 70%, 50%)`
    ctx.fill()
  })
}

/**
 * 渲染循环
 */
const render = () => {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  // 清空画布
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  // 绘制效果
  switch (props.effectType) {
    case 'wave':
      drawWave(ctx)
      break
    case 'circle':
      drawCircle(ctx)
      break
    case 'dots':
      drawDots(ctx)
      break
    case 'bars':
    default:
      drawBars(ctx)
      break
  }

  animationId = requestAnimationFrame(render)
}

/**
 * 启动可视化
 */
const start = () => {
  initAudioContext()
  render()
}

/**
 * 停止可视化
 */
const stop = () => {
  if (animationId) {
    cancelAnimationFrame(animationId)
    animationId = null
  }
}

/**
 * 切换效果类型
 */
const switchEffect = (type: 'bars' | 'wave' | 'circle' | 'dots') => {
  stop()
  start()
}

// 监听 effectType 变化
watch(() => props.effectType, () => {
  stop()
  start()
})

// 挂载时启动
onMounted(() => {
  // 延迟初始化，等待 audio 元素
  setTimeout(() => {
    start()
  }, 100)
})

// 卸载时清理
onUnmounted(() => {
  stop()

  if (source) {
    source.disconnect()
    source = null
  }

  if (analyser) {
    analyser.disconnect()
    analyser = null
  }

  if (audioContext) {
    audioContext.close()
    audioContext = null
  }
})

defineExpose({
  start,
  stop,
  switchEffect,
})
</script>

<style scoped>
.visualizer-container {
  display: flex;
  align-items: center;
  justify-content: center;
}

.visualizer {
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.8) 0%, rgba(24, 24, 27, 0.8) 100%);
  border-radius: 8px;
}

/* 效果切换动画 */
.visualizer {
  transition: opacity 0.3s ease;
}
</style>