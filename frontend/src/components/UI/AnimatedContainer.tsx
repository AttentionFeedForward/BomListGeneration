import React from 'react';
import { motion } from 'framer-motion';
import { staggerChildren } from '../../utils/animations';

interface AnimatedContainerProps {
  children: React.ReactNode;
  className?: string;
  staggerDelay?: number;
  direction?: 'vertical' | 'horizontal';
}

const AnimatedContainer: React.FC<AnimatedContainerProps> = ({
  children,
  className = '',
  staggerDelay = 0.1,
  direction = 'vertical'
}) => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: staggerDelay,
        delayChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: {
      opacity: 0,
      y: direction === 'vertical' ? 20 : 0,
      x: direction === 'horizontal' ? 20 : 0
    },
    visible: {
      opacity: 1,
      y: 0,
      x: 0,
      transition: {
        duration: 0.5
      }
    }
  };

  return (
    <motion.div
      className={className}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {React.Children.map(children, (child, index) => (
        <motion.div key={index} variants={itemVariants}>
          {child}
        </motion.div>
      ))}
    </motion.div>
  );
};

export default AnimatedContainer;