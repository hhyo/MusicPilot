export interface NavigationModule {
  key: string;
  title: string;
  route: string;
  description: string;
  status: string;
  icon: string;
}

export const navigationModules: NavigationModule[] = [
  {
    key: 'home',
    title: '首页',
    route: '/',
    description: '音乐工作台与快捷入口',
    status: '可用',
    icon: 'mdi-view-dashboard-outline',
  },
  {
    key: 'charts',
    title: '榜单',
    route: '/charts',
    description: '发现入口、识别状态和从榜单项创建订阅',
    status: '可用',
    icon: 'mdi-chart-line',
  },
  {
    key: 'search',
    title: '搜索',
    route: '/search',
    description: '元数据搜索、媒体识别结果与获取入口',
    status: '可用',
    icon: 'mdi-magnify',
  },
  {
    key: 'subscriptions',
    title: '订阅',
    route: '/subscriptions',
    description: '订阅、执行记录与主链运行状态',
    status: '可用',
    icon: 'mdi-rss',
  },
  {
    key: 'downloads',
    title: '下载',
    route: '/downloads',
    description: '候选评分、人工确认与下载派发边界，自动闭环仍待接入',
    status: '待接入',
    icon: 'mdi-download-outline',
  },
  {
    key: 'organize',
    title: '整理',
    route: '/organize',
    description: '音乐 preview/apply 已嵌入订阅执行流，独立整理工作台仍待补齐',
    status: '可用（嵌入订阅流）',
    icon: 'mdi-folder-music-outline',
  },
  {
    key: 'settings',
    title: '设置',
    route: '/settings',
    description: 'chart provider mode 与 RSS feed 配置',
    status: '可用（providers）',
    icon: 'mdi-cog-outline',
  },
];
