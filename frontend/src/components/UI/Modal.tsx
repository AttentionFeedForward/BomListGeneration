import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  variant?: 'default' | 'glass' | 'neon';
  showCloseButton?: boolean;
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  className?: string;
}

const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  variant = 'default',
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  className = ''
}) => {
  // 处理 ESC 键关闭
  useEffect(() => {
    if (!closeOnEscape) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose, closeOnEscape]);

  // 防止背景滚动
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-[95vw] max-h-[95vh]'
  };

  const variantClasses = {
    default: 'bg-gray-900/95 border-gray-700/50',
    glass: 'bg-gray-900/30 backdrop-blur-xl border-white/10',
    neon: 'bg-gray-900/90 border-cyan-400/50 shadow-cyan-400/20'
  };

  const overlayVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 }
  };

  const modalVariants = {
    hidden: {
      opacity: 0,
      scale: 0.8,
      y: 50
    },
    visible: {
      opacity: 1,
      scale: 1,
      y: 0
    },
    exit: {
      opacity: 0,
      scale: 0.8,
      y: 50
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* 背景遮罩 */}
          <motion.div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            variants={overlayVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            onClick={closeOnOverlayClick ? onClose : undefined}
          />

          {/* 模态框内容 */}
          <motion.div
            className={`
              relative w-full ${sizeClasses[size]} max-h-[90vh] overflow-hidden
              rounded-2xl border ${variantClasses[variant]}
              shadow-2xl ${variant === 'neon' ? 'shadow-cyan-400/20' : ''}
              ${className}
            `}
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={{
              type: "spring",
              damping: 25,
              stiffness: 300
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* 背景光效 */}
            {variant === 'neon' && (
              <motion.div
                className="absolute inset-0 bg-gradient-to-br from-cyan-400/5 via-transparent to-blue-500/5 rounded-2xl"
                animate={{
                  opacity: [0.3, 0.6, 0.3],
                }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              />
            )}

            {/* 头部 */}
            {(title || showCloseButton) && (
              <motion.div
                className="relative flex items-center justify-between p-6 border-b border-gray-700/50"
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                {title && (
                  <h2 className="text-xl font-semibold text-white">
                    {title}
                  </h2>
                )}
                
                {showCloseButton && (
                  <motion.button
                    onClick={onClose}
                    className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                  >
                    <X size={20} className="text-gray-400 hover:text-white" />
                  </motion.button>
                )}
              </motion.div>
            )}

            {/* 内容区域 */}
            <motion.div
              className="relative p-6 overflow-y-auto max-h-[calc(90vh-8rem)]"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              {children}
            </motion.div>

            {/* 装饰性元素 */}
            <div className="absolute top-4 right-16 w-2 h-2 bg-blue-400/50 rounded-full animate-pulse" />
            <div className="absolute bottom-4 left-4 w-1 h-1 bg-cyan-400/50 rounded-full animate-pulse" style={{ animationDelay: '1s' }} />
            
            {/* 边框光效 */}
            {variant === 'neon' && (
              <motion.div
                className="absolute inset-0 rounded-2xl border border-cyan-400/30"
                animate={{
                  boxShadow: [
                    '0 0 20px rgba(34, 211, 238, 0.1)',
                    '0 0 40px rgba(34, 211, 238, 0.2)',
                    '0 0 20px rgba(34, 211, 238, 0.1)'
                  ]
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              />
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default Modal;