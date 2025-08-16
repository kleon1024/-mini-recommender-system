import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../utils/api';

// 异步获取用户信息
export const fetchUserProfile = createAsyncThunk(
  'user/fetchUserProfile',
  async (userId, { rejectWithValue }) => {
    try {
      const response = await api.get(`/api/users/${userId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

// 异步获取用户活动历史
export const fetchUserActivity = createAsyncThunk(
  'user/fetchUserActivity',
  async (userId, { rejectWithValue }) => {
    try {
      const response = await api.get(`/api/users/${userId}/activity`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

const initialState = {
  currentUser: null,
  userActivity: [],
  status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
  activityStatus: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
  error: null,
};

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setCurrentUser: (state, action) => {
      state.currentUser = action.payload;
    },
    resetUserProfile: (state) => {
      state.currentUser = null;
      state.userActivity = [];
      state.status = 'idle';
      state.activityStatus = 'idle';
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUserProfile.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchUserProfile.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.currentUser = action.payload; // API直接返回用户数据，不是包含在user字段中
      })
      .addCase(fetchUserProfile.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Failed to fetch user profile';
      })
      .addCase(fetchUserActivity.pending, (state) => {
        state.activityStatus = 'loading';
      })
      .addCase(fetchUserActivity.fulfilled, (state, action) => {
        state.activityStatus = 'succeeded';
        state.userActivity = action.payload; // API直接返回活动数据数组，不是包含在activity字段中
      })
      .addCase(fetchUserActivity.rejected, (state, action) => {
        state.activityStatus = 'failed';
        state.error = action.payload || 'Failed to fetch user activity';
      });
  },
});

export const { setCurrentUser, resetUserProfile } = userSlice.actions;

export default userSlice.reducer;