import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../utils/api';

// 异步获取用户点赞列表
export const fetchUserLikes = createAsyncThunk(
  'likes/fetchUserLikes',
  async (userId, { rejectWithValue }) => {
    try {
      const response = await api.get(`/api/likes/user/${userId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

// 异步获取帖子点赞列表
export const fetchPostLikes = createAsyncThunk(
  'likes/fetchPostLikes',
  async (postId, { rejectWithValue }) => {
    try {
      const response = await api.get(`/api/likes/post/${postId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

// 检查用户是否点赞了帖子
export const checkUserLike = createAsyncThunk(
  'likes/checkUserLike',
  async ({ userId, postId }, { rejectWithValue }) => {
    try {
      const response = await api.get(`/api/likes/check/${userId}/${postId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

// 点赞帖子
export const likePost = createAsyncThunk(
  'likes/likePost',
  async ({ userId, postId }, { rejectWithValue }) => {
    try {
      const { data } = await api.post('/api/likes', { user_id: userId, post_id: postId });
      return data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

// 取消点赞
export const unlikePost = createAsyncThunk(
  'likes/unlikePost',
  async ({ userId, postId }, { rejectWithValue }) => {
    try {
      await api.delete(`/api/likes/${userId}/${postId}`);
      return { userId, postId, success: true };
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

const initialState = {
  userLikes: [],
  postLikes: [],
  isLiked: false,
  status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
  error: null,
};

const likesSlice = createSlice({
  name: 'likes',
  initialState,
  reducers: {
    resetLikes: (state) => {
      state.userLikes = [];
      state.postLikes = [];
      state.isLiked = false;
      state.status = 'idle';
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // 处理获取用户点赞列表
      .addCase(fetchUserLikes.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchUserLikes.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.userLikes = action.payload;
      })
      .addCase(fetchUserLikes.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Failed to fetch user likes';
      })
      
      // 处理获取帖子点赞列表
      .addCase(fetchPostLikes.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchPostLikes.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.postLikes = action.payload;
      })
      .addCase(fetchPostLikes.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Failed to fetch post likes';
      })
      
      // 处理检查用户是否点赞
      .addCase(checkUserLike.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(checkUserLike.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.isLiked = action.payload.is_liked;
      })
      .addCase(checkUserLike.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Failed to check user like';
      })
      
      // 处理点赞帖子
      .addCase(likePost.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(likePost.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.isLiked = true;
        // 更新用户点赞列表
        if (!state.userLikes.some(like => like.post_id === action.payload.post_id)) {
          state.userLikes.push(action.payload);
        }
      })
      .addCase(likePost.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Failed to like post';
      })
      
      // 处理取消点赞
      .addCase(unlikePost.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(unlikePost.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.isLiked = false;
        // 从用户点赞列表中移除
        state.userLikes = state.userLikes.filter(
          like => !(like.post_id === action.payload.postId && like.user_id === action.payload.userId)
        );
      })
      .addCase(unlikePost.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Failed to unlike post';
      });
  },
});

export const { resetLikes } = likesSlice.actions;

export default likesSlice.reducer;