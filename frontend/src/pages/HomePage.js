import React, { useEffect, useState, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { EyeOutlined, UserOutlined, LikeOutlined, StarOutlined, ExclamationCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { fetchRecommendations, resetRecommendations, updateItems } from '../store/recommendationsSlice';
import { likePost, unlikePost, checkUserLike } from '../store/likesSlice';
import { favoritePost, unfavoritePost, checkUserFavorite } from '../store/favoritesSlice';
import { getTracker } from '../utils/tracker';
import { theme, combinedStyles } from '../styles/theme';

// 创建一个简单的消息提示函数
const showMessage = (content, type = 'info') => {
  // 创建消息元素
  const messageEl = document.createElement('div');
  messageEl.className = `fixed top-4 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-lg shadow-md z-50 ${type === 'info' ? 'bg-blue-500' : type === 'error' ? 'bg-red-500' : 'bg-green-500'} text-white`;
  messageEl.textContent = content;
  
  // 添加到页面
  document.body.appendChild(messageEl);
  
  // 2秒后移除
  setTimeout(() => {
    messageEl.classList.add('opacity-0', 'transition-opacity', 'duration-300');
    setTimeout(() => document.body.removeChild(messageEl), 300);
  }, 2000);
};

// 创建消息API
const message = {
  info: (content) => showMessage(content, 'info'),
  success: (content) => showMessage(content, 'success'),
  error: (content) => showMessage(content, 'error'),
  warning: (content) => showMessage(content, 'warning')
};

const HomePage = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [likedPosts, setLikedPosts] = useState({});
  const [collectedPosts, setCollectedPosts] = useState({});
  
  // 初始化埋点SDK
  const userId = 'u1001';
  const tracker = getTracker(userId);
  
  // 从Redux store获取推荐数据
  const { items, hasMore, status, error } = useSelector(state => state.recommendations);
  
  // 组件挂载时获取推荐内容
  useEffect(() => {
    // 请求新数据
    dispatch(resetRecommendations());
    dispatch(fetchRecommendations({ userId: 'u1001', page: 1, pageSize: 10 }))
      .unwrap()
      .then(response => {
        // 获取推荐列表后，检查每个帖子的点赞和收藏状态
        if (response && response.items) {
          const likedPostsData = {};
          const collectedPostsData = {};
          
          response.items.forEach(post => {
            // 检查点赞状态
            if (post.is_liked) {
              likedPostsData[post.post_id] = true;
            }
            
            // 检查收藏状态
            if (post.is_favorited) {
              collectedPostsData[post.post_id] = true;
            }
          });
          
          setLikedPosts(likedPostsData);
          setCollectedPosts(collectedPostsData);
        }
      })
      .catch(error => {
        showMessage('获取推荐内容失败: ' + (error.message || '未知错误'), 'error');
      });
    
    return () => {
      // 组件卸载时销毁观察器
      tracker.destroyViewObserver();
    };
  }, [dispatch]);
  
  // 数据加载后初始化曝光观察器
  useEffect(() => {
    if (items.length > 0 && status === 'succeeded') {
      // 等待DOM更新后初始化观察器
      setTimeout(() => {
        tracker.initViewObserver('.post-card', 'home');
      }, 100);
    }
  }, [items, status, tracker]);
  
  // 处理刷新
  const handleRefresh = () => {
    // 重置状态
    dispatch(resetRecommendations());
    // 重新请求数据
    dispatch(fetchRecommendations({ userId }))
      .unwrap()
      .then(response => {
        if (response && response.items) {
          // 重置点赞和收藏状态
          const newLikedPosts = {};
          const newCollectedPosts = {};
          
          response.items.forEach(post => {
            // 检查点赞状态
            if (post.is_liked) {
              newLikedPosts[post.post_id] = true;
            }
            
            // 检查收藏状态
            if (post.is_favorited) {
              newCollectedPosts[post.post_id] = true;
            }
          });
          
          setLikedPosts(newLikedPosts);
          setCollectedPosts(newCollectedPosts);
          
          message.success('刷新成功');
        }
      })
      .catch(error => {
        message.error('刷新失败: ' + (error.message || '未知错误'));
      });
  };
  
  // 处理加载更多
  const handleLoadMore = () => {
    if (hasMore && status !== 'loading') {
      // 计算当前偏移量
      const offset = items.length;
      dispatch(fetchRecommendations({ userId, offset }))
        .unwrap()
        .then(response => {
          if (response && response.items) {
            // 更新点赞和收藏状态
            const newLikedPosts = { ...likedPosts };
            const newCollectedPosts = { ...collectedPosts };
            
            response.items.forEach(post => {
              // 检查点赞状态
              if (post.is_liked) {
                newLikedPosts[post.post_id] = true;
              }
              
              // 检查收藏状态
              if (post.is_favorited) {
                newCollectedPosts[post.post_id] = true;
              }
            });
            
            setLikedPosts(newLikedPosts);
            setCollectedPosts(newCollectedPosts);
          }
        });
    }
  };
  
  // 处理帖子点击
  const handlePostClick = (postId) => {
    // 上报点击事件
    tracker.trackClick(postId, 'home');
    // 导航到帖子详情页
    navigate(`/post/${postId}`);
  };
  
  // 处理点赞
  const handleLike = (e, postId) => {
    e.stopPropagation(); // 阻止冒泡，避免触发卡片点击
    const newLikedState = !likedPosts[postId];
    
    // 调用后端API进行点赞/取消点赞
    if (newLikedState) {
      dispatch(likePost({ userId: 'u1001', postId }))
        .unwrap()
        .then(() => {
          // 更新本地状态
          setLikedPosts({ ...likedPosts, [postId]: true });
          // 上报点赞事件
          tracker.trackLike(postId, 'home');
          showMessage('点赞成功', 'success');
          // 更新本地推荐列表中的点赞状态，而不是重新请求
          const updatedItems = items.map(item => {
            if (item.post_id === postId) {
              return { ...item, like_count: (item.like_count || 0) + 1, is_liked: true };
            }
            return item;
          });
          dispatch(updateItems(updatedItems));
        })
        .catch(error => {
          showMessage('点赞失败: ' + (error.message || '未知错误'), 'error');
        });
    } else {
      dispatch(unlikePost({ userId: 'u1001', postId }))
        .unwrap()
        .then(() => {
          // 更新本地状态
          setLikedPosts({ ...likedPosts, [postId]: false });
          // 上报取消点赞事件
          tracker.trackEvent(postId, 'unlike', 'home');
          showMessage('已取消点赞', 'success');
          // 更新本地推荐列表中的点赞状态，而不是重新请求
          const updatedItems = items.map(item => {
            if (item.post_id === postId) {
              return { ...item, like_count: Math.max((item.like_count || 0) - 1, 0), is_liked: false };
            }
            return item;
          });
          dispatch(updateItems(updatedItems));
        })
        .catch(error => {
          showMessage('取消点赞失败: ' + (error.message || '未知错误'), 'error');
        });
    }
  };
  
  // 处理收藏
  const handleCollect = (e, postId) => {
    e.stopPropagation(); // 阻止冒泡，避免触发卡片点击
    const newCollectedState = !collectedPosts[postId];
    
    // 调用后端API进行收藏/取消收藏
    if (newCollectedState) {
      dispatch(favoritePost({ userId: 'u1001', postId }))
        .unwrap()
        .then(() => {
          // 更新本地状态
          setCollectedPosts({ ...collectedPosts, [postId]: true });
          // 上报收藏事件
          tracker.trackFavorite(postId, 'home');
          showMessage('收藏成功', 'success');
          // 更新本地推荐列表中的收藏状态，而不是重新请求
          const updatedItems = items.map(item => {
            if (item.post_id === postId) {
              return { ...item, favorite_count: (item.favorite_count || 0) + 1, is_favorited: true };
            }
            return item;
          });
          dispatch(updateItems(updatedItems));
        })
        .catch(error => {
          showMessage('收藏失败: ' + (error.message || '未知错误'), 'error');
        });
    } else {
      dispatch(unfavoritePost({ userId: 'u1001', postId }))
        .unwrap()
        .then(() => {
          // 更新本地状态
          setCollectedPosts({ ...collectedPosts, [postId]: false });
          // 上报取消收藏事件
          tracker.trackEvent(postId, 'unfavorite', 'home');
          showMessage('已取消收藏', 'success');
          // 更新本地推荐列表中的收藏状态，而不是重新请求
          const updatedItems = items.map(item => {
            if (item.post_id === postId) {
              return { ...item, favorite_count: Math.max((item.favorite_count || 0) - 1, 0), is_favorited: false };
            }
            return item;
          });
          dispatch(updateItems(updatedItems));
        })
        .catch(error => {
          showMessage('取消收藏失败: ' + (error.message || '未知错误'), 'error');
        });
    }
  };
  
  // 处理卡片滑动
  const handleSlide = useCallback((direction) => {
    // 防止动画过程中重复触发
    const cardContainer = document.querySelector('.card-container');
    if (cardContainer && cardContainer.classList.contains('animating')) {
      return;
    }
    
    if (direction === 'up' && currentIndex > 0) {
      // 添加动画标记
      if (cardContainer) cardContainer.classList.add('animating');
      setTimeout(() => {
        setCurrentIndex(prev => prev - 1);
        message.info(`查看上一条推荐`);
        // 上报滑动事件
        tracker.trackEvent(items[currentIndex - 1]?.post_id, 'slide', 'home', { direction: 'up' });
        // 移除动画标记
        setTimeout(() => {
          if (cardContainer) cardContainer.classList.remove('animating');
        }, 300);
      }, 50);
    } else if (direction === 'down' && currentIndex < items.length - 1) {
      // 添加动画标记
      if (cardContainer) cardContainer.classList.add('animating');
      setTimeout(() => {
        setCurrentIndex(prev => prev + 1);
        message.info(`查看下一条推荐`);
        // 上报滑动事件
        tracker.trackEvent(items[currentIndex + 1]?.post_id, 'slide', 'home', { direction: 'down' });
        // 移除动画标记
        setTimeout(() => {
          if (cardContainer) cardContainer.classList.remove('animating');
        }, 300);
      }, 50);
    }
  }, [currentIndex, items, tracker]);
  
  // 监听键盘事件
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowUp') {
        handleSlide('up');
      } else if (e.key === 'ArrowDown') {
        handleSlide('down');
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleSlide]);
  
  // 如果加载失败，显示错误信息
  if (status === 'failed') {
    // 使用Tailwind样式显示错误信息
    return (
      <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-200 dark:from-neutral-900 dark:to-neutral-800 flex items-center justify-center">
        <div className="mx-auto max-w-md rounded-2xl bg-white/80 backdrop-blur-sm shadow-lg ring-1 ring-black/5 p-8 dark:bg-neutral-900/80 dark:ring-white/10 text-center">
          <ExclamationCircleOutlined className="text-red-500 text-2xl mb-2" />
          <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100">加载失败</h3>
          <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">{error || '加载推荐内容失败'}</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="p-6 min-h-screen">
      <div className={`${theme.layout.container} text-center mb-8`}>
        <div className="flex justify-between items-center">
          <h1 className={`${theme.text.title} uppercase tracking-wide mb-2`}>推荐内容</h1>
          <button 
            className={`inline-flex items-center justify-center rounded-xl ${theme.buttons.secondary} px-4 py-2 text-sm font-medium shadow-md hover:shadow-lg transition-all`}
            onClick={handleRefresh}
          >
            <ReloadOutlined className="mr-1" /> 刷新
          </button>
        </div>
        <p className={`mt-2 text-sm ${theme.text.light} max-w-md mx-auto`}>根据您的兴趣为您推荐的内容</p>
      </div>
      
      <div className={theme.layout.container}>
        {items.length > 0 && (
          <>
            <div className="flex justify-center mb-4">
              <button 
                className={`inline-flex items-center justify-center rounded-xl ${theme.buttons.primary} ${currentIndex > 0 ? 'visible' : 'invisible'} px-6 py-3 text-lg font-medium shadow-lg hover:shadow-xl transition-all`}
                onClick={() => handleSlide('up')}
              >
                <LikeOutlined className="mr-2 transform rotate-180" /> 上一条
              </button>
            </div>
            
            {items[currentIndex] && (
              <div 
                className={`mx-auto max-w-3xl ${combinedStyles.card} ${theme.cards.hover} p-8 mt-6 cursor-pointer transition-all hover:shadow-xl slide-card post-card h-[500px]`} 
                data-post-id={items[currentIndex].post_id}
                onClick={() => handlePostClick(items[currentIndex].post_id)}
              >
                <div className="flex justify-between items-center mb-4">
                  <h2 className={theme.text.subtitle}>{items[currentIndex].title}</h2>
                  {/* 移除顶部收藏按钮 */}
                </div>
                <div className="card-content flex flex-col flex-1">
                  <p 
                    className={`summary flex-1 mb-3 ${theme.text.body} line-clamp-3`}
                  >
                    {items[currentIndex].content}
                  </p>
                  <div className="mt-3">
                    {items[currentIndex].tags && items[currentIndex].tags.tags && 
                      items[currentIndex].tags.tags.slice(0, 3).map(tag => (
                        <button 
                          key={tag} 
                          className={`${theme.buttons.tag} mr-2`}
                          onClick={(e) => e.stopPropagation()}
                        >
                          {tag}
                        </button>
                      ))
                    }
                    {items[currentIndex].tags && items[currentIndex].tags.tags && 
                      items[currentIndex].tags.tags.length > 3 && (
                        <button 
                          className={theme.buttons.tag}
                          onClick={(e) => e.stopPropagation()}
                        >
                          +{items[currentIndex].tags.tags.length - 3}
                        </button>
                      )
                    }
                  </div>
                </div>
                <div className="flex justify-between items-center mt-4 pt-4 border-t border-neutral-200">
                  <div className="flex flex-wrap gap-4">
                    <button className={theme.buttons.stat}>
                      <EyeOutlined className="text-indigo-500 mr-2" /> 
                      <span className="text-sm font-medium">{items[currentIndex].view_count}</span>
                    </button>
                    <button 
                      className={`${theme.buttons.stat} ${likedPosts[items[currentIndex].post_id] ? 'bg-indigo-100' : ''} px-4 py-2 rounded-lg flex items-center hover:bg-indigo-100 transition-colors`}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleLike(e, items[currentIndex].post_id);
                      }}
                    >
                      {likedPosts[items[currentIndex].post_id] ? 
                        <LikeOutlined className="mr-2 text-red-500" style={{ fontSize: '16px' }} /> : 
                        <LikeOutlined className="mr-2 text-neutral-600" style={{ fontSize: '16px' }} />}
                      <span className="text-sm font-medium">{items[currentIndex].like_count + (likedPosts[items[currentIndex].post_id] ? 1 : 0)}</span>
                    </button>
                    <button 
                      className={`${theme.buttons.stat} ${collectedPosts[items[currentIndex].post_id] ? 'bg-indigo-100' : ''} px-4 py-2 rounded-lg flex items-center hover:bg-indigo-100 transition-colors`}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCollect(e, items[currentIndex].post_id);
                      }}
                    >
                      {collectedPosts[items[currentIndex].post_id] ? 
                        <StarOutlined className="mr-2 text-yellow-500" style={{ fontSize: '16px' }} /> : 
                        <StarOutlined className="mr-2 text-neutral-600" style={{ fontSize: '16px' }} />}
                      <span className="text-sm font-medium">{items[currentIndex].favorite_count + (collectedPosts[items[currentIndex].post_id] ? 1 : 0)}</span>
                    </button>
                  </div>
                  <button 
                    className={theme.buttons.secondary}
                    onClick={(e) => {
                      e.stopPropagation();
                      // 跳转到作者页面
                    }}
                  >
                    <UserOutlined className="mr-1" />
                    作者: {items[currentIndex].author_id}
                  </button>
                </div>
              </div>
            )}
            
            <div className="flex justify-center mt-4">
              <button 
                className={`inline-flex items-center justify-center rounded-xl ${theme.buttons.primary} ${currentIndex < items.length - 1 ? 'visible' : 'invisible'} px-6 py-3 text-lg font-medium shadow-lg hover:shadow-xl transition-all`}
                onClick={() => handleSlide('down')}
              >
                <LikeOutlined className="mr-2" /> 下一条
              </button>
            </div>
          </>
        )}
        
        {status === 'loading' && items.length === 0 && (
          <div className={`mx-auto max-w-3xl ${combinedStyles.card} p-8 mt-6 h-[500px]`}>
            <div className="animate-pulse">
              <div className="h-4 bg-neutral-200 rounded mb-4 w-2/3"></div>
              <div className="h-4 bg-neutral-200 rounded mb-4 w-5/6"></div>
              <div className="h-4 bg-neutral-200 rounded mb-4 w-1/2"></div>
              <div className="h-4 bg-neutral-200 rounded mb-4 w-full"></div>
              <div className="h-4 bg-neutral-200 rounded w-4/5"></div>
            </div>
          </div>
        )}
      </div>
      
      {hasMore && currentIndex >= items.length - 3 && (
        <div className="container mx-auto text-center my-6">
          <button 
            className="inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:from-indigo-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            onClick={handleLoadMore} 
            disabled={status === 'loading'}
          >
            {status === 'loading' ? '加载中...' : '加载更多'}
          </button>
        </div>
      )}
    </div>
  );
};

export default HomePage;