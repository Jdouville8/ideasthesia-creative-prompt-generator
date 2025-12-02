import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../utils/axiosConfig';

export const generatePrompt = createAsyncThunk(
  'prompt/generate',
  async (genres) => {
    const token = localStorage.getItem('token');
    const response = await axiosInstance.post(
      '/api/prompts/generate',
      { genres },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  }
);

const promptSlice = createSlice({
  name: 'prompt',
  initialState: {
    prompt: null,
    loading: false,
    error: null,
  },
  reducers: {
    clearPrompt: (state) => {
      state.prompt = null;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(generatePrompt.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(generatePrompt.fulfilled, (state, action) => {
        state.loading = false;
        state.prompt = action.payload;
      })
      .addCase(generatePrompt.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  },
});

export const { clearPrompt } = promptSlice.actions;
export default promptSlice.reducer;