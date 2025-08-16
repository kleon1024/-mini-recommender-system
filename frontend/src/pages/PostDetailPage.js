import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { EyeOutlined, LikeOutlined, StarOutlined, UserOutlined } from '@ant-design/icons';
import { fetchPostDetail, resetPostDetail } from '../store/postsSlice';
import { likePost, unlikePost, checkUserLike } from '../store/likesSlice';
import { favoritePost, unfavoritePost, checkUserFavorite } from '../store/favoritesSlice';
import { getTracker } from '../utils/tracker';
import { theme, combinedStyles } from '../styles/theme';

const PostDetailPage = () => {
  const { postId } = useParams();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  // 从Redux store获取帖子详情数据
  const { currentPost, relatedPosts, status, error } = useSelector(state => state.posts);
  const { isLiked } = useSelector(state => state.likes);
  const { isFavorited } = useSelector(state => state.favorites);
  
  // 默认使用u1001用户ID
  const userId = 'u1001';
  
  // 初始化埋点SDK
  const tracker = getTracker(userId);
  
  // 组件挂载时获取帖子详情
  useEffect(() => {
    dispatch(resetPostDetail());
    dispatch(fetchPostDetail(postId));
    
    // 检查用户是否已点赞和收藏
    dispatch(checkUserLike({ userId, postId }));
    dispatch(checkUserFavorite({ userId, postId }));
    
    // 上报浏览事件
    tracker.trackView(postId, 'detail');
    // 开始记录停留时间
    tracker.startStayTime(postId);
    
    return () => {
      // 组件卸载时上报停留时间
      tracker.endStayTime(postId, 'detail');
    };
  }, [dispatch, postId, userId, tracker]);
  
  // 处理点赞
  const handleLike = () => {
    if (!currentPost) return;
    
    // 根据当前状态执行点赞或取消点赞
    if (isLiked) {
      dispatch(unlikePost({ userId, postId }))
        .unwrap()
        .then(() => {
          // 上报取消点赞事件
          tracker.trackEvent(postId, 'unlike', 'detail');
          showSuccess('已取消点赞');
        })
        .catch(error => {
          showError('取消点赞失败: ' + error.message);
        });
    } else {
      dispatch(likePost({ userId, postId }))
        .unwrap()
        .then(() => {
          // 上报点赞事件
          tracker.trackLike(postId, 'detail');
          showSuccess('点赞成功');
        })
        .catch(error => {
          showError('点赞失败: ' + error.message);
        });
    }
  };
  
  // 显示成功消息的函数（替代message.success）
  const showSuccess = (msg) => {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-50 text-green-800 px-4 py-2 rounded-lg shadow-md z-50';
    notification.textContent = msg;
    document.body.appendChild(notification);
    setTimeout(() => {
      notification.remove();
    }, 3000);
  };
  
  // 显示错误消息的函数
  const showError = (msg) => {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-red-50 text-red-800 px-4 py-2 rounded-lg shadow-md z-50';
    notification.textContent = msg;
    document.body.appendChild(notification);
    setTimeout(() => {
      notification.remove();
    }, 3000);
  };
  
  // 处理收藏
  const handleFavorite = () => {
    if (!currentPost) return;
    
    // 根据当前状态执行收藏或取消收藏
    if (isFavorited) {
      dispatch(unfavoritePost({ userId, postId }))
        .unwrap()
        .then(() => {
          // 上报取消收藏事件
          tracker.trackEvent(postId, 'unfavorite', 'detail');
          showSuccess('已取消收藏');
        })
        .catch(error => {
          showError('取消收藏失败: ' + error.message);
        });
    } else {
      dispatch(favoritePost({ userId, postId }))
        .unwrap()
        .then(() => {
          // 上报收藏事件
          tracker.trackFavorite(postId, 'detail');
          showSuccess('收藏成功');
        })
        .catch(error => {
          showError('收藏失败: ' + error.message);
        });
    }
  };
  
  // 处理相关帖子点击
  const handleRelatedPostClick = (relatedPostId) => {
    // 上报点击事件
    tracker.trackClick(relatedPostId, 'related');
    // 导航到相关帖子详情页
    navigate(`/post/${relatedPostId}`);
  };
  
  // 处理作者点击
  const handleAuthorClick = (authorId) => {
    navigate(`/user/${authorId}`);
  };
  
  // 如果加载失败，显示错误信息在UI中
  
  // 加载中显示加载状态
  if (status === 'loading' || !currentPost) {
    return (
      <div className="flex justify-center items-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return (
    <div className="p-6 min-h-screen">
      {status === 'failed' && (
        <div className="mx-auto max-w-3xl rounded-2xl bg-red-50 p-4 mb-6 text-red-600 border border-red-200">
          {error || '加载帖子详情失败'}
        </div>
      )}
      
      <div className={`mx-auto max-w-3xl ${combinedStyles.card} p-8 mb-6`}>
        <div className="mb-6">
          <h2 className={theme.text.subtitle}>{currentPost.title}</h2>
          <div className="mt-4 flex items-center gap-4">
            <button 
              className={theme.buttons.secondary} 
              onClick={() => handleAuthorClick(currentPost.author_id)}
            >
              <UserOutlined className="mr-1" /> {currentPost.author_id}
            </button>
            <span className="text-sm text-neutral-600">发布于 {new Date(currentPost.create_time).toLocaleString()}</span>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {currentPost.tags && currentPost.tags.tags && currentPost.tags.tags.map(tag => (
              <button key={tag} className={theme.buttons.tag}>
                {tag}
              </button>
            ))}
          </div>
        </div>
        
        <div className={`mt-6 ${theme.text.body}`}>
          <p className="whitespace-pre-line">
            {currentPost.content}
          </p>
        </div>
        
        <div className="mt-8 flex flex-wrap gap-4 justify-center">
          <button className={theme.buttons.secondary}>
            <EyeOutlined className="mr-2 text-neutral-600" />
            {currentPost.view_count} 浏览
          </button>
          <button 
            className={isLiked ? `${theme.buttons.primary} bg-red-600 hover:bg-red-700` : `${theme.buttons.primary} hover:bg-indigo-700`}
            onClick={handleLike}
          >
            <LikeOutlined className="mr-2" style={{ fontSize: '16px' }} />
            {currentPost.like_count} {isLiked ? '已点赞' : '点赞'}
          </button>
          <button 
            className={isFavorited ? `${theme.buttons.primary} bg-yellow-600 hover:bg-yellow-700` : `${theme.buttons.primary} hover:bg-indigo-700`}
            onClick={handleFavorite}
          >
            <StarOutlined className="mr-2" style={{ fontSize: '16px' }} />
            {currentPost.favorite_count} {isFavorited ? '已收藏' : '收藏'}
          </button>
        </div>
        
        <div className="mt-6 flex justify-between">
          <button 
            className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-indigo-700 text-neutral-200 rounded-lg shadow-md hover:shadow-lg transition-all duration-300 flex items-center gap-2"
            onClick={() => navigate(`/post/${(parseInt(postId) - 1).toString()}`)}
          >
            <LikeOutlined className="transform rotate-180" /> 上一条
          </button>
          <button 
            className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-indigo-700 text-neutral-200 rounded-lg shadow-md hover:shadow-lg transition-all duration-300 flex items-center gap-2"
            onClick={() => navigate(`/post/${(parseInt(postId) + 1).toString()}`)}
          >
            下一条 <LikeOutlined />
          </button>
        </div>
      </div>
      
      {relatedPosts.length > 0 && (
        <div className={`mx-auto max-w-3xl ${combinedStyles.card} p-8 mt-6`}>
          <h3 className={`${theme.text.subtitle} mb-6`}>相关推荐</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {relatedPosts.map(item => (
              <div 
                key={item.post_id}
                className="rounded-xl bg-white/90 shadow-md hover:shadow-lg transition-shadow cursor-pointer overflow-hidden border border-white/20"
                onClick={() => handleRelatedPostClick(item.post_id)}
              >
                <div className="p-5">
                  <h4 className="text-lg font-medium text-neutral-900 mb-2">{item.title}</h4>
                  <p className="text-neutral-600 line-clamp-2 mb-4">
                    {item.content}
                  </p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {item.tags && (typeof item.tags === 'string' ? JSON.parse(item.tags) : item.tags).tags.map(tag => (
                      <button key={tag} className={theme.buttons.tag}>
                        {tag}
                      </button>
                    ))}
                  </div>
                  <div className="flex justify-between items-center text-sm text-neutral-500">
                    <div className="flex gap-4">
                      <button className={theme.buttons.stat}><EyeOutlined className="mr-1" /> {item.view_count}</button>
                      <button className={theme.buttons.stat}><LikeOutlined className="mr-1" /> {item.like_count}</button>
                      <button className={theme.buttons.stat}><StarOutlined className="mr-1" /> {item.favorite_count}</button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PostDetailPage;