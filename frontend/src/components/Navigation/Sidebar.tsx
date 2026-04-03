import React from 'react';
import { motion } from 'framer-motion';
import { 
  Home, 
  Scan, 
  Calculator, 
  FileText, 
  Settings,
  Zap,
  Layout
} from 'lucide-react';
import { PageType } from '../Router/AppRouter';

interface SidebarProps {
  currentPage: PageType;
  onPageChange: (page: PageType) => void;
}

interface NavItem {
  id: PageType;
  label: string;
  icon: React.ReactNode;
  description: string;
}

const navItems: NavItem[] = [
  {
    id: 'dashboard',
    label: '仪表盘',
    icon: <Home size={20} />,
    description: '系统概览'
  },
  {
    id: 'contour-processing',
    label: '模块识别',
    icon: <Scan size={20} />,
    description: '模块平面识别'
  },
  {
    id: 'layout-recognition',
    label: '户型图识别',
    icon: <Layout size={20} />,
    description: '户型图分割与分析'
  },
  {
    id: 'material-calculation',
    label: '物料计算',
    icon: <Calculator size={20} />,
    description: '材料用量计算'
  },
  {
    id: 'bom-generation',
    label: 'BOM生成',
    icon: <FileText size={20} />,
    description: '物料清单生成'
  },
  {
    id: 'settings',
    label: '系统设置',
    icon: <Settings size={20} />,
    description: '系统配置'
  }
];

const Sidebar: React.FC<SidebarProps> = ({ currentPage, onPageChange }) => {
  return (
    <motion.aside
      initial={{ x: -300 }}
      animate={{ x: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="fixed left-0 top-0 h-full w-64 glass-effect border-r border-white/20 z-20"
    >
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex items-center space-x-3"
        >
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <Zap className="text-white" size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">BOM系统</h1>
            <p className="text-xs text-gray-400">智能制造解决方案</p>
          </div>
        </motion.div>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-2">
        {navItems.map((item, index) => (
          <motion.button
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 * (index + 1) }}
            onClick={() => onPageChange(item.id)}
            className={`w-full flex items-center space-x-3 p-3 rounded-lg transition-all duration-200 group ${
              currentPage === item.id
                ? 'bg-gradient-to-r from-blue-500/20 to-purple-600/20 border border-blue-500/30 text-white'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <div className={`transition-colors duration-200 ${
              currentPage === item.id ? 'text-blue-400' : 'group-hover:text-blue-400'
            }`}>
              {item.icon}
            </div>
            <div className="flex-1 text-left">
              <div className="font-medium">{item.label}</div>
              <div className="text-xs opacity-70">{item.description}</div>
            </div>
            {currentPage === item.id && (
              <motion.div
                layoutId="activeIndicator"
                className="w-2 h-2 bg-blue-400 rounded-full"
              />
            )}
          </motion.button>
        ))}
      </nav>

      {/* Status */}
      <div className="absolute bottom-4 left-4 right-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="glass-effect rounded-lg p-3 border border-green-500/30"
        >
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-green-400">系统运行正常</span>
          </div>
          <div className="text-xs text-gray-400 mt-1">
            CPU: 45% | 内存: 2.1GB
          </div>
        </motion.div>
      </div>
    </motion.aside>
  );
};

export default Sidebar;