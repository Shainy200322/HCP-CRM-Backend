import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API = 'http://localhost:8000/api';

export const sendAgentMessage = createAsyncThunk('agent/sendMessage', async ({ message, sessionId, history }) => {
  const res = await axios.post(`${API}/agent/chat`, {
    message,
    session_id: sessionId,
    history: history || [],
  });
  return res.data;
});

const agentSlice = createSlice({
  name: 'agent',
  initialState: {
    messages: [
      {
        role: 'assistant',
        content: 'Hello! I\'m your AI assistant for logging HCP interactions. You can:\n• Tell me about a meeting (e.g., "Met Dr. Sharma, discussed OncoBoost efficacy, positive sentiment")\n• Ask for history ("Show me Dr. Patel\'s interaction history")\n• Request follow-ups ("Suggest follow-ups for my meeting with Dr. Kumar")\n• Analyze notes ("Analyze: Dr. Smith was interested but had pricing concerns")',
      }
    ],
    sessionId: null,
    loading: false,
    error: null,
    lastToolResults: [],
  },
  reducers: {
    addUserMessage: (state, action) => {
      state.messages.push({ role: 'user', content: action.payload });
    },
    setSessionId: (state, action) => {
      state.sessionId = action.payload;
    },
    clearChat: (state) => {
      state.messages = [{
        role: 'assistant',
        content: 'Chat cleared. How can I help you log an HCP interaction?'
      }];
      state.sessionId = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendAgentMessage.pending, (state) => {
        state.loading = true;
      })
      .addCase(sendAgentMessage.fulfilled, (state, action) => {
        state.loading = false;
        state.messages.push({ role: 'assistant', content: action.payload.response });
        state.lastToolResults = action.payload.tool_results || [];
        if (action.payload.session_id) {
          state.sessionId = action.payload.session_id;
        }
      })
      .addCase(sendAgentMessage.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
        state.messages.push({
          role: 'assistant',
          content: 'I encountered an error. Please check that the backend is running and try again.'
        });
      });
  },
});

export const { addUserMessage, setSessionId, clearChat } = agentSlice.actions;
export default agentSlice.reducer;