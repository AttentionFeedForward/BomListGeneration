import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { animations } from '../../utils/animations';

interface PageTransitionProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'fade' | 'slide' | 'scale';
}

const PageTransition: React.FC<PageTransitionProps> = ({
  children,
  className = '',
  variant = 'fade'
}) => {
  const getVariant = () => {
    switch (variant) {
      case 'slide':
        return animations.slideInUp;
      case 'scale':
        return animations.scaleIn;
      default:
        return animations.fadeIn;
    }
  };

  return (
    <motion.div
      className={`w-full h-full ${className}`}
      {...getVariant()}
    >
      {children}
    </motion.div>
  );
};

export default PageTransition;