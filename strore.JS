import { configureStore } from '@reduxjs/toolkit';
import interactionReducer from './interactionSlice';
import agentReducer from './agentSlice';
import hcpReducer from './hcpSlice';

export const store = configureStore({
  reducer: {
    interactions: interactionReducer,
    agent: agentReducer,
    hcps: hcpReducer,
  },
});

export default store;