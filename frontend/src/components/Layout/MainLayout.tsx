import React from 'react';
import { motion } from 'framer-motion';
import Header from './Header';
import Sidebar from './Sidebar';
import ParticleBackground from '../Effects/ParticleBackground';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-space-gradient tech-grid">
      {/* 粒子背景效果 */}
      <ParticleBackground />
      
      {/* 头部导航 */}
      <Header />
      
      {/* 侧边栏 */}
      <Sidebar />
      
      {/* 主内容区域 */}
      <motion.main
        className="ml-64 mt-20 p-6 min-h-screen"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
      >
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </motion.main>
    </div>
  );
};

export default MainLayout;