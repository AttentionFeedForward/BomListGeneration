import React from 'react';
import { motion } from 'framer-motion';
import { Search, Bell, User, Settings } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <motion.header 
      className="fixed top-0 left-0 right-0 z-50 glass-effect border-b border-neon-cyan/20"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
    >
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo区域 */}
          <motion.div 
            className="flex items-center space-x-3"
            whileHover={{ scale: 1.05 }}
          >
            <div className="w-10 h-10 bg-neon-gradient rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">B</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">BOM System</h1>
              <p className="text-xs text-gray-400">智能物料清单生成</p>
            </div>
          </motion.div>

          {/* 搜索栏 */}
          <div className="flex-1 max-w-md mx-8">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="搜索物料、项目或功能..."
                className="w-full pl-10 pr-4 py-2 bg-glass-white border border-white/20 rounded-lg 
                         text-white placeholder-gray-400 focus:outline-none focus:border-neon-cyan 
                         focus:shadow-neon-cyan transition-all duration-300"
              />
            </div>
          </div>

          {/* 用户操作区 */}
          <div className="flex items-center space-x-4">
            <motion.button
              className="p-2 rounded-lg glass-effect hover:bg-white/20 transition-all duration-300"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              <Bell className="w-5 h-5 text-gray-300" />
            </motion.button>
            
            <motion.button
              className="p-2 rounded-lg glass-effect hover:bg-white/20 transition-all duration-300"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              <Settings className="w-5 h-5 text-gray-300" />
            </motion.button>

            <motion.div
              className="flex items-center space-x-2 p-2 rounded-lg glass-effect hover:bg-white/20 
                         cursor-pointer transition-all duration-300"
              whileHover={{ scale: 1.05 }}
            >
              <User className="w-5 h-5 text-gray-300" />
              <span className="text-sm text-gray-300">管理员</span>
            </motion.div>
          </div>
        </div>
      </div>
      
      {/* 数据流线装饰 */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neon-cyan to-transparent opacity-50"></div>
    </motion.header>
  );
};

export default Header;