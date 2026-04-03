import React from 'react';
import { motion } from 'framer-motion';

export interface ProgressBarProps {
  value: number; // 0-100
  max?: number;
  label?: string;
  showPercentage?: boolean;
  variant?: 'default' | 'gradient' | 'neon';
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
  className?: string;
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  label,
  showPercentage = true,
  variant = 'default',
  size = 'md',
  animated = true,
  className = ''
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const sizeClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4'
  };

  const variantClasses = {
    default: 'bg-gradient-to-r from-blue-500 to-blue-600',
    gradient: 'bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500',
    neon: 'bg-gradient-to-r from-cyan-400 to-blue-500'
  };

  return (
    <div className={`w-full ${className}`}>
      {/* 标签和百分比 */}
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-2">
          {label && (
            <motion.span
              className="text-sm font-medium text-gray-300"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
            >
              {label}
            </motion.span>
          )}
          {showPercentage && (
            <motion.span
              className="text-sm font-medium text-blue-400"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
            >
              {Math.round(percentage)}%
            </motion.span>
          )}
        </div>
      )}

      {/* 进度条容器 */}
      <div className={`relative w-full ${sizeClasses[size]} bg-gray-700/50 rounded-full overflow-hidden backdrop-blur-sm`}>
        {/* 背景光效 */}
        {variant === 'neon' && (
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
        )}

        {/* 进度条 */}
        <motion.div
          className={`relative h-full ${variantClasses[variant]} rounded-full`}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{
            duration: animated ? 1.5 : 0,
            ease: "easeOut"
          }}
        >
          {/* 光泽效果 */}
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-full"
            animate={{
              x: ['-100%', '100%']
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />

          {/* 脉冲效果 */}
          {animated && percentage > 0 && (
            <motion.div
              className="absolute right-0 top-0 bottom-0 w-4 bg-white/30 rounded-full blur-sm"
              animate={{
                opacity: [0.5, 1, 0.5],
                scale: [1, 1.2, 1]
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            />
          )}
        </motion.div>

        {/* 刻度线 */}
        <div className="absolute inset-0 flex justify-between items-center px-1">
          {[...Array(11)].map((_, i) => (
            <div
              key={i}
              className="w-px h-1/2 bg-white/10"
              style={{ opacity: i % 5 === 0 ? 1 : 0.5 }}
            />
          ))}
        </div>
      </div>

      {/* 数值显示 */}
      {max !== 100 && (
        <motion.div
          className="mt-1 text-xs text-gray-400 text-center"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          {value} / {max}
        </motion.div>
      )}
    </div>
  );
};

export default ProgressBar;