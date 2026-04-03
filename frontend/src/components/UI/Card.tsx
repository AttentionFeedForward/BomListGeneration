import React from 'react';
import { motion } from 'framer-motion';

export interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  variant?: 'default' | 'gradient' | 'neon' | 'glass';
  hover?: boolean;
  className?: string;
  onClick?: () => void;
}

const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  variant = 'default',
  hover = true,
  className = '',
  onClick
}) => {
  const baseClasses = 'relative rounded-xl border transition-all duration-300';
  
  const variantClasses = {
    default: 'glass-effect border-white/20 hover:border-white/30',
    gradient: 'bg-gradient-to-br from-blue-500/10 to-purple-600/10 border-blue-500/30 hover:border-blue-400/50',
    neon: 'glass-effect border-cyan-400/30 hover:border-cyan-400/60 hover:shadow-cyan-400/20 hover:shadow-lg',
    glass: 'bg-gray-900/30 backdrop-blur-md border-white/10 hover:border-white/20'
  };

  const combinedClasses = `${baseClasses} ${variantClasses[variant]} ${onClick ? 'cursor-pointer' : ''} ${className}`;

  return (
    <motion.div
      className={combinedClasses}
      onClick={onClick}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      whileHover={hover ? { y: -5, scale: 1.02 } : {}}
      whileTap={onClick ? { scale: 0.98 } : {}}
    >
      {/* 背景光效 */}
      {variant === 'neon' && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-cyan-400/5 to-blue-500/5 rounded-xl"
          animate={{
            opacity: [0.3, 0.6, 0.3],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      )}

      {/* 边框光效 */}
      {variant === 'gradient' && (
        <motion.div
          className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-600/20 blur-sm"
          animate={{
            opacity: [0.4, 0.7, 0.4],
            scale: [1, 1.02, 1]
          }}
          transition={{
            duration: 2.5,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      )}

      <div className="relative p-6">
        {/* 标题区域 */}
        {(title || subtitle) && (
          <div className="mb-4">
            {title && (
              <motion.h3
                className="text-lg font-semibold text-white mb-1"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
              >
                {title}
              </motion.h3>
            )}
            {subtitle && (
              <motion.p
                className="text-sm text-gray-400"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                {subtitle}
              </motion.p>
            )}
          </div>
        )}

        {/* 内容区域 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          {children}
        </motion.div>
      </div>

      {/* 悬浮时的光晕效果 */}
      <motion.div
        className="absolute inset-0 rounded-xl bg-white/5 opacity-0 pointer-events-none"
        whileHover={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      />

      {/* 角落装饰 */}
      <div className="absolute top-2 right-2 w-2 h-2 bg-blue-400/50 rounded-full animate-pulse" />
      <div className="absolute bottom-2 left-2 w-1 h-1 bg-purple-400/50 rounded-full animate-pulse" style={{ animationDelay: '1s' }} />
    </motion.div>
  );
};

export default Card;