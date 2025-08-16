import React, { useState, useEffect, Component } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { HomeOutlined, UserOutlined, BarChartOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { theme, combinedStyles } from './styles/theme';
import HomePage from './pages/HomePage';
import PostDetailPage from './pages/PostDetailPage';
import UserProfilePage from './pages/UserProfilePage';
import DashboardPage from './pages/DashboardPage';


// 错误边界组件
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('组件渲染错误:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // 自定义错误显示
      return (
        <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-200 dark:from-neutral-900 dark:to-neutral-800 flex items-center justify-center">
          <div className="mx-auto max-w-md rounded-2xl bg-white/80 backdrop-blur-sm shadow-lg ring-1 ring-black/5 p-8 dark:bg-neutral-900/80 dark:ring-white/10 text-center">
            <ExclamationCircleOutlined className="text-red-500 text-2xl mb-2" />
            <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100">页面渲染错误</h3>
            <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">抱歉，页面渲染出现问题</p>
            <button 
              className="mt-4 px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors"
              onClick={() => window.location.reload()}
            >
              刷新页面
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// 保持HomePage组件状态的包装组件
const KeepAliveHomePage = () => {
  const [homePageInstance, setHomePageInstance] = useState(null);
  
  useEffect(() => {
    // 只在首次渲染时创建HomePage实例
    if (!homePageInstance) {
      setHomePageInstance(<HomePage />);
    }
  }, [homePageInstance]);
  
  return homePageInstance || <div>Loading...</div>;
};



const App = () => {
  const location = useLocation();
  
  // 确定当前选中的菜单项
  const getSelectedKey = () => {
    const path = location.pathname;
    if (path.startsWith('/post/')) return '1';
    if (path.startsWith('/user/')) return '2';
    if (path.startsWith('/dashboard')) return '3';
    return '1'; // 默认选中首页
  };

  return (
    <ErrorBoundary>
      <div className={`min-h-screen flex flex-col ${theme.backgrounds.main}`}>
        <header className={`${theme.backgrounds.header} sticky top-0 z-10`}>
          <div className="container mx-auto px-4 py-3 flex items-center justify-between">
            <div className={`${theme.text.title}`}>迷你推荐</div>
            <nav className="flex space-x-6">
              <Link 
                to="/" 
                className={getSelectedKey() === '1' ? combinedStyles.navLink(true) : combinedStyles.navLink(false)}
              >
                <HomeOutlined className="mr-1" />
              首页
            </Link>
            <Link 
              to="/user/1001" 
              className={getSelectedKey() === '2' ? combinedStyles.navLink(true) : combinedStyles.navLink(false)}
            >
              <UserOutlined className="mr-1" />
              用户中心
            </Link>
            <Link 
              to="/dashboard" 
              className={getSelectedKey() === '3' ? combinedStyles.navLink(true) : combinedStyles.navLink(false)}
            >
              <BarChartOutlined className="mr-1" />
              数据看板
            </Link>
          </nav>
        </div>
      </header>
      <main className={`${theme.layout.container} py-6 flex-grow`}>
        <Routes>
          <Route path="/" element={<KeepAliveHomePage />} />
          <Route path="/post/:postId" element={<PostDetailPage />} />
          <Route path="/user/:userId" element={<UserProfilePage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Routes>
      </main>
      <footer className="py-4 mt-auto text-center text-sm bg-white">
        迷你推荐系统 ©{new Date().getFullYear()} Created by AI Engineer
      </footer>
    </div>
    </ErrorBoundary>
  );
};

export default App;