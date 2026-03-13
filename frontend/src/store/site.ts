import { defineStore } from 'pinia'
import { ref } from 'vue'
import { siteApi, type Site, type SiteCreate, type SiteUpdate } from '@/api/site'
import { useMessage } from 'naive-ui'

export const useSiteStore = defineStore('site', () => {
  const message = useMessage()
  const sites = ref<Site[]>([])
  const loading = ref(false)
  const total = ref(0)

  /**
   * 获取站点列表
   */
  const fetchSites = async (params?: {
    skip?: number
    limit?: number
    enabled?: boolean
    downloader?: string
  }) => {
    loading.value = true
    try {
      const response = await siteApi.getSites(params)
      sites.value = response.items
      total.value = response.total
    } catch (error) {
      message.error('获取站点列表失败')
      console.error(error)
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建站点
   */
  const createSite = async (data: SiteCreate) => {
    loading.value = true
    try {
      await siteApi.createSite(data)
      message.success('站点创建成功')
      await fetchSites()
    } catch (error) {
      message.error('站点创建失败')
      console.error(error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新站点
   */
  const updateSite = async (id: number, data: SiteUpdate) => {
    loading.value = true
    try {
      await siteApi.updateSite(id, data)
      message.success('站点更新成功')
      await fetchSites()
    } catch (error) {
      message.error('站点更新失败')
      console.error(error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除站点
   */
  const deleteSite = async (id: number) => {
    loading.value = true
    try {
      await siteApi.deleteSite(id)
      message.success('站点删除成功')
      await fetchSites()
    } catch (error) {
      message.error('站点删除失败')
      console.error(error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 切换站点启用状态
   */
  const toggleSite = async (id: number) => {
    try {
      const updatedSite = await siteApi.toggleSite(id)
      const index = sites.value.findIndex(s => s.id === id)
      if (index !== -1) {
        sites.value[index] = updatedSite
      }
      message.success(`站点已${updatedSite.enabled ? '启用' : '禁用'}`)
    } catch (error) {
      message.error('切换站点状态失败')
      console.error(error)
      throw error
    }
  }

  /**
   * 测试站点连接
   */
  const testSite = async (id: number) => {
    try {
      const response = await siteApi.testSite({ id })
      if (response.success) {
        message.success(`站点连接成功: ${response.message}`)
      } else {
        message.error(`站点连接失败: ${response.message}`)
      }
      return response
    } catch (error) {
      message.error('测试站点连接失败')
      console.error(error)
      throw error
    }
  }

  return {
    sites,
    loading,
    total,
    fetchSites,
    createSite,
    updateSite,
    deleteSite,
    toggleSite,
    testSite
  }
})