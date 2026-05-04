import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API = 'http://localhost:8000/api';

export const fetchInteractions = createAsyncThunk('interactions/fetchAll', async () => {
  const res = await axios.get(`${API}/interactions/`);
  return res.data;
});

export const saveInteraction = createAsyncThunk('interactions/save', async (data) => {
  const res = await axios.post(`${API}/interactions/`, data);
  return res.data;
});

export const updateInteraction = createAsyncThunk('interactions/update', async ({ id, data }) => {
  const res = await axios.put(`${API}/interactions/${id}`, data);
  return res.data;
});

const interactionSlice = createSlice({
  name: 'interactions',
  initialState: {
    list: [],
    loading: false,
    error: null,
    currentForm: {
      hcp_name: '',
      interaction_type: 'Meeting',
      date: new Date().toISOString().split('T')[0],
      time: new Date().toTimeString().slice(0, 5),
      attendees: '',
      topics_discussed: '',
      materials_shared: [],
      samples_distributed: [],
      sentiment: 'Neutral',
      outcomes: '',
      follow_up_actions: '',
      ai_summary: '',
      ai_suggested_follow_ups: [],
    },
    saveStatus: null,
  },
  reducers: {
    updateFormField: (state, action) => {
      state.currentForm[action.payload.field] = action.payload.value;
    },
    resetForm: (state) => {
      state.currentForm = {
        hcp_name: '',
        interaction_type: 'Meeting',
        date: new Date().toISOString().split('T')[0],
        time: new Date().toTimeString().slice(0, 5),
        attendees: '',
        topics_discussed: '',
        materials_shared: [],
        samples_distributed: [],
        sentiment: 'Neutral',
        outcomes: '',
        follow_up_actions: '',
        ai_summary: '',
        ai_suggested_follow_ups: [],
      };
    },
    setFormFromAgent: (state, action) => {
      state.currentForm = { ...state.currentForm, ...action.payload };
    },
    setSaveStatus: (state, action) => {
      state.saveStatus = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (state) => { state.loading = true; })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload;
      })
      .addCase(fetchInteractions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(saveInteraction.fulfilled, (state) => {
        state.saveStatus = 'success';
      });
  },
});

export const { updateFormField, resetForm, setFormFromAgent, setSaveStatus } = interactionSlice.actions;
export default interactionSlice.reducer;