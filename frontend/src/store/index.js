import { configureStore } from '@reduxjs/toolkit';
import recommendationsReducer from './recommendationsSlice';
import postsReducer from './postsSlice';
import eventsReducer from './eventsSlice';
import userReducer from './userSlice';
import likesReducer from './likesSlice';
import favoritesReducer from './favoritesSlice';

export const store = configureStore({
  reducer: {
    recommendations: recommendationsReducer,
    posts: postsReducer,
    events: eventsReducer,
    user: userReducer,
    likes: likesReducer,
    favorites: favoritesReducer,
  },
});