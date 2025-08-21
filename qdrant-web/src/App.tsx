// src/App.tsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

// 导入你的页面组件
import HomePage from './pages/HomePage';
import ChatPage from './pages/ChatPage';
import ChatPage_v2 from './pages/chat_v2';
const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat_v2" element={<ChatPage_v2 />} />

      </Routes>
    </BrowserRouter>
  );
};

export default App;