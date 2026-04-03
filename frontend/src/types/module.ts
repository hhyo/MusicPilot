export interface NavigationModule {
  key: string;
  title: string;
  route: string;
  description: string;
  status: string;
}

export const navigationModules: NavigationModule[] = [
  {
    key: 'home',
    title: '首页',
    route: '/',
    description: '音乐工作台与快捷入口',
    status: '可用',
  },
  {
    key: 'charts',
    title: '榜单',
    route: '/charts',
    description: 'mock 榜单发现与从榜单项创建订阅',
    status: 'Phase 6 可联调',
  },
  {
    key: 'search',
    title: '搜索',
    route: '/search',
    description: 'metadata 搜索、搜索任务与从详情创建订阅',
    status: 'Phase 6 可联调',
  },
  {
    key: 'subscriptions',
    title: '订阅',
    route: '/subscriptions',
    description: '四类订阅管理、执行记录与 organize 状态',
    status: 'Phase 6 可联调',
  },
  {
    key: 'downloads',
    title: '下载',
    route: '/downloads',
    description: '候选评分、人工确认与 mock dispatch 边界',
    status: 'Phase 3 骨架',
  },
  {
    key: 'organize',
    title: '整理',
    route: '/organize',
    description: 'host-aware organize preview / apply 与状态记录边界',
    status: 'Phase 6 骨架',
  },
  {
    key: 'settings',
    title: '设置',
    route: '/settings',
    description: '插件设置与宿主接入入口占位',
    status: '占位完成',
  },
];
