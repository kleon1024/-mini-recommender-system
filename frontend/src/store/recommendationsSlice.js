import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../utils/api';

// 异步获取推荐内容
export const fetchRecommendations = createAsyncThunk(
  'recommendations/fetchRecommendations',
  async ({ userId, offset = 0, count = 10, filters = null }, { rejectWithValue }) => {
    try {
      // 从posts接口获取推荐内容
      const response = await api.get(`/api/posts`, {
        params: { user_id: userId, offset, count, filters }
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

const initialState = {
  items: [],
  hasMore: true,
  total: 0,
  status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
  error: null,
};

const recommendationsSlice = createSlice({
  name: 'recommendations',
  initialState,
  reducers: {
    resetRecommendations: (state) => {
      state.items = [];
      state.hasMore = true;
      state.total = 0;
      state.status = 'idle';
      state.error = null;
    },
    updateItems: (state, action) => {
      // 更新推荐列表中的项目，用于本地更新点赞和收藏状态
      state.items = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchRecommendations.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchRecommendations.fulfilled, (state, action) => {
        state.status = 'succeeded';
        // 追加新的推荐内容
        state.items = [...state.items, ...action.payload.items];
        state.hasMore = action.payload.has_more;
        state.total = action.payload.total;
      })
      .addCase(fetchRecommendations.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Failed to fetch recommendations';
      });
  },
});

export const { resetRecommendations, updateItems } = recommendationsSlice.actions;

export default recommendationsSlice.reducer;