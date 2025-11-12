import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import promptReducer from './promptSlice';
import soundDesignReducer from './soundDesignSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    prompt: promptReducer,
    soundDesign: soundDesignReducer,
  },
});