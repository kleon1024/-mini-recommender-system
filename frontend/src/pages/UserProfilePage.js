import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { UserOutlined, HistoryOutlined, TagOutlined, LikeOutlined, StarOutlined } from '@ant-design/icons';
import { fetchUserProfile, fetchUserActivity, resetUserProfile } from '../store/userSlice';
import { fetchUserLikes } from '../store/likesSlice';
import { fetchUserFavorites } from '../store/favoritesSlice';
import { theme, combinedStyles } from '../styles/theme';

const UserProfilePage = () => {
  const { userId } = useParams();
  const dispatch = useDispatch();
  const [activeTab, setActiveTab] = useState('activity'); // 'activity', 'likes', 'favorites'
  const [visibleItems, setVisibleItems] = useState(5); // 初始显示5条记录
  
  // 从Redux store获取用户数据
  const { currentUser, userActivity, userStatus, activityStatus, error } = useSelector(state => state.user);
  const { userLikes, status: likesStatus } = useSelector(state => state.likes);
  const { userFavorites, status: favoritesStatus } = useSelector(state => state.favorites);
  
  // 组件挂载时获取用户信息和活动历史
  useEffect(() => {
    dispatch(resetUserProfile());
    dispatch(fetchUserProfile(userId));
    dispatch(fetchUserActivity(userId));
    dispatch(fetchUserLikes(userId));
    dispatch(fetchUserFavorites(userId));
  }, [dispatch, userId]);
  
  // 加载更多记录
  const loadMore = () => {
    setVisibleItems(prev => prev + 5);
  };
  
  // 切换标签页时重置显示数量
  useEffect(() => {
    setVisibleItems(5);
  }, [activeTab]);
  
  // 如果加载失败，显示错误信息
  if (userStatus === 'failed') {
    // 错误信息将在UI中显示
  }
  
  // 加载中显示加载状态
  if (userStatus === 'loading' || !currentUser) {
    return (
      <div className="flex justify-center items-center min-h-[50vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-indigo-200 border-t-indigo-600 shadow-md"></div>
          <p className="text-indigo-600 font-medium">加载中...</p>
        </div>
      </div>
    );
  }
  
  // 格式化事件类型
  const formatEventType = (type) => {
    const typeMap = {
      'view': '浏览',
      'click': '点击',
      'like': '点赞',
      'favorite': '收藏',
      'play': '播放',
      'stay': '停留'
    };
    return typeMap[type] || type;
  };
  
  return (
    <div className="container mx-auto px-4 py-6">
      {userStatus === 'failed' && (
        <div className="mx-auto max-w-3xl rounded-2xl bg-red-50 p-4 mb-6 text-red-600 border border-red-200">
          {error || '加载用户信息失败'}
        </div>
      )}
      
      <div className={`mx-auto max-w-3xl ${combinedStyles.card} p-8 mb-6`}>
        <div className="mb-6">
          <h2 className={`text-2xl font-bold tracking-tight text-indigo-700 flex items-center gap-2`}>
            <UserOutlined /> {currentUser.username} 的个人中心
          </h2>
          <p className={`mt-2 ${theme.text.body} font-medium`}>
            用户ID: {currentUser.user_id}
          </p>
          <p className={`mt-2 ${theme.text.body} font-medium`}>
            注册时间: {new Date(currentUser.create_time).toLocaleString()}
          </p>
        </div>
      </div>
      
      <div className={`mx-auto max-w-3xl ${combinedStyles.card} p-8 mb-6`}>
        <h3 className={`text-xl font-semibold tracking-tight text-indigo-600 mb-4 flex items-center gap-2`}>
          <TagOutlined /> 兴趣标签
        </h3>
        <div className="flex flex-wrap gap-2">
          {currentUser.tags && currentUser.tags.interests && currentUser.tags.interests.map(tag => (
            <button key={tag} className="px-2 py-1 text-xs rounded-full border border-blue-200 bg-blue-50 text-blue-800 hover:bg-blue-100 transition-colors">
              <TagOutlined className="mr-1" /> {tag}
            </button>
          ))}
        </div>
      </div>
      
      <div className={`mx-auto max-w-3xl ${combinedStyles.card} p-8 mb-6`}>
        <h3 className={`text-xl font-semibold tracking-tight text-indigo-600 mb-4 flex items-center gap-2`}>
          <TagOutlined /> 偏好分类
        </h3>
        <div className="flex flex-wrap gap-2">
          {currentUser.preferences && currentUser.preferences.categories && currentUser.preferences.categories.map(category => (
            <button key={category} className="px-2 py-1 text-xs rounded-full border border-green-200 bg-green-50 text-green-800 hover:bg-green-100 transition-colors">
              {category}
            </button>
          ))}
        </div>
      </div>
      
      <div className={`mx-auto max-w-3xl ${combinedStyles.card} p-8`}>
        {/* 标签页切换 */}
        <div className="flex border-b border-gray-200 mb-6">
          <button 
            className={`py-2 px-4 font-medium flex items-center gap-1 ${activeTab === 'activity' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-500 hover:text-indigo-500'}`}
            onClick={() => setActiveTab('activity')}
          >
            <HistoryOutlined /> 最近活动
          </button>
          <button 
            className={`py-2 px-4 font-medium flex items-center gap-1 ${activeTab === 'likes' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-500 hover:text-indigo-500'}`}
            onClick={() => setActiveTab('likes')}
          >
            <LikeOutlined style={{ fontSize: '16px' }} /> 喜欢列表
          </button>
          <button 
            className={`py-2 px-4 font-medium flex items-center gap-1 ${activeTab === 'favorites' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-500 hover:text-indigo-500'}`}
            onClick={() => setActiveTab('favorites')}
          >
            <StarOutlined style={{ fontSize: '16px' }} /> 收藏列表
          </button>
        </div>
        
        {/* 最近活动标签页 */}
        {activeTab === 'activity' && (
          <div>
            {activityStatus === 'loading' ? (
              <div className="flex justify-center py-6">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600"></div>
              </div>
            ) : userActivity.length > 0 ? (
              <div>
                <div className="divide-y divide-neutral-200 dark:divide-neutral-700 max-h-80 overflow-y-auto">
                  {userActivity.slice(0, visibleItems).map((item, index) => (
                    <div key={index} className="py-4">
                      <h4 className="text-lg font-medium text-neutral-800">
                        {`${formatEventType(item.event_type)} 了内容 ${item.post_id}`}
                      </h4>
                      <p className={`mt-1 ${theme.text.body} text-sm`}>
                        {`时间: ${new Date(item.timestamp).toLocaleString()} | 来源: ${item.source}`}
                      </p>
                    </div>
                  ))}
                </div>
                {visibleItems < userActivity.length && (
                  <div className="text-center mt-4">
                    <button 
                      onClick={loadMore}
                      className="px-4 py-2 bg-indigo-50 text-indigo-600 rounded-md hover:bg-indigo-100 transition-colors"
                    >
                      加载更多
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className={`${theme.text.body} italic`}>暂无活动记录</p>
              </div>
            )}
          </div>
        )}
        
        {/* 喜欢列表标签页 */}
        {activeTab === 'likes' && (
          <div>
            {likesStatus === 'loading' ? (
              <div className="flex justify-center py-6">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600"></div>
              </div>
            ) : userLikes && userLikes.length > 0 ? (
              <div>
                <div className="divide-y divide-neutral-200 dark:divide-neutral-700 max-h-80 overflow-y-auto">
                  {userLikes
                    .slice(0, visibleItems)
                    .map((like, index) => (
                      <div key={index} className="py-4">
                        <h4 className="text-lg font-medium text-neutral-800 flex items-center gap-2">
                          <LikeOutlined className="text-red-500" style={{ fontSize: '16px' }} />
                          <Link to={`/post/${like.post_id}`} className="hover:text-indigo-600 hover:underline">
                            {`点赞了内容 ${like.post_id}`}
                          </Link>
                        </h4>
                        <p className={`mt-1 ${theme.text.body} text-sm`}>
                          {`时间: ${new Date(like.create_time).toLocaleString()}`}
                        </p>
                      </div>
                    ))}
                </div>
                {visibleItems < userLikes.length && (
                  <div className="text-center mt-4">
                    <button 
                      onClick={loadMore}
                      className="px-4 py-2 bg-indigo-50 text-indigo-600 rounded-md hover:bg-indigo-100 transition-colors"
                    >
                      加载更多
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className={`${theme.text.body} italic`}>暂无点赞记录</p>
              </div>
            )}
          </div>
        )}
        
        {/* 收藏列表标签页 */}
        {activeTab === 'favorites' && (
          <div>
            {favoritesStatus === 'loading' ? (
              <div className="flex justify-center py-6">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600"></div>
              </div>
            ) : userFavorites && userFavorites.length > 0 ? (
              <div>
                <div className="divide-y divide-neutral-200 dark:divide-neutral-700 max-h-80 overflow-y-auto">
                  {userFavorites
                    .slice(0, visibleItems)
                    .map((favorite, index) => (
                      <div key={index} className="py-4">
                        <h4 className="text-lg font-medium text-neutral-800 flex items-center gap-2">
                          <StarOutlined className="text-yellow-500" style={{ fontSize: '16px' }} />
                          <Link to={`/post/${favorite.post_id}`} className="hover:text-indigo-600 hover:underline">
                            {`收藏了内容 ${favorite.post_id}`}
                          </Link>
                        </h4>
                        <p className={`mt-1 ${theme.text.body} text-sm`}>
                          {`时间: ${new Date(favorite.create_time).toLocaleString()}`}
                        </p>
                        {favorite.notes && (
                          <p className={`mt-1 ${theme.text.body} text-sm italic bg-yellow-50 p-2 rounded-md`}>
                            备注: {favorite.notes}
                          </p>
                        )}
                      </div>
                    ))}
                </div>
                {visibleItems < userFavorites.length && (
                  <div className="text-center mt-4">
                    <button 
                      onClick={loadMore}
                      className="px-4 py-2 bg-indigo-50 text-indigo-600 rounded-md hover:bg-indigo-100 transition-colors"
                    >
                      加载更多
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className={`${theme.text.body} italic`}>暂无收藏记录</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default UserProfilePage;