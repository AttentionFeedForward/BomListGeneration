import React from 'react';
import { motion } from 'framer-motion';

export interface LoadingProps {
  type?: 'spinner' | 'dots' | 'pulse' | 'circuit' | 'matrix';
  size?: 'sm' | 'md' | 'lg';
  color?: 'blue' | 'cyan' | 'purple' | 'green';
  text?: string;
  overlay?: boolean;
  className?: string;
}

const Loading: React.FC<LoadingProps> = ({
  type = 'spinner',
  size = 'md',
  color = 'blue',
  text,
  overlay = false,
  className = ''
}) => {
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  const colorClasses = {
    blue: 'text-blue-400',
    cyan: 'text-cyan-400',
    purple: 'text-purple-400',
    green: 'text-green-400'
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };

  // 旋转加载器
  const SpinnerLoader = () => (
    <motion.div
      className={`${sizeClasses[size]} border-2 border-gray-600 border-t-current rounded-full ${colorClasses[color]}`}
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
    />
  );

  // 点状加载器
  const DotsLoader = () => (
    <div className="flex space-x-1">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className={`w-2 h-2 rounded-full ${colorClasses[color].replace('text-', 'bg-')}`}
          animate={{
            scale: [1, 1.5, 1],
            opacity: [0.5, 1, 0.5]
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            delay: i * 0.2
          }}
        />
      ))}
    </div>
  );

  // 脉冲加载器
  const PulseLoader = () => (
    <motion.div
      className={`${sizeClasses[size]} rounded-full ${colorClasses[color].replace('text-', 'bg-')}`}
      animate={{
        scale: [1, 1.2, 1],
        opacity: [0.7, 1, 0.7]
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        ease: "easeInOut"
      }}
    />
  );

  // 电路加载器
  const CircuitLoader = () => (
    <div className={`${sizeClasses[size]} relative`}>
      <motion.div
        className={`absolute inset-0 border-2 border-dashed ${colorClasses[color].replace('text-', 'border-')} rounded-lg`}
        animate={{ rotate: 360 }}
        transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        className={`absolute top-1/2 left-1/2 w-1 h-1 ${colorClasses[color].replace('text-', 'bg-')} rounded-full`}
        style={{ transform: 'translate(-50%, -50%)' }}
        animate={{
          scale: [1, 2, 1],
          opacity: [0.5, 1, 0.5]
        }}
        transition={{
          duration: 1,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      {/* 装饰性线条 */}
      <motion.div
        className={`absolute top-0 left-1/2 w-px h-2 ${colorClasses[color].replace('text-', 'bg-')}`}
        style={{ transform: 'translateX(-50%)' }}
        animate={{ opacity: [0, 1, 0] }}
        transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
      />
      <motion.div
        className={`absolute bottom-0 left-1/2 w-px h-2 ${colorClasses[color].replace('text-', 'bg-')}`}
        style={{ transform: 'translateX(-50%)' }}
        animate={{ opacity: [0, 1, 0] }}
        transition={{ duration: 2, repeat: Infinity, delay: 1 }}
      />
    </div>
  );

  // 矩阵加载器
  const MatrixLoader = () => (
    <div className="grid grid-cols-3 gap-1">
      {[...Array(9)].map((_, i) => (
        <motion.div
          key={i}
          className={`w-2 h-2 ${colorClasses[color].replace('text-', 'bg-')} rounded-sm`}
          animate={{
            opacity: [0.3, 1, 0.3],
            scale: [0.8, 1, 0.8]
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            delay: i * 0.1
          }}
        />
      ))}
    </div>
  );

  const loaders = {
    spinner: SpinnerLoader,
    dots: DotsLoader,
    pulse: PulseLoader,
    circuit: CircuitLoader,
    matrix: MatrixLoader
  };

  const LoaderComponent = loaders[type];

  const content = (
    <div className={`flex flex-col items-center justify-center space-y-4 ${className}`}>
      <LoaderComponent />
      {text && (
        <motion.p
          className={`${textSizeClasses[size]} ${colorClasses[color]} font-medium`}
          animate={{ opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          {text}
        </motion.p>
      )}
    </div>
  );

  if (overlay) {
    return (
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <motion.div
          className="p-8 rounded-2xl bg-gray-900/90 border border-gray-700/50 backdrop-blur-md"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          {content}
        </motion.div>
      </motion.div>
    );
  }

  return content;
};

// 页面级加载组件
export const PageLoading: React.FC<{ text?: string }> = ({ text = "加载中..." }) => (
  <div className="min-h-screen flex items-center justify-center bg-gray-900">
    <Loading type="circuit" size="lg" color="cyan" text={text} />
  </div>
);

// 按钮内加载组件
export const ButtonLoading: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'sm' }) => (
  <Loading type="spinner" size={size} color="blue" />
);

// 卡片加载骨架
export const CardSkeleton: React.FC = () => (
  <div className="animate-pulse">
    <div className="bg-gray-700/50 h-4 rounded mb-2"></div>
    <div className="bg-gray-700/50 h-4 rounded w-3/4 mb-2"></div>
    <div className="bg-gray-700/50 h-4 rounded w-1/2"></div>
  </div>
);

export default Loading;