/**
 * 全局主题样式定义
 * 用于统一管理应用的主题样式，提高代码复用性
 */

export const theme = {
  // 背景样式
  backgrounds: {
    main: 'bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700', // 主背景渐变
    header: 'bg-white/10 backdrop-blur-sm shadow-sm', // 半透明头部
    footer: 'bg-white/10 backdrop-blur-sm shadow-sm', // 半透明底部
    card: 'bg-white/90 backdrop-blur-sm shadow-lg ring-1 ring-white/20', // 卡片背景
  },
  
  // 文本样式
  text: {
    title: 'text-2xl font-bold tracking-tight text-white', // 主标题
    subtitle: 'text-xl font-semibold tracking-tight text-neutral-900', // 副标题
    body: 'text-neutral-800', // 正文
    light: 'text-white/80', // 浅色文本
    nav: 'text-white', // 导航文本
  },
  
  // 按钮样式
  buttons: {
    primary: 'px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors', // 主按钮
    secondary: 'px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors', // 次要按钮
    nav: 'px-3 py-2 rounded-lg hover:bg-white/20 transition-colors', // 导航按钮
    tag: 'px-2 py-1 text-xs rounded-full border border-indigo-200 bg-indigo-50 text-indigo-800 hover:bg-indigo-100 transition-colors', // 标签按钮
    icon: 'p-1 rounded-full hover:bg-indigo-100 transition-colors', // 图标按钮
    stat: 'px-2 py-1 rounded-lg hover:bg-indigo-100 transition-colors text-neutral-600', // 统计按钮
  },
  
  // 卡片样式
  cards: {
    container: 'rounded-2xl p-6 h-full', // 卡片容器
    spacing: 'space-y-4', // 卡片内部间距
    hover: 'hover:ring-2 hover:ring-indigo-300 transition-all duration-300', // 卡片悬停效果
  },
  
  // 布局样式
  layout: {
    container: 'container mx-auto px-4', // 内容容器
    section: 'py-8', // 区块间距
    grid: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6', // 网格布局
  },
};

// 导出组合样式函数
export const combineStyles = (...styles) => {
  return styles.join(' ');
};

// 预定义的组合样式
export const combinedStyles = {
  // 卡片组合样式
  card: combineStyles(theme.backgrounds.card, theme.cards.container),
  
  // 标题组合样式
  pageTitle: combineStyles(theme.text.title, 'mb-6'),
  
  // 导航链接组合样式
  navLink: (isActive) => combineStyles(
    theme.text.nav, 
    theme.buttons.nav, 
    'flex items-center text-sm font-medium',
    isActive ? 'bg-white/10' : ''
  ),
};