import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import promptReducer from './promptSlice';
import soundDesignReducer from './soundDesignSlice';
import { setStore } from '../utils/axiosConfig';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    prompt: promptReducer,
    soundDesign: soundDesignReducer,
  },
});

// Register store with axios interceptor
setStore(store);