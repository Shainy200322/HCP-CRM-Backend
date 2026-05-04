import React from 'react';
import { Provider } from 'react-redux';
import { store } from './store/store';
import LogInteractionScreen from './components/LogInteractionScreen';
import './styles/global.css';

function App() {
  return (
    <Provider store={store}>
      <div className="app">
        <LogInteractionScreen />
      </div>
    </Provider>
  );
}

export default App;