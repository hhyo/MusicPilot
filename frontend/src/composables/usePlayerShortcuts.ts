/**
 * 播放器快捷键
 * 支持空格播放/暂停、方向键控制、音量快捷键
 */
import { usePlayerStore } from '@/store/player'
import { onMounted, onUnmounted } from 'vue'

export function usePlayerShortcuts() {
  const player = usePlayerStore()

  // 键盘事件处理器
  const handleKeydown = (event: KeyboardEvent) => {
    // 忽略在输入框中的按键
    if (
      event.target instanceof HTMLInputElement ||
      event.target instanceof HTMLTextAreaElement ||
      event.target.isContentEditable
    ) {
      return
    }

    switch (event.key) {
      case ' ':
      case 'Space':
        // 空格键：播放/暂停
        event.preventDefault()
        if (player.hasTrack) {
          player.togglePlay()
        }
        break

      case 'ArrowLeft':
        // 左箭头：快退 10 秒
        event.preventDefault()
        if (player.hasTrack) {
          const newPosition = Math.max(0, player.progress - 10)
          player.seek(newPosition)
        }
        break

      case 'ArrowRight':
        // 右箭头：快进 10 秒
        event.preventDefault()
        if (player.hasTrack) {
          const newPosition = Math.min(player.duration, player.progress + 10)
          player.seek(newPosition)
        }
        break

      case 'ArrowUp':
        // 上箭头：增加音量
        event.preventDefault()
        const newVolumeUp = Math.min(1, player.volume + 0.1)
        player.setVolume(newVolumeUp)
        break

      case 'ArrowDown':
        // 下箭头：减小音量
        event.preventDefault()
        const newVolumeDown = Math.max(0, player.volume - 0.1)
        player.setVolume(newVolumeDown)
        break

      case 'm':
      case 'M':
        // M 键：静音切换
        event.preventDefault()
        player.toggleMute()
        break

      case 'n':
      case 'N':
        // N 键：下一首
        event.preventDefault()
        player.next()
        break

      case 'p':
      case 'P':
        // P 键：上一首
        event.preventDefault()
        player.previous()
        break

      case 's':
      case 'S':
        // S 键：随机播放切换
        event.preventDefault()
        player.toggleShuffle()
        break

      case 'r':
      case 'R':
        // R 键：循环模式切换
        event.preventDefault()
        const modes: ('off' | 'one' | 'all')[] = ['off', 'all', 'one']
        const currentIndex = modes.indexOf(player.repeatMode)
        const nextIndex = (currentIndex + 1) % modes.length
        player.setRepeatMode(modes[nextIndex])
        break

      case '0':
      case '1':
      case '2':
      case '3':
      case '4':
      case '5':
      case '6':
      case '7':
      case '8':
      case '9':
        // 数字键 0-9：跳转到对应百分比位置
        event.preventDefault()
        if (player.hasTrack && player.duration > 0) {
          const percent = parseInt(event.key) / 10
          const position = player.duration * percent
          player.seek(position)
        }
        break
    }
  }

  // 挂载时注册键盘事件
  onMounted(() => {
    document.addEventListener('keydown', handleKeydown)
  })

  // 卸载时移除键盘事件
  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeydown)
  })

  return {
    // 快捷键提示
    shortcuts: [
      { key: 'Space', description: '播放/暂停' },
      { key: '←', description: '快退 10 秒' },
      { key: '→', description: '快进 10 秒' },
      { key: '↑', description: '增加音量' },
      { key: '↓', description: '减小音量' },
      { key: 'M', description: '静音切换' },
      { key: 'N', description: '下一首' },
      { key: 'P', description: '上一首' },
      { key: 'S', description: '随机播放' },
      { key: 'R', description: '循环模式' },
      { key: '0-9', description: '跳转到进度百分比' },
    ],
  }
}