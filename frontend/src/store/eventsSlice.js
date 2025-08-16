import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../utils/api';

// 异步上报用户行为
export const reportEvent = createAsyncThunk(
  'events/reportEvent',
  async (eventData, { rejectWithValue }) => {
    try {
      const response = await api.post(`/api/events`, eventData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

const initialState = {
  status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
  error: null,
};

const eventsSlice = createSlice({
  name: 'events',
  initialState,
  reducers: {
    resetEventStatus: (state) => {
      state.status = 'idle';
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(reportEvent.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(reportEvent.fulfilled, (state) => {
        state.status = 'succeeded';
      })
      .addCase(reportEvent.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Failed to report event';
      });
  },
});

export const { resetEventStatus } = eventsSlice.actions;

export default eventsSlice.reducer;