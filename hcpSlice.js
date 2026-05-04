import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

export const fetchHCPs = createAsyncThunk('hcps/fetchAll', async () => {
  const res = await axios.get('http://localhost:8000/api/hcp/');
  return res.data;
});

const hcpSlice = createSlice({
  name: 'hcps',
  initialState: { list: [], loading: false },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchHCPs.pending, (state) => { state.loading = true; })
      .addCase(fetchHCPs.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload;
      });
  },
});

export default hcpSlice.reducer;