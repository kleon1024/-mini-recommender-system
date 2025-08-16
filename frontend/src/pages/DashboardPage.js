import React, { useState, useEffect } from 'react';
import { UserOutlined, FileOutlined, EyeOutlined, LikeOutlined, StarOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const DashboardPage = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);
  
  // 获取统计数据
  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        // 在实际项目中，这里应该调用后端API获取数据
        // const response = await axios.get(`${API_URL}/api/stats`);
        // setStats(response.data);
        
        // 模拟数据
        setTimeout(() => {
          setStats({
            userCount: 5,
            postCount: 10,
            eventCount: 15,
            viewCount: 120,
            likeCount: 45,
            favoriteCount: 25,
            eventsByType: [
              { value: 60, name: '浏览' },
              { value: 20, name: '点击' },
              { value: 15, name: '点赞' },
              { value: 10, name: '收藏' },
              { value: 5, name: '停留' }
            ],
            topPosts: [
              { name: '人工智能入门指南', value: 120 },
              { name: '东京旅游攻略', value: 80 },
              { name: '家庭健身计划', value: 60 },
              { name: '2023年最值得期待的电影', value: 40 },
              { name: '最新游戏评测', value: 30 }
            ],
            userActivity: [
              { date: '2023-01', count: 10 },
              { date: '2023-02', count: 15 },
              { date: '2023-03', count: 20 },
              { date: '2023-04', count: 25 },
              { date: '2023-05', count: 30 },
              { date: '2023-06', count: 35 }
            ]
          });
          setLoading(false);
        }, 1000);
      } catch (err) {
        setError(err.message || '获取统计数据失败');
        setLoading(false);
      }
    };
    
    fetchStats();
  }, []);
  
  // 事件类型分布图表配置
  const getEventTypeOption = () => ({
    title: {
      text: '事件类型分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b} : {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      data: stats?.eventsByType.map(item => item.name) || []
    },
    series: [
      {
        name: '事件类型',
        type: 'pie',
        radius: '55%',
        center: ['50%', '60%'],
        data: stats?.eventsByType || [],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  });
  
  // 热门内容图表配置
  const getTopPostsOption = () => ({
    title: {
      text: '热门内容排行',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      boundaryGap: [0, 0.01]
    },
    yAxis: {
      type: 'category',
      data: stats?.topPosts.map(item => item.name) || []
    },
    series: [
      {
        name: '浏览量',
        type: 'bar',
        data: stats?.topPosts.map(item => item.value) || []
      }
    ]
  });
  
  // 用户活跃度趋势图表配置
  const getUserActivityOption = () => ({
    title: {
      text: '用户活跃度趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: stats?.userActivity.map(item => item.date) || []
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        data: stats?.userActivity.map(item => item.count) || [],
        type: 'line',
        smooth: true
      }
    ]
  });
  
  // 如果加载失败，显示错误信息
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">错误！</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      </div>
    );
  }
  
  // 加载中显示加载状态
  if (loading) {
    return <div className="flex items-center justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"></div></div>;
  }
  
  return (
    <div className="p-6">
      <div className="mx-auto max-w-3xl rounded-2xl bg-white/90 backdrop-blur-sm shadow-lg ring-1 ring-white/20 p-8">
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-900">数据看板</h1>
          <p className="mt-2 text-sm text-neutral-600">系统运行数据统计与分析</p>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
          <div className="rounded-xl bg-white/80 backdrop-blur-sm shadow-sm ring-1 ring-black/5 p-4 dark:bg-neutral-800/80 dark:ring-white/10">
            <div className="flex items-center">
              <UserOutlined className="text-blue-600 mr-2" />
              <div>
                <div className="text-sm text-neutral-600 dark:text-neutral-400">用户总数</div>
                <div className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">{stats.userCount}</div>
              </div>
            </div>
          </div>
          
          <div className="rounded-xl bg-white/80 backdrop-blur-sm shadow-sm ring-1 ring-black/5 p-4 dark:bg-neutral-800/80 dark:ring-white/10">
            <div className="flex items-center">
              <FileOutlined className="text-blue-600 mr-2" />
              <div>
                <div className="text-sm text-neutral-600 dark:text-neutral-400">内容总数</div>
                <div className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">{stats.postCount}</div>
              </div>
            </div>
          </div>
          
          <div className="rounded-xl bg-white/80 backdrop-blur-sm shadow-sm ring-1 ring-black/5 p-4 dark:bg-neutral-800/80 dark:ring-white/10">
            <div className="flex items-center">
              <EyeOutlined className="text-indigo-500 mr-2" />
              <div>
                <div className="text-sm text-neutral-600 dark:text-neutral-400">浏览总数</div>
                <div className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">{stats.viewCount}</div>
              </div>
            </div>
          </div>
          
          <div className="rounded-xl bg-white/80 backdrop-blur-sm shadow-sm ring-1 ring-black/5 p-4 dark:bg-neutral-800/80 dark:ring-white/10">
            <div className="flex items-center">
              <LikeOutlined className="text-indigo-500 mr-2" />
              <div>
                <div className="text-sm text-neutral-600 dark:text-neutral-400">互动总数</div>
                <div className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">{stats.likeCount + stats.favoriteCount}</div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
          <div className="rounded-xl bg-white/80 backdrop-blur-sm shadow-sm ring-1 ring-black/5 p-4 dark:bg-neutral-800/80 dark:ring-white/10">
            <ReactECharts
              option={getEventTypeOption()}
              style={{ height: '300px' }}
            />
          </div>
          
          <div className="rounded-xl bg-white/80 backdrop-blur-sm shadow-sm ring-1 ring-black/5 p-4 dark:bg-neutral-800/80 dark:ring-white/10">
            <ReactECharts
              option={getTopPostsOption()}
              style={{ height: '300px' }}
            />
          </div>
          
          <div className="rounded-xl bg-white/80 backdrop-blur-sm shadow-sm ring-1 ring-black/5 p-4 dark:bg-neutral-800/80 dark:ring-white/10">
            <ReactECharts
              option={getUserActivityOption()}
              style={{ height: '300px' }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;