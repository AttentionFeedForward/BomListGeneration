import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react';

export interface ToastProps {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  onClose: (id: string) => void;
}

interface ToastContainerProps {
  toasts: ToastProps[];
  onClose: (id: string) => void;
}

const Toast: React.FC<ToastProps & { onClose: (id: string) => void }> = ({
  id,
  type,
  title,
  message,
  onClose
}) => {
  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertCircle,
    info: Info
  };

  const colors = {
    success: {
      bg: 'from-green-500/20 to-emerald-600/20',
      border: 'border-green-400/50',
      icon: 'text-green-400',
      glow: 'shadow-green-400/20'
    },
    error: {
      bg: 'from-red-500/20 to-red-600/20',
      border: 'border-red-400/50',
      icon: 'text-red-400',
      glow: 'shadow-red-400/20'
    },
    warning: {
      bg: 'from-yellow-500/20 to-orange-600/20',
      border: 'border-yellow-400/50',
      icon: 'text-yellow-400',
      glow: 'shadow-yellow-400/20'
    },
    info: {
      bg: 'from-blue-500/20 to-cyan-600/20',
      border: 'border-blue-400/50',
      icon: 'text-blue-400',
      glow: 'shadow-blue-400/20'
    }
  };

  const Icon = icons[type];
  const colorScheme = colors[type];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 300, scale: 0.8 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 300, scale: 0.8 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={`
        relative max-w-sm w-full glass-effect rounded-xl border ${colorScheme.border}
        bg-gradient-to-r ${colorScheme.bg} backdrop-blur-md
        shadow-lg ${colorScheme.glow} hover:shadow-xl
        transform transition-all duration-300
      `}
    >
      {/* 背景光效 */}
      <motion.div
        className={`absolute inset-0 bg-gradient-to-r ${colorScheme.bg} rounded-xl opacity-50`}
        animate={{
          opacity: [0.3, 0.6, 0.3],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />

      <div className="relative p-4">
        <div className="flex items-start space-x-3">
          {/* 图标 */}
          <motion.div
            className={`flex-shrink-0 ${colorScheme.icon}`}
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 0.2, duration: 0.5, ease: "easeOut" }}
          >
            <Icon size={20} />
          </motion.div>

          {/* 内容 */}
          <div className="flex-1 min-w-0">
            <motion.h4
              className="text-sm font-semibold text-white"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              {title}
            </motion.h4>
            {message && (
              <motion.p
                className="mt-1 text-sm text-gray-300"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                {message}
              </motion.p>
            )}
          </div>

          {/* 关闭按钮 */}
          <motion.button
            onClick={() => onClose(id)}
            className="flex-shrink-0 p-1 rounded-lg hover:bg-white/10 transition-colors"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <X size={16} className="text-gray-400 hover:text-white" />
          </motion.button>
        </div>

        {/* 进度条 */}
        <motion.div
          className="absolute bottom-0 left-0 right-0 h-1 bg-white/10 rounded-b-xl overflow-hidden"
        >
          <motion.div
            className={`h-full bg-gradient-to-r ${colorScheme.bg.replace('/20', '/60')}`}
            initial={{ width: '100%' }}
            animate={{ width: '0%' }}
            transition={{ duration: 5, ease: "linear" }}
            onAnimationComplete={() => onClose(id)}
          />
        </motion.div>
      </div>

      {/* 装饰性元素 */}
      <div className={`absolute top-2 right-8 w-1 h-1 ${colorScheme.icon} rounded-full animate-pulse`} />
      <div className={`absolute bottom-2 left-2 w-0.5 h-0.5 ${colorScheme.icon} rounded-full animate-pulse`} style={{ animationDelay: '1s' }} />
    </motion.div>
  );
};

const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onClose }) => {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-3">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <Toast key={toast.id} {...toast} onClose={onClose} />
        ))}
      </AnimatePresence>
    </div>
  );
};

// Hook for managing toasts
export const useToast = () => {
  const [toasts, setToasts] = React.useState<ToastProps[]>([]);

  const addToast = (toast: Omit<ToastProps, 'id' | 'onClose'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { ...toast, id, onClose: removeToast }]);
  };

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };

  const ToastProvider = () => (
    <ToastContainer toasts={toasts} onClose={removeToast} />
  );

  return {
    addToast,
    removeToast,
    ToastProvider
  };
};

export default Toast;