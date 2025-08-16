import { render, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import configureMockStore from 'redux-mock-store';
import thunk from 'redux-thunk';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import HomePage from '../../frontend/src/pages/HomePage';

// 创建模拟store
const mockStore = configureMockStore([thunk]);
const mock = new MockAdapter(axios);

// 模拟推荐数据
const mockRecommendations = {
  items: [
    {
      post_id: 'p1001',
      title: '测试帖子1',
      content: '这是测试帖子内容1',
      author_id: 'u2001',
      tags: JSON.stringify({tags: ['科技', '编程']}),
      view_count: 100,
      like_count: 20,
      favorite_count: 10,
      create_time: '2023-11-01T12:00:00Z'
    },
    {
      post_id: 'p1002',
      title: '测试帖子2',
      content: '这是测试帖子内容2',
      author_id: 'u3001',
      tags: JSON.stringify({tags: ['人工智能']}),
      view_count: 200,
      like_count: 30,
      favorite_count: 15,
      create_time: '2023-11-02T12:00:00Z'
    }
  ],
  has_more: true,
  total: 10
};

describe('HomePage组件', () => {
  let store;

  beforeEach(() => {
    // 重置模拟
    mock.reset();
    
    // 模拟API响应
    mock.onGet('http://localhost:8000/api/posts').reply(200, mockRecommendations);
    
    // 初始化store
    store = mockStore({
      recommendations: {
        items: [],
        hasMore: true,
        total: 0,
        status: 'idle',
        error: null
      }
    });
  });

  test('加载并显示推荐内容', async () => {
    render(
      <Provider store={store}>
        <BrowserRouter>
          <HomePage />
        </BrowserRouter>
      </Provider>
    );

    // 验证加载状态
    expect(screen.getByText('推荐内容')).toBeInTheDocument();
    
    // 等待API调用完成
    await waitFor(() => {
      const actions = store.getActions();
      return actions.some(action => action.type === 'recommendations/fetchRecommendations/fulfilled');
    });
    
    // 验证store中的actions
    const actions = store.getActions();
    expect(actions[0].type).toBe('recommendations/resetRecommendations');
    expect(actions[1].type).toBe('recommendations/fetchRecommendations/pending');
    expect(actions[2].type).toBe('recommendations/fetchRecommendations/fulfilled');
    expect(actions[2].payload).toEqual(mockRecommendations);
  });

  test('处理API错误', async () => {
    // 模拟API错误
    mock.onGet('http://localhost:8000/api/posts').reply(500, { detail: '服务器错误' });
    
    render(
      <Provider store={store}>
        <BrowserRouter>
          <HomePage />
        </BrowserRouter>
      </Provider>
    );
    
    // 等待API调用完成
    await waitFor(() => {
      const actions = store.getActions();
      return actions.some(action => action.type === 'recommendations/fetchRecommendations/rejected');
    });
    
    // 验证store中的actions
    const actions = store.getActions();
    expect(actions[0].type).toBe('recommendations/resetRecommendations');
    expect(actions[1].type).toBe('recommendations/fetchRecommendations/pending');
    expect(actions[2].type).toBe('recommendations/fetchRecommendations/rejected');
  });
});