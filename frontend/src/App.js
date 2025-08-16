import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { HomeOutlined, UserOutlined, BarChartOutlined } from '@ant-design/icons';
import { theme, combinedStyles } from './styles/theme';

// 页面组件
import HomePage from './pages/HomePage';
import PostDetailPage from './pages/PostDetailPage';
import UserProfilePage from './pages/UserProfilePage';
import DashboardPage from './pages/DashboardPage';

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
              to="/user/u1001" 
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
  );
};

export default App;