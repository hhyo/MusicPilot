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
    description: '本地榜单入口与从榜单项创建订阅，真实榜单源待接入',
    status: '本地入口',
  },
  {
    key: 'search',
    title: '搜索',
    route: '/search',
    description: 'metadata 搜索、搜索任务与从详情创建订阅，当前以 seed/provider 骨架为主',
    status: '可用（seed）',
  },
  {
    key: 'subscriptions',
    title: '订阅',
    route: '/subscriptions',
    description: '四类订阅管理、手动执行记录与音乐 organize 状态',
    status: '可用（手动 run）',
  },
  {
    key: 'downloads',
    title: '下载',
    route: '/downloads',
    description: '候选评分、人工确认与下载派发边界，自动闭环仍待接入',
    status: '待接入',
  },
  {
    key: 'organize',
    title: '整理',
    route: '/organize',
    description: '音乐 preview/apply 已嵌入订阅执行流，独立整理工作台仍待补齐',
    status: '可用（嵌入订阅流）',
  },
  {
    key: 'settings',
    title: '设置',
    route: '/settings',
    description: '插件设置与宿主接入入口占位',
    status: '占位完成',
  },
];
