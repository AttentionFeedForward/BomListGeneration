import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, X } from 'lucide-react';

interface FloatingAction {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  color?: string;
  disabled?: boolean;
}

interface FloatingActionButtonProps {
  actions: FloatingAction[];
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  size?: 'sm' | 'md' | 'lg';
}

const FloatingActionButton: React.FC<FloatingActionButtonProps> = ({
  actions,
  position = 'bottom-right',
  size = 'md'
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const positionClasses = {
    'bottom-right': 'bottom-6 right-6',
    'bottom-left': 'bottom-6 left-6',
    'top-right': 'top-6 right-6',
    'top-left': 'top-6 left-6'
  };

  const sizeClasses = {
    sm: 'w-12 h-12',
    md: 'w-14 h-14',
    lg: 'w-16 h-16'
  };

  const iconSizes = {
    sm: 20,
    md: 24,
    lg: 28
  };

  const getActionPosition = (index: number) => {
    const isBottom = position.includes('bottom');
    const isRight = position.includes('right');
    
    const distance = 70;
    const yOffset = isBottom ? -(index + 1) * distance : (index + 1) * distance;
    
    return {
      y: yOffset,
      x: 0
    };
  };

  return (
    <div className={`fixed ${positionClasses[position]} z-50`}>
      {/* 动作按钮列表 */}
      <AnimatePresence>
        {isOpen && actions.map((action, index) => (
          <motion.div
            key={index}
            className="absolute"
            initial={{ opacity: 0, scale: 0, ...getActionPosition(index) }}
            animate={{ 
              opacity: 1, 
              scale: 1, 
              ...getActionPosition(index),
              transition: { delay: index * 0.1 }
            }}
            exit={{ 
              opacity: 0, 
              scale: 0, 
              y: 0,
              transition: { delay: (actions.length - index - 1) * 0.05 }
            }}
          >
            <motion.button
              className={`${sizeClasses[size]} ${
                action.disabled 
                  ? 'bg-gray-600 cursor-not-allowed opacity-50' 
                  : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:scale-110'
              } rounded-full shadow-lg flex items-center justify-center text-white relative overflow-hidden group`}
              onClick={action.disabled ? undefined : action.onClick}
              whileHover={action.disabled ? {} : { scale: 1.1 }}
              whileTap={action.disabled ? {} : { scale: 0.9 }}
              disabled={action.disabled}
            >
              {/* 背景光效 */}
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-cyan-400/20 to-blue-500/20 rounded-full"
                animate={{
                  opacity: [0.3, 0.6, 0.3],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              />
              
              {/* 图标 */}
              <div className="relative z-10">
                {action.icon}
              </div>

              {/* 悬浮提示 */}
              <motion.div
                className="absolute right-full mr-3 px-3 py-1 bg-gray-900 text-white text-sm rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity"
                initial={{ opacity: 0, x: 10 }}
                whileHover={{ opacity: 1, x: 0 }}
              >
                {action.label}
                <div className="absolute top-1/2 -right-1 w-2 h-2 bg-gray-900 rotate-45 transform -translate-y-1/2" />
              </motion.div>
            </motion.button>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* 主按钮 */}
      <motion.button
        className={`${sizeClasses[size]} bg-gradient-to-r from-blue-500 to-purple-600 rounded-full shadow-lg flex items-center justify-center text-white relative overflow-hidden`}
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        animate={{ rotate: isOpen ? 45 : 0 }}
        transition={{ duration: 0.3 }}
      >
        {/* 背景光效 */}
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-cyan-400/20 to-blue-500/20 rounded-full"
          animate={{
            opacity: [0.3, 0.6, 0.3],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        
        {/* 图标 */}
        <div className="relative z-10">
          <AnimatePresence mode="wait">
            {isOpen ? (
              <motion.div
                key="close"
                initial={{ opacity: 0, rotate: -90 }}
                animate={{ opacity: 1, rotate: 0 }}
                exit={{ opacity: 0, rotate: 90 }}
                transition={{ duration: 0.2 }}
              >
                <X size={iconSizes[size]} />
              </motion.div>
            ) : (
              <motion.div
                key="plus"
                initial={{ opacity: 0, rotate: 90 }}
                animate={{ opacity: 1, rotate: 0 }}
                exit={{ opacity: 0, rotate: -90 }}
                transition={{ duration: 0.2 }}
              >
                <Plus size={iconSizes[size]} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* 涟漪效果 */}
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-white/30"
          animate={{
            scale: [1, 1.5, 1],
            opacity: [0.5, 0, 0.5],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </motion.button>
    </div>
  );
};

export default FloatingActionButton;