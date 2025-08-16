import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../utils/api';

// 异步获取用户收藏列表
export const fetchUserFavorites = createAsyncThunk(
  'favorites/fetchUserFavorites',
  async (userId, { rejectWithValue }) => {
    try {
      const response = await api.get(`/api/favorites/user/${userId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

// 异步获取帖子收藏列表
export const fetchPostFavorites = createAsyncThunk(
  'favorites/fetchPostFavorites',
  async (postId, { rejectWithValue }) => {
    try {
      const response = await api.get(`/api/favorites/post/${postId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

// 检查用户是否收藏了帖子
export const checkUserFavorite = createAsyncThunk(
  'favorites/checkUserFavorite',
  async ({ userId, postId }, { rejectWithValue }) => {
    try {
      const response = await api.get(`/api/favorites/check/${userId}/${postId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

// 收藏帖子
export const favoritePost = createAsyncThunk(
  'favorites/favoritePost',
  async ({ userId, postId, notes = '' }, { rejectWithValue }) => {
    try {
      const { data } = await api.post('/api/favorites', { 
        user_id: userId, 
        post_id: postId,
        notes: notes
      });
      return data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

// 取消收藏
export const unfavoritePost = createAsyncThunk(
  'favorites/unfavoritePost',
  async ({ userId, postId }, { rejectWithValue }) => {
    try {
      await api.delete(`/api/favorites/${userId}/${postId}`);
      return { userId, postId, success: true };
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

const initialState = {
  userFavorites: [],
  postFavorites: [],
  isFavorited: false,
  status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
  error: null,
};

const favoritesSlice = createSlice({
  name: 'favorites',
  initialState,
  reducers: {
    resetFavorites: (state) => {
      state.userFavorites = [];
      state.postFavorites = [];
      state.isFavorited = false;
      state.status = 'idle';
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // 处理获取用户收藏列表
      .addCase(fetchUserFavorites.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchUserFavorites.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.userFavorites = action.payload;
      })
      .addCase(fetchUserFavorites.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Failed to fetch user favorites';
      })
      
      // 处理获取帖子收藏列表
      .addCase(fetchPostFavorites.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchPostFavorites.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.postFavorites = action.payload;
      })
      .addCase(fetchPostFavorites.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Failed to fetch post favorites';
      })
      
      // 处理检查用户是否收藏
      .addCase(checkUserFavorite.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(checkUserFavorite.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.isFavorited = action.payload.is_favorited;
      })
      .addCase(checkUserFavorite.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Failed to check user favorite';
      })
      
      // 处理收藏帖子
      .addCase(favoritePost.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(favoritePost.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.isFavorited = true;
        // 更新用户收藏列表
        if (!state.userFavorites.some(favorite => favorite.post_id === action.payload.post_id)) {
          state.userFavorites.push(action.payload);
        }
      })
      .addCase(favoritePost.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Failed to favorite post';
      })
      
      // 处理取消收藏
      .addCase(unfavoritePost.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(unfavoritePost.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.isFavorited = false;
        // 从用户收藏列表中移除
        state.userFavorites = state.userFavorites.filter(
          favorite => !(favorite.post_id === action.payload.postId && favorite.user_id === action.payload.userId)
        );
      })
      .addCase(unfavoritePost.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Failed to unfavorite post';
      });
  },
});

export const { resetFavorites } = favoritesSlice.actions;

export default favoritesSlice.reducer;