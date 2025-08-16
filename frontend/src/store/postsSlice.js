import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../utils/api';

// 异步获取帖子详情
export const fetchPostDetail = createAsyncThunk(
  'posts/fetchPostDetail',
  async (postId, { rejectWithValue }) => {
    try {
      // 获取帖子详情
      const detailResponse = await api.get(`/api/posts/${postId}`);
      
      // 获取相关推荐
      const relatedResponse = await api.get(`/api/posts/${postId}/related`, {
        params: { user_id: '1001', count: 5 }
      });
      
      return {
        post: detailResponse.data,
        related_posts: relatedResponse.data
      };
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

const initialState = {
  currentPost: null,
  relatedPosts: [],
  status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
  error: null,
};

const postsSlice = createSlice({
  name: 'posts',
  initialState,
  reducers: {
    resetPostDetail: (state) => {
      state.currentPost = null;
      state.relatedPosts = [];
      state.status = 'idle';
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPostDetail.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchPostDetail.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.currentPost = action.payload.post;
        state.relatedPosts = action.payload.related_posts;
      })
      .addCase(fetchPostDetail.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Failed to fetch post detail';
      });
  },
});

export const { resetPostDetail } = postsSlice.actions;

export default postsSlice.reducer;