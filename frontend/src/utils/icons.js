/**
 * 语义图标名 → Heroicons 标识符映射表
 *
 * 通过 unplugin-icons 在构建时内联为 SVG，零运行时成本。
 * 在组件中使用：<AppIcon name="like" :size="16" />
 */

export const iconMap = {
  // === 侧边栏导航 ===
  discuss:    'heroicons-outline:chat-bubble-left-right',
  stock:      'heroicons-outline:chart-bar',
  fund:       'heroicons-outline:banknotes',
  question:   'heroicons-outline:question-mark-circle',
  strategy:   'heroicons-outline:light-bulb',
  trending:   'heroicons-outline:fire',
  search:     'heroicons-outline:magnifying-glass',
  feed:       'heroicons-outline:newspaper',
  collections:'heroicons-outline:star',
  followers:  'heroicons-outline:user-group',
  groups:     'heroicons-outline:building-storefront',

  // === 操作按钮 ===
  like:       'heroicons-outline:hand-thumb-up',
  likeSolid:  'heroicons-solid:hand-thumb-up',
  comment:    'heroicons-outline:chat-bubble-left',
  collect:    'heroicons-outline:bookmark',
  collectSolid:'heroicons-solid:bookmark',
  share:      'heroicons-outline:arrow-up-tray',
  reply:      'heroicons-outline:arrow-uturn-left',
  edit:       'heroicons-outline:pencil',
  delete:     'heroicons-outline:trash',
  close:      'heroicons-outline:x-mark',
  add:        'heroicons-outline:plus',
  ellipsis:   'heroicons-outline:ellipsis-horizontal',

  // === 编辑器工具栏 ===
  'list-bullet':  'heroicons-outline:list-bullet',
  'list-ordered': 'heroicons-outline:queue-list',

  // === 状态/反馈 ===
  empty:      'heroicons-outline:inbox',
  error:      'heroicons-outline:exclamation-triangle',
  notFound:   'heroicons-outline:magnifying-glass',
  chart:      'heroicons-outline:presentation-chart-line',
  success:    'heroicons-outline:check-circle',
  info:       'heroicons-outline:information-circle',

  // === 功能 ===
  bell:       'heroicons-outline:bell',
  attachment:'heroicons-outline:paper-clip',
  image:      'heroicons-outline:photo',
  link:       'heroicons-outline:link',
  message:    'heroicons-outline:envelope',
  badge:      'heroicons-outline:shield-check',
  user:       'heroicons-outline:user',
  home:       'heroicons-outline:home',
  settings:   'heroicons-outline:cog-6-tooth',
  logout:     'heroicons-outline:arrow-right-on-rectangle',
  download:   'heroicons-outline:arrow-down-tray',
  upload:     'heroicons-outline:arrow-up-tray',
  filter:     'heroicons-outline:funnel',
  arrowUp:    'heroicons-outline:arrow-trending-up',
  arrowDown:  'heroicons-outline:arrow-trending-down',
  external:   'heroicons-outline:arrow-top-right-on-square',
  flag:       'heroicons-outline:flag',

  // === 第三方登录品牌 ===
  qq:         'fa-brands:qq',
  wechat:     'fa-brands:weixin',
  weibo:      'fa-brands:weibo',
}
