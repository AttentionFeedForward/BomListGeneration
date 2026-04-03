import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, 
  Upload, 
  Eye, 
  Calculator, 
  FileText, 
  BarChart3, 
  Database,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

interface MenuItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  active?: boolean;
  badge?: string;
}

const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [activeItem, setActiveItem] = useState('dashboard');

  const menuItems: MenuItem[] = [
    { id: 'dashboard', label: '控制台', icon: <Home className="w-5 h-5" />, active: true },
    { id: 'upload', label: '数据上传', icon: <Upload className="w-5 h-5" /> },
    { id: 'contour', label: '轮廓识别', icon: <Eye className="w-5 h-5" />, badge: '3' },
    { id: 'calculate', label: '物料计算', icon: <Calculator className="w-5 h-5" /> },
    { id: 'bom', label: 'BOM生成', icon: <FileText className="w-5 h-5" /> },
    { id: 'analytics', label: '数据分析', icon: <BarChart3 className="w-5 h-5" /> },
    { id: 'database', label: '物料库', icon: <Database className="w-5 h-5" /> },
  ];

  return (
    <motion.aside
      className={`fixed left-0 top-20 bottom-0 z-40 glass-effect border-r border-white/20 
                  transition-all duration-300 ${isCollapsed ? 'w-16' : 'w-64'}`}
      initial={{ x: -100 }}
      animate={{ x: 0 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
    >
      {/* 折叠按钮 */}
      <motion.button
        className="absolute -right-3 top-6 w-6 h-6 bg-space-blue border border-neon-cyan/50 
                   rounded-full flex items-center justify-center hover:bg-neon-cyan/20 
                   transition-all duration-300"
        onClick={() => setIsCollapsed(!isCollapsed)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
      >
        {isCollapsed ? (
          <ChevronRight className="w-3 h-3 text-neon-cyan" />
        ) : (
          <ChevronLeft className="w-3 h-3 text-neon-cyan" />
        )}
      </motion.button>

      {/* 导航菜单 */}
      <nav className="p-4 space-y-2">
        {menuItems.map((item, index) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <motion.button
              className={`w-full flex items-center space-x-3 p-3 rounded-lg transition-all duration-300
                         ${activeItem === item.id 
                           ? 'bg-neon-cyan/20 border border-neon-cyan/50 text-neon-cyan' 
                           : 'hover:bg-white/10 text-gray-300 hover:text-white'
                         }`}
              onClick={() => setActiveItem(item.id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className={`${activeItem === item.id ? 'text-neon-cyan' : ''}`}>
                {item.icon}
              </div>
              
              <AnimatePresence>
                {!isCollapsed && (
                  <motion.div
                    className="flex-1 flex items-center justify-between"
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: 'auto' }}
                    exit={{ opacity: 0, width: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <span className="text-sm font-medium">{item.label}</span>
                    {item.badge && (
                      <span className="px-2 py-1 text-xs bg-neon-orange rounded-full text-white">
                        {item.badge}
                      </span>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.button>
          </motion.div>
        ))}
      </nav>

      {/* 底部状态指示 */}
      <AnimatePresence>
        {!isCollapsed && (
          <motion.div
            className="absolute bottom-4 left-4 right-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="p-3 rounded-lg bg-glass-blue border border-neon-blue/30">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-2 h-2 bg-neon-green rounded-full animate-pulse"></div>
                <span className="text-xs text-gray-300">系统状态</span>
              </div>
              <div className="text-xs text-gray-400">
                <div>CPU: 45%</div>
                <div>内存: 2.1GB</div>
                <div>在线用户: 12</div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.aside>
  );
};

export default Sidebar;