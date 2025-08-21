// src/pages/HomePage.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button'; // 导入 shadcn 的 Button 组件

const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 dark:text-gray-100 sm:text-5xl">
          Retrieval-augmented generation with Qdrant
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Click the button below to start using the RAG (Retrieval-Augmented Generation) system with Qdrant.
        </p>
        <Link to="/chat">
          <Button size="lg"> Start Chat </Button> 
        </Link>
      </div>
    </div>
  );
};

export default HomePage;