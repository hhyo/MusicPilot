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
    description: '发现与批量订阅入口占位',
    status: '占位完成',
  },
  {
    key: 'search',
    title: '搜索',
    route: '/search',
    description: 'metadata -> query -> job -> candidate 最小闭环',
    status: 'Phase 3 可联调',
  },
  {
    key: 'subscriptions',
    title: '订阅',
    route: '/subscriptions',
    description: '四类订阅管理入口占位',
    status: '占位完成',
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
    description: '整理日志与结果入口占位',
    status: '占位完成',
  },
  {
    key: 'settings',
    title: '设置',
    route: '/settings',
    description: '插件设置与宿主接入入口占位',
    status: '占位完成',
  },
];
