import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// Async thunk for generating sound design prompts
export const generateSoundDesignPrompt = createAsyncThunk(
  'soundDesign/generate',
  async ({ synthesizer, exerciseType, genre }, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL}/api/sound-design/generate`,
        { synthesizer, exerciseType, genre },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.error || 'Failed to generate sound design prompt');
    }
  }
);

const soundDesignSlice = createSlice({
  name: 'soundDesign',
  initialState: {
    prompt: null,
    loading: false,
    error: null,
    selectedSynthesizer: 'Serum 2',
    selectedExerciseType: 'technical',
    selectedGenre: 'all'
  },
  reducers: {
    setSynthesizer: (state, action) => {
      state.selectedSynthesizer = action.payload;
    },
    setExerciseType: (state, action) => {
      state.selectedExerciseType = action.payload;
    },
    setGenre: (state, action) => {
      state.selectedGenre = action.payload;
    },
    clearPrompt: (state) => {
      state.prompt = null;
      state.error = null;
    },
    clearError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(generateSoundDesignPrompt.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(generateSoundDesignPrompt.fulfilled, (state, action) => {
        state.loading = false;
        state.prompt = action.payload;
        state.error = null;
      })
      .addCase(generateSoundDesignPrompt.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  }
});

export const { setSynthesizer, setExerciseType, setGenre, clearPrompt, clearError } = soundDesignSlice.actions;
export default soundDesignSlice.reducer;
