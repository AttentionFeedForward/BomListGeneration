import React from 'react';
import { motion } from 'framer-motion';
import { Eye, Calculator, FileText, Plus, Layout } from 'lucide-react';
import { useNavigation } from '../../App';
import { useActions } from '../../store';

const QuickActions: React.FC = () => {
  const { navigateTo } = useNavigation();
  const { triggerUploadPrompt } = useActions();
  const actions = [
    {
      id: 'contour',
      title: '模块识别',
      description: '智能识别模块轮廓',
      icon: <Eye className="w-6 h-6" />,
      color: 'neon-cyan',
      gradient: 'from-cyan-500 to-teal-500'
    },
    {
      id: 'layout',
      title: '户型图识别',
      description: '识别整屋户型结构',
      icon: <Layout className="w-6 h-6" />,
      color: 'neon-blue',
      gradient: 'from-blue-500 to-indigo-500'
    },
    {
      id: 'calculate',
      title: '物料计算',
      description: '自动计算物料用量',
      icon: <Calculator className="w-6 h-6" />,
      color: 'neon-green',
      gradient: 'from-green-500 to-emerald-500'
    },
    {
      id: 'generate',
      title: '生成BOM',
      description: '创建物料清单',
      icon: <FileText className="w-6 h-6" />,
      color: 'neon-purple',
      gradient: 'from-purple-500 to-pink-500'
    }
  ];

  return (
    <div className="glass-effect rounded-xl p-6 border border-white/20 h-full min-h-[400px]">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-white">快速操作</h3>
        <motion.button
          className="p-2 rounded-lg glass-effect hover:bg-white/20 transition-all duration-300"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
        >
          <Plus className="w-5 h-5 text-gray-300" />
        </motion.button>
      </div>

      <div className="space-y-3">
        {actions.map((action, index) => (
          <motion.button
            key={action.id}
            className="w-full p-4 rounded-lg glass-effect border border-white/10 
                       hover:border-white/30 hover:bg-white/10 transition-all duration-300 
                       group text-left"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: index * 0.1 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => {
              switch (action.id) {
                case 'contour':
                  navigateTo('contour-processing');
                  break;
                case 'layout':
                  navigateTo('layout-recognition');
                  break;
                case 'calculate':
                  navigateTo('material-calculation');
                  break;
                case 'generate':
                  navigateTo('bom-generation');
                  break;
                default:
                  break;
              }
            }}
          >
            <div className="flex items-center space-x-4">
              <div className={`p-3 rounded-lg bg-gradient-to-r ${action.gradient} 
                              group-hover:scale-110 transition-transform duration-300`}>
                <div className="text-white">
                  {action.icon}
                </div>
              </div>
              
              <div className="flex-1">
                <h4 className="text-white font-medium group-hover:text-neon-cyan transition-colors duration-300">
                  {action.title}
                </h4>
                <p className="text-gray-400 text-sm mt-1">
                  {action.description}
                </p>
              </div>

              <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div className="w-2 h-2 bg-neon-cyan rounded-full animate-pulse"></div>
              </div>
            </div>

            {/* 悬停时的数据流线效果 */}
            <div className="mt-3 h-px bg-gradient-to-r from-transparent via-neon-cyan to-transparent 
                           opacity-0 group-hover:opacity-50 transition-opacity duration-300"></div>
          </motion.button>
        ))}
      </div>

      {/* 底部提示 */}
      <div className="mt-6 p-3 rounded-lg bg-glass-blue border border-neon-blue/30">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-neon-blue rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-300">
            提示：支持拖拽文件直接上传
          </span>
        </div>
      </div>
    </div>
  );
};

export default QuickActions;