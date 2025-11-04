import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import promptReducer from './promptSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    prompt: promptReducer,
  },
});